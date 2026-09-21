#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
from pathlib import Path

from redact import contains_secret

REQUIRED_SECTIONS = (
    "Agent Handoff",
    "Session Goal",
    "Current State",
    "Key Chat Context",
    "Files In Play",
    "Verification",
    "Next Step",
    "Resume Recipe",
    "Git Snapshot",
)


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
    return sorted((path for path in d.glob("*.md") if path.name != "current.md"), reverse=True)


def current_checkpoint(root: Path) -> Path | None:
    path = checkpoint_dir(root) / "current.md"
    return path if path.is_file() else None


def checkpoint_status(metadata: dict[str, str], root: Path | None = None) -> str:
    statuses: list[str] = []
    expires_at = metadata.get("expires_at", "")
    if not expires_at or expires_at == "never":
        statuses.append("legacy" if not expires_at else "active")
    else:
        try:
            expires = dt.datetime.strptime(expires_at, "%Y-%m-%d %H:%M:%S %z")
        except ValueError:
            statuses.append("invalid-expiry")
        else:
            statuses.append("stale" if expires <= dt.datetime.now().astimezone() else "active")

    if root is not None:
        branch = metadata.get("branch", "")
        current_branch = run_git(root, "branch", "--show-current")
        if branch and branch not in {"[unknown]", "(detached)"} and current_branch and branch != current_branch:
            statuses.append("branch-mismatch")
        base_commit = metadata.get("base_commit", "")
        if base_commit and base_commit != "[unknown]":
            result = subprocess.run(
                ["git", "-C", str(root), "cat-file", "-e", f"{base_commit}^{{commit}}"],
                capture_output=True,
            )
            if result.returncode != 0:
                statuses.append("base-commit-missing")
    return ",".join(statuses) or "unknown"


def load_checkpoint(path: Path, root: Path) -> dict[str, str]:
    metadata, body = parse_frontmatter(path.read_text(encoding="utf-8"))
    return {
        "path": str(path.relative_to(root)),
        "title": metadata.get("title") or path.stem,
        "created_at": metadata.get("created_at") or "[unknown]",
        "checkpoint_schema": metadata.get("checkpoint_schema") or "[legacy]",
        "created_by": metadata.get("created_by") or "[unknown]",
        "compatible_agents": metadata.get("compatible_agents") or "[unknown]",
        "branch": metadata.get("branch") or "[unknown]",
        "status": checkpoint_status(metadata, root),
        "base_commit": metadata.get("base_commit") or "[unknown]",
        "agent_handoff": extract_section(body, "Agent Handoff"),
        "session_goal": extract_section(body, "Session Goal"),
        "current_state": extract_section(body, "Current State"),
        "key_chat_context": extract_section(body, "Key Chat Context"),
        "files_in_play": extract_section(body, "Files In Play"),
        "verification": extract_section(body, "Verification"),
        "next_step": extract_section(body, "Next Step"),
    }


def load_latest_checkpoint(root: Path) -> dict[str, str] | None:
    current = current_checkpoint(root)
    if current:
        return load_checkpoint(current, root)
    files = list_checkpoints(root)
    if not files:
        return None
    return load_checkpoint(files[0], root)


def validate_checkpoint(path: Path, root: Path, strict: bool = False) -> list[str]:
    """Return validation errors and warnings for one checkpoint."""
    errors: list[str] = []
    metadata, body = parse_frontmatter(path.read_text(encoding="utf-8"))
    if not metadata:
        errors.append("missing frontmatter")
    for key in ("title", "created_at", "checkpoint_schema", "branch"):
        if not metadata.get(key):
            errors.append(f"missing metadata: {key}")
    for section in REQUIRED_SECTIONS:
        if not extract_section(body, section):
            errors.append(f"missing or empty section: {section}")
    if strict and "TODO" in body:
        errors.append("contains TODO placeholders")
    if contains_secret(path.read_text(encoding="utf-8")):
        errors.append("contains a credential-like value")
    expires_at = metadata.get("expires_at")
    if expires_at and expires_at != "never":
        try:
            dt.datetime.strptime(expires_at, "%Y-%m-%d %H:%M:%S %z")
        except ValueError:
            errors.append("invalid expires_at")
    if metadata.get("base_commit") not in (None, "", "[unknown]"):
        result = subprocess.run(["git", "-C", str(root), "cat-file", "-e", f"{metadata['base_commit']}^{{commit}}"], capture_output=True)
        if result.returncode != 0:
            errors.append("base_commit is not present in this repository")
    return errors


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
        print(f"- Schema: `{checkpoint['checkpoint_schema']}`")
        print(f"- Created by: `{checkpoint['created_by']}`")
        print(f"- Compatible agents: `{checkpoint['compatible_agents']}`")
        print(f"- Branch: `{checkpoint['branch']}`")
        print(f"- Status: `{checkpoint['status']}`")
        if checkpoint["status"] != "active" and checkpoint["status"] != "legacy":
            print("- Warning: checkpoint metadata does not fully match the current repository; verify it before resuming.")
        print()
        for label, key in [
            ("Agent Handoff", "agent_handoff"),
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
    current = current_checkpoint(root)
    if not files and not current:
        print("No checkpoints found.")
        return 0

    print(f"{'Date':<22} {'Status':<14} {'Branch':<16} {'Title'}")
    print("-" * 60)
    if current:
        metadata, _ = parse_frontmatter(current.read_text(encoding="utf-8"))
        print(f"{'current':<22} {checkpoint_status(metadata, root):<14} {metadata.get('branch', '[unknown]'):<16} {metadata.get('title', 'current')}")
    for f in files:
        metadata, _ = parse_frontmatter(f.read_text(encoding="utf-8"))
        created = metadata.get("created_at", "[unknown]")
        branch = metadata.get("branch", "[unknown]")
        title = metadata.get("title", f.stem)
        print(f"{created:<22} {checkpoint_status(metadata, root):<14} {branch:<16} {title}")
    print()
    print(f"{len(files) + (1 if current else 0)} checkpoint(s) total.")
    return 0


def cmd_validate(root: Path, strict: bool) -> int:
    paths = ([current_checkpoint(root)] if current_checkpoint(root) else []) + list_checkpoints(root)
    if not paths:
        print("No checkpoints found.")
        return 0
    invalid = 0
    for path in paths:
        errors = validate_checkpoint(path, root, strict=strict)
        if errors:
            invalid += 1
            print(f"INVALID {path.relative_to(root)}")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"OK      {path.relative_to(root)}")
    print(f"\nValidated {len(paths)} checkpoint(s); {invalid} invalid.")
    return 1 if invalid else 0


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
    parser.add_argument("--version", action="version", version="repo-resume 0.4.0")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("list", help="List all checkpoints with metadata.")
    prune_p = sub.add_parser("prune", help="Remove old checkpoints, keeping only the N most recent.")
    prune_p.add_argument("keep", type=int, nargs="?", default=5, help="Number of checkpoints to keep (default: 5)")
    validate_p = sub.add_parser("validate", help="Validate checkpoint structure and credential redaction.")
    validate_p.add_argument("--strict", action="store_true", help="Also reject TODO placeholders.")

    args = parser.parse_args()
    root = repo_root()

    if args.command == "list":
        return cmd_list(root)
    if args.command == "prune":
        return cmd_prune(root, args.keep)
    if args.command == "validate":
        return cmd_validate(root, args.strict)
    return cmd_resume(root)


if __name__ == "__main__":
    sys.exit(main())
