---
name: repo-checkpoint
description: Repo-local progress checkpoint workflow for any git repository. Use this skill whenever the user says save progress, checkpoint, snapshot the current lane, capture key chat context, write down what matters before closing, or wants the next session to resume immediately even if external session memory is missing.
---

# repo Checkpoint

Use this skill inside a git repository.

## Why this skill exists

Conversation state is fragile. A repo-local markdown checkpoint is not.

This skill writes a timestamped markdown handoff under `.agents/checkpoints/`
inside the current repository so the next session can recover:

- what the user actually wanted
- what constraints mattered
- what files were in play
- what remains next

## Mandatory first step

From the target repo root, run:

```bash
python3 ~/.agents/skills/repo-checkpoint/scripts/save_checkpoint.py --title "<short-title>"
```

If the skill is vendored into the repo instead of installed globally, run the same
script from the vendored path.

## Workflow

1. Create the scaffold first. Do not invent the path manually.
2. Replace every `TODO` with concrete current-session state.
3. Treat `Key Chat Context` as first-class data:
   - user goal
   - explicit constraints
   - scope changes
   - rejected paths
   - exact wording worth preserving
4. Keep `Files In Play`, `Verification`, and `Next Step` executable.
5. End with the checkpoint path and tell the user to run `repo-resume` next time.

## Output contract

Keep these top-level sections exactly:

- `## Session Goal`
- `## Current State`
- `## Key Chat Context`
- `## Files In Play`
- `## Verification`
- `## Next Step`
- `## Resume Recipe`
- `## Git Snapshot`
