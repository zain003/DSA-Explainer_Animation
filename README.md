# Data Structure Explainer

Narrated DSA video lessons from a typed topic. The planner emits a **structured scene plan** (JSON); Manim draws that plan; a **step verifier** runs the real data structure in code and **refuses to render** if any step is wrong. Voice is **local Piper TTS** (never cloud).

## Is a UI required?

**No.** The assignment needs a product where a learner can type a topic — the CLI satisfies that. A Gradio web UI is included anyway so demos feel like a product (`dsa-explainer ui`).

## Covered topics

| Kind | Example prompt |
|------|----------------|
| `linked_list` | how does a linked list work |
| `stack` | explain stacks |
| `queue` | how does a queue work |
| `tree` | show binary search trees |
| `graph_bfs` | show BFS on this graph |
| `sorting` | explain bubble sort |

Every lesson is **≥ 30 seconds** and ends with a **verified quiz**.

## Architecture (6 core modules)

1. **Lesson planner** — topic + level → `LessonPlan` JSON  
2. **Step verifier** — real structure execution vs `expected_state`  
3. **Narration + local TTS** — Piper (`piper-tts`)  
4. **Animation renderer** — Manim from actions only (no free-form drawing)  
5. **Quiz generator** — answers checked in code  
6. **Revision control** — e.g. `slow down step 4` changes only that scene  

```
topic → plan (JSON) → verify → Piper TTS → Manim → lesson.mp4 + quiz
                      ↑ refuse if wrong
```

## Setup

```bash
cd NLP_Project
python -m venv .venv
# Windows:
.venv\Scripts\activate
pip install -e ".[dev]"
copy .env.example .env

# Download local Piper voice (~63 MB)
python -m piper.download_voices en_US-lessac-medium --data-dir assets/voices
```

Also need **FFmpeg** on PATH (`winget install Gyan.FFmpeg`).

### LLM planning (optional)

Set `OPENAI_API_KEY` in `.env` and run with `--llm`. Default `--offline` uses verified templates (no API).

## Usage

```bash
# Web UI (recommended for demos)
dsa-explainer ui

# CLI — full lesson
dsa-explainer generate "how does a queue work" --offline

# Plan + verify only
dsa-explainer plan "show BFS on this graph" --offline

# Revise one part
dsa-explainer revise output/lessons/<lesson-id> "slow down step 4"
dsa-explainer revise output/lessons/<lesson-id> "explain it for a beginner"

# Verify a saved plan
dsa-explainer verify output/lessons/<lesson-id>/plan.json
```

Artifacts in `output/lessons/<id>/`:

- `plan.json` — structured scene plan  
- `verification.json` — step-check report  
- `audio/` — per-scene Piper WAVs  
- `lesson.mp4` — final video + quiz  

## Design rule: no free-form drawing

The model may only emit `ActionType` values in `schema.py`. The renderer maps those to Manim mobjects. A wrong `expected_state` fails verification and blocks export.

## Tests

```bash
pytest -q
```

# DSA-Explainer_Animation
