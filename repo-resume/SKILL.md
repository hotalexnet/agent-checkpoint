---
name: repo-resume
description: Fast repo-local resume workflow for any git repository. Use this skill whenever the user says resume previous work, continue where we left off, recover context after reopening, or wants the exact current lane without broad repo exploration. Prefer the latest repo-local checkpoint under `.agents/checkpoints/` when it exists.
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

1. Read the latest repo-local checkpoint under `.agents/checkpoints/` if present.
2. Check git branch, working tree, and recent commits.
3. If the repo has `PROJECT_STATUS.md`, read it after the checkpoint, not before.
4. Open only the files named in `Files In Play` or `Next Step` unless the checkpoint is stale.

## Report shape

When summarizing for the user, lead with:

1. latest repo checkpoint
2. current git state
3. active files and verification state
4. next concrete step

Keep it short unless the user asks for more.
