#!/usr/bin/env python3
from __future__ import annotations

import argparse
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
        if re.match(r"^## ", line) and not line.strip().startswith("###"):
            break
        collected.append(line)
    return "\n".join(collected).strip()


def checkpoint_dir(root: Path) -> Path:
    return root / ".agents" / "checkpoints"


def list_checkpoints(root: Path) -> list[Path]:
    d = checkpoint_dir(root)
    if not d.exists():
        return []
    return sorted(d.glob("*.md"), reverse=True)


def load_checkpoint(path: Path, root: Path) -> dict[str, str]:
    metadata, body = parse_frontmatter(path.read_text(encoding="utf-8"))
    return {
        "path": str(path.relative_to(root)),
        "title": metadata.get("title") or path.stem,
        "created_at": metadata.get("created_at") or "[unknown]",
        "branch": metadata.get("branch") or "[unknown]",
        "session_goal": extract_section(body, "Session Goal"),
        "current_state": extract_section(body, "Current State"),
        "key_chat_context": extract_section(body, "Key Chat Context"),
        "files_in_play": extract_section(body, "Files In Play"),
        "verification": extract_section(body, "Verification"),
        "next_step": extract_section(body, "Next Step"),
    }


def load_latest_checkpoint(root: Path) -> dict[str, str] | None:
    files = list_checkpoints(root)
    if not files:
        return None
    return load_checkpoint(files[0], root)


def cmd_resume(root: Path) -> int:
    branch = run_git(root, "branch", "--show-current") or "[unknown]"
    working_tree = run_git(root, "status", "--short") or "[clean]"
    recent_commits = run_git(root, "log", "--oneline", "-5") or "[no commits]"
    checkpoint = load_latest_checkpoint(root)

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


def cmd_list(root: Path) -> int:
    files = list_checkpoints(root)
    if not files:
        print("No checkpoints found.")
        return 0

    print(f"{'Date':<22} {'Branch':<16} {'Title'}")
    print("-" * 60)
    for f in files:
        metadata, _ = parse_frontmatter(f.read_text(encoding="utf-8"))
        created = metadata.get("created_at", "[unknown]")
        branch = metadata.get("branch", "[unknown]")
        title = metadata.get("title", f.stem)
        print(f"{created:<22} {branch:<16} {title}")
    print()
    print(f"{len(files)} checkpoint(s) total.")
    return 0


def cmd_prune(root: Path, keep: int) -> int:
    if keep < 1:
        print("Error: keep must be at least 1. Use git to remove all checkpoints if needed.")
        return 1
    files = list_checkpoints(root)
    if len(files) <= keep:
        print(f"Only {len(files)} checkpoint(s) found, nothing to prune (keep={keep}).")
        return 0

    to_remove = files[keep:]
    for f in to_remove:
        f.unlink()
        print(f"Removed {f.name}")

    print(f"\nPruned {len(to_remove)} checkpoint(s), kept {keep} most recent.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Repo-local resume and checkpoint management.")
    parser.add_argument("--version", action="version", version="repo-resume 0.2.0")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("list", help="List all checkpoints with metadata.")
    prune_p = sub.add_parser("prune", help="Remove old checkpoints, keeping only the N most recent.")
    prune_p.add_argument("keep", type=int, nargs="?", default=5, help="Number of checkpoints to keep (default: 5)")

    args = parser.parse_args()
    root = repo_root()

    if args.command == "list":
        return cmd_list(root)
    if args.command == "prune":
        return cmd_prune(root, args.keep)
    return cmd_resume(root)


if __name__ == "__main__":
    sys.exit(main())
