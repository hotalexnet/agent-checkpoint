#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from redact import redact_text


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


def reserve_checkpoint_path(checkpoint_dir: Path, stamp: str, title: str) -> Path:
    """Reserve a unique checkpoint path without overwriting another snapshot."""
    slug = slugify(title)
    for counter in range(1000):
        suffix = "" if counter == 0 else f"-{counter}"
        path = checkpoint_dir / f"{stamp}-{slug}{suffix}.md"
        try:
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        except FileExistsError:
            continue
        os.close(fd)
        return path
    raise RuntimeError("Could not allocate a unique checkpoint filename")


def atomic_write(path: Path, content: str) -> None:
    """Write a checkpoint completely before replacing the destination."""
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(content)
    os.chmod(temporary, 0o644)
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def build_content(
    *,
    title: str,
    created_at: str,
    branch: str,
    working_tree: str,
    recent_commits: str,
    agent: str,
    base_commit: str,
    expires_at: str,
    current: bool,
) -> str:
    git_state = "clean" if working_tree == "[clean]" else "dirty"
    return f"""---
title: {title}
created_at: {created_at}
expires_at: {expires_at}
checkpoint_schema: agent-handoff/v1
checkpoint_scope: repo
checkpoint_dir: .agents/checkpoints
created_by: {agent}
compatible_agents: codex, claude-code, opencode, generic
branch: {branch}
base_commit: {base_commit}
checkpoint_kind: {"current" if current else "snapshot"}
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
    parser.add_argument("--version", action="version", version="repo-checkpoint 0.4.0")
    parser.add_argument("--title", default="progress-checkpoint", help="Short title for the checkpoint filename and header.")
    parser.add_argument("--agent", default=None, help="Agent name for cross-agent handoff metadata, e.g. codex, claude-code, opencode.")
    parser.add_argument("--current", action="store_true", help="Update .agents/checkpoints/current.md instead of creating a timestamped snapshot.")
    parser.add_argument("--expires-in", type=int, default=30, metavar="DAYS", help="Days until the checkpoint is marked stale (default: 30). Use 0 to disable.")
    args = parser.parse_args()

    root = repo_root()
    branch = run_git(root, "branch", "--show-current") or "[unknown]"
    working_tree = run_git(root, "status", "--short") or "[clean]"
    recent_commits = run_git(root, "log", "--oneline", "-5") or "[no commits]"
    base_commit = run_git(root, "rev-parse", "HEAD") or "[unknown]"

    checkpoint_dir = root / ".agents" / "checkpoints"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    now = dt.datetime.now().astimezone()
    stamp = now.strftime("%Y%m%d-%H%M%S")
    if args.expires_in < 0:
        parser.error("--expires-in must be zero or greater")
    expires_at = "never" if args.expires_in == 0 else (now + dt.timedelta(days=args.expires_in)).strftime("%Y-%m-%d %H:%M:%S %z")
    title = redact_text(" ".join(args.title.splitlines())).strip() or "checkpoint"
    path = checkpoint_dir / "current.md" if args.current else reserve_checkpoint_path(checkpoint_dir, stamp, title)
    content = build_content(
        title=title,
        created_at=now.strftime("%Y-%m-%d %H:%M:%S %z"),
        expires_at=expires_at,
        branch=redact_text(branch),
        working_tree=redact_text(working_tree),
        recent_commits=redact_text(recent_commits),
        agent=redact_text(detect_agent(args.agent)),
        base_commit=base_commit,
        current=args.current,
    )
    atomic_write(path, content)

    print(path)
    print()
    print("Created repo-local checkpoint scaffold.")
    print("Replace every TODO before ending the session.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
