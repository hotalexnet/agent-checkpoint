"""Tests for repo-checkpoint/save_checkpoint.py."""
from __future__ import annotations

import subprocess
from pathlib import Path

from conftest import git_repo  # noqa: F401

SCRIPT = Path(__file__).resolve().parent.parent / "repo-checkpoint" / "scripts" / "save_checkpoint.py"


def run_checkpoint(repo: Path, title: str = "test") -> subprocess.CompletedProcess:
    return subprocess.run(
        ["python3", str(SCRIPT), "--title", title],
        cwd=repo,
        capture_output=True,
        text=True,
    )


def test_creates_checkpoint_file(git_repo: Path):
    result = run_checkpoint(git_repo)
    assert result.returncode == 0

    files = list((git_repo / ".agents" / "checkpoints").glob("*.md"))
    assert len(files) == 1

    content = files[0].read_text()
    assert "title: test" in content
    assert "## Session Goal" in content
    assert "## Key Chat Context" in content
    assert "## Files In Play" in content
    assert "## Next Step" in content


def test_slugifies_title(git_repo: Path):
    run_checkpoint(git_repo, title="My Cool Feature!!")
    files = list((git_repo / ".agents" / "checkpoints").glob("*.md"))
    assert len(files) == 1
    assert "my-cool-feature" in files[0].name


def test_git_state_in_template(git_repo: Path):
    run_checkpoint(git_repo)
    content = list((git_repo / ".agents" / "checkpoints").glob("*.md"))[0].read_text()
    assert "git_state: clean" in content
    assert "Working tree: `clean`" in content


def test_git_state_dirty(git_repo: Path):
    (git_repo / "dirty.txt").write_text("change")
    run_checkpoint(git_repo)
    content = list((git_repo / ".agents" / "checkpoints").glob("*.md"))[0].read_text()
    assert "git_state: dirty" in content


def test_no_todo_in_chinese(git_repo: Path):
    run_checkpoint(git_repo)
    content = list((git_repo / ".agents" / "checkpoints").glob("*.md"))[0].read_text()
    assert "这轮" not in content
    assert "列出" not in content
    assert "下次继续" not in content


def test_multiple_checkpoints_ordered(git_repo: Path):
    import time

    run_checkpoint(git_repo, "first")
    time.sleep(1.1)
    run_checkpoint(git_repo, "second")

    files = sorted((git_repo / ".agents" / "checkpoints").glob("*.md"), reverse=True)
    assert len(files) == 2
    assert "second" in files[0].read_text()
    assert "first" in files[1].read_text()
