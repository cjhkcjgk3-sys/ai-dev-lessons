"""Bounded local Markdown checks; no network or semantic review."""
from collections import Counter
from html import unescape
from pathlib import Path
import re
import sys
import unicodedata
from urllib.parse import unquote, urlsplit

FORMAL = '\u6b63\u5f0f'
PENDING = '\u5f85\u5ba1'
INDEX = '\u7d22\u5f15.md'
SOFTWARE = '\u9886\u57df\u7ecf\u9a8c/\u8f6f\u4ef6\u5de5\u7a0b'
METHOD_NAME = '\u65b9\u6cd5'
LINK = re.compile(r'(?<!\\)\]\(\s*(<[^>\n]+>|(?:[^()\n]|\([^()\n]*\))+?)\s*\)')
REF = re.compile(r'^ {0,3}\[[^\]\n]+\]:\s*(<[^>\n]+>|\S+)', re.M)
ID = re.compile(r'^# ((?:HA|FD|AG|RI)-\d+)(?:[\uFF5C| ]|$)', re.M)
METHOD = re.compile(r'method-(\d{2,})$')
FENCE = re.compile(r'^ {0,3}(`{3,}|~{3,})(.*)$')
ATX = re.compile(r'^ {0,3}#{1,6}\s+(.+?)\s*#*\s*$')
INLINE_CODE = re.compile(r'(`+)(.*?)\1')
EXPLICIT = re.compile(r'<[A-Za-z][^>]*?\b(?:id|name)\s*=\s*[\'\"]([^\'\"]+)[\'\"]', re.I)


def prose(content):
    """Remove fenced examples and HTML comments, keeping line boundaries."""
    content = re.sub(r'<!--.*?-->', '', content, flags=re.S)
    lines = []
    fence = None
    for line in content.splitlines():
        match = FENCE.match(line)
        if fence:
            if match and match[1][0] == fence[0] and len(match[1]) >= len(fence) and not match[2].strip():
                fence = None
            lines.append('')
        elif match:
            fence = match[1]
            lines.append('')
        else:
            lines.append(line)
    return '\n'.join(lines)


def anchors(content):
    """Common GitHub Markdown headings (ATX/Setext) and explicit IDs."""
    found = set(EXPLICIT.findall(content))
    used = set()
    lines = content.splitlines()
    for i, line in enumerate(lines):
        match = ATX.match(line)
        if match:
            heading = match[1]
        elif i and re.fullmatch(r' {0,3}(?:=+|-+)\s*', line) and lines[i-1].strip() and not lines[i-1].lstrip().startswith(('#', '|', '-', '>')):
            heading = lines[i-1].strip()
        else:
            continue
        heading = re.sub(r'!?\[([^\]]+)\]\([^)]*\)', r'\1', heading)
        heading = unescape(re.sub(r'<[^>]+>', '', heading)).lower()
        slug = ''.join('-' if ch == ' ' else ch for ch in heading
                       if ch in '-_ ' or not unicodedata.category(ch).startswith(('P', 'S', 'C')))
        candidate = slug
        count = 0
        while candidate in used:
            count += 1
            candidate = f'{slug}-{count}'
        used.add(candidate)
    return found | used


def destinations(content):
    content = INLINE_CODE.sub('', content)
    for match in (*LINK.finditer(content), *REF.finditer(content)):
        raw = match[1].strip()
        if raw.startswith('<') and raw.endswith('>'):
            yield raw[1:-1]
        else:
            yield re.sub(r'\s+[\'\"][^\n]*[\'\"]$', '', raw)


def historical(rel):
    return (rel.as_posix() == 'CHANGELOG.md' or rel.parts[0] == '\u6574\u7406\u8bb0\u5f55'
            or rel.parts[:2] in ((PENDING, '\u5df2\u9a73\u56de'), (FORMAL, 'cases')))


def check(root, warnings=None):
    root = root.resolve()
    formal = root / FORMAL
    errors = []
    if warnings is None:
        warnings = []
    required = [root / name for name in ('README.md', 'AGENTS.md', '\u603b\u7d22\u5f15.md', '\u89e6\u53d1\u4fe1\u53f7\u7d22\u5f15.md',
                                         FORMAL + '/\u901a\u7528\u65b9\u6cd5.md', '\u6280\u672f\u53c2\u8003/README.md')]
    for p in required:
        if not p.is_file():
            errors.append(f'missing index: {p.relative_to(root)}')
    docs = {p: prose(p.read_text(encoding='utf-8')) for p in sorted(root.rglob('*.md'))
            if '.git' not in p.relative_to(root).parts and p.is_file() and not p.is_symlink()}
    anchor_cache = {}
    for p, content in docs.items():
        rel = p.relative_to(root)
        issues = warnings if historical(rel) else errors
        for raw in destinations(content):
            url = urlsplit(raw)
            if url.scheme or url.netloc:
                continue
            path = unquote(url.path)
            if path.startswith('/'):
                target = (root / path.lstrip('/')).resolve()
            else:
                target = (p.parent / path).resolve() if path else p
            if not target.is_relative_to(root) or not target.exists():
                issues.append(f'{rel}: missing or outside: {raw}')
                continue
            target_rel = target.relative_to(root)
            active_index = (p.is_relative_to(formal) and p.name == INDEX) or rel.as_posix() in ('\u603b\u7d22\u5f15.md', '\u89e6\u53d1\u4fe1\u53f7\u7d22\u5f15.md')
            if active_index and target_rel.parts[:1] == (PENDING,) and target.is_file() and target.name != 'README.md':
                errors.append(f'{rel}: pending entry in active index: {raw}')
            fragment = unquote(url.fragment)
            if fragment and target.suffix.lower() == '.md' and target.is_file():
                if target not in anchor_cache:
                    anchor_cache[target] = anchors(docs[target] if target in docs else prose(target.read_text(encoding='utf-8')))
                if fragment not in anchor_cache[target]:
                    kind = 'missing explicit anchor' if METHOD.fullmatch(fragment) else 'missing heading/anchor'
                    issues.append(f'{rel}: {kind}: {raw}')
    methods = formal / SOFTWARE
    seen = {}
    for p, content in docs.items():
        if not p.is_relative_to(formal):
            continue
        ids = ID.findall(content)
        if p.parent == methods and re.fullmatch(METHOD_NAME + r'-\d{2,}\.md', p.name):
            number = p.stem.split('-')[-1]
            key = 'method-' + number
            ids.append(key)
            if key not in EXPLICIT.findall(content):
                errors.append(f'{p.relative_to(root)}: missing method anchor')
        for key in ids:
            if key in seen:
                errors.append(f'duplicate ID {key}: {seen[key]}, {p.relative_to(root)}')
            else:
                seen[key] = p.relative_to(root)
    for key, rel in seen.items():
        parent_index = root / rel.parent / INDEX
        if not parent_index.is_file() or rel.name not in docs.get(parent_index, ''):
            errors.append(f'{key}: missing topic index entry: {rel}')
    return errors


if __name__ == '__main__':
    warnings = []
    errors = check(Path(__file__).resolve().parents[2], warnings)
    for item in warnings[:10]:
        print(f'::warning::historical reference: {item}')
    if len(warnings) > 10:
        print(f'{len(warnings) - 10} more historical reference warnings')
    for err in errors:
        print(f'::error::{err}')
    if errors:
        sys.exit(1)
    print(f'Local Markdown links, supported headings/anchors and canonical IDs checked; {len(warnings)} historical warnings; no semantic claim.')
