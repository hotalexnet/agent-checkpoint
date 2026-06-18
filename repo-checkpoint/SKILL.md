---
name: repo-checkpoint
description: Cross-agent repo-local progress checkpoint workflow for any git repository. Use this skill whenever the user says save progress, checkpoint, snapshot the current lane, capture key chat context, write down what matters before closing, or wants the next session to resume immediately from Codex, Claude Code, opencode, or another programming agent.
---

# repo Checkpoint

Use this skill inside a git repository.

## Why this skill exists

Conversation state is fragile. A repo-local markdown checkpoint is not.

This skill writes a timestamped markdown handoff under the fixed repo-local
directory `.agents/checkpoints/` so the next session can recover from any
programming agent: Codex/OpenAI CLI, Claude Code, opencode, or a generic shell
agent. The checkpoint belongs to the repository, not to a particular tool.

- what the user actually wanted
- what constraints mattered
- what files were in play
- what remains next

## Mandatory first step

From the target repo root, run:

```bash
python3 ~/.agents/skills/repo-checkpoint/scripts/save_checkpoint.py --title "<short-title>" --agent "<codex|claude-code|opencode|other>"
```

If the skill is vendored into the repo instead of installed globally, run the same
script from the vendored path.

## Workflow

1. Create the scaffold first. Do not invent the path manually.
2. Replace every `TODO` with concrete current-session state.
3. Treat `Agent Handoff` and `Key Chat Context` as first-class data:
   - which agent wrote the checkpoint
   - which agent should be able to resume it
   - where to start without relying on hidden conversation memory
   - user goal
   - explicit constraints
   - scope changes
   - rejected paths
   - exact wording worth preserving
4. Keep `Files In Play`, `Verification`, and `Next Step` executable.
5. End with the checkpoint path and tell the user that any supported agent can
   run `repo-resume` from the same repo next time.

## Output contract

Keep these top-level sections exactly:

- `## Agent Handoff`
- `## Session Goal`
- `## Current State`
- `## Key Chat Context`
- `## Files In Play`
- `## Verification`
- `## Next Step`
- `## Resume Recipe`
- `## Git Snapshot`
