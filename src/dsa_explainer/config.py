from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = ROOT / "output"
ASSETS_DIR = ROOT / "assets"
VOICES_DIR = ASSETS_DIR / "voices"
LESSONS_DIR = OUTPUT_DIR / "lessons"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"
    offline_mode: bool = False

    piper_bin: str = "piper"
    piper_voice: str = "en_US-lessac-medium"
    piper_voice_path: str = str(VOICES_DIR / "en_US-lessac-medium.onnx")
    tts_fallback: str = "espeak"

    min_video_seconds: float = 30.0
    default_fps: int = 30
    manim_quality: str = "l"  # l=480p, m=720p, h=1080p


def get_settings() -> Settings:
    return Settings()


def ensure_dirs() -> None:
    for path in (OUTPUT_DIR, ASSETS_DIR, VOICES_DIR, LESSONS_DIR):
        path.mkdir(parents=True, exist_ok=True)
