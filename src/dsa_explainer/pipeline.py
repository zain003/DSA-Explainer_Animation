"""End-to-end: plan → verify → narrate → TTS → render → quiz."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from dsa_explainer.config import LESSONS_DIR, ensure_dirs, get_settings
from dsa_explainer.narration.tts import synthesize_lesson_audio
from dsa_explainer.narration.writer import enrich_narration
from dsa_explainer.planner.planner import plan_lesson
from dsa_explainer.quiz.generator import generate_quiz
from dsa_explainer.renderer.render import render_lesson
from dsa_explainer.revision.revise import apply_revision, parse_revision_utterance
from dsa_explainer.schema import LearnerLevel, LessonPlan, TopicKind
from dsa_explainer.verifier.engine import verify_plan


@dataclass
class LessonArtifact:
    lesson_dir: Path
    plan: LessonPlan
    video_path: Path | None
    audio_manifest: dict
    verification_ok: bool


def _slug(text: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    return s[:48] or "lesson"


def create_lesson(
    topic: str,
    level: LearnerLevel | str = LearnerLevel.BEGINNER,
    topic_kind: TopicKind | str | None = None,
    *,
    offline: bool | None = None,
    skip_render: bool = False,
    lesson_id: str | None = None,
) -> LessonArtifact:
    ensure_dirs()
    settings = get_settings()
    if isinstance(level, str):
        level = LearnerLevel(level)

    plan = plan_lesson(topic, level=level, topic_kind=topic_kind, offline=offline)
    plan = enrich_narration(plan, offline=offline)
    quiz = generate_quiz(plan)
    # Drop unverified quiz items — wrong answers are worse than none
    quiz = [q for q in quiz if q.verified]
    plan = plan.model_copy(update={"quiz": quiz})

    report = verify_plan(plan)
    if not report.ok:
        raise RuntimeError(f"Refusing to render incorrect lesson: {report.issues}")

    if plan.estimated_duration_sec < settings.min_video_seconds:
        raise RuntimeError(
            f"Lesson under {settings.min_video_seconds}s "
            f"({plan.estimated_duration_sec:.1f}s)"
        )

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lid = lesson_id or f"{_slug(topic)}-{stamp}"
    lesson_dir = LESSONS_DIR / lid
    lesson_dir.mkdir(parents=True, exist_ok=True)

    (lesson_dir / "plan.json").write_text(plan.model_dump_json(indent=2), encoding="utf-8")
    (lesson_dir / "verification.json").write_text(
        report.model_dump_json(indent=2), encoding="utf-8"
    )

    audio_manifest = synthesize_lesson_audio(plan, lesson_dir)
    # Persist durations updated by TTS
    (lesson_dir / "plan.json").write_text(plan.model_dump_json(indent=2), encoding="utf-8")

    video_path = None
    if not skip_render:
        video_path = render_lesson(plan, lesson_dir, audio_manifest=audio_manifest)

    meta = {
        "lesson_id": lid,
        "topic": topic,
        "video": str(video_path) if video_path else None,
        "duration_sec": audio_manifest.get("total_duration_sec", plan.estimated_duration_sec),
        "verification_ok": True,
    }
    (lesson_dir / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    return LessonArtifact(
        lesson_dir=lesson_dir,
        plan=plan,
        video_path=video_path,
        audio_manifest=audio_manifest,
        verification_ok=True,
    )


def revise_lesson(
    lesson_dir: Path,
    utterance: str,
    *,
    skip_render: bool = False,
) -> LessonArtifact:
    """Apply a learner revision and re-render only the updated plan."""
    plan_path = Path(lesson_dir) / "plan.json"
    plan = LessonPlan.model_validate_json(plan_path.read_text(encoding="utf-8"))
    request = parse_revision_utterance(utterance)
    revised = apply_revision(plan, request)

    report = verify_plan(revised)
    if not report.ok:
        raise RuntimeError(f"Revision failed verification: {report.issues}")

    out_dir = Path(lesson_dir) / f"rev-v{revised.version}"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "plan.json").write_text(revised.model_dump_json(indent=2), encoding="utf-8")
    (out_dir / "verification.json").write_text(
        report.model_dump_json(indent=2), encoding="utf-8"
    )
    (out_dir / "revision.json").write_text(request.model_dump_json(indent=2), encoding="utf-8")

    audio_manifest = synthesize_lesson_audio(revised, out_dir)
    video_path = None
    if not skip_render:
        video_path = render_lesson(revised, out_dir, audio_manifest=audio_manifest)

    return LessonArtifact(
        lesson_dir=out_dir,
        plan=revised,
        video_path=video_path,
        audio_manifest=audio_manifest,
        verification_ok=True,
    )
