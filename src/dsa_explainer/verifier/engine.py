"""Step verifier: execute real DS/algorithm code and match plan state."""

from __future__ import annotations

from typing import Any

from dsa_explainer.schema import (
    ActionType,
    LessonPlan,
    TopicKind,
    VerificationIssue,
    VerificationReport,
)
from dsa_explainer.verifier.structures import (
    BinarySearchTree,
    Graph,
    LinkedList,
    Queue,
    SortArray,
    Stack,
)

# Actions that do not change structural state
PASS_THROUGH = {
    ActionType.TITLE,
    ActionType.NARRATE,
    ActionType.HIGHLIGHT,
    ActionType.CLEAR_HIGHLIGHT,
    ActionType.SET_LABEL,
    ActionType.PEEK,
    ActionType.FRONT,
    ActionType.TRAVERSE,
    ActionType.TRAVERSE_INORDER,
    ActionType.TRAVERSE_PREORDER,
    ActionType.TRAVERSE_POSTORDER,
}


def _normalize(state: dict[str, Any] | None) -> dict[str, Any] | None:
    if state is None:
        return None
    # Convert lists of pairs etc. for stable compare
    out: dict[str, Any] = {}
    for k, v in state.items():
        if isinstance(v, list):
            out[k] = [
                list(x) if isinstance(x, (list, tuple)) else x for x in v
            ]
        elif isinstance(v, tuple):
            out[k] = list(v)
        elif isinstance(v, set):
            out[k] = sorted(v)
        else:
            out[k] = v
    return out


def _states_equal(expected: dict[str, Any] | None, actual: dict[str, Any]) -> bool:
    if expected is None:
        return True
    exp = _normalize(expected) or {}
    act = _normalize(actual) or {}
    # Only compare keys the plan claimed
    for key, value in exp.items():
        if key not in act:
            return False
        if act[key] != value:
            return False
    return True


def _require_arg(args: dict[str, Any], key: str) -> Any:
    if key not in args:
        raise KeyError(f"missing required arg {key!r}")
    return args[key]


class StructureRunner:
    """Dispatches actions onto the correct structure for a topic kind."""

    def __init__(self, topic_kind: TopicKind) -> None:
        self.topic_kind = topic_kind
        self.ll = LinkedList()
        self.stack = Stack()
        self.queue = Queue()
        self.tree = BinarySearchTree()
        self.graph = Graph()
        self.array = SortArray()

    def snapshot(self) -> dict[str, Any]:
        mapping = {
            TopicKind.LINKED_LIST: self.ll.snapshot,
            TopicKind.STACK: self.stack.snapshot,
            TopicKind.QUEUE: self.queue.snapshot,
            TopicKind.TREE: self.tree.snapshot,
            TopicKind.GRAPH_BFS: self.graph.snapshot,
            TopicKind.SORTING: self.array.snapshot,
        }
        return mapping[self.topic_kind]()

    def apply(self, action_type: ActionType, args: dict[str, Any]) -> Any:
        if action_type in PASS_THROUGH:
            if action_type == ActionType.TRAVERSE:
                return self.ll.traverse()
            if action_type == ActionType.TRAVERSE_INORDER:
                return self.tree.inorder()
            if action_type == ActionType.TRAVERSE_PREORDER:
                return self.tree.preorder()
            if action_type == ActionType.TRAVERSE_POSTORDER:
                return self.tree.postorder()
            if action_type == ActionType.PEEK:
                return self.stack.peek()
            if action_type == ActionType.FRONT:
                return self.queue.front()
            return None

        handlers = {
            ActionType.CREATE_LIST: lambda: self.ll.create(
                list(_require_arg(args, "values"))
            ),
            ActionType.INSERT_HEAD: lambda: self.ll.insert_head(int(_require_arg(args, "value"))),
            ActionType.INSERT_TAIL: lambda: self.ll.insert_tail(int(_require_arg(args, "value"))),
            ActionType.INSERT_AT: lambda: self.ll.insert_at(
                int(_require_arg(args, "index")), int(_require_arg(args, "value"))
            ),
            ActionType.DELETE_VALUE: lambda: self.ll.delete_value(int(_require_arg(args, "value"))),
            ActionType.CREATE_STACK: lambda: self.stack.create(list(args.get("values") or [])),
            ActionType.PUSH: lambda: self.stack.push(int(_require_arg(args, "value"))),
            ActionType.POP: lambda: self.stack.pop(),
            ActionType.CREATE_QUEUE: lambda: self.queue.create(list(args.get("values") or [])),
            ActionType.ENQUEUE: lambda: self.queue.enqueue(int(_require_arg(args, "value"))),
            ActionType.DEQUEUE: lambda: self.queue.dequeue(),
            ActionType.CREATE_TREE: lambda: self.tree.create(list(_require_arg(args, "values"))),
            ActionType.INSERT_BST: lambda: self.tree.insert(int(_require_arg(args, "value"))),
            ActionType.CREATE_GRAPH: lambda: self.graph.create(
                [list(e) for e in _require_arg(args, "edges")],
                undirected=bool(args.get("undirected", True)),
            ),
            ActionType.BFS_START: lambda: self.graph.bfs_start(str(_require_arg(args, "start"))),
            ActionType.BFS_VISIT: lambda: self.graph.bfs_visit(str(_require_arg(args, "node"))),
            ActionType.BFS_ENQUEUE_NEIGHBOR: lambda: self.graph.bfs_enqueue_neighbor(
                str(_require_arg(args, "node"))
            ),
            ActionType.BFS_DONE: lambda: self.graph.bfs_done(),
            ActionType.CREATE_ARRAY: lambda: self.array.create(list(_require_arg(args, "values"))),
            ActionType.COMPARE: lambda: self.array.compare(
                int(_require_arg(args, "i")), int(_require_arg(args, "j"))
            ),
            ActionType.SWAP: lambda: self.array.swap(
                int(_require_arg(args, "i")), int(_require_arg(args, "j"))
            ),
            ActionType.MARK_SORTED: lambda: self.array.mark_sorted(
                int(_require_arg(args, "count_from_end"))
            ),
        }

        if action_type not in handlers:
            raise ValueError(f"unsupported action for verification: {action_type}")
        return handlers[action_type]()


def verify_plan(plan: LessonPlan) -> VerificationReport:
    runner = StructureRunner(plan.topic_kind)
    issues: list[VerificationIssue] = []

    for scene in plan.scenes:
        for idx, action in enumerate(scene.actions):
            try:
                runner.apply(action.type, action.args)
            except Exception as exc:  # noqa: BLE001 — collect all issues
                issues.append(
                    VerificationIssue(
                        scene_id=scene.id,
                        action_index=idx,
                        message=f"Action failed: {exc}",
                        expected=action.expected_state,
                        actual=None,
                    )
                )
                continue

            actual = runner.snapshot()
            if action.expected_state is not None and not _states_equal(
                action.expected_state, actual
            ):
                issues.append(
                    VerificationIssue(
                        scene_id=scene.id,
                        action_index=idx,
                        message="expected_state does not match true structure state",
                        expected=action.expected_state,
                        actual=actual,
                    )
                )

            # Narration sanity: if expected_state lists values, narration should
            # mention at least one of them for mutation scenes (soft check skipped
            # for title/narrate-only actions).

    return VerificationReport(
        ok=len(issues) == 0,
        issues=issues,
        final_state=runner.snapshot(),
    )


def verify_quiz_answers(plan: LessonPlan) -> list[str]:
    """Return list of quiz problem descriptions; empty means all ok."""
    problems: list[str] = []
    for q in plan.quiz:
        if not q.verified:
            problems.append(f"Quiz {q.id} is not marked verified")
        ids = {o.id for o in q.options}
        if q.correct_option_id not in ids:
            problems.append(f"Quiz {q.id} correct_option_id invalid")
    return problems
