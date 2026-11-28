"""Bounded structural checks for current experience indexes, not semantic review."""
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

LINK = re.compile(r"\]\(([^)\n]+)\)")
ID = re.compile(r"^# ((?:HA|FD|AG|RI)-\d+)(?:[｜| ]|$)", re.M)
METHOD = re.compile(r"method-(\d{2,})$")


def check(root):
    root = root.resolve()
    formal = root / "正式"
    errors = []
    indexes = [root / name for name in ("README.md", "AGENTS.md", "总索引.md", "触发信号索引.md")]
    indexes += sorted(formal.rglob("索引.md"))
    indexes += [formal / "通用方法.md", root / "技术参考/README.md"]
    for index in indexes:
        if not index.is_file():
            errors.append(f"missing index: {index.relative_to(root)}")
            continue
        for raw in LINK.findall(index.read_text(encoding="utf-8")):
            url = urlsplit(raw.strip())
            if url.scheme or url.netloc:
                continue
            target = (index.parent / unquote(url.path)).resolve() if url.path else index
            if not target.is_relative_to(root) or not target.exists():
                errors.append(f"{index.relative_to(root)}: missing or outside: {raw}")
                continue
            # Pending README is a legitimate workflow reference, pending entries are not.
            rel = target.relative_to(root)
            if index.is_relative_to(formal) and index.name == "索引.md":
                if rel.parts[0] == "待审" and target.is_file() and target.name != "README.md":
                    errors.append(f"{index.relative_to(root)}: pending entry in active index: {raw}")
            if METHOD.fullmatch(unquote(url.fragment)):
                anchor = unquote(url.fragment)
                if not target.is_file() or f'id="{anchor}"' not in target.read_text(encoding="utf-8"):
                    errors.append(f"{index.relative_to(root)}: missing explicit anchor: {raw}")
    methods = formal / "领域经验/软件工程"
    seen = {}
    for p in sorted(formal.rglob("*.md")):
        content = p.read_text(encoding="utf-8")
        ids = ID.findall(content)
        if p.parent == methods and re.fullmatch(r"方法-\d{2,}\.md", p.name):
            number = p.stem.split("-")[-1]
            ids.append("method-" + number)
            if f'id="method-{number}"' not in content:
                errors.append(f"{p.relative_to(root)}: missing method anchor")
        for key in ids:
            if key in seen:
                errors.append(f"duplicate ID {key}: {seen[key]}, {p.relative_to(root)}")
            else:
                seen[key] = p.relative_to(root)
    for key, rel in seen.items():
        parent_index = root / rel.parent / "索引.md"
        if not parent_index.is_file() or rel.name not in parent_index.read_text(encoding="utf-8"):
            errors.append(f"{key}: missing topic index entry: {rel}")
    return errors


if __name__ == "__main__":
    errors = check(Path(__file__).resolve().parents[2])
    for err in errors:
        print(f"::error::{err}")
    if errors:
        sys.exit(1)
    print("Active indexes, explicit method anchors, canonical IDs checked; no semantic claim.")
