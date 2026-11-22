# Project Report: Data Structure Explainer

**Course project:** Project 1 — Data Structure Explainer  
**Repository:** https://github.com/zain003/DSA-Explainer_Animation  

**Group members:** Zain Ali Khan (22i2624, Section B); Rafay Ul Haq (22i2520, Section B).

---

## 1. Introduction

This product teaches Data Structures and Algorithms through **narrated, animated videos**. A learner types a natural-language topic (for example, “how does a queue work” or “show BFS on this graph”). The system plans a lesson, writes narration, draws animation from a structured scene plan, synthesizes voice **locally**, and exports a video (≥ 30 seconds) with a short quiz.

Covered topics: linked lists, stacks, queues, trees (BST), graph BFS, and bubble sort.

---

## 2. Core Modules

### 2.1 Lesson planner
Takes a topic and learner level and produces a structured `LessonPlan` JSON (scenes, actions, narration hints, quiz). Plans are validated against a Pydantic schema before any rendering. In offline mode, deterministic templates are used; with an API key, an OpenAI-compatible LLM can propose plans that must still pass verification.

### 2.2 Animation renderer
**Manim** draws only declared `ActionType` values (e.g. `enqueue`, `bfs_visit`, `swap`). The language model never draws freely; the renderer is the sole drawing authority.

### 2.3 Step verifier
Executes real data-structure / algorithm code in Python and checks each action’s `expected_state`. A mismatch **blocks export** — a wrong video is worse than no video.

### 2.4 Narration and voice
Narration is stored per scene and synchronized with animation timing. **Text-to-speech runs locally via Piper** (`piper-tts` + ONNX voice). Cloud TTS is not used.

### 2.5 Quiz generator
Builds multiple-choice questions from the lesson. Correct answers are checked against live structure execution where applicable; unverified items are dropped.

### 2.6 Revision control
Utterances such as “slow down step 4” or “explain it for a beginner” update only the targeted scene(s), then re-verify and re-export.

---

## 3. Setup and Technical Details

### 3.1 Stack
| Layer | Choice |
|-------|--------|
| Language | Python 3.10+ |
| Schema / validation | Pydantic v2 |
| Planner | Offline templates + optional OpenAI-compatible API |
| Verifier | In-process DS implementations |
| Renderer | Manim Community + FFmpeg |
| TTS | Piper (`en_US-lessac-medium`) local |
| UI | Gradio (optional) + Typer CLI |
| Tests | pytest |

### 3.2 Setup (summary)
```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -e ".[dev]"
copy .env.example .env
python -m piper.download_voices en_US-lessac-medium --data-dir assets/voices
# FFmpeg required on PATH
dsa-explainer ui                # or: dsa-explainer generate "how does a queue work" --offline
pytest -q
```

### 3.3 What runs locally vs remotely
- **Local:** planning templates, schema validation, step verifier, Piper TTS, Manim render, quiz checks, Gradio/CLI UI, revision.
- **Optional remote:** OpenAI-compatible chat API for planning / narration polish only (not required; `--offline` is default for demos).

### 3.4 Pipeline
```
topic → LessonPlan JSON → validate → verify steps → Piper WAV per scene
      → Manim render → lesson.mp4 + quiz → optional revise → re-verify → re-render
```

Architecture diagram: [`architecture.svg`](architecture.svg) (also embedded in `README.md`).

---

## 4. Critical Analysis

### 4.1 Problem Statement

**Real-world gap.** Students often learn DSA from static slides, text, or generic YouTube videos that are not personalized to a typed question, learner level, or a specific example graph/array. Interactive coding sites show code but rarely produce a coherent, narrated visual lesson on demand.

**Why a “standard” LLM chat solution fails.** Asking a chatbot to “explain queues” or even to emit raw Manim/Remotion code is unsafe for teaching:
- Models hallucinate algorithm steps and edge cases.
- Free-form drawing or free-form animation code can look polished while being **factually wrong**.
- There is no hard gate that the on-screen state matches a real data structure.

This project targets that gap: **on-demand video** with a **verified** scene plan, so incorrect explanations are rejected before export.

### 4.2 Complexity Drivers

1. **Conflicting requirements:** Use LLMs for flexible planning/writing, but forbid free-form drawing and forbid shipping wrong content.
2. **No single obvious stack:** Planner, verifier, renderer, TTS, and quiz each have independent failure modes and must agree on one schema.
3. **Temporal sync:** Narration length, animation beats, and ≥30s minimum must stay consistent after local TTS.
4. **Partial revision:** Learners expect to change one step without regenerating an unrelated lesson from scratch, while re-verification must still pass.
5. **Local TTS constraint:** Voice quality and latency must be acceptable without cloud speech APIs.

### 4.3 Design Justification (alternatives considered)

**Alternative A — LLM emits Manim/Remotion source code directly.**  
*Rejected.* High flexibility, but verification of arbitrary code is intractable; a single off-by-one in generated animation code can teach the wrong algorithm. We instead constrain the LLM (or templates) to a **closed action vocabulary** and render that vocabulary ourselves.

**Alternative B — Remotion (React) instead of Manim.**  
*Rejected for this team/timeline.* Remotion is excellent for web-native video, but Python already hosts the verifier and Piper integration; Manim is the academic default for algorithm animation and kept the stack in one language. Remotion remains a viable future port of the same JSON scene plan.

**Alternative C — Cloud TTS (e.g. commercial neural voices).**  
*Rejected.* The brief requires **local** TTS. Piper satisfies the rule with acceptable quality; espeak/tone remain emergency fallbacks only.

**Alternative D — Skip formal verification; rely on prompt engineering.**  
*Rejected.* Prompting alone cannot guarantee correctness. The product rule is explicit: a wrong video is worse than no video.

### 4.4 Trade-off Analysis

| Trade-off | Choice | Reason |
|-----------|--------|--------|
| Flexibility vs safety | Closed `ActionType` schema | Safety and verifiability over open-ended drawing |
| Offline templates vs LLM plans | Templates default; LLM optional | Deterministic demos + API when available; both must verify |
| Voice quality vs locality | Piper ONNX local | Meets assignment; no audio leaves the machine |
| Render quality vs speed | Manim 480p default (`-ql`) | Fast iteration for demos; quality flag can raise to 720p/1080p |
| Full regenerate vs patch | Scene-level revision | Faster feedback; still full verify on the revised plan |
| UI polish vs scope | Gradio + CLI | Spec does not require a UI; Gradio added for product demos without a large frontend |

### 4.5 Societal and Ethical Impact

**Privacy.** Lesson topics and optional API prompts may reveal what a student is studying. Offline mode keeps planning local; Piper keeps voice local. If an LLM API is enabled, prompts leave the device — documented in the README; students should avoid pasting personal data into topics.

**Safety / educational integrity.** Incorrect algorithm instruction can harm exam performance and mental models. The verifier is an ethical control: we prefer refusal over confident false animation. Residual risk remains for soft narration wording that does not change `expected_state`; quizzes are used to reinforce checked facts.

**Fairness / access.** Local TTS and offline templates reduce dependence on paid APIs, which helps students with limited cloud budget. Hardware still matters (CPU for Manim/Piper). Voice models and English-centric narration may underserve non-English learners — a limitation to address with more Piper locales.

**Legal / copyright.** Generated videos are original renders from our plan/renderer. Third-party model/voice licenses (OpenAI ToS if used; Piper voice model cards) must be respected for redistribution. Course submission should not redistribute proprietary voice weights if a license forbids it; we document download steps instead of vendoring large binaries where inappropriate.

**Misuse.** Automated “explanation videos” could be submitted as a student’s own coursework. The tool is intended as a **learning aid**; institutions may need disclosure policies similar to other generative tools.

---

## 5. Testing

Automated tests (`pytest`) cover:
- Topic detection and offline planning  
- Verification of all topic templates  
- Quiz answer verification  
- Revision parsing and scene-local updates  

Manual demos: CLI generate, Gradio UI, revision commands, inspection of `verification.json` and `lesson.mp4`.

---

## 6. Conclusion

The Data Structure Explainer meets the project brief by combining structured planning, hard step verification, local Piper narration, Manim rendering, quizzes, and revision. The central design thesis — **models propose, code verifies, renderer draws** — is what makes on-demand DSA video safer than chat-only or free-form animation generation.
