# Karpathy-style note:
# Keep the universe small and explicit. This file is the single source of truth
# for constants, paths, model names, and operating assumptions. Every other
# module imports from here so behavior is easy to inspect, test, and change.

from __future__ import annotations

import os
from pathlib import Path

# -----------------------------
# Mathematical / acoustic core
# -----------------------------
PHI: float = 1.618033988749895
PHI_SCALE: tuple[float, ...] = tuple(PHI**i for i in range(8))
SCHUMANN_BASE: float = 7.83
SAMPLE_RATE: int = 44_100

# Conservative audible limits for generated tones.
MIN_FREQ_HZ: float = 20.0
MAX_FREQ_HZ: float = 20_000.0
DEFAULT_ROOT_FREQ_HZ: float = 194.4
DEFAULT_DURATION_SECONDS: float = 60.0
MAX_DURATION_SECONDS: float = 20 * 60.0

# Brainwave target beat frequencies. These are audio beat-rate labels, not
# medical claims. Phi is used to create proportional transitions around these
# centers instead of arbitrary jumps.
BRAINWAVE_TARGETS_HZ: dict[str, float] = {
    "delta": 2.5,
    "theta": 6.0,
    "schumann": SCHUMANN_BASE,
    "alpha": 10.0,
    "beta": 18.0,
}

# -----------------------------
# File system configuration
# -----------------------------
BASE_DIR: Path = Path(__file__).resolve().parent
DATA_DIR: Path = BASE_DIR / "data"
UPLOAD_DIR: Path = DATA_DIR / "uploads"
OUTPUT_DIR: Path = DATA_DIR / "journeys"
VISUAL_DIR: Path = DATA_DIR / "visuals"

for directory in (DATA_DIR, UPLOAD_DIR, OUTPUT_DIR, VISUAL_DIR):
    directory.mkdir(parents=True, exist_ok=True)

ALLOWED_AUDIO_EXTENSIONS: set[str] = {"wav", "mp3", "m4a", "flac", "ogg", "aac", "webm"}
MAX_UPLOAD_BYTES: int = 50 * 1024 * 1024

# -----------------------------
# DashScope / Alibaba Cloud AI
# -----------------------------
API_KEY: str | None = os.getenv("DASHSCOPE_API_KEY")
DASHSCOPE_BASE_HTTP_API_URL: str = os.getenv(
    "DASHSCOPE_BASE_HTTP_API_URL",
    "https://dashscope-intl.aliyuncs.com/api/v1",
)
DASHSCOPE_MODEL: str = os.getenv("DASHSCOPE_MODEL", "qwen-plus")
DASHSCOPE_TEST_MODEL: str = os.getenv("DASHSCOPE_TEST_MODEL", "qwen-turbo")
DASHSCOPE_MAX_TOKENS: int = int(os.getenv("DASHSCOPE_MAX_TOKENS", "300"))
DASHSCOPE_TEMPERATURE: float = float(os.getenv("DASHSCOPE_TEMPERATURE", "0.85"))

# Cost schema: deliberately relative units rather than hardcoded official USD.
# Replace with the current Alibaba Cloud pricing table before production billing.
# Operational rule requested by the product owner: qwen-turbo is treated as ~10x
# cheaper than qwen-plus for prototypes and regression tests.
RELATIVE_COST_UNITS_PER_1K_TOKENS: dict[str, float] = {
    "qwen-plus": 1.0,
    "qwen-turbo": 0.1,
}
TOKEN_CHARS_APPROX: int = 4

# -----------------------------
# Runtime / streaming
# -----------------------------
STREAM_CHUNK_SECONDS: float = 0.25
STREAM_NAMESPACE: str = "/"
SECRET_KEY: str = os.getenv("PHIVOX_SECRET_KEY", "phivox-local-dev")
SOCKETIO_ASYNC_MODE: str | None = os.getenv("SOCKETIO_ASYNC_MODE") or None
