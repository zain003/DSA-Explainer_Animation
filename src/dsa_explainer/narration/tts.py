"""Local text-to-speech.

Primary: Piper via Python API (`piper-tts`) or CLI binary.
Fallbacks: espeak-ng / espeak, then a generated tone bed (never cloud TTS).
"""

from __future__ import annotations

import json
import math
import shutil
import struct
import subprocess
import wave
from functools import lru_cache
from pathlib import Path

from dsa_explainer.config import VOICES_DIR, get_settings
from dsa_explainer.schema import LessonPlan


def _write_silence_wav(path: Path, seconds: float, rate: int = 22050) -> None:
    n = max(1, int(seconds * rate))
    with wave.open(str(path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(b"\x00\x00" * n)


def _write_tone_wav(path: Path, seconds: float, rate: int = 22050, freq: float = 220.0) -> None:
    """Soft tone so the video is never mute if TTS binaries are missing."""
    n = max(1, int(seconds * rate))
    frames = bytearray()
    for i in range(n):
        t = i / rate
        env = min(1.0, t * 4) * min(1.0, (seconds - t) * 4)
        sample = int(3000 * env * math.sin(2 * math.pi * freq * t))
        frames += struct.pack("<h", max(-32767, min(32767, sample)))
    with wave.open(str(path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(bytes(frames))


def _wav_duration(path: Path) -> float:
    with wave.open(str(path), "r") as wf:
        return wf.getnframes() / float(wf.getframerate())


def resolve_voice_model() -> Path | None:
    settings = get_settings()
    candidates: list[Path] = []
    if settings.piper_voice_path:
        candidates.append(Path(settings.piper_voice_path))
    name = settings.piper_voice
    candidates.extend(
        [
            VOICES_DIR / f"{name}.onnx",
            VOICES_DIR / name / f"{name}.onnx",
            Path(name) if name.endswith(".onnx") else Path(f"{name}.onnx"),
        ]
    )
    for path in candidates:
        if path.exists():
            return path.resolve()
    # Any onnx in voices dir
    matches = sorted(VOICES_DIR.glob("*.onnx"))
    return matches[0].resolve() if matches else None


@lru_cache(maxsize=1)
def _load_piper_voice():
    model = resolve_voice_model()
    if model is None:
        return None
    try:
        from piper import PiperVoice

        return PiperVoice.load(str(model))
    except Exception:
        return None


def _run_piper_python(text: str, out_wav: Path) -> bool:
    voice = _load_piper_voice()
    if voice is None:
        return False
    try:
        with wave.open(str(out_wav), "wb") as wf:
            voice.synthesize_wav(text, wf)
        return out_wav.exists() and out_wav.stat().st_size > 44
    except Exception:
        # Older piper API variants
        try:
            from piper import SynthesisConfig

            with wave.open(str(out_wav), "wb") as wf:
                voice.synthesize_wav(text, wf, syn_config=SynthesisConfig())
            return out_wav.exists() and out_wav.stat().st_size > 44
        except Exception:
            return False


def _run_piper_cli(text: str, out_wav: Path) -> bool:
    settings = get_settings()
    piper = shutil.which(settings.piper_bin) or (
        settings.piper_bin if Path(settings.piper_bin).exists() else None
    )
    if not piper:
        # python -m piper
        py_piper = shutil.which("piper")
        if py_piper:
            piper = py_piper
        else:
            return False

    model = resolve_voice_model()
    cmd = [piper, "--output_file", str(out_wav)]
    if model:
        cmd.extend(["--model", str(model)])
    else:
        cmd.extend(["-m", settings.piper_voice])

    try:
        subprocess.run(
            cmd,
            input=text.encode("utf-8"),
            check=True,
            capture_output=True,
        )
        return out_wav.exists() and out_wav.stat().st_size > 44
    except (OSError, subprocess.CalledProcessError):
        # Try: python -m piper -m MODEL -f out.wav -- text
        if model is None:
            return False
        try:
            import sys

            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "piper",
                    "-m",
                    str(model),
                    "-f",
                    str(out_wav),
                    "--",
                    text,
                ],
                check=True,
                capture_output=True,
            )
            return out_wav.exists() and out_wav.stat().st_size > 44
        except (OSError, subprocess.CalledProcessError):
            return False


def _run_piper(text: str, out_wav: Path) -> bool:
    if _run_piper_python(text, out_wav):
        return True
    return _run_piper_cli(text, out_wav)


def _run_espeak(text: str, out_wav: Path) -> bool:
    for binary in ("espeak-ng", "espeak"):
        exe = shutil.which(binary)
        if not exe:
            continue
        try:
            subprocess.run(
                [exe, "-w", str(out_wav), text],
                check=True,
                capture_output=True,
            )
            return out_wav.exists() and out_wav.stat().st_size > 44
        except (OSError, subprocess.CalledProcessError):
            continue
    return False


def synthesize_utterance(text: str, out_wav: Path, *, min_seconds: float = 2.0) -> float:
    """Synthesize one utterance locally. Returns duration in seconds."""
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    settings = get_settings()

    if _run_piper(text, out_wav):
        return max(_wav_duration(out_wav), min_seconds)

    if settings.tts_fallback == "espeak" and _run_espeak(text, out_wav):
        return max(_wav_duration(out_wav), min_seconds)

    approx = max(min_seconds, min(40.0, 0.06 * len(text)))
    if settings.tts_fallback == "silent":
        _write_silence_wav(out_wav, approx)
    else:
        _write_tone_wav(out_wav, approx)
    return approx


def synthesize_lesson_audio(plan: LessonPlan, lesson_dir: Path) -> dict:
    """Create per-scene wav files + a manifest for the renderer."""
    audio_dir = lesson_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    manifest = {"scenes": [], "quiz": []}

    for scene in plan.scenes:
        wav_path = audio_dir / f"{scene.id}.wav"
        duration = synthesize_utterance(
            scene.narration,
            wav_path,
            min_seconds=max(2.0, scene.duration_hint_sec * 0.75),
        )
        scene.duration_hint_sec = max(scene.duration_hint_sec, duration)
        manifest["scenes"].append(
            {
                "id": scene.id,
                "wav": str(wav_path.relative_to(lesson_dir)),
                "duration_sec": duration,
                "narration": scene.narration,
            }
        )

    for q in plan.quiz:
        text = f"Quiz. {q.prompt} " + " ".join(
            f"Option {opt.id}: {opt.text}." for opt in q.options
        )
        wav_path = audio_dir / f"{q.id}.wav"
        duration = synthesize_utterance(text, wav_path, min_seconds=5.0)
        manifest["quiz"].append(
            {
                "id": q.id,
                "wav": str(wav_path.relative_to(lesson_dir)),
                "duration_sec": duration,
            }
        )

    total = sum(s["duration_sec"] for s in manifest["scenes"]) + sum(
        q["duration_sec"] for q in manifest["quiz"]
    )
    manifest["total_duration_sec"] = total
    manifest["tts_engine"] = "piper" if resolve_voice_model() and _load_piper_voice() else "fallback"
    manifest_path = lesson_dir / "audio_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest
