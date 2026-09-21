# agent-checkpoint

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Runtime: Python 3](https://img.shields.io/badge/runtime-python3-blue.svg)](https://www.python.org/)
[![Version: 0.4.0](https://img.shields.io/badge/version-0.4.0-2ea44f.svg)](VERSION)

**English** | [中文](./README.zh-CN.md)

Repo-local continuity skills for coding agents. Save the goal, decisions, files,
verification, and next steps in `.agents/checkpoints/`, then resume the same
working lane after an interruption, model switch, or machine change.

The checkpoint format is shared across Codex/OpenAI CLI, Claude Code, opencode,
and other agents that can read Markdown.

## Demo

![Terminal demo of repo-checkpoint and repo-resume](./assets/demo.gif)

The workflow is simple: save a handoff at the end of a session, then read it
before exploring the repository in the next session.

## Quick start

Requirements: Python 3, Git, and Bash.

```bash
git clone https://github.com/hotalexnet/agent-checkpoint.git
cd agent-checkpoint
bash install-repo-skills.sh
```

From the root of any Git repository:

```bash
# End a session: create a handoff scaffold and fill in its TODOs.
python3 ~/.agents/skills/repo-checkpoint/scripts/save_checkpoint.py \
  --title "chat-routing-root-cause" --agent codex

# Start the next session: restore the active lane.
python3 ~/.agents/skills/repo-resume/scripts/resume_snapshot.py
```

## What gets installed

The installer places two self-contained skills under `~/.agents/skills/`:

- `repo-checkpoint` — creates a Markdown handoff in
  `.agents/checkpoints/`.
- `repo-resume` — reads the current handoff, Git status, branch, and recent
  commits.

Both scripts can also be run directly, without an agent runtime.

## Commands

Run these commands from the target repository root.

The table omits the `python3 ~/.agents/skills/.../scripts/` prefix for
readability; use the full paths shown in the example below when copying a
command into a shell.

| Need | Command |
| --- | --- |
| Create a timestamped checkpoint | `save_checkpoint.py --title "work"` |
| Update one active handoff | `save_checkpoint.py --current --title "active-lane"` |
| Keep a checkpoint indefinitely | `save_checkpoint.py --expires-in 0` |
| Resume the active lane | `resume_snapshot.py` |
| List checkpoints and status | `resume_snapshot.py list` |
| Validate structure and metadata | `resume_snapshot.py validate` |
| Reject unfinished `TODO`s too | `resume_snapshot.py validate --strict` |
| Keep the five newest snapshots | `resume_snapshot.py prune 5` |

For example:

```bash
CHECKPOINT=~/.agents/skills/repo-checkpoint/scripts/save_checkpoint.py
RESUME=~/.agents/skills/repo-resume/scripts/resume_snapshot.py

python3 "$CHECKPOINT" --current --title "fix-login-flow" --agent codex
python3 "$RESUME" validate
python3 "$RESUME" list
```

The generated file is a scaffold. Replace every `TODO` with concrete session
information before handing the repository to another agent.

## Features in 0.4.0

- **Active lane:** `--current` atomically updates
  `.agents/checkpoints/current.md`; it takes precedence over timestamped
  snapshots when resuming.
- **Expiry tracking:** new checkpoints expire after 30 days by default.
  Use `--expires-in 0` to disable expiry.
- **Git association:** checkpoints record the branch and base commit. Resume
  reports branch mismatches and missing commits.
- **Secret redaction:** common passwords, tokens, API keys, bearer credentials,
  private keys, and credential-bearing URLs are redacted from generated fields
  before writing. Content you add manually should still be reviewed.
- **Validation:** `validate` checks frontmatter, required sections, expiry,
  credentials, and the recorded commit. `--strict` also rejects `TODO`s.
- **Safe writes:** checkpoint files are written to a temporary file and then
  replaced atomically.

Older timestamped checkpoints without the new metadata remain readable and are
reported as `legacy`.

## How a checkpoint works

Each checkpoint contains these sections:

```text
Agent Handoff       who can resume it and how
Session Goal        what must be completed
Current State       what is already true
Key Chat Context    user intent and constraints
Files In Play       files and data paths that matter
Verification        tests and checks already run
Next Step           the next executable actions
Resume Recipe       the standard recovery command
Git Snapshot        working tree and recent commits
```

The files are ordinary Markdown. You can review, edit, commit, ignore, copy,
or archive them with normal Git workflows.

## Install and upgrade

Install to a different skill directory:

```bash
bash install-repo-skills.sh --target /path/to/skills
```

Upgrade an existing installation from a cloned checkout:

```bash
bash upgrade-repo-skills.sh
```

Upgrade directly from GitHub:

```bash
bash <(curl -fsSL \
  https://raw.githubusercontent.com/hotalexnet/agent-checkpoint/main/upgrade-repo-skills.sh)
```

Use `--no-pull` when testing the current checkout, or `--target DIR` to choose
another installation directory. The installer backs up an existing skill
directory before replacing it.

## Cross-agent and multi-machine use

The handoff is intentionally tool-independent. A typical workflow is:

1. Agent A runs `save_checkpoint.py` and fills in the handoff.
2. The checkpoint is committed, copied, or left locally according to your
   privacy needs.
3. Agent B runs `resume_snapshot.py` from the same repository.

On another machine, clone this repository and run the installer, or copy the
`repo-checkpoint/` and `repo-resume/` directories into that machine's skill
directory.

## Privacy and Git policy

Checkpoint files may contain project names, paths, task details, and Git output.
Common credential patterns are redacted, but no pattern-based scanner can find
every possible secret. Review a checkpoint before committing it.

To keep personal handoffs out of Git:

```gitignore
.agents/checkpoints/
```

To share handoffs with a team, commit them like any other Markdown files.

## Limitations

- Resume quality depends on the details written into the checkpoint.
- The scaffold does not summarize an entire conversation automatically.
- A checkpoint with unfilled `TODO`s is a template, not a complete handoff.
- The project targets Git repositories and requires Python 3 and Git.

## Development

Run the test suite and static checks from the project root:

```bash
pytest -q
bash -n install-repo-skills.sh upgrade-repo-skills.sh
python3 -m compileall -q repo-checkpoint repo-resume tests
git diff --check
```

## Project structure

```text
agent-checkpoint/
├── install-repo-skills.sh
├── upgrade-repo-skills.sh
├── repo-checkpoint/
│   ├── SKILL.md
│   └── scripts/
│       ├── redact.py
│       └── save_checkpoint.py
├── repo-resume/
│   ├── SKILL.md
│   └── scripts/
│       ├── redact.py
│       └── resume_snapshot.py
├── tests/
├── assets/demo.gif
├── CHANGELOG.md
└── VERSION
```

## License

[MIT License](LICENSE)
