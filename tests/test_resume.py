"""Tests for repo-resume/resume_snapshot.py."""
from __future__ import annotations

import subprocess
from pathlib import Path

from conftest import git_repo  # noqa: F401

CHECKPOINT_SCRIPT = Path(__file__).resolve().parent.parent / "repo-checkpoint" / "scripts" / "save_checkpoint.py"
RESUME_SCRIPT = Path(__file__).resolve().parent.parent / "repo-resume" / "scripts" / "resume_snapshot.py"


def create_checkpoint(repo: Path, title: str = "test") -> None:
    subprocess.run(
        ["python3", str(CHECKPOINT_SCRIPT), "--title", title],
        cwd=repo,
        check=True,
        capture_output=True,
    )


def run_resume(repo: Path, *extra_args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["python3", str(RESUME_SCRIPT), *extra_args],
        cwd=repo,
        capture_output=True,
        text=True,
    )


def test_resume_no_checkpoint(git_repo: Path):
    result = run_resume(git_repo)
    assert result.returncode == 0
    assert "None found" in result.stdout


def test_resume_with_checkpoint(git_repo: Path):
    create_checkpoint(git_repo, "my-session")
    result = run_resume(git_repo)
    assert result.returncode == 0
    assert "my-session" in result.stdout
    assert "Session Goal" in result.stdout
    assert "Working Tree" in result.stdout
    assert "Recent Commits" in result.stdout


def test_resume_no_project_status(git_repo: Path):
    create_checkpoint(git_repo)
    result = run_resume(git_repo)
    assert "PROJECT_STATUS" not in result.stdout


def test_list_empty(git_repo: Path):
    result = run_resume(git_repo, "list")
    assert result.returncode == 0
    assert "No checkpoints found" in result.stdout


def test_list_with_checkpoints(git_repo: Path):
    create_checkpoint(git_repo, "alpha")
    create_checkpoint(git_repo, "beta")
    result = run_resume(git_repo, "list")
    assert result.returncode == 0
    assert "alpha" in result.stdout
    assert "beta" in result.stdout
    assert "2 checkpoint(s)" in result.stdout


def test_prune_nothing_to_do(git_repo: Path):
    create_checkpoint(git_repo, "only-one")
    result = run_resume(git_repo, "prune", "5")
    assert result.returncode == 0
    assert "nothing to prune" in result.stdout
    assert len(list((git_repo / ".agents" / "checkpoints").glob("*.md"))) == 1


def test_prune_removes_old(git_repo: Path):
    import time

    create_checkpoint(git_repo, "old")
    time.sleep(1.1)
    create_checkpoint(git_repo, "new")
    assert len(list((git_repo / ".agents" / "checkpoints").glob("*.md"))) == 2

    result = run_resume(git_repo, "prune", "1")
    assert result.returncode == 0
    assert "Pruned 1" in result.stdout

    remaining = list((git_repo / ".agents" / "checkpoints").glob("*.md"))
    assert len(remaining) == 1
    assert "new" in remaining[0].read_text()


def test_prune_default_keep_5(git_repo: Path):
    result = run_resume(git_repo, "prune")
    assert result.returncode == 0
