#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


DEMO_FILENAME = "20260513-114233-chat-routing-fix.md"
DEMO_CREATED_AT = "2026-05-13 11:42:33 +0800"
WINDOW_WIDTH = 1320
WINDOW_HEIGHT = 860
FRAME_BG = "#0b1020"
PANEL_BG = "#111827"
PANEL_BORDER = "#334155"
HEADER_BG = "#0f172a"
TEXT_COLOR = "#e5e7eb"
MUTED_TEXT = "#94a3b8"
ACCENT_TEXT = "#60a5fa"
PROMPT_TEXT = "#34d399"
PADDING_X = 34
PADDING_Y = 28
TOP_BAR_HEIGHT = 54
FONT_SIZE = 19
LINE_HEIGHT = 29
MAX_CONTENT_WIDTH = WINDOW_WIDTH - (PADDING_X * 2) - 36
FPS_TYPING_MS = 90


@dataclass
class Scene:
    label: str
    prompt: str
    command: str
    output: str
    hold_ms: int
    chunk_size: int


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def run(
    args: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    check: bool = True,
) -> str:
    result = subprocess.run(
        args,
        cwd=str(cwd),
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    if check and result.returncode != 0:
        raise RuntimeError(
            f"command failed ({result.returncode}): {' '.join(args)}\n"
            f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
        )
    combined = result.stdout if result.stdout.strip() else result.stderr
    return combined.strip()


def pick_font() -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/google-noto/NotoSansMono-Regular.ttf",
        "/usr/share/fonts/dejavu-sans-mono-fonts/DejaVuSansMono.ttf",
        "/usr/share/fonts/dejavu/DejaVuSansMono.ttf",
    ]
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), FONT_SIZE)
    return ImageFont.load_default()


def wrap_lines(draw: ImageDraw.ImageDraw, font: ImageFont.ImageFont, text: str) -> list[str]:
    wrapped: list[str] = []
    for raw_line in text.splitlines():
        if not raw_line:
            wrapped.append("")
            continue
        current = raw_line
        while draw.textlength(current, font=font) > MAX_CONTENT_WIDTH:
            cut = len(current)
            while cut > 1 and draw.textlength(current[:cut], font=font) > MAX_CONTENT_WIDTH:
                cut -= 1
            split_at = current.rfind(" ", 0, cut)
            if split_at <= 0:
                split_at = cut
            wrapped.append(current[:split_at].rstrip())
            current = current[split_at:].lstrip()
        wrapped.append(current)
    return wrapped


def render_frame(
    *,
    font: ImageFont.ImageFont,
    scene_label: str,
    prompt: str,
    command_text: str,
    output_text: str,
) -> Image.Image:
    image = Image.new("RGB", (WINDOW_WIDTH, WINDOW_HEIGHT), FRAME_BG)
    draw = ImageDraw.Draw(image)

    panel_left = 26
    panel_top = 28
    panel_right = WINDOW_WIDTH - 26
    panel_bottom = WINDOW_HEIGHT - 28
    draw.rounded_rectangle(
        [(panel_left, panel_top), (panel_right, panel_bottom)],
        radius=14,
        fill=PANEL_BG,
        outline=PANEL_BORDER,
        width=1,
    )

    draw.rounded_rectangle(
        [(panel_left, panel_top), (panel_right, panel_top + TOP_BAR_HEIGHT)],
        radius=14,
        fill=HEADER_BG,
    )
    draw.rectangle(
        [(panel_left, panel_top + TOP_BAR_HEIGHT - 14), (panel_right, panel_top + TOP_BAR_HEIGHT)],
        fill=HEADER_BG,
    )

    circle_y = panel_top + 18
    circle_x = panel_left + 18
    for color in ["#fb7185", "#f59e0b", "#34d399"]:
        draw.ellipse([(circle_x, circle_y), (circle_x + 12, circle_y + 12)], fill=color)
        circle_x += 20

    draw.text(
        (panel_left + 88, panel_top + 14),
        "repo-continuity-skills demo",
        font=font,
        fill=TEXT_COLOR,
    )
    draw.text(
        (panel_right - 170, panel_top + 14),
        scene_label,
        font=font,
        fill=MUTED_TEXT,
    )

    content_x = panel_left + PADDING_X
    content_y = panel_top + TOP_BAR_HEIGHT + PADDING_Y

    prompt_prefix = f"{prompt} $ "
    draw.text((content_x, content_y), prompt_prefix, font=font, fill=PROMPT_TEXT)
    prompt_width = draw.textlength(prompt_prefix, font=font)
    draw.text((content_x + prompt_width, content_y), command_text, font=font, fill=TEXT_COLOR)

    body = wrap_lines(draw, font, output_text)
    y = content_y + LINE_HEIGHT + 16
    for line in body:
        color = ACCENT_TEXT if line.startswith("# ") else TEXT_COLOR
        draw.text((content_x, y), line, font=font, fill=color)
        y += LINE_HEIGHT

    return image


def build_frames(font: ImageFont.ImageFont, scene: Scene) -> tuple[list[Image.Image], list[int]]:
    frames: list[Image.Image] = []
    durations: list[int] = []
    typed = scene.command
    step = max(1, scene.chunk_size)
    for end in range(step, len(typed) + step, step):
        current = typed[:end]
        frames.append(
            render_frame(
                font=font,
                scene_label=scene.label,
                prompt=scene.prompt,
                command_text=current,
                output_text="",
            )
        )
        durations.append(FPS_TYPING_MS)

    frames.append(
        render_frame(
            font=font,
            scene_label=scene.label,
            prompt=scene.prompt,
            command_text=typed,
            output_text=scene.output,
        )
    )
    durations.append(scene.hold_ms)
    return frames, durations


def normalize_text(text: str, *, repo_path: Path, fake_home: Path) -> str:
    normalized = text.replace(str(repo_path), "~/work/demo-app")
    normalized = normalized.replace(str(fake_home), "~")
    normalized = normalized.replace(str(fake_home / ".agents" / "skills"), "~/.agents/skills")
    return normalized


def write_demo_repo(repo_path: Path) -> None:
    files = {
        "src/chat/router.py": """def route_message(message: str) -> str:
    lowered = message.lower()
    if "upload" in lowered or "import" in lowered:
        return "open-import-guide"
    return "answer-with-course-context"
""",
        "src/prompts/chat_prompt.py": """SYSTEM_PROMPT = \"\"\"Answer from imported course material first.
Do not leak onboarding guidance into ordinary study questions.
\"\"\"
""",
        "tests/test_chat_router.py": """def test_placeholder() -> None:
    assert True
""",
    }
    for relative, content in files.items():
        target = repo_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")


def populate_checkpoint(path: Path, *, repo_path: Path, env: dict[str, str]) -> None:
    working_tree = run(["git", "status", "--short"], cwd=repo_path, env=env) or "[clean]"
    recent_commits = run(["git", "log", "--oneline", "-5"], cwd=repo_path, env=env) or "[no commits]"
    content = f"""---
title: chat-routing-fix
created_at: {DEMO_CREATED_AT}
branch: main
git_state: dirty
---

# chat-routing-fix

## Session Goal
- Fix the chat fallback so non-matching questions stop returning stale onboarding guidance.

## Current State
- Router guard is patched locally.
- One local smoke pass is done.
- Staging verification still needs to run.

## Key Chat Context
- The user wants a root-cause cleanup, not a keyword patch.
- Old onboarding copy must stop leaking into ordinary chat replies.
- Do not broaden scope into model switching yet.

## Files In Play
- src/chat/router.py
- src/prompts/chat_prompt.py
- tests/test_chat_router.py

## Verification
- Ran a local smoke check against representative prompts.
- Still need to verify the deployed path separately.

## Next Step
1. Reproduce against the current deploy chain.
2. Verify fallback selection with 3 representative prompts.
3. Commit only after the bad greeting path is gone.

## Resume Recipe
- Run `python3 ~/.agents/skills/repo-resume/scripts/resume_snapshot.py`
- Open the files listed above first.

## Git Snapshot

### Working Tree
```text
{working_tree}
```

### Recent Commits
```text
{recent_commits}
```
"""
    path.write_text(content, encoding="utf-8")


def build_demo_scenes(root: Path) -> list[Scene]:
    with tempfile.TemporaryDirectory(prefix="repo-continuity-demo-") as temp_dir:
        temp_root = Path(temp_dir)
        fake_home = temp_root / "home"
        skills_root = fake_home / ".agents" / "skills"
        skills_root.mkdir(parents=True, exist_ok=True)
        shutil.copytree(root / "repo-checkpoint", skills_root / "repo-checkpoint")
        shutil.copytree(root / "repo-resume", skills_root / "repo-resume")

        repo_path = temp_root / "demo-app"
        repo_path.mkdir(parents=True, exist_ok=True)
        write_demo_repo(repo_path)

        env = os.environ.copy()
        env["HOME"] = str(fake_home)
        env["GIT_AUTHOR_NAME"] = "Demo Bot"
        env["GIT_AUTHOR_EMAIL"] = "demo@example.com"
        env["GIT_COMMITTER_NAME"] = "Demo Bot"
        env["GIT_COMMITTER_EMAIL"] = "demo@example.com"
        env["GIT_AUTHOR_DATE"] = "2026-05-13T11:20:00+08:00"
        env["GIT_COMMITTER_DATE"] = "2026-05-13T11:20:00+08:00"

        run(["git", "init", "-b", "main"], cwd=repo_path, env=env)
        run(["git", "config", "user.name", "Demo Bot"], cwd=repo_path, env=env)
        run(["git", "config", "user.email", "demo@example.com"], cwd=repo_path, env=env)
        run(["git", "add", "."], cwd=repo_path, env=env)
        run(["git", "commit", "-m", "feat: add chat routing baseline"], cwd=repo_path, env=env)

        router_path = repo_path / "src/chat/router.py"
        router_path.write_text(
            router_path.read_text(encoding="utf-8")
            + "\n# TODO: keep onboarding guidance out of ordinary chat replies.\n",
            encoding="utf-8",
        )

        checkpoint_stdout = run(
            [
                "python3",
                str(skills_root / "repo-checkpoint/scripts/save_checkpoint.py"),
                "--title",
                "chat-routing-fix",
            ],
            cwd=repo_path,
            env=env,
        )
        created_path = Path(checkpoint_stdout.splitlines()[0].strip())
        stable_path = repo_path / ".agents" / "checkpoints" / DEMO_FILENAME
        created_path.rename(stable_path)
        populate_checkpoint(stable_path, repo_path=repo_path, env=env)

        list_output = run(["ls", ".agents/checkpoints"], cwd=repo_path, env=env)
        preview_output = run(
            ["sed", "-n", "1,28p", f".agents/checkpoints/{DEMO_FILENAME}"],
            cwd=repo_path,
            env=env,
        )
        resume_output = run(
            [
                "python3",
                str(skills_root / "repo-resume/scripts/resume_snapshot.py"),
            ],
            cwd=repo_path,
            env=env,
        )

        checkpoint_stdout = normalize_text(checkpoint_stdout, repo_path=repo_path, fake_home=fake_home)
        preview_output = normalize_text(preview_output, repo_path=repo_path, fake_home=fake_home)
        resume_output = normalize_text(resume_output, repo_path=repo_path, fake_home=fake_home)

        return [
            Scene(
                label="1/4 checkpoint",
                prompt="alex@demo ~/work/demo-app",
                command='python3 ~/.agents/skills/repo-checkpoint/scripts/save_checkpoint.py --title "chat-routing-fix"',
                output=checkpoint_stdout,
                hold_ms=1700,
                chunk_size=7,
            ),
            Scene(
                label="2/4 artifact",
                prompt="alex@demo ~/work/demo-app",
                command="ls .agents/checkpoints",
                output=list_output,
                hold_ms=1200,
                chunk_size=8,
            ),
            Scene(
                label="3/4 content",
                prompt="alex@demo ~/work/demo-app",
                command=f"sed -n '1,28p' .agents/checkpoints/{DEMO_FILENAME}",
                output=preview_output,
                hold_ms=2300,
                chunk_size=10,
            ),
            Scene(
                label="4/4 resume",
                prompt="alex@demo ~/work/demo-app",
                command="python3 ~/.agents/skills/repo-resume/scripts/resume_snapshot.py",
                output=resume_output,
                hold_ms=2600,
                chunk_size=8,
            ),
        ]


def save_gif(frames: list[Image.Image], durations: list[int], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        optimize=True,
        disposal=2,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a terminal demo GIF for repo-continuity-skills.")
    parser.add_argument(
        "--output",
        default=str(repo_root() / "assets" / "demo.gif"),
        help="Output GIF path.",
    )
    args = parser.parse_args()

    root = repo_root()
    font = pick_font()
    scenes = build_demo_scenes(root)

    all_frames: list[Image.Image] = []
    all_durations: list[int] = []
    for scene in scenes:
        frames, durations = build_frames(font, scene)
        all_frames.extend(frames)
        all_durations.extend(durations)

    output_path = Path(args.output).resolve()
    save_gif(all_frames, all_durations, output_path)
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
