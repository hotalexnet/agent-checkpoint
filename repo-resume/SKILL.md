---
name: repo-resume
description: Fast cross-agent repo-local resume workflow for any git repository. Use this skill whenever the user says resume previous work, continue where we left off, recover context after reopening, or wants the exact current lane without broad repo exploration. Prefer the latest repo-local checkpoint under `.agents/checkpoints/` when it exists, regardless of whether it was written by Codex, Claude Code, opencode, or another programming agent.
---

# repo Resume

Use this skill inside a git repository.

## Mandatory first step

From the target repo root, run:

```bash
python3 ~/.agents/skills/repo-resume/scripts/resume_snapshot.py
```

If the skill is vendored into the repo instead of installed globally, run the same
script from the vendored path.

## Recovery workflow

1. Read the latest repo-local checkpoint under the fixed directory `.agents/checkpoints/` if present.
   Treat it as a shared agent handoff, not as tool-specific memory.
2. Check git branch, working tree, and recent commits.
3. Read `Agent Handoff`, `Files In Play`, and `Next Step` first. Open only
   those files unless the checkpoint is stale.

## Checkpoint management

```bash
# List all checkpoints
python3 ~/.agents/skills/repo-resume/scripts/resume_snapshot.py list

# Prune old checkpoints, keep 5 most recent
python3 ~/.agents/skills/repo-resume/scripts/resume_snapshot.py prune 5
```

## Report shape

When summarizing for the user, lead with:

1. latest repo checkpoint
2. checkpoint author / compatible agents when present
3. current git state
4. active files and verification state
5. next concrete step

Keep it short unless the user asks for more.
