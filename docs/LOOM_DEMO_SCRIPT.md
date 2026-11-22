# Loom Demo Script (2–3 minutes)

Record at [loom.com](https://www.loom.com) while sharing your screen. Target **2:00–3:00**.

## Before you hit record
1. Activate the venv and start the UI: `dsa-explainer ui`
2. Open http://127.0.0.1:7860 and the GitHub repo README in a browser tab
3. Have one finished video ready (e.g. queue lesson) so you are not waiting on a long render during the talk track
4. Optional: keep `output/lessons/.../plan.json` and `verification.json` ready to flash on screen

## Talk track (≈150 seconds)

| Time | What to show | What to say |
|------|----------------|-------------|
| 0:00–0:20 | README / repo | “We built Project 1, the Data Structure Explainer. Learners type a DSA topic; we plan a structured lesson, verify every step in code, narrate with local Piper TTS, and render a Manim video with a quiz.” |
| 0:20–0:45 | Architecture diagram (`docs/architecture.svg` or README mermaid) | “The LLM never draws freely. It only emits a JSON scene plan. A step verifier runs the real data structure and blocks export if state is wrong. TTS is local Piper. Manim draws the actions.” |
| 0:45–1:20 | Gradio UI — type `how does a queue work`, show Generate (or open an already-generated result) | “Here is the product UI. I enter a topic and learner level. Offline mode uses verified templates; with an API key the planner can use an LLM, but verification still gates the video.” |
| 1:20–1:50 | Play `lesson.mp4` (20–30 seconds of playback) | “The exported video is over thirty seconds, shows enqueue and dequeue with narration, and ends with a short quiz whose answers we checked in code.” |
| 1:50–2:20 | Show `verification.json` + revise tab / CLI `slow down step 4` | “Revision control lets a learner say ‘slow down step 4’ or ‘explain it for a beginner’ and only that part changes, then we re-verify.” |
| 2:20–2:45 | Tests / topics list | “We cover linked lists, stacks, queues, trees, BFS, and bubble sort. pytest covers planner, verifier, quiz, and revision.” |
| 2:45–3:00 | Closing on repo URL | “Full code, docs, report, and tests are on GitHub. Thanks for watching.” |

## Checklist before submitting the Loom link
- [ ] Video is 2–3 minutes  
- [ ] Product demo visible (UI or CLI + output video)  
- [ ] Architecture mentioned or shown  
- [ ] Local Piper / verification called out  
- [ ] Link added to README “Demo video” section  

## Note
Loom must be recorded by a group member (login + screen share). This script is the submission aid; the Loom URL is the deliverable.
