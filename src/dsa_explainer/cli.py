"""CLI for the Data Structure Explainer."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from dsa_explainer.config import ensure_dirs, get_settings
from dsa_explainer.pipeline import create_lesson, revise_lesson
from dsa_explainer.planner.planner import plan_lesson
from dsa_explainer.planner.templates import detect_topic_kind
from dsa_explainer.schema import LearnerLevel, TopicKind
from dsa_explainer.verifier.engine import verify_plan

app = typer.Typer(
    name="dsa-explainer",
    help="Narrated Data Structures & Algorithms video lessons",
    add_completion=False,
)
console = Console()


@app.command()
def topics() -> None:
    """List supported topic kinds."""
    table = Table(title="Supported topics")
    table.add_column("Kind")
    table.add_column("Examples")
    rows = [
        (TopicKind.LINKED_LIST.value, "how does a linked list work"),
        (TopicKind.STACK.value, "explain stacks"),
        (TopicKind.QUEUE.value, "how does a queue work"),
        (TopicKind.TREE.value, "show binary search trees"),
        (TopicKind.GRAPH_BFS.value, "show BFS on this graph"),
        (TopicKind.SORTING.value, "explain bubble sort"),
    ]
    for kind, example in rows:
        table.add_row(kind, example)
    console.print(table)


@app.command("plan")
def plan_cmd(
    topic: str = typer.Argument(..., help='e.g. "how does a queue work"'),
    level: LearnerLevel = typer.Option(LearnerLevel.BEGINNER, "--level", "-l"),
    kind: Optional[TopicKind] = typer.Option(None, "--kind", "-k"),
    offline: bool = typer.Option(False, "--offline", help="Use template plans only"),
    out: Optional[Path] = typer.Option(None, "--out", help="Write plan JSON here"),
) -> None:
    """Plan + verify a lesson without rendering."""
    ensure_dirs()
    detected = kind or detect_topic_kind(topic)
    console.print(f"[bold]Topic kind:[/bold] {detected.value}")
    plan = plan_lesson(topic, level=level, topic_kind=detected, offline=offline or None)
    report = verify_plan(plan)
    console.print(
        f"Scenes: {len(plan.scenes)} | "
        f"Duration ≈ {plan.estimated_duration_sec:.1f}s | "
        f"Verified: {'yes' if report.ok else 'NO'}"
    )
    if out:
        out.write_text(plan.model_dump_json(indent=2), encoding="utf-8")
        console.print(f"Wrote {out}")
    else:
        console.print_json(plan.model_dump_json())


@app.command()
def generate(
    topic: str = typer.Argument(...),
    level: LearnerLevel = typer.Option(LearnerLevel.BEGINNER, "--level", "-l"),
    kind: Optional[TopicKind] = typer.Option(None, "--kind", "-k"),
    offline: bool = typer.Option(True, "--offline/--llm", help="Templates vs LLM planner"),
    skip_render: bool = typer.Option(False, "--skip-render", help="Plan+TTS only"),
) -> None:
    """Full pipeline: plan, verify, narrate, TTS, render, quiz."""
    ensure_dirs()
    settings = get_settings()
    console.print(
        f"[cyan]Generating[/cyan] {topic!r} "
        f"(offline={offline}, model={settings.openai_model})"
    )
    artifact = create_lesson(
        topic,
        level=level,
        topic_kind=kind,
        offline=offline,
        skip_render=skip_render,
    )
    console.print(f"[green]OK[/green] lesson dir: {artifact.lesson_dir}")
    console.print(f"Duration audio ≈ {artifact.audio_manifest.get('total_duration_sec', 0):.1f}s")
    if artifact.video_path:
        console.print(f"Video: {artifact.video_path}")
    else:
        console.print("Video skipped (--skip-render)")


@app.command()
def revise(
    lesson_dir: Path = typer.Argument(..., exists=True, file_okay=False),
    instruction: str = typer.Argument(..., help='e.g. "slow down step 4"'),
    skip_render: bool = typer.Option(False, "--skip-render"),
) -> None:
    """Revise part of an existing lesson and re-export."""
    artifact = revise_lesson(lesson_dir, instruction, skip_render=skip_render)
    console.print(f"[green]Revised[/green] → {artifact.lesson_dir}")
    if artifact.video_path:
        console.print(f"Video: {artifact.video_path}")


@app.command()
def verify(
    plan_path: Path = typer.Argument(..., exists=True, dir_okay=False),
) -> None:
    """Verify an existing plan.json against real structure execution."""
    from dsa_explainer.schema import LessonPlan

    plan = LessonPlan.model_validate_json(plan_path.read_text(encoding="utf-8"))
    report = verify_plan(plan)
    if report.ok:
        console.print("[green]Verification passed[/green]")
        console.print_json(data=report.final_state)
    else:
        console.print("[red]Verification FAILED[/red]")
        console.print_json(report.model_dump_json())
        raise typer.Exit(code=1)


@app.command("ui")
def ui_cmd(
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(7860, "--port"),
) -> None:
    """Launch the learner web UI (type a topic → verified video)."""
    from dsa_explainer.ui.app import build_ui

    console.print(f"[cyan]Opening UI[/cyan] http://{host}:{port}")
    build_ui().launch(server_name=host, server_port=port)


if __name__ == "__main__":
    app()
