from dsa_explainer.planner.templates import template_for
from dsa_explainer.quiz.generator import generate_quiz
from dsa_explainer.schema import LearnerLevel, TopicKind


def test_quiz_verified() -> None:
    for kind in TopicKind:
        plan = template_for("t", LearnerLevel.BEGINNER, kind)
        plan = plan.model_copy(update={"quiz": []})
        quiz = generate_quiz(plan)
        assert quiz, f"no quiz for {kind}"
        assert all(q.verified for q in quiz)
