from dsa_explainer.planner.planner import plan_lesson
from dsa_explainer.planner.templates import detect_topic_kind
from dsa_explainer.schema import LearnerLevel, TopicKind


def test_detect_topics() -> None:
    assert detect_topic_kind("how does a queue work") == TopicKind.QUEUE
    assert detect_topic_kind("show BFS on this graph") == TopicKind.GRAPH_BFS
    assert detect_topic_kind("linked list insert") == TopicKind.LINKED_LIST


def test_offline_plan() -> None:
    plan = plan_lesson("how does a queue work", level=LearnerLevel.BEGINNER, offline=True)
    assert plan.topic_kind == TopicKind.QUEUE
    assert len(plan.scenes) >= 2
