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
    if result.returncode != 0:
        return f"[git error: {result.stderr.strip() or 'unknown'}]"
    return (result.stdout or "").strip()


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-") or "checkpoint"


def detect_agent(explicit: str | None) -> str:
    if explicit:
        return explicit
    import os

    for key in ("AGENT_NAME", "AI_AGENT", "CODING_AGENT"):
        value = os.environ.get(key)
        if value:
            return value
    if os.environ.get("CODEX_HOME"):
        return "codex"
    if os.environ.get("CLAUDECODE") or os.environ.get("CLAUDE_CODE"):
        return "claude-code"
    if os.environ.get("OPENCODE") or os.environ.get("OPENCODE_HOME"):
        return "opencode"
    return "unknown-agent"


def build_content(
    *,
    title: str,
    created_at: str,
    branch: str,
    working_tree: str,
    recent_commits: str,
    agent: str,
) -> str:
    git_state = "clean" if working_tree == "[clean]" else "dirty"
    return f"""---
title: {title}
created_at: {created_at}
checkpoint_schema: agent-handoff/v1
checkpoint_scope: repo
checkpoint_dir: .agents/checkpoints
created_by: {agent}
compatible_agents: codex, claude-code, opencode, generic
branch: {branch}
git_state: {git_state}
---

# {title}

## Agent Handoff
- Created by: {agent}
- Checkpoint protocol: `agent-handoff/v1`
- Shared checkpoint directory: `.agents/checkpoints/`
- Compatible agents: Codex/OpenAI CLI, Claude Code, opencode, and generic programming agents.
- Resume rule: trust this file over hidden chat memory; verify git state before editing.

## Session Goal
- TODO: What to accomplish this session and the definition of done.

## Current State
- Working tree: `{git_state}`
- TODO: Where things stand — what is landed, what is still in progress.

## Key Chat Context
- User goal: TODO
- Explicit constraints / do-not-do: TODO
- Scope changes or corrections: TODO
- Rejected paths to avoid rediscovering: TODO
- Exact wording worth preserving: TODO

## Files In Play
- TODO: List the files, docs, scripts, and data paths that matter.

## Verification
- TODO: Tests / acceptance checks / manual tests already run.
- TODO: Explicitly note what has NOT been verified yet.

## Next Step
1. TODO: First thing to do when resuming.
2. TODO: Second thing.
3. TODO: Blockers or assumptions to watch for.

## Resume Recipe
- Run `python3 ~/.agents/skills/repo-resume/scripts/resume_snapshot.py`
- If using Claude Code or opencode, run the same command from this repository root.
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
    parser.add_argument("--version", action="version", version="repo-checkpoint 0.3.0")
    parser.add_argument("--title", default="progress-checkpoint", help="Short title for the checkpoint filename and header.")
    parser.add_argument("--agent", default=None, help="Agent name for cross-agent handoff metadata, e.g. codex, claude-code, opencode.")
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
            agent=detect_agent(args.agent),
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
