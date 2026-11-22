"""Lesson planner: topic + level → validated LessonPlan JSON."""

from __future__ import annotations

import json
import re
from typing import Any

from dsa_explainer.config import get_settings
from dsa_explainer.planner.templates import detect_topic_kind, template_for
from dsa_explainer.planner.validator import validate_plan
from dsa_explainer.schema import LESSON_PLAN_JSON_SCHEMA, LearnerLevel, LessonPlan, TopicKind
from dsa_explainer.verifier.engine import verify_plan


SYSTEM_PROMPT = """You are a careful DSA lesson planner.
Return ONLY valid JSON matching the provided schema.
Rules:
- Emit a structured scene plan. Do NOT invent free-form drawing instructions.
- Every mutating action MUST include expected_state that matches a real execution.
- Cover the topic with clear narration suitable for the learner level.
- estimated duration via scene duration_hint_sec sums should be >= 30 seconds.
- Include 1-3 quiz questions with verified=true and a correct_option_id.
- Use only these action types as needed for the topic_kind.
Supported topic_kind values: linked_list, stack, queue, tree, graph_bfs, sorting.
"""


def _llm_plan(topic: str, level: LearnerLevel, kind: TopicKind) -> dict[str, Any]:
    settings = get_settings()
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY missing; use OFFLINE_MODE=1 or set a key")

    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
    user = {
        "topic": topic,
        "learner_level": level.value,
        "topic_kind": kind.value,
        "schema": LESSON_PLAN_JSON_SCHEMA,
        "hints": (
            "Prefer small concrete examples. "
            "For graph_bfs use letter node labels. "
            "For sorting use bubble sort on a short array."
        ),
    }
    response = client.chat.completions.create(
        model=settings.openai_model,
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(user)},
        ],
    )
    content = response.choices[0].message.content or "{}"
    return json.loads(content)


def _repair_with_template(topic: str, level: LearnerLevel, kind: TopicKind) -> LessonPlan:
    return template_for(topic, level, kind)


def plan_lesson(
    topic: str,
    level: LearnerLevel | str = LearnerLevel.BEGINNER,
    topic_kind: TopicKind | str | None = None,
    *,
    offline: bool | None = None,
    max_attempts: int = 2,
) -> LessonPlan:
    """Produce a schema-valid, step-verified lesson plan."""
    settings = get_settings()
    if isinstance(level, str):
        level = LearnerLevel(level)
    if topic_kind is None:
        kind = detect_topic_kind(topic)
    elif isinstance(topic_kind, str):
        kind = TopicKind(topic_kind)
    else:
        kind = topic_kind

    use_offline = settings.offline_mode if offline is None else offline
    if use_offline or not settings.openai_api_key:
        plan = template_for(topic, level, kind)
        plan = validate_plan(plan)
        report = verify_plan(plan)
        if not report.ok:
            raise RuntimeError(f"Template plan failed verification: {report.issues}")
        return plan

    last_error: Exception | None = None
    for _ in range(max_attempts):
        try:
            raw = _llm_plan(topic, level, kind)
            # Ensure required fields if model omitted them
            raw.setdefault("topic", topic)
            raw.setdefault("topic_kind", kind.value)
            raw.setdefault("learner_level", level.value)
            plan = validate_plan(raw)
            report = verify_plan(plan)
            if report.ok:
                return plan
            last_error = RuntimeError(f"Verification failed: {report.model_dump()}")
        except Exception as exc:  # noqa: BLE001
            last_error = exc

    # Safe fallback: deterministic verified templates
    plan = _repair_with_template(topic, level, kind)
    plan = validate_plan(plan)
    report = verify_plan(plan)
    if not report.ok:
        raise RuntimeError(f"Fallback template invalid: {report.issues}") from last_error
    plan.revision_notes = f"Fell back to template after LLM/verify issues: {last_error}"
    return plan


def plan_from_json_file(path: str) -> LessonPlan:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    plan = validate_plan(data)
    report = verify_plan(plan)
    if not report.ok:
        raise RuntimeError(f"Plan failed verification: {report.issues}")
    return plan


def extract_json_block(text: str) -> dict[str, Any]:
    """Utility for models that wrap JSON in markdown fences."""
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence:
        return json.loads(fence.group(1))
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        return json.loads(text[start : end + 1])
    raise ValueError("No JSON object found")
