from dsa_explainer.planner.templates import template_for
from dsa_explainer.revision.revise import apply_revision, parse_revision_utterance
from dsa_explainer.schema import LearnerLevel, TopicKind


def test_parse_slow_down_step() -> None:
    req = parse_revision_utterance("slow down step 4")
    assert req.kind == "slow_down"
    assert req.scene_id == "s4"


def test_apply_slow_down_only_one_scene() -> None:
    plan = template_for("queue", LearnerLevel.BEGINNER, TopicKind.QUEUE)
    before = {s.id: s.duration_hint_sec for s in plan.scenes}
    revised = apply_revision(plan, parse_revision_utterance("slow down step 4"))
    assert revised.version == plan.version + 1
    for s in revised.scenes:
        if s.id == "s4":
            assert s.duration_hint_sec > before["s4"]
        else:
            assert s.duration_hint_sec == before[s.id]
