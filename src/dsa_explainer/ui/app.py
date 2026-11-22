"""Simple learner UI — type a topic, get a narrated DSA video."""

from __future__ import annotations

from pathlib import Path

import gradio as gr

from dsa_explainer.config import LESSONS_DIR, ensure_dirs
from dsa_explainer.pipeline import create_lesson, revise_lesson
from dsa_explainer.schema import LearnerLevel, TopicKind

EXAMPLES = [
    "how does a queue work",
    "explain stacks",
    "how does a linked list work",
    "show binary search trees",
    "show BFS on this graph",
    "explain bubble sort",
]


def _generate(topic: str, level: str, kind: str, offline: bool, skip_render: bool):
    topic = (topic or "").strip()
    if not topic:
        raise gr.Error("Type a topic first, e.g. “how does a queue work”.")

    ensure_dirs()
    topic_kind = None if kind == "auto" else TopicKind(kind)
    artifact = create_lesson(
        topic,
        level=LearnerLevel(level),
        topic_kind=topic_kind,
        offline=offline,
        skip_render=skip_render,
    )

    quiz_lines = []
    for q in artifact.plan.quiz:
        opts = ", ".join(f"{o.id}) {o.text}" for o in q.options)
        quiz_lines.append(
            f"**{q.id}.** {q.prompt}\n- Options: {opts}\n"
            f"- Answer: `{q.correct_option_id}` — {q.explanation}"
        )
    quiz_md = "\n\n".join(quiz_lines) if quiz_lines else "_No quiz questions._"

    video = str(artifact.video_path) if artifact.video_path and artifact.video_path.exists() else None
    summary = (
        f"**Lesson:** `{artifact.lesson_dir.name}`  \n"
        f"**Topic kind:** `{artifact.plan.topic_kind.value}`  \n"
        f"**Scenes:** {len(artifact.plan.scenes)}  \n"
        f"**Duration ≈** {artifact.audio_manifest.get('total_duration_sec', 0):.1f}s  \n"
        f"**TTS:** `{artifact.audio_manifest.get('tts_engine', 'unknown')}`  \n"
        f"**Verified:** yes  \n"
        f"**Folder:** `{artifact.lesson_dir}`"
    )
    return video, summary, quiz_md, str(artifact.lesson_dir)


def _revise(lesson_dir: str, instruction: str, skip_render: bool):
    if not lesson_dir or not Path(lesson_dir).exists():
        raise gr.Error("Generate a lesson first (or paste a valid lesson folder path).")
    instruction = (instruction or "").strip()
    if not instruction:
        raise gr.Error('Try “slow down step 4” or “explain it for a beginner”.')

    artifact = revise_lesson(Path(lesson_dir), instruction, skip_render=skip_render)
    video = str(artifact.video_path) if artifact.video_path and artifact.video_path.exists() else None
    summary = (
        f"**Revised lesson:** `{artifact.lesson_dir}`  \n"
        f"**Version:** {artifact.plan.version}  \n"
        f"**Note:** {artifact.plan.revision_notes or instruction}"
    )
    return video, summary, str(artifact.lesson_dir)


def build_ui() -> gr.Blocks:
    ensure_dirs()
    with gr.Blocks(title="DSA Explainer") as demo:
        gr.Markdown(
            """
            # Data Structure Explainer
            Type a topic. The system plans a lesson, verifies every step in code,
            narrates with **local Piper TTS**, renders a Manim video, and adds a quiz.
            """
        )
        lesson_dir_state = gr.State("")

        with gr.Tab("Generate lesson"):
            topic = gr.Textbox(
                label="Topic",
                placeholder="how does a queue work",
                lines=1,
            )
            with gr.Row():
                level = gr.Dropdown(
                    choices=[l.value for l in LearnerLevel],
                    value=LearnerLevel.BEGINNER.value,
                    label="Learner level",
                )
                kind = gr.Dropdown(
                    choices=["auto"] + [k.value for k in TopicKind],
                    value="auto",
                    label="Topic kind",
                )
            with gr.Row():
                offline = gr.Checkbox(value=True, label="Offline templates (no LLM API)")
                skip_render = gr.Checkbox(
                    value=False,
                    label="Skip video render (plan + audio only)",
                )
            go = gr.Button("Generate verified video", variant="primary")
            gr.Examples(examples=EXAMPLES, inputs=[topic], label="Try one")

            video = gr.Video(label="Lesson video")
            summary = gr.Markdown()
            quiz = gr.Markdown(label="Quiz")

            go.click(
                _generate,
                inputs=[topic, level, kind, offline, skip_render],
                outputs=[video, summary, quiz, lesson_dir_state],
            )

        with gr.Tab("Revise"):
            gr.Markdown(
                "Change only part of the last lesson, e.g. "
                "`slow down step 4` or `explain it for a beginner`."
            )
            lesson_path = gr.Textbox(
                label="Lesson folder",
                placeholder=str(LESSONS_DIR / "<lesson-id>"),
            )
            instruction = gr.Textbox(
                label="Revision request",
                placeholder="slow down step 4",
            )
            skip_rev = gr.Checkbox(value=False, label="Skip video render")
            rev_btn = gr.Button("Apply revision", variant="primary")
            rev_video = gr.Video(label="Revised video")
            rev_summary = gr.Markdown()

            def _sync_path(path: str) -> str:
                return path or ""

            lesson_dir_state.change(_sync_path, inputs=[lesson_dir_state], outputs=[lesson_path])
            rev_btn.click(
                _revise,
                inputs=[lesson_path, instruction, skip_rev],
                outputs=[rev_video, rev_summary, lesson_dir_state],
            )

    return demo


def main() -> None:
    demo = build_ui()
    demo.launch(server_name="127.0.0.1", server_port=7860)


if __name__ == "__main__":
    main()
