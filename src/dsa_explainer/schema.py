"""Structured scene-plan schema.

The LLM never draws freely — it emits a LessonPlan that the renderer
and verifier both consume.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class TopicKind(str, Enum):
    LINKED_LIST = "linked_list"
    STACK = "stack"
    QUEUE = "queue"
    TREE = "tree"
    GRAPH_BFS = "graph_bfs"
    SORTING = "sorting"


class LearnerLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class ActionType(str, Enum):
    # Shared / UI
    TITLE = "title"
    NARRATE = "narrate"
    HIGHLIGHT = "highlight"
    CLEAR_HIGHLIGHT = "clear_highlight"
    SET_LABEL = "set_label"

    # Linked list
    CREATE_LIST = "create_list"
    INSERT_HEAD = "insert_head"
    INSERT_TAIL = "insert_tail"
    INSERT_AT = "insert_at"
    DELETE_VALUE = "delete_value"
    TRAVERSE = "traverse"

    # Stack
    CREATE_STACK = "create_stack"
    PUSH = "push"
    POP = "pop"
    PEEK = "peek"

    # Queue
    CREATE_QUEUE = "create_queue"
    ENQUEUE = "enqueue"
    DEQUEUE = "dequeue"
    FRONT = "front"

    # Tree
    CREATE_TREE = "create_tree"
    INSERT_BST = "insert_bst"
    TRAVERSE_INORDER = "traverse_inorder"
    TRAVERSE_PREORDER = "traverse_preorder"
    TRAVERSE_POSTORDER = "traverse_postorder"

    # Graph BFS
    CREATE_GRAPH = "create_graph"
    BFS_START = "bfs_start"
    BFS_VISIT = "bfs_visit"
    BFS_ENQUEUE_NEIGHBOR = "bfs_enqueue_neighbor"
    BFS_DONE = "bfs_done"

    # Sorting (bubble as the covered sorting algorithm)
    CREATE_ARRAY = "create_array"
    COMPARE = "compare"
    SWAP = "swap"
    MARK_SORTED = "mark_sorted"


class SceneAction(BaseModel):
    """One atomic visual + state change."""

    type: ActionType
    args: dict[str, Any] = Field(default_factory=dict)
    expected_state: dict[str, Any] | None = Field(
        default=None,
        description="Canonical structure state after this action, used by the verifier.",
    )


class Scene(BaseModel):
    """One timed beat of the lesson."""

    id: str
    title: str
    narration: str = Field(min_length=1)
    duration_hint_sec: float = Field(default=4.0, ge=1.0, le=60.0)
    actions: list[SceneAction] = Field(min_length=1)
    visual_focus: str | None = None

    @field_validator("id")
    @classmethod
    def non_empty_id(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("scene id must be non-empty")
        return v.strip()


class QuizOption(BaseModel):
    id: str
    text: str


class QuizQuestion(BaseModel):
    id: str
    prompt: str
    options: list[QuizOption] = Field(min_length=2)
    correct_option_id: str
    explanation: str
    verified: bool = False

    @model_validator(mode="after")
    def correct_must_exist(self) -> QuizQuestion:
        ids = {o.id for o in self.options}
        if self.correct_option_id not in ids:
            raise ValueError("correct_option_id must match an option")
        return self


class LessonPlan(BaseModel):
    """Validated plan produced by the lesson planner."""

    topic: str
    topic_kind: TopicKind
    learner_level: LearnerLevel = LearnerLevel.BEGINNER
    learning_objectives: list[str] = Field(min_length=1)
    scenes: list[Scene] = Field(min_length=2)
    quiz: list[QuizQuestion] = Field(default_factory=list)
    estimated_duration_sec: float = Field(default=0.0, ge=0.0)
    version: int = 1
    revision_notes: str | None = None

    @model_validator(mode="after")
    def compute_duration(self) -> LessonPlan:
        total = sum(s.duration_hint_sec for s in self.scenes)
        # Quiz cards add a bit of runtime when rendered
        total += max(0, len(self.quiz)) * 5.0
        object.__setattr__(self, "estimated_duration_sec", total)
        return self

    def scene_by_id(self, scene_id: str) -> Scene:
        for scene in self.scenes:
            if scene.id == scene_id:
                return scene
        raise KeyError(f"No scene with id={scene_id!r}")


class VerificationIssue(BaseModel):
    scene_id: str
    action_index: int
    message: str
    expected: Any = None
    actual: Any = None


class VerificationReport(BaseModel):
    ok: bool
    issues: list[VerificationIssue] = Field(default_factory=list)
    final_state: dict[str, Any] = Field(default_factory=dict)


class RevisionRequest(BaseModel):
    kind: Literal[
        "slow_down",
        "speed_up",
        "relevel",
        "rewrite_narration",
        "replace_scene",
    ]
    scene_id: str | None = None
    target_level: LearnerLevel | None = None
    instruction: str = ""


# JSON Schema export for LLM tool-calling / external validators
LESSON_PLAN_JSON_SCHEMA: dict[str, Any] = LessonPlan.model_json_schema()
