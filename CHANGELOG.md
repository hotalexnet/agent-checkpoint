# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-05-14

### Added

- `resume_snapshot.py list` — list all checkpoints with date, branch, and title.
- `resume_snapshot.py prune [N]` — remove old checkpoints, keeping the N most recent (default 5).
- Test suite (14 tests) covering scaffold generation, frontmatter parsing, list, and prune.
- `VERSION` file and `CHANGELOG.md`.
- `.gitignore` guidance in README.

### Fixed

- Removed note-agent-specific `PROJECT_STATUS.md` parsing from `resume_snapshot.py`.
- Replaced all Chinese TODO prompts in scaffold template with English.
