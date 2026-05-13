#!/usr/bin/env python3
from __future__ import annotations

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


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            metadata: dict[str, str] = {}
            for line in lines[1:index]:
                if ":" not in line:
                    continue
                key, value = line.split(":", 1)
                metadata[key.strip()] = value.strip()
            return metadata, "\n".join(lines[index + 1 :]).strip()
    return {}, text


def extract_section(text: str, heading: str) -> str:
    lines = text.splitlines()
    target = f"## {heading}"
    start = -1
    for index, line in enumerate(lines):
        if line.strip() == target:
            start = index + 1
            break
    if start == -1:
        return ""
    collected: list[str] = []
    for index in range(start, len(lines)):
        line = lines[index]
        if line.startswith("## "):
            break
        collected.append(line)
    return "\n".join(collected).strip()


def load_latest_checkpoint(root: Path) -> dict[str, str] | None:
    checkpoint_dir = root / ".agents" / "checkpoints"
    files = sorted(checkpoint_dir.glob("*.md"), reverse=True) if checkpoint_dir.exists() else []
    if not files:
        return None
    latest = files[0]
    metadata, body = parse_frontmatter(latest.read_text(encoding="utf-8"))
    return {
        "path": str(latest.relative_to(root)),
        "title": metadata.get("title") or latest.stem,
        "created_at": metadata.get("created_at") or "[unknown]",
        "branch": metadata.get("branch") or "[unknown]",
        "session_goal": extract_section(body, "Session Goal"),
        "current_state": extract_section(body, "Current State"),
        "key_chat_context": extract_section(body, "Key Chat Context"),
        "files_in_play": extract_section(body, "Files In Play"),
        "verification": extract_section(body, "Verification"),
        "next_step": extract_section(body, "Next Step"),
    }


def read_project_status_top(root: Path) -> str:
    path = root / "PROJECT_STATUS.md"
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8")
    marker = "## 最近一次更新（固定模板)"
    start = text.find(marker)
    if start == -1:
        return ""
    tl_dr = text.find("\n## TL;DR", start)
    return text[start:tl_dr].strip() if tl_dr != -1 else text[start:].strip()


def main() -> int:
    root = repo_root()
    branch = run_git(root, "branch", "--show-current") or "[unknown]"
    working_tree = run_git(root, "status", "--short") or "[clean]"
    recent_commits = run_git(root, "log", "--oneline", "-5") or "[no commits]"
    checkpoint = load_latest_checkpoint(root)
    project_status = read_project_status_top(root)

    print("# Repo Resume Snapshot")
    print()
    print(f"- Repo: `{root}`")
    print(f"- Branch: `{branch}`")
    print()

    if checkpoint:
        print("## Latest Repo Checkpoint")
        print(f"- File: `{checkpoint['path']}`")
        print(f"- Title: `{checkpoint['title']}`")
        print(f"- Saved: `{checkpoint['created_at']}`")
        print(f"- Branch: `{checkpoint['branch']}`")
        print()
        for label, key in [
            ("Session Goal", "session_goal"),
            ("Current State", "current_state"),
            ("Key Chat Context", "key_chat_context"),
            ("Files In Play", "files_in_play"),
            ("Verification", "verification"),
            ("Next Step", "next_step"),
        ]:
            if checkpoint[key]:
                print(f"### {label}")
                print(checkpoint[key])
                print()
    else:
        print("## Latest Repo Checkpoint")
        print("- None found under `.agents/checkpoints/`")
        print()

    if project_status:
        print("## PROJECT_STATUS.md Top Block")
        print(project_status)
        print()

    print("## Working Tree")
    print("```text")
    print(working_tree)
    print("```")
    print()
    print("## Recent Commits")
    print("```text")
    print(recent_commits)
    print("```")
    return 0


if __name__ == "__main__":
    sys.exit(main())
