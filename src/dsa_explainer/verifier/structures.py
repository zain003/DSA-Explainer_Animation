"""Canonical in-memory structures used by the step verifier.

These are the source of truth. Scene expected_state must match these
snapshots after each action.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LinkedList:
    nodes: list[int] = field(default_factory=list)

    def snapshot(self) -> dict[str, Any]:
        return {"type": "linked_list", "nodes": list(self.nodes)}

    def create(self, values: list[int]) -> None:
        self.nodes = list(values)

    def insert_head(self, value: int) -> None:
        self.nodes.insert(0, value)

    def insert_tail(self, value: int) -> None:
        self.nodes.append(value)

    def insert_at(self, index: int, value: int) -> None:
        if index < 0 or index > len(self.nodes):
            raise IndexError(f"insert_at index {index} out of range")
        self.nodes.insert(index, value)

    def delete_value(self, value: int) -> None:
        if value not in self.nodes:
            raise ValueError(f"value {value} not in list")
        self.nodes.remove(value)

    def traverse(self) -> list[int]:
        return list(self.nodes)


@dataclass
class Stack:
    items: list[int] = field(default_factory=list)

    def snapshot(self) -> dict[str, Any]:
        return {"type": "stack", "items": list(self.items), "top": self.items[-1] if self.items else None}

    def create(self, values: list[int] | None = None) -> None:
        self.items = list(values or [])

    def push(self, value: int) -> None:
        self.items.append(value)

    def pop(self) -> int:
        if not self.items:
            raise IndexError("pop from empty stack")
        return self.items.pop()

    def peek(self) -> int | None:
        return self.items[-1] if self.items else None


@dataclass
class Queue:
    items: deque[int] = field(default_factory=deque)

    def snapshot(self) -> dict[str, Any]:
        data = list(self.items)
        return {
            "type": "queue",
            "items": data,
            "front": data[0] if data else None,
            "rear": data[-1] if data else None,
        }

    def create(self, values: list[int] | None = None) -> None:
        self.items = deque(values or [])

    def enqueue(self, value: int) -> None:
        self.items.append(value)

    def dequeue(self) -> int:
        if not self.items:
            raise IndexError("dequeue from empty queue")
        return self.items.popleft()

    def front(self) -> int | None:
        return self.items[0] if self.items else None


@dataclass
class BSTNode:
    value: int
    left: BSTNode | None = None
    right: BSTNode | None = None


@dataclass
class BinarySearchTree:
    root: BSTNode | None = None

    def snapshot(self) -> dict[str, Any]:
        return {
            "type": "tree",
            "root": self.root.value if self.root else None,
            "inorder": self.inorder(),
            "preorder": self.preorder(),
            "nodes": self._level_order_values(),
        }

    def create(self, values: list[int]) -> None:
        self.root = None
        for v in values:
            self.insert(v)

    def insert(self, value: int) -> None:
        if self.root is None:
            self.root = BSTNode(value)
            return
        cur = self.root
        while True:
            if value < cur.value:
                if cur.left is None:
                    cur.left = BSTNode(value)
                    return
                cur = cur.left
            elif value > cur.value:
                if cur.right is None:
                    cur.right = BSTNode(value)
                    return
                cur = cur.right
            else:
                return  # duplicate ignored

    def inorder(self) -> list[int]:
        out: list[int] = []

        def walk(n: BSTNode | None) -> None:
            if not n:
                return
            walk(n.left)
            out.append(n.value)
            walk(n.right)

        walk(self.root)
        return out

    def preorder(self) -> list[int]:
        out: list[int] = []

        def walk(n: BSTNode | None) -> None:
            if not n:
                return
            out.append(n.value)
            walk(n.left)
            walk(n.right)

        walk(self.root)
        return out

    def postorder(self) -> list[int]:
        out: list[int] = []

        def walk(n: BSTNode | None) -> None:
            if not n:
                return
            walk(n.left)
            walk(n.right)
            out.append(n.value)

        walk(self.root)
        return out

    def _level_order_values(self) -> list[int]:
        if not self.root:
            return []
        result: list[int] = []
        q: deque[BSTNode] = deque([self.root])
        while q:
            n = q.popleft()
            result.append(n.value)
            if n.left:
                q.append(n.left)
            if n.right:
                q.append(n.right)
        return result


@dataclass
class Graph:
    adjacency: dict[str, list[str]] = field(default_factory=dict)
    visit_order: list[str] = field(default_factory=list)
    queue: list[str] = field(default_factory=list)
    visited: set[str] = field(default_factory=set)
    started: bool = False
    done: bool = False

    def snapshot(self) -> dict[str, Any]:
        return {
            "type": "graph",
            "nodes": sorted(self.adjacency.keys()),
            "edges": sorted(
                (u, v) for u, nbrs in self.adjacency.items() for v in nbrs if u <= v
            ),
            "visit_order": list(self.visit_order),
            "queue": list(self.queue),
            "visited": sorted(self.visited),
            "done": self.done,
        }

    def create(self, edges: list[list[str]], undirected: bool = True) -> None:
        self.adjacency = {}
        self.visit_order = []
        self.queue = []
        self.visited = set()
        self.started = False
        self.done = False
        for edge in edges:
            if len(edge) != 2:
                raise ValueError(f"edge must have 2 nodes, got {edge}")
            u, v = edge
            self.adjacency.setdefault(u, [])
            self.adjacency.setdefault(v, [])
            if v not in self.adjacency[u]:
                self.adjacency[u].append(v)
            if undirected and u not in self.adjacency[v]:
                self.adjacency[v].append(u)

    def bfs_start(self, start: str) -> None:
        if start not in self.adjacency:
            raise KeyError(f"start node {start!r} not in graph")
        self.visit_order = []
        self.visited = {start}
        self.queue = [start]
        self.started = True
        self.done = False

    def bfs_visit(self, node: str) -> None:
        if not self.queue or self.queue[0] != node:
            raise ValueError(f"BFS expected to visit {self.queue[:1]!r}, got {node!r}")
        self.queue.pop(0)
        self.visit_order.append(node)

    def bfs_enqueue_neighbor(self, node: str) -> None:
        if node in self.visited:
            raise ValueError(f"neighbor {node!r} already visited")
        # Must be adjacent to some visited node (typically current)
        neighbors_of_visited = {
            n for v in self.visited for n in self.adjacency.get(v, [])
        }
        if node not in neighbors_of_visited and node not in self.adjacency:
            raise ValueError(f"{node!r} is not a valid BFS neighbor")
        # Soft check: node should be adjacent to last visited if any
        if self.visit_order:
            current = self.visit_order[-1]
            if node not in self.adjacency.get(current, []):
                # still allow if adjacent to any dequeued-but-frontier path;
                # require adjacency to some visited node
                if node not in neighbors_of_visited:
                    raise ValueError(f"{node!r} not adjacent to visited set")
        self.visited.add(node)
        self.queue.append(node)

    def bfs_done(self) -> None:
        if self.queue:
            raise ValueError("BFS not done; queue still has nodes")
        self.done = True


@dataclass
class SortArray:
    values: list[int] = field(default_factory=list)
    sorted_prefix_from_end: int = 0
    last_compare: tuple[int, int] | None = None

    def snapshot(self) -> dict[str, Any]:
        return {
            "type": "array",
            "values": list(self.values),
            "sorted_from_end": self.sorted_prefix_from_end,
            "last_compare": list(self.last_compare) if self.last_compare else None,
        }

    def create(self, values: list[int]) -> None:
        self.values = list(values)
        self.sorted_prefix_from_end = 0
        self.last_compare = None

    def compare(self, i: int, j: int) -> bool:
        self.last_compare = (i, j)
        return self.values[i] > self.values[j]

    def swap(self, i: int, j: int) -> None:
        self.values[i], self.values[j] = self.values[j], self.values[i]

    def mark_sorted(self, count_from_end: int) -> None:
        self.sorted_prefix_from_end = count_from_end
