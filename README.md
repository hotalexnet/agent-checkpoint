# Repo Skills Bundle

This bundle provides two global skills for any git repository:

- `repo-checkpoint`
- `repo-resume`

## Install

Run:

```bash
bash install-repo-skills.sh
```

By default this installs to:

```bash
~/.agents/skills
```

You can override the target directory:

```bash
bash install-repo-skills.sh --target /path/to/skills
```

## Use

Inside any git repository:

```bash
python3 ~/.agents/skills/repo-checkpoint/scripts/save_checkpoint.py --title "my-work"
python3 ~/.agents/skills/repo-resume/scripts/resume_snapshot.py
```

## Notes

- `repo-checkpoint` writes checkpoint markdown files under `.agents/checkpoints/`
  inside the current repository.
- The skills require `python3` and `git` on the target machine.
