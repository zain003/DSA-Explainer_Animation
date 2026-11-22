from dsa_explainer.planner.templates import template_for
from dsa_explainer.schema import LearnerLevel, TopicKind
from dsa_explainer.verifier.engine import verify_plan


def test_all_templates_verify() -> None:
    for kind in TopicKind:
        plan = template_for(f"demo {kind.value}", LearnerLevel.BEGINNER, kind)
        report = verify_plan(plan)
        assert report.ok, f"{kind}: {report.issues}"


def test_queue_duration_at_least_30s() -> None:
    plan = template_for("how does a queue work", LearnerLevel.BEGINNER, TopicKind.QUEUE)
    assert plan.estimated_duration_sec >= 30
