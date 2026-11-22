"""Validate a lesson plan against the Pydantic schema and duration rules."""

from __future__ import annotations

from dsa_explainer.config import get_settings
from dsa_explainer.schema import LessonPlan


class PlanValidationError(ValueError):
    pass


def validate_plan(data: dict | LessonPlan) -> LessonPlan:
    if isinstance(data, LessonPlan):
        plan = data
    else:
        plan = LessonPlan.model_validate(data)

    settings = get_settings()
    if plan.estimated_duration_sec < settings.min_video_seconds:
        raise PlanValidationError(
            f"Lesson too short ({plan.estimated_duration_sec:.1f}s); "
            f"need at least {settings.min_video_seconds}s"
        )

    if len(plan.scenes) < 2:
        raise PlanValidationError("Need at least 2 scenes")

    ids = [s.id for s in plan.scenes]
    if len(ids) != len(set(ids)):
        raise PlanValidationError("Scene ids must be unique")

    return plan
