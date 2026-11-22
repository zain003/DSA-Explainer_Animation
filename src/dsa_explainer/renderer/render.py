"""Invoke Manim against a verified lesson plan."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from dsa_explainer.config import get_settings
from dsa_explainer.schema import LessonPlan


def render_lesson(
    plan: LessonPlan,
    lesson_dir: Path,
    *,
    audio_manifest: dict | None = None,
    quality: str | None = None,
) -> Path:
    """Render MP4 into lesson_dir/video. Returns path to final mp4."""
    lesson_dir.mkdir(parents=True, exist_ok=True)
    plan_path = lesson_dir / "plan.json"
    plan_path.write_text(plan.model_dump_json(indent=2), encoding="utf-8")

    if audio_manifest is not None:
        (lesson_dir / "audio_manifest.json").write_text(
            json.dumps(audio_manifest, indent=2), encoding="utf-8"
        )

    settings = get_settings()
    q = quality or settings.manim_quality
    media_dir = lesson_dir / "manim_media"
    media_dir.mkdir(parents=True, exist_ok=True)

    scene_file = Path(__file__).with_name("manim_lesson.py")
    env = os.environ.copy()
    env["DSA_LESSON_PLAN"] = str(plan_path.resolve())
    env["DSA_AUDIO_MANIFEST"] = str((lesson_dir / "audio_manifest.json").resolve())
    env["PYTHONPATH"] = os.pathsep.join(
        [str(Path(__file__).resolve().parents[2]), env.get("PYTHONPATH", "")]
    )

    cmd = [
        sys.executable,
        "-m",
        "manim",
        "render",
        str(scene_file),
        "DSALessonScene",
        f"-q{q}",
        "--media_dir",
        str(media_dir),
        "--fps",
        str(settings.default_fps),
    ]

    subprocess.run(cmd, check=True, env=env, cwd=str(lesson_dir))

    # Find produced mp4
    mp4s = sorted(media_dir.rglob("DSALessonScene.mp4"), key=lambda p: p.stat().st_mtime)
    if not mp4s:
        mp4s = sorted(media_dir.rglob("*.mp4"), key=lambda p: p.stat().st_mtime)
    if not mp4s:
        raise FileNotFoundError(f"Manim did not produce an mp4 under {media_dir}")

    final_path = lesson_dir / "lesson.mp4"
    shutil.copy2(mp4s[-1], final_path)
    return final_path
