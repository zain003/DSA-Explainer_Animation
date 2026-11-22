"""Deterministic offline lesson templates (no LLM required)."""

from __future__ import annotations

from dsa_explainer.schema import (
    ActionType,
    LearnerLevel,
    LessonPlan,
    QuizOption,
    QuizQuestion,
    Scene,
    SceneAction,
    TopicKind,
)


def detect_topic_kind(topic: str) -> TopicKind:
    t = topic.lower()
    if any(w in t for w in ("bfs", "breadth", "graph")):
        return TopicKind.GRAPH_BFS
    if any(w in t for w in ("sort", "bubble")):
        return TopicKind.SORTING
    if any(w in t for w in ("tree", "bst", "binary search tree")):
        return TopicKind.TREE
    if "stack" in t:
        return TopicKind.STACK
    if "queue" in t:
        return TopicKind.QUEUE
    if any(w in t for w in ("linked list", "linkedlist", "list node")):
        return TopicKind.LINKED_LIST
    if "list" in t:
        return TopicKind.LINKED_LIST
    # default
    return TopicKind.QUEUE


def template_for(
    topic: str,
    level: LearnerLevel = LearnerLevel.BEGINNER,
    kind: TopicKind | None = None,
) -> LessonPlan:
    kind = kind or detect_topic_kind(topic)
    builders = {
        TopicKind.QUEUE: _queue_lesson,
        TopicKind.STACK: _stack_lesson,
        TopicKind.LINKED_LIST: _linked_list_lesson,
        TopicKind.TREE: _tree_lesson,
        TopicKind.GRAPH_BFS: _bfs_lesson,
        TopicKind.SORTING: _bubble_sort_lesson,
    }
    return builders[kind](topic, level)


def _queue_lesson(topic: str, level: LearnerLevel) -> LessonPlan:
    scenes = [
        Scene(
            id="s1",
            title="What is a Queue?",
            narration=(
                "A queue is a First In First Out structure. "
                "Think of a line at a ticket counter: the person who arrives first "
                "is served first. We enqueue at the rear and dequeue from the front."
            ),
            duration_hint_sec=8.0,
            actions=[
                SceneAction(type=ActionType.TITLE, args={"text": "Queues: FIFO"}),
                SceneAction(
                    type=ActionType.CREATE_QUEUE,
                    args={"values": []},
                    expected_state={"type": "queue", "items": [], "front": None, "rear": None},
                ),
            ],
        ),
        Scene(
            id="s2",
            title="Enqueue 10, then 20",
            narration=(
                "We enqueue ten. It becomes both the front and the rear. "
                "Next we enqueue twenty. Ten stays at the front; twenty is now at the rear."
            ),
            duration_hint_sec=8.0,
            actions=[
                SceneAction(
                    type=ActionType.ENQUEUE,
                    args={"value": 10},
                    expected_state={"type": "queue", "items": [10], "front": 10, "rear": 10},
                ),
                SceneAction(
                    type=ActionType.ENQUEUE,
                    args={"value": 20},
                    expected_state={"type": "queue", "items": [10, 20], "front": 10, "rear": 20},
                ),
            ],
        ),
        Scene(
            id="s3",
            title="Enqueue 30",
            narration=(
                "Enqueue thirty at the rear. The queue is now ten, twenty, thirty. "
                "Front is still ten. Rear is thirty."
            ),
            duration_hint_sec=6.0,
            actions=[
                SceneAction(
                    type=ActionType.ENQUEUE,
                    args={"value": 30},
                    expected_state={
                        "type": "queue",
                        "items": [10, 20, 30],
                        "front": 10,
                        "rear": 30,
                    },
                ),
            ],
        ),
        Scene(
            id="s4",
            title="Dequeue",
            narration=(
                "Dequeue removes from the front. Ten leaves the queue. "
                "Twenty becomes the new front, and thirty remains at the rear."
            ),
            duration_hint_sec=8.0,
            actions=[
                SceneAction(
                    type=ActionType.DEQUEUE,
                    args={},
                    expected_state={
                        "type": "queue",
                        "items": [20, 30],
                        "front": 20,
                        "rear": 30,
                    },
                ),
            ],
        ),
        Scene(
            id="s5",
            title="Peek at the front",
            narration=(
                "Front, or peek, lets us look at twenty without removing it. "
                "Queues preserve arrival order — that is the key idea of FIFO."
            ),
            duration_hint_sec=7.0,
            actions=[
                SceneAction(
                    type=ActionType.FRONT,
                    args={},
                    expected_state={
                        "type": "queue",
                        "items": [20, 30],
                        "front": 20,
                        "rear": 30,
                    },
                ),
            ],
        ),
    ]
    if level == LearnerLevel.BEGINNER:
        scenes[0].narration += " You only need to remember: enter at the back, leave at the front."

    quiz = [
        QuizQuestion(
            id="q1",
            prompt="After enqueue 1, enqueue 2, dequeue — what is at the front?",
            options=[
                QuizOption(id="a", text="1"),
                QuizOption(id="b", text="2"),
                QuizOption(id="c", text="empty"),
            ],
            correct_option_id="b",
            explanation="Dequeue removes 1; 2 becomes front.",
            verified=True,
        ),
        QuizQuestion(
            id="q2",
            prompt="Queue order is:",
            options=[
                QuizOption(id="a", text="LIFO"),
                QuizOption(id="b", text="FIFO"),
                QuizOption(id="c", text="Random"),
            ],
            correct_option_id="b",
            explanation="Queues are First In First Out.",
            verified=True,
        ),
    ]
    return LessonPlan(
        topic=topic,
        topic_kind=TopicKind.QUEUE,
        learner_level=level,
        learning_objectives=[
            "Define FIFO",
            "Perform enqueue and dequeue",
            "Identify front and rear",
        ],
        scenes=scenes,
        quiz=quiz,
    )


def _stack_lesson(topic: str, level: LearnerLevel) -> LessonPlan:
    scenes = [
        Scene(
            id="s1",
            title="What is a Stack?",
            narration=(
                "A stack is Last In First Out. Like a stack of plates: "
                "you put a plate on top, and you remove from the top."
            ),
            duration_hint_sec=7.0,
            actions=[
                SceneAction(type=ActionType.TITLE, args={"text": "Stacks: LIFO"}),
                SceneAction(
                    type=ActionType.CREATE_STACK,
                    args={"values": []},
                    expected_state={"type": "stack", "items": [], "top": None},
                ),
            ],
        ),
        Scene(
            id="s2",
            title="Push 5 and 8",
            narration="Push five onto the stack. Then push eight. Eight is now on top.",
            duration_hint_sec=7.0,
            actions=[
                SceneAction(
                    type=ActionType.PUSH,
                    args={"value": 5},
                    expected_state={"type": "stack", "items": [5], "top": 5},
                ),
                SceneAction(
                    type=ActionType.PUSH,
                    args={"value": 8},
                    expected_state={"type": "stack", "items": [5, 8], "top": 8},
                ),
            ],
        ),
        Scene(
            id="s3",
            title="Push 3",
            narration="Push three. The stack from bottom to top is five, eight, three. Top is three.",
            duration_hint_sec=6.0,
            actions=[
                SceneAction(
                    type=ActionType.PUSH,
                    args={"value": 3},
                    expected_state={"type": "stack", "items": [5, 8, 3], "top": 3},
                ),
            ],
        ),
        Scene(
            id="s4",
            title="Pop",
            narration="Pop removes the top. Three leaves. Eight is the new top.",
            duration_hint_sec=7.0,
            actions=[
                SceneAction(
                    type=ActionType.POP,
                    args={},
                    expected_state={"type": "stack", "items": [5, 8], "top": 8},
                ),
            ],
        ),
        Scene(
            id="s5",
            title="Peek",
            narration="Peek looks at eight without removing it. Remember: last in, first out.",
            duration_hint_sec=6.0,
            actions=[
                SceneAction(
                    type=ActionType.PEEK,
                    args={},
                    expected_state={"type": "stack", "items": [5, 8], "top": 8},
                ),
            ],
        ),
    ]
    quiz = [
        QuizQuestion(
            id="q1",
            prompt="Push 1, push 2, pop — what remains on top?",
            options=[
                QuizOption(id="a", text="1"),
                QuizOption(id="b", text="2"),
                QuizOption(id="c", text="empty"),
            ],
            correct_option_id="a",
            explanation="Pop removes 2; 1 remains.",
            verified=True,
        ),
    ]
    return LessonPlan(
        topic=topic,
        topic_kind=TopicKind.STACK,
        learner_level=level,
        learning_objectives=["Define LIFO", "Push and pop", "Identify the top"],
        scenes=scenes,
        quiz=quiz,
    )


def _linked_list_lesson(topic: str, level: LearnerLevel) -> LessonPlan:
    scenes = [
        Scene(
            id="s1",
            title="Linked List Basics",
            narration=(
                "A singly linked list stores values in nodes. Each node points to the next. "
                "Unlike arrays, nodes need not sit in contiguous memory."
            ),
            duration_hint_sec=8.0,
            actions=[
                SceneAction(type=ActionType.TITLE, args={"text": "Singly Linked Lists"}),
                SceneAction(
                    type=ActionType.CREATE_LIST,
                    args={"values": [1, 2, 3]},
                    expected_state={"type": "linked_list", "nodes": [1, 2, 3]},
                ),
            ],
        ),
        Scene(
            id="s2",
            title="Insert at head",
            narration="Insert zero at the head. Zero becomes the new first node, pointing to one.",
            duration_hint_sec=7.0,
            actions=[
                SceneAction(
                    type=ActionType.INSERT_HEAD,
                    args={"value": 0},
                    expected_state={"type": "linked_list", "nodes": [0, 1, 2, 3]},
                ),
            ],
        ),
        Scene(
            id="s3",
            title="Insert at tail",
            narration="Insert four at the tail. The last node now points to four, then null.",
            duration_hint_sec=7.0,
            actions=[
                SceneAction(
                    type=ActionType.INSERT_TAIL,
                    args={"value": 4},
                    expected_state={"type": "linked_list", "nodes": [0, 1, 2, 3, 4]},
                ),
            ],
        ),
        Scene(
            id="s4",
            title="Delete a value",
            narration="Delete two. The node holding one is rewired to point directly to three.",
            duration_hint_sec=7.0,
            actions=[
                SceneAction(
                    type=ActionType.DELETE_VALUE,
                    args={"value": 2},
                    expected_state={"type": "linked_list", "nodes": [0, 1, 3, 4]},
                ),
            ],
        ),
        Scene(
            id="s5",
            title="Traverse",
            narration="We traverse from head to tail: zero, one, three, four. That visits every node once.",
            duration_hint_sec=7.0,
            actions=[
                SceneAction(
                    type=ActionType.TRAVERSE,
                    args={},
                    expected_state={"type": "linked_list", "nodes": [0, 1, 3, 4]},
                ),
            ],
        ),
    ]
    quiz = [
        QuizQuestion(
            id="q1",
            prompt="Inserting at the head of a singly linked list is typically:",
            options=[
                QuizOption(id="a", text="O(1)"),
                QuizOption(id="b", text="O(n)"),
                QuizOption(id="c", text="O(n log n)"),
            ],
            correct_option_id="a",
            explanation="Only the head pointer changes.",
            verified=True,
        ),
    ]
    return LessonPlan(
        topic=topic,
        topic_kind=TopicKind.LINKED_LIST,
        learner_level=level,
        learning_objectives=["Describe nodes and next pointers", "Insert and delete", "Traverse"],
        scenes=scenes,
        quiz=quiz,
    )


def _tree_lesson(topic: str, level: LearnerLevel) -> LessonPlan:
    scenes = [
        Scene(
            id="s1",
            title="Binary Search Trees",
            narration=(
                "In a binary search tree, left children are smaller than the parent, "
                "and right children are larger. This keeps search efficient."
            ),
            duration_hint_sec=8.0,
            actions=[
                SceneAction(type=ActionType.TITLE, args={"text": "Binary Search Trees"}),
                SceneAction(
                    type=ActionType.CREATE_TREE,
                    args={"values": [8]},
                    expected_state={"type": "tree", "root": 8, "inorder": [8], "nodes": [8]},
                ),
            ],
        ),
        Scene(
            id="s2",
            title="Insert 3 and 10",
            narration="Insert three: it goes left of eight. Insert ten: it goes right of eight.",
            duration_hint_sec=8.0,
            actions=[
                SceneAction(
                    type=ActionType.INSERT_BST,
                    args={"value": 3},
                    expected_state={
                        "type": "tree",
                        "root": 8,
                        "inorder": [3, 8],
                        "nodes": [8, 3],
                    },
                ),
                SceneAction(
                    type=ActionType.INSERT_BST,
                    args={"value": 10},
                    expected_state={
                        "type": "tree",
                        "root": 8,
                        "inorder": [3, 8, 10],
                        "nodes": [8, 3, 10],
                    },
                ),
            ],
        ),
        Scene(
            id="s3",
            title="Insert 1 and 6",
            narration="Insert one under three on the left. Insert six under three on the right.",
            duration_hint_sec=8.0,
            actions=[
                SceneAction(
                    type=ActionType.INSERT_BST,
                    args={"value": 1},
                    expected_state={
                        "type": "tree",
                        "root": 8,
                        "inorder": [1, 3, 8, 10],
                        "nodes": [8, 3, 10, 1],
                    },
                ),
                SceneAction(
                    type=ActionType.INSERT_BST,
                    args={"value": 6},
                    expected_state={
                        "type": "tree",
                        "root": 8,
                        "inorder": [1, 3, 6, 8, 10],
                        "nodes": [8, 3, 10, 1, 6],
                    },
                ),
            ],
        ),
        Scene(
            id="s4",
            title="Inorder traversal",
            narration=(
                "Inorder traversal visits left, node, right. For a BST that yields sorted order: "
                "one, three, six, eight, ten."
            ),
            duration_hint_sec=8.0,
            actions=[
                SceneAction(
                    type=ActionType.TRAVERSE_INORDER,
                    args={},
                    expected_state={
                        "type": "tree",
                        "root": 8,
                        "inorder": [1, 3, 6, 8, 10],
                        "nodes": [8, 3, 10, 1, 6],
                    },
                ),
            ],
        ),
    ]
    quiz = [
        QuizQuestion(
            id="q1",
            prompt="Inorder traversal of a BST produces values in:",
            options=[
                QuizOption(id="a", text="Random order"),
                QuizOption(id="b", text="Sorted order"),
                QuizOption(id="c", text="Level order only"),
            ],
            correct_option_id="b",
            explanation="Left-root-right on a BST is sorted.",
            verified=True,
        ),
    ]
    return LessonPlan(
        topic=topic,
        topic_kind=TopicKind.TREE,
        learner_level=level,
        learning_objectives=["State BST invariant", "Insert nodes", "Explain inorder"],
        scenes=scenes,
        quiz=quiz,
    )


def _bfs_lesson(topic: str, level: LearnerLevel) -> LessonPlan:
    # Graph: A-B, A-C, B-D, C-D
    scenes = [
        Scene(
            id="s1",
            title="Breadth-First Search",
            narration=(
                "Breadth-first search explores a graph level by level using a queue. "
                "We start at A, connected to B and C. B and C connect onward to D."
            ),
            duration_hint_sec=9.0,
            actions=[
                SceneAction(type=ActionType.TITLE, args={"text": "Graph BFS"}),
                SceneAction(
                    type=ActionType.CREATE_GRAPH,
                    args={"edges": [["A", "B"], ["A", "C"], ["B", "D"], ["C", "D"]], "undirected": True},
                    expected_state={
                        "type": "graph",
                        "nodes": ["A", "B", "C", "D"],
                        "visit_order": [],
                        "queue": [],
                        "done": False,
                    },
                ),
            ],
        ),
        Scene(
            id="s2",
            title="Start at A",
            narration="Mark A visited and enqueue A. The frontier queue holds A.",
            duration_hint_sec=6.0,
            actions=[
                SceneAction(
                    type=ActionType.BFS_START,
                    args={"start": "A"},
                    expected_state={
                        "type": "graph",
                        "visit_order": [],
                        "queue": ["A"],
                        "visited": ["A"],
                    },
                ),
            ],
        ),
        Scene(
            id="s3",
            title="Visit A, enqueue B and C",
            narration=(
                "Dequeue A and visit it. Then enqueue unvisited neighbors B and C. "
                "Queue is now B, then C."
            ),
            duration_hint_sec=9.0,
            actions=[
                SceneAction(
                    type=ActionType.BFS_VISIT,
                    args={"node": "A"},
                    expected_state={
                        "type": "graph",
                        "visit_order": ["A"],
                        "queue": [],
                        "visited": ["A"],
                    },
                ),
                SceneAction(
                    type=ActionType.BFS_ENQUEUE_NEIGHBOR,
                    args={"node": "B"},
                    expected_state={
                        "type": "graph",
                        "visit_order": ["A"],
                        "queue": ["B"],
                        "visited": ["A", "B"],
                    },
                ),
                SceneAction(
                    type=ActionType.BFS_ENQUEUE_NEIGHBOR,
                    args={"node": "C"},
                    expected_state={
                        "type": "graph",
                        "visit_order": ["A"],
                        "queue": ["B", "C"],
                        "visited": ["A", "B", "C"],
                    },
                ),
            ],
        ),
        Scene(
            id="s4",
            title="Visit B, enqueue D",
            narration="Visit B. Its unvisited neighbor is D, so we enqueue D.",
            duration_hint_sec=7.0,
            actions=[
                SceneAction(
                    type=ActionType.BFS_VISIT,
                    args={"node": "B"},
                    expected_state={
                        "type": "graph",
                        "visit_order": ["A", "B"],
                        "queue": ["C"],
                        "visited": ["A", "B", "C"],
                    },
                ),
                SceneAction(
                    type=ActionType.BFS_ENQUEUE_NEIGHBOR,
                    args={"node": "D"},
                    expected_state={
                        "type": "graph",
                        "visit_order": ["A", "B"],
                        "queue": ["C", "D"],
                        "visited": ["A", "B", "C", "D"],
                    },
                ),
            ],
        ),
        Scene(
            id="s5",
            title="Finish C and D",
            narration=(
                "Visit C; D is already visited so we skip it. "
                "Visit D next. The queue is empty — BFS is done. Order was A, B, C, D."
            ),
            duration_hint_sec=10.0,
            actions=[
                SceneAction(
                    type=ActionType.BFS_VISIT,
                    args={"node": "C"},
                    expected_state={
                        "type": "graph",
                        "visit_order": ["A", "B", "C"],
                        "queue": ["D"],
                        "visited": ["A", "B", "C", "D"],
                    },
                ),
                SceneAction(
                    type=ActionType.BFS_VISIT,
                    args={"node": "D"},
                    expected_state={
                        "type": "graph",
                        "visit_order": ["A", "B", "C", "D"],
                        "queue": [],
                        "visited": ["A", "B", "C", "D"],
                    },
                ),
                SceneAction(
                    type=ActionType.BFS_DONE,
                    args={},
                    expected_state={
                        "type": "graph",
                        "visit_order": ["A", "B", "C", "D"],
                        "queue": [],
                        "done": True,
                    },
                ),
            ],
        ),
    ]
    quiz = [
        QuizQuestion(
            id="q1",
            prompt="BFS uses which auxiliary structure?",
            options=[
                QuizOption(id="a", text="Stack"),
                QuizOption(id="b", text="Queue"),
                QuizOption(id="c", text="Heap only"),
            ],
            correct_option_id="b",
            explanation="BFS explores level by level with a queue.",
            verified=True,
        ),
    ]
    return LessonPlan(
        topic=topic,
        topic_kind=TopicKind.GRAPH_BFS,
        learner_level=level,
        learning_objectives=["Explain BFS levels", "Use a queue frontier", "Produce visit order"],
        scenes=scenes,
        quiz=quiz,
    )


def _bubble_sort_lesson(topic: str, level: LearnerLevel) -> LessonPlan:
    scenes = [
        Scene(
            id="s1",
            title="Bubble Sort",
            narration=(
                "Bubble sort repeatedly compares adjacent pairs and swaps them if they are out of order. "
                "Larger values bubble toward the end."
            ),
            duration_hint_sec=8.0,
            actions=[
                SceneAction(type=ActionType.TITLE, args={"text": "Bubble Sort"}),
                SceneAction(
                    type=ActionType.CREATE_ARRAY,
                    args={"values": [4, 2, 3]},
                    expected_state={"type": "array", "values": [4, 2, 3], "sorted_from_end": 0},
                ),
            ],
        ),
        Scene(
            id="s2",
            title="Pass 1: compare and swap",
            narration="Compare four and two. They are out of order, so we swap. Array becomes two, four, three.",
            duration_hint_sec=8.0,
            actions=[
                SceneAction(
                    type=ActionType.COMPARE,
                    args={"i": 0, "j": 1},
                    expected_state={"type": "array", "values": [4, 2, 3]},
                ),
                SceneAction(
                    type=ActionType.SWAP,
                    args={"i": 0, "j": 1},
                    expected_state={"type": "array", "values": [2, 4, 3]},
                ),
            ],
        ),
        Scene(
            id="s3",
            title="Pass 1 continues",
            narration="Compare four and three. Swap them. Array is two, three, four. Mark four as sorted.",
            duration_hint_sec=8.0,
            actions=[
                SceneAction(
                    type=ActionType.COMPARE,
                    args={"i": 1, "j": 2},
                    expected_state={"type": "array", "values": [2, 4, 3]},
                ),
                SceneAction(
                    type=ActionType.SWAP,
                    args={"i": 1, "j": 2},
                    expected_state={"type": "array", "values": [2, 3, 4]},
                ),
                SceneAction(
                    type=ActionType.MARK_SORTED,
                    args={"count_from_end": 1},
                    expected_state={"type": "array", "values": [2, 3, 4], "sorted_from_end": 1},
                ),
            ],
        ),
        Scene(
            id="s4",
            title="Pass 2",
            narration=(
                "Compare two and three. They are already in order, no swap. "
                "The list is sorted: two, three, four."
            ),
            duration_hint_sec=8.0,
            actions=[
                SceneAction(
                    type=ActionType.COMPARE,
                    args={"i": 0, "j": 1},
                    expected_state={"type": "array", "values": [2, 3, 4], "sorted_from_end": 1},
                ),
                SceneAction(
                    type=ActionType.MARK_SORTED,
                    args={"count_from_end": 3},
                    expected_state={"type": "array", "values": [2, 3, 4], "sorted_from_end": 3},
                ),
            ],
        ),
    ]
    quiz = [
        QuizQuestion(
            id="q1",
            prompt="Bubble sort's typical worst-case time is:",
            options=[
                QuizOption(id="a", text="O(n)"),
                QuizOption(id="b", text="O(n log n)"),
                QuizOption(id="c", text="O(n²)"),
            ],
            correct_option_id="c",
            explanation="Nested passes over the array.",
            verified=True,
        ),
    ]
    return LessonPlan(
        topic=topic,
        topic_kind=TopicKind.SORTING,
        learner_level=level,
        learning_objectives=["Describe adjacent swaps", "Trace one bubble pass"],
        scenes=scenes,
        quiz=quiz,
    )
