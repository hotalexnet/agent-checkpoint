#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
from pathlib import Path


def repo_root() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=False,
        capture_output=True,
        text=True,
    )
    root = (result.stdout or "").strip()
    if result.returncode != 0 or not root:
        raise SystemExit("Not inside a git repository.")
    return Path(root)


def run_git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    return (result.stdout or result.stderr or "").strip()


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-") or "checkpoint"


def build_content(*, title: str, created_at: str, branch: str, working_tree: str, recent_commits: str) -> str:
    git_state = "clean" if working_tree == "[clean]" else "dirty"
    return f"""---
title: {title}
created_at: {created_at}
branch: {branch}
git_state: {git_state}
---

# {title}

## Session Goal
- TODO: 这轮要完成什么，完成到什么算结束。

## Current State
- Working tree: `{git_state}`
- TODO: 当前已经做到哪一步，哪些改动已落地，哪些还在半路。

## Key Chat Context
- User goal: TODO
- Explicit constraints / do-not-do: TODO
- Scope changes or corrections: TODO
- Rejected paths to avoid rediscovering: TODO
- Exact wording worth preserving: TODO

## Files In Play
- TODO: 列出真正相关的代码、文档、脚本、数据路径。

## Verification
- TODO: 已运行的测试 / 验收 / 手测。
- TODO: 明确写未验证项，不要假装已经验证。

## Next Step
1. TODO: 下次继续时第一步先做什么。
2. TODO: 第二步做什么。
3. TODO: blocker / assumption 是什么。

## Resume Recipe
- Run `python3 ~/.agents/skills/repo-resume/scripts/resume_snapshot.py`
- Read the files listed above.

## Git Snapshot

### Working Tree
```text
{working_tree}
```

### Recent Commits
```text
{recent_commits}
```
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a repo-local checkpoint scaffold.")
    parser.add_argument("--title", default="progress-checkpoint", help="Short title for the checkpoint filename and header.")
    args = parser.parse_args()

    root = repo_root()
    branch = run_git(root, "branch", "--show-current") or "[unknown]"
    working_tree = run_git(root, "status", "--short") or "[clean]"
    recent_commits = run_git(root, "log", "--oneline", "-5") or "[no commits]"

    checkpoint_dir = root / ".agents" / "checkpoints"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    now = dt.datetime.now().astimezone()
    stamp = now.strftime("%Y%m%d-%H%M%S")
    path = checkpoint_dir / f"{stamp}-{slugify(args.title)}.md"
    path.write_text(
        build_content(
            title=args.title,
            created_at=now.strftime("%Y-%m-%d %H:%M:%S %z"),
            branch=branch,
            working_tree=working_tree,
            recent_commits=recent_commits,
        ),
        encoding="utf-8",
    )

    print(path)
    print()
    print("Created repo-local checkpoint scaffold.")
    print("Replace every TODO before ending the session.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
