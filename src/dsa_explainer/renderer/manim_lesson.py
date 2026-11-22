"""Manim scene that draws a validated LessonPlan (never free-form LLM drawing)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from manim import (
    BLUE,
    DOWN,
    GREEN,
    GREY,
    LEFT,
    ORANGE,
    ORIGIN,
    RIGHT,
    UP,
    WHITE,
    YELLOW,
    Circle,
    FadeIn,
    FadeOut,
    Indicate,
    Line,
    RoundedRectangle,
    Scene,
    Square,
    Text,
    Transform,
    VGroup,
    Write,
)

from dsa_explainer.schema import ActionType, LessonPlan, TopicKind


def _load_plan(path: str | Path) -> LessonPlan:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return LessonPlan.model_validate(data)


class DSALessonScene(Scene):
    """Reads DSA_LESSON_PLAN and optional DSA_AUDIO_MANIFEST from the environment."""

    def construct(self) -> None:
        plan_path = os.environ.get("DSA_LESSON_PLAN")
        if not plan_path:
            raise RuntimeError("Set DSA_LESSON_PLAN to a plan.json path")

        self.plan = _load_plan(plan_path)
        self.audio_manifest = None
        audio_path = os.environ.get("DSA_AUDIO_MANIFEST")
        if audio_path and Path(audio_path).exists():
            self.audio_manifest = json.loads(Path(audio_path).read_text(encoding="utf-8"))

        self.state: dict[str, Any] = {}
        self.title_mobject = None
        self.structure_group = VGroup()
        self.add(self.structure_group)

        audio_by_id: dict[str, Path] = {}
        if self.audio_manifest:
            lesson_dir = Path(plan_path).parent
            for item in self.audio_manifest.get("scenes", []):
                audio_by_id[item["id"]] = lesson_dir / item["wav"]

        for scene in self.plan.scenes:
            self._play_scene(scene, audio_by_id.get(scene.id))

        quiz_audio: dict[str, tuple[Path, float]] = {}
        if self.audio_manifest:
            lesson_dir = Path(plan_path).parent
            for item in self.audio_manifest.get("quiz", []):
                quiz_audio[item["id"]] = (lesson_dir / item["wav"], item["duration_sec"])

        for q in self.plan.quiz:
            self._play_quiz(q, quiz_audio.get(q.id))

    def _scene_wait(self, seconds: float, audio_file: Path | None) -> None:
        if audio_file and audio_file.exists():
            try:
                self.add_sound(str(audio_file))
            except Exception:
                pass
        self.wait(max(1.0, seconds))

    def _set_title(self, text: str) -> None:
        new_title = Text(text, font_size=36, color=WHITE).to_edge(UP)
        if self.title_mobject is None:
            self.play(FadeIn(new_title), run_time=0.5)
            self.title_mobject = new_title
        else:
            self.play(Transform(self.title_mobject, new_title), run_time=0.5)

    def _play_scene(self, scene, audio_file: Path | None) -> None:
        self._set_title(scene.title)
        n = max(1, len(scene.actions))
        per = max(0.6, (scene.duration_hint_sec * 0.55) / n)
        for action in scene.actions:
            self._apply_action(action.type, action.args, run_time=per)
        remaining = max(0.5, scene.duration_hint_sec - per * n)
        if self.audio_manifest:
            for item in self.audio_manifest.get("scenes", []):
                if item["id"] == scene.id:
                    remaining = max(remaining, item["duration_sec"] - per * n)
                    break
        self._scene_wait(remaining, audio_file)

    def _play_quiz(self, q, audio_info) -> None:
        self.clear()
        self.title_mobject = None
        self.structure_group = VGroup()
        self.add(self.structure_group)
        header = Text("Quiz", font_size=40, color=YELLOW).to_edge(UP)
        prompt = Text(q.prompt, font_size=28, color=WHITE).next_to(header, DOWN, buff=0.6)
        opts = VGroup(
            *[Text(f"{o.id}) {o.text}", font_size=26, color=WHITE) for o in q.options]
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.35)
        opts.next_to(prompt, DOWN, buff=0.5)
        self.play(FadeIn(header), Write(prompt), FadeIn(opts), run_time=1.0)
        duration = 5.0
        audio_file = None
        if audio_info:
            audio_file, duration = audio_info
        self._scene_wait(duration, audio_file)
        ans = next(o for o in q.options if o.id == q.correct_option_id)
        reveal = Text(f"Answer: {ans.id}) {ans.text}", font_size=28, color=GREEN).to_edge(DOWN)
        self.play(FadeIn(reveal), run_time=0.5)
        self.wait(2.0)

    def _redraw_structure(self) -> None:
        self.play(FadeOut(self.structure_group), run_time=0.2)
        self.remove(self.structure_group)
        self.structure_group = self._build_structure_mobject()
        self.add(self.structure_group)
        self.play(FadeIn(self.structure_group), run_time=0.4)

    def _build_structure_mobject(self) -> VGroup:
        kind = self.plan.topic_kind
        if kind == TopicKind.QUEUE:
            return self._draw_queue(self.state.get("items", []))
        if kind == TopicKind.STACK:
            return self._draw_stack(self.state.get("items", []))
        if kind == TopicKind.LINKED_LIST:
            return self._draw_linked_list(self.state.get("nodes", []))
        if kind == TopicKind.TREE:
            return self._draw_tree(self.state.get("nodes", []), self.state.get("root"))
        if kind == TopicKind.GRAPH_BFS:
            return self._draw_graph()
        if kind == TopicKind.SORTING:
            return self._draw_array(self.state.get("values", []))
        return VGroup()

    def _draw_queue(self, items: list) -> VGroup:
        group = VGroup()
        boxes = VGroup()
        for val in items:
            box = RoundedRectangle(width=1.2, height=1.0, corner_radius=0.1, color=BLUE)
            label = Text(str(val), font_size=28).move_to(box)
            boxes.add(VGroup(box, label))
        if boxes:
            boxes.arrange(RIGHT, buff=0.25)
            label_front = Text("front", font_size=20, color=GREEN).next_to(boxes[0], DOWN)
            label_rear = Text("rear", font_size=20, color=ORANGE).next_to(boxes[-1], DOWN)
            group.add(boxes, label_front, label_rear)
        else:
            group.add(Text("(empty queue)", font_size=28, color=GREY))
        group.move_to(ORIGIN)
        return group

    def _draw_stack(self, items: list) -> VGroup:
        group = VGroup()
        boxes = VGroup()
        for val in items:
            box = RoundedRectangle(width=2.0, height=0.8, corner_radius=0.1, color=BLUE)
            label = Text(str(val), font_size=28).move_to(box)
            boxes.add(VGroup(box, label))
        if boxes:
            boxes.arrange(UP, buff=0.15)
            top = Text("top", font_size=20, color=GREEN).next_to(boxes[-1], RIGHT)
            group.add(boxes, top)
        else:
            group.add(Text("(empty stack)", font_size=28, color=GREY))
        group.move_to(ORIGIN)
        return group

    def _draw_linked_list(self, nodes: list) -> VGroup:
        group = VGroup()
        parts = VGroup()
        for i, val in enumerate(nodes):
            box = RoundedRectangle(width=1.1, height=0.9, corner_radius=0.1, color=BLUE)
            label = Text(str(val), font_size=28).move_to(box)
            parts.add(VGroup(box, label))
            if i < len(nodes) - 1:
                parts.add(Line(LEFT, RIGHT, color=WHITE).set_length(0.45))
            else:
                parts.add(Text("null", font_size=20, color=GREY))
        if parts:
            parts.arrange(RIGHT, buff=0.15)
            group.add(parts)
        else:
            group.add(Text("(empty list)", font_size=28, color=GREY))
        group.move_to(ORIGIN)
        return group

    def _draw_tree(self, nodes: list, root: Any) -> VGroup:
        values = list(nodes or ([] if root is None else [root]))
        if not values:
            return VGroup(Text("(empty tree)", font_size=28, color=GREY))
        coords = {
            0: (0, 1.5),
            1: (-2.2, 0.3),
            2: (2.2, 0.3),
            3: (-3.2, -1.0),
            4: (-1.2, -1.0),
            5: (1.2, -1.0),
            6: (3.2, -1.0),
        }
        group = VGroup()
        positions: dict[int, tuple[float, float]] = {}
        for i, val in enumerate(values[:7]):
            x, y = coords.get(i, (0.0, -1.5))
            c = Circle(radius=0.4, color=BLUE)
            t = Text(str(val), font_size=24).move_to(c)
            node = VGroup(c, t).move_to([x, y, 0])
            positions[i] = (x, y)
            group.add(node)
        for i in range(1, min(len(values), 7)):
            parent = (i - 1) // 2
            if parent in positions:
                line = Line([*positions[parent], 0], [*positions[i], 0], color=GREY)
                line.z_index = -1
                group.add(line)
        return group

    def _draw_graph(self) -> VGroup:
        nodes = self.state.get("nodes", [])
        edges = self.state.get("edges", [])
        visited = set(self.state.get("visited", []))
        visit_order = self.state.get("visit_order", [])
        queue = self.state.get("queue", [])
        layout = {"A": (-2.2, 1.0), "B": (2.2, 1.0), "C": (-2.2, -1.2), "D": (2.2, -1.2)}
        for i, n in enumerate(nodes):
            layout.setdefault(n, (-2 + i * 1.5, 0.0))
        group = VGroup()
        for e in edges:
            if isinstance(e, (list, tuple)) and len(e) == 2:
                u, v = e
                if u in layout and v in layout:
                    line = Line([*layout[u], 0], [*layout[v], 0], color=GREY)
                    line.z_index = -1
                    group.add(line)
        for n in nodes:
            color = GREEN if n in visit_order else (ORANGE if n in visited else BLUE)
            c = Circle(radius=0.4, color=color)
            t = Text(str(n), font_size=26).move_to(c)
            group.add(VGroup(c, t).move_to([*layout[n], 0]))
        qtext = Text("Queue: " + ", ".join(queue) if queue else "Queue: empty", font_size=22)
        qtext.to_edge(DOWN)
        group.add(qtext)
        return group

    def _draw_array(self, values: list) -> VGroup:
        boxes = VGroup()
        sorted_from_end = int(self.state.get("sorted_from_end") or 0)
        n = len(values)
        for i, val in enumerate(values):
            color = GREEN if sorted_from_end and i >= n - sorted_from_end else BLUE
            if self.state.get("last_compare") and i in self.state["last_compare"]:
                color = YELLOW
            box = Square(1.0, color=color)
            label = Text(str(val), font_size=30).move_to(box)
            boxes.add(VGroup(box, label))
        if boxes:
            boxes.arrange(RIGHT, buff=0.2)
        else:
            boxes = VGroup(Text("(empty)", font_size=28, color=GREY))
        boxes.move_to(ORIGIN)
        return boxes

    def _apply_action(self, action_type: ActionType, args: dict, run_time: float = 0.8) -> None:
        if action_type == ActionType.TITLE:
            self._set_title(str(args.get("text", "")))
            return
        if action_type in {ActionType.NARRATE, ActionType.SET_LABEL, ActionType.HIGHLIGHT}:
            self.wait(run_time * 0.3)
            return
        if action_type == ActionType.CLEAR_HIGHLIGHT:
            return

        if action_type == ActionType.CREATE_QUEUE:
            items = list(args.get("values") or [])
            self.state = {
                "items": items,
                "front": items[0] if items else None,
                "rear": items[-1] if items else None,
            }
        elif action_type == ActionType.ENQUEUE:
            items = list(self.state.get("items", []))
            items.append(int(args["value"]))
            self.state = {"items": items, "front": items[0], "rear": items[-1]}
        elif action_type == ActionType.DEQUEUE:
            items = list(self.state.get("items", []))
            items.pop(0)
            self.state = {
                "items": items,
                "front": items[0] if items else None,
                "rear": items[-1] if items else None,
            }
        elif action_type == ActionType.FRONT:
            pass
        elif action_type == ActionType.CREATE_STACK:
            items = list(args.get("values") or [])
            self.state = {"items": items, "top": items[-1] if items else None}
        elif action_type == ActionType.PUSH:
            items = list(self.state.get("items", []))
            items.append(int(args["value"]))
            self.state = {"items": items, "top": items[-1]}
        elif action_type == ActionType.POP:
            items = list(self.state.get("items", []))
            items.pop()
            self.state = {"items": items, "top": items[-1] if items else None}
        elif action_type == ActionType.PEEK:
            pass
        elif action_type == ActionType.CREATE_LIST:
            self.state = {"nodes": list(args.get("values") or [])}
        elif action_type == ActionType.INSERT_HEAD:
            nodes = list(self.state.get("nodes", []))
            nodes.insert(0, int(args["value"]))
            self.state = {"nodes": nodes}
        elif action_type == ActionType.INSERT_TAIL:
            nodes = list(self.state.get("nodes", []))
            nodes.append(int(args["value"]))
            self.state = {"nodes": nodes}
        elif action_type == ActionType.INSERT_AT:
            nodes = list(self.state.get("nodes", []))
            nodes.insert(int(args["index"]), int(args["value"]))
            self.state = {"nodes": nodes}
        elif action_type == ActionType.DELETE_VALUE:
            nodes = list(self.state.get("nodes", []))
            nodes.remove(int(args["value"]))
            self.state = {"nodes": nodes}
        elif action_type == ActionType.TRAVERSE:
            if self.structure_group:
                self.play(Indicate(self.structure_group), run_time=run_time)
                return
        elif action_type == ActionType.CREATE_TREE:
            values = list(args.get("values") or [])
            self.state = {"nodes": values, "root": values[0] if values else None}
        elif action_type == ActionType.INSERT_BST:
            nodes = list(self.state.get("nodes", []))
            val = int(args["value"])
            if val not in nodes:
                nodes.append(val)
            self.state = {"nodes": nodes, "root": nodes[0] if nodes else None}
        elif action_type in {
            ActionType.TRAVERSE_INORDER,
            ActionType.TRAVERSE_PREORDER,
            ActionType.TRAVERSE_POSTORDER,
        }:
            if self.structure_group:
                self.play(Indicate(self.structure_group), run_time=run_time)
                return
        elif action_type == ActionType.CREATE_GRAPH:
            edges = [list(e) for e in args.get("edges", [])]
            nodes = sorted({n for e in edges for n in e})
            self.state = {
                "nodes": nodes,
                "edges": edges,
                "visit_order": [],
                "queue": [],
                "visited": [],
                "done": False,
            }
        elif action_type == ActionType.BFS_START:
            start = str(args["start"])
            self.state["visited"] = [start]
            self.state["queue"] = [start]
            self.state["visit_order"] = []
            self.state["done"] = False
        elif action_type == ActionType.BFS_VISIT:
            node = str(args["node"])
            q = list(self.state.get("queue", []))
            if q and q[0] == node:
                q.pop(0)
            self.state["queue"] = q
            order = list(self.state.get("visit_order", []))
            order.append(node)
            self.state["visit_order"] = order
        elif action_type == ActionType.BFS_ENQUEUE_NEIGHBOR:
            node = str(args["node"])
            visited = list(self.state.get("visited", []))
            if node not in visited:
                visited.append(node)
            self.state["visited"] = visited
            q = list(self.state.get("queue", []))
            q.append(node)
            self.state["queue"] = q
        elif action_type == ActionType.BFS_DONE:
            self.state["done"] = True
        elif action_type == ActionType.CREATE_ARRAY:
            self.state = {
                "values": list(args.get("values") or []),
                "sorted_from_end": 0,
                "last_compare": None,
            }
        elif action_type == ActionType.COMPARE:
            self.state["last_compare"] = [int(args["i"]), int(args["j"])]
        elif action_type == ActionType.SWAP:
            vals = list(self.state.get("values", []))
            i, j = int(args["i"]), int(args["j"])
            vals[i], vals[j] = vals[j], vals[i]
            self.state["values"] = vals
        elif action_type == ActionType.MARK_SORTED:
            self.state["sorted_from_end"] = int(args["count_from_end"])
            self.state["last_compare"] = None
        else:
            self.wait(run_time * 0.2)
            return

        self._redraw_structure()
        self.wait(0.15)
