"""Revision control: change only the requested part of a lesson."""

from __future__ import annotations

import re

from dsa_explainer.planner.validator import validate_plan
from dsa_explainer.schema import LearnerLevel, LessonPlan, RevisionRequest, Scene
from dsa_explainer.verifier.engine import verify_plan


def parse_revision_utterance(text: str) -> RevisionRequest:
    """Map natural language like 'slow down step 4' to a RevisionRequest."""
    t = text.strip().lower()
    scene_id = None
    m = re.search(r"(?:step|scene)\s*(\d+)", t)
    if m:
        scene_id = f"s{m.group(1)}"
    m2 = re.search(r"\b(s\d+)\b", t)
    if m2:
        scene_id = m2.group(1)

    if "slow" in t:
        return RevisionRequest(kind="slow_down", scene_id=scene_id, instruction=text)
    if "speed" in t or "faster" in t:
        return RevisionRequest(kind="speed_up", scene_id=scene_id, instruction=text)
    if "beginner" in t:
        return RevisionRequest(
            kind="relevel",
            scene_id=scene_id,
            target_level=LearnerLevel.BEGINNER,
            instruction=text,
        )
    if "intermediate" in t:
        return RevisionRequest(
            kind="relevel",
            scene_id=scene_id,
            target_level=LearnerLevel.INTERMEDIATE,
            instruction=text,
        )
    if "advanced" in t:
        return RevisionRequest(
            kind="relevel",
            scene_id=scene_id,
            target_level=LearnerLevel.ADVANCED,
            instruction=text,
        )
    if "narrat" in t or "explain" in t or "rewrite" in t:
        return RevisionRequest(
            kind="rewrite_narration",
            scene_id=scene_id,
            instruction=text,
        )
    return RevisionRequest(kind="rewrite_narration", scene_id=scene_id, instruction=text)


def apply_revision(plan: LessonPlan, request: RevisionRequest) -> LessonPlan:
    """Return a new plan with only the targeted scene(s) modified."""
    scenes = list(plan.scenes)
    targets = _target_indices(scenes, request.scene_id)

    new_scenes: list[Scene] = []
    for i, scene in enumerate(scenes):
        if i not in targets:
            new_scenes.append(scene)
            continue
        new_scenes.append(_revise_scene(scene, request, plan.learner_level))

    level = request.target_level or plan.learner_level
    updated = plan.model_copy(
        update={
            "scenes": new_scenes,
            "learner_level": level,
            "version": plan.version + 1,
            "revision_notes": request.instruction or request.kind,
        }
    )
    updated = validate_plan(updated)
    report = verify_plan(updated)
    if not report.ok:
        raise RuntimeError(f"Revised plan failed verification: {report.issues}")
    return updated


def _target_indices(scenes: list[Scene], scene_id: str | None) -> set[int]:
    if not scene_id:
        return set(range(len(scenes)))
    for i, s in enumerate(scenes):
        if s.id == scene_id:
            return {i}
    # Also allow 1-based numeric
    if scene_id.startswith("s") and scene_id[1:].isdigit():
        idx = int(scene_id[1:]) - 1
        if 0 <= idx < len(scenes):
            return {idx}
    raise KeyError(f"Unknown scene id {scene_id!r}")


def _revise_scene(scene: Scene, request: RevisionRequest, level: LearnerLevel) -> Scene:
    if request.kind == "slow_down":
        return scene.model_copy(
            update={
                "duration_hint_sec": min(60.0, scene.duration_hint_sec * 1.6),
                "narration": _expand_narration(scene.narration, level),
            }
        )
    if request.kind == "speed_up":
        return scene.model_copy(
            update={
                "duration_hint_sec": max(2.0, scene.duration_hint_sec * 0.7),
                "narration": _condense_narration(scene.narration),
            }
        )
    if request.kind == "relevel":
        target = request.target_level or LearnerLevel.BEGINNER
        return scene.model_copy(update={"narration": _relevel_narration(scene.narration, target)})
    if request.kind in {"rewrite_narration", "replace_scene"}:
        extra = request.instruction.strip()
        narration = scene.narration
        if extra:
            narration = f"{narration} ({extra})"
        return scene.model_copy(update={"narration": narration})
    return scene


def _expand_narration(text: str, level: LearnerLevel) -> str:
    tip = " Let's take this slowly and watch each change."
    if level == LearnerLevel.BEGINNER:
        tip = " Let's take this slowly. Watch one change at a time."
    if tip.strip() in text:
        return text
    return text.rstrip(".") + "." + tip


def _condense_narration(text: str) -> str:
    # Keep first two sentences if possible
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    if len(parts) <= 2:
        return text
    return " ".join(parts[:2])


def _relevel_narration(text: str, level: LearnerLevel) -> str:
    if level == LearnerLevel.BEGINNER:
        return text.rstrip(".") + ". In simple terms: follow the highlighted step."
    if level == LearnerLevel.ADVANCED:
        return _condense_narration(text)
    return text
