"""Optional LLM narration polish — never changes structural actions."""

from __future__ import annotations

import json

from dsa_explainer.config import get_settings
from dsa_explainer.schema import LearnerLevel, LessonPlan


def enrich_narration(plan: LessonPlan, *, offline: bool | None = None) -> LessonPlan:
    """Rewrite narration text only, keeping actions/expected_state intact."""
    settings = get_settings()
    use_offline = settings.offline_mode if offline is None else offline
    if use_offline or not settings.openai_api_key:
        return _offline_polish(plan)

    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
    payload = {
        "learner_level": plan.learner_level.value,
        "scenes": [{"id": s.id, "title": s.title, "narration": s.narration} for s in plan.scenes],
    }
    response = client.chat.completions.create(
        model=settings.openai_model,
        temperature=0.3,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "Rewrite each scene narration to be clearer for the learner level. "
                    "Do not change facts or introduce new algorithm steps. "
                    "Return JSON {\"scenes\":[{\"id\":\"...\",\"narration\":\"...\"}]}."
                ),
            },
            {"role": "user", "content": json.dumps(payload)},
        ],
    )
    data = json.loads(response.choices[0].message.content or "{}")
    by_id = {item["id"]: item["narration"] for item in data.get("scenes", []) if "id" in item}
    new_scenes = []
    for scene in plan.scenes:
        if scene.id in by_id and by_id[scene.id].strip():
            new_scenes.append(scene.model_copy(update={"narration": by_id[scene.id].strip()}))
        else:
            new_scenes.append(scene)
    return plan.model_copy(update={"scenes": new_scenes})


def _offline_polish(plan: LessonPlan) -> LessonPlan:
    if plan.learner_level != LearnerLevel.BEGINNER:
        return plan
    new_scenes = []
    for scene in plan.scenes:
        text = scene.narration
        if not text.endswith("."):
            text += "."
        new_scenes.append(scene.model_copy(update={"narration": text}))
    return plan.model_copy(update={"scenes": new_scenes})
