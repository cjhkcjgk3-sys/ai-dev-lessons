from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from check_structure import check, FORMAL, PENDING, SOFTWARE, METHOD_NAME, INDEX


class StructureTests(unittest.TestCase):
    def test_valid_and_defects(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            def write(path, content=''):
                p = root / path
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(content, encoding='utf-8')
            for path in ('README.md', 'AGENTS.md', '\u603b\u7d22\u5f15.md', '\u89e6\u53d1\u4fe1\u53f7\u7d22\u5f15.md',
                         FORMAL + '/\u901a\u7528\u65b9\u6cd5.md', '\u6280\u672f\u53c2\u8003/README.md'):
                write(path)
            topic = FORMAL + '/\u666e\u9002\u7ecf\u9a8c/'
            method_dir = FORMAL + '/' + SOFTWARE + '/'
            method = METHOD_NAME + '-01.md'
            write(PENDING + '/README.md')
            write(topic + INDEX, '[experience](example.md)\n[workflow](../../' + PENDING + '/README.md)')
            write(topic + 'example.md', '# HA-01\uFF5CExample\n## Review\uFF1A\u6761\u4ef6\n## Review\uFF1A\u6761\u4ef6\n[repeat](#review\u6761\u4ef6-1)\n[template](../../template.md#steps)')
            write('template.md', '# Steps\n```md\n[example](missing.md)\n```\n`[inline example](missing.md)`\n[doc][ref]\n[ref]: ' + topic + 'example.md#review\u6761\u4ef6\n')
            write(method_dir + INDEX, '[method](' + method + '#method-01)')
            write(method_dir + method, '<a id="method-01"></a>')
            warnings = []
            write('\u6574\u7406\u8bb0\u5f55/old.md', '[old](gone.md)')
            self.assertEqual(check(root, warnings), [])
            self.assertEqual(len(warnings), 1)
            write(PENDING + '/candidate.md', 'candidate')
            write(topic + 'duplicate.md', '# HA-01\uFF5Cduplicate')
            write(topic + INDEX, '[missing](missing.md)\n[candidate](../../' + PENDING + '/candidate.md)')
            write(method_dir + method, 'no anchor')
            write('template.md', '[broken](missing.md)\n[bad heading](' + topic + 'example.md#absent)')
            errors = '\n'.join(check(root))
            for expected in ('missing or outside', 'pending entry', 'duplicate ID',
                             'missing explicit anchor', 'missing topic index entry',
                             'template.md: missing heading/anchor', 'template.md: missing or outside'):
                self.assertIn(expected, errors)


if __name__ == '__main__':
    unittest.main()
