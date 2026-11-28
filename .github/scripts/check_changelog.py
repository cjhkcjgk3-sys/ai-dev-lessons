"""Check traceability, not truth or reviewer identity. Standard library only."""
import os
import re
import subprocess
import sys


def git(*args):
    return subprocess.check_output(["git", *args], text=True, encoding="utf-8")


def exists(commit):
    return subprocess.run(["git", "cat-file", "-e", f"{commit}^{{commit}}"],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0


def read_log(commit):
    return git("show", f"{commit}:CHANGELOG.md")


def entries(old, new):
    """Existing lines must remain in order; return contiguous inserted blocks."""
    previous = old.splitlines()
    i = 0
    blocks = []
    pending = []
    for line in new.splitlines():
        if i < len(previous) and line == previous[i]:
            if pending:
                blocks.append(pending)
                pending = []
            i += 1
        else:
            pending.append(line)
    if pending:
        blocks.append(pending)
    if i != len(previous):
        raise ValueError("旧日志被删除或改写；请用新增条目更正")
    return blocks


FIELDS = ("更新人", "修改范围", "修改原因", "修改内容", "核验状态")
HEADER = re.compile(r"^## (?:\d{4}-\d{2}-\d{2}｜\S.*|\S+（\d{4}-\d{2}-\d{2}）)\s*$")


def validate_log(old, new):
    for block in entries(old, new):
        sections = re.split(r"(?m)(?=^## )", "\n".join(block))
        for section in sections:
            lines = section.splitlines()
            if not lines or not HEADER.match(lines[0]):
                continue
            if all(any(re.match(r"^" + f + r"：\s*\S", line) for line in lines[1:])
                   for f in FIELDS):
                return
    raise ValueError("缺少新增日志条目或日期、修改者、范围、原因、内容、核验状态字段")


def main():
    event = os.environ.get("EVENT")
    head = os.environ["PR_HEAD"] if event == "pull_request" else os.environ["AFTER"]
    before = os.environ.get("PR_BASE") if event == "pull_request" else os.environ.get("BEFORE")
    if not before or not exists(before):
        commits = [head]
    else:
        # On pushes audit mainline commits, including merge result against first parent.
        # On PRs check commits introduced by the PR, excluding merges of base history.
        mode = "--no-merges" if event == "pull_request" else "--first-parent"
        commits = git("rev-list", "--reverse", mode, f"{before}..{head}").splitlines()
    failures = []
    for commit in commits:
        parents = git("show", "-s", "--format=%P", commit).split()
        if not parents:
            continue
        parent = parents[0]
        if not git("diff", "--name-only", parent, commit).strip():
            continue
        try:
            validate_log(read_log(parent), read_log(commit))
        except (ValueError, subprocess.CalledProcessError) as exc:
            failures.append(f"{commit[:8]}: {exc}")
    # Also check net PR change to catch merge-only edits / overwritten history.
    if event == "pull_request" and before and exists(before):
        fork = git("merge-base", before, head).strip()
        if git("diff", "--name-only", fork, head).strip():
            try:
                validate_log(read_log(fork), read_log(head))
            except (ValueError, subprocess.CalledProcessError) as exc:
                failures.append(f"PR: {exc}")
    for failure in failures:
        print(f"::error::{failure}")
    if failures:
        return 1
    print("修改留痕检查通过（不代表内容、模型身份或共识已验证）。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
