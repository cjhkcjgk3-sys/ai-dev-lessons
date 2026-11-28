from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from check_structure import check


class StructureTests(unittest.TestCase):
    def test_valid_and_defects(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            def write(path, content=""):
                p = root / path
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(content, encoding="utf-8")
            for path in ("README.md", "AGENTS.md", "总索引.md", "触发信号索引.md",
                         "正式/通用方法.md", "技术参考/README.md"):
                write(path)
            write("待审/README.md")
            write("正式/普适经验/索引.md", "[经验](例.md)\n[流程](../../待审/README.md)")
            write("正式/普适经验/例.md", "# HA-01｜例")
            write("正式/领域经验/软件工程/索引.md", "[方法](方法-01.md#method-01)")
            write("正式/领域经验/软件工程/方法-01.md", '<a id="method-01"></a>')
            self.assertEqual(check(root), [])
            write("待审/候选.md", "candidate")
            write("正式/普适经验/重复.md", "# HA-01｜duplicate")
            write("正式/普适经验/索引.md", "[缺失](missing.md)\n[候选](../../待审/候选.md)")
            write("正式/领域经验/软件工程/方法-01.md", "no anchor")
            errors = "\n".join(check(root))
            for expected in ("missing or outside", "pending entry", "duplicate ID",
                             "missing explicit anchor", "missing topic index entry"):
                self.assertIn(expected, errors)


if __name__ == "__main__":
    unittest.main()
