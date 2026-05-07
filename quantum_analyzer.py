# Karpathy-style note:
# Voice analysis must be explainable. The user gives the system its value through
# a voice trace, so every extracted feature is returned with enough metadata to
# audit the calibration instead of hiding it behind mystical language.

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import warnings

import librosa
import numpy as np

from config import DEFAULT_ROOT_FREQ_HZ, SAMPLE_RATE


@dataclass(frozen=True)
class VibrationalProfile:
    audio_path: str
    human_base_freq: float
    duration_seconds: float
    estimated_valence: float
    confidence: float
    trace: dict[str, float | int | str]

    def to_dict(self) -> dict:
        return asdict(self)


class VoiceAnalyzer:
    """Extracts a transparent vibrational profile from a human voice sample."""

    def __init__(self, sample_rate: int = SAMPLE_RATE) -> None:
        self.sample_rate = int(sample_rate)

    def calibrate_voice(self, audio_path: str | Path) -> dict:
        """
        Analyze voice and return a profile with human_base_freq.

        Steps:
        1. Load audio mono at project sample rate.
        2. Estimate f0 with librosa.pyin, falling back to librosa.yin.
        3. Use median voiced f0 as the user's root frequency.
        4. Estimate a transparent acoustic valence proxy from brightness, energy,
           and stability. This is not clinical emotion recognition.
        """
        path = Path(audio_path)
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {path}")

        # Browser recordings often arrive as webm/ogg containers. PySoundFile may
        # warn and librosa will transparently fall back to audioread/ffmpeg. The
        # fallback is expected, so we keep the calibration console clean.
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="PySoundFile failed.*")
            warnings.filterwarnings("ignore", category=FutureWarning)
            y, sr = librosa.load(path, sr=self.sample_rate, mono=True)
        if y.size == 0:
            raise ValueError("Audio file is empty or unsupported")

        y = librosa.util.normalize(y)
        duration = float(librosa.get_duration(y=y, sr=sr))
        f0_values, f0_method = self._extract_f0(y, sr)

        voiced = f0_values[np.isfinite(f0_values) & (f0_values > 0)]
        if voiced.size == 0:
            human_base_freq = DEFAULT_ROOT_FREQ_HZ
            confidence = 0.0
        else:
            human_base_freq = float(np.median(voiced))
            confidence = float(np.clip(voiced.size / max(len(f0_values), 1), 0.0, 1.0))

        valence, valence_trace = self._estimate_valence_proxy(y, sr, voiced)
        trace = {
            "sample_rate": sr,
            "samples": int(y.size),
            "f0_method": f0_method,
            "voiced_frames": int(voiced.size),
            "median_f0_hz": round(human_base_freq, 4),
            "min_f0_hz": round(float(np.min(voiced)), 4) if voiced.size else 0.0,
            "max_f0_hz": round(float(np.max(voiced)), 4) if voiced.size else 0.0,
            **valence_trace,
        }

        profile = VibrationalProfile(
            audio_path=str(path),
            human_base_freq=round(human_base_freq, 4),
            duration_seconds=round(duration, 4),
            estimated_valence=round(valence, 4),
            confidence=round(confidence, 4),
            trace=trace,
        )
        return profile.to_dict()

    def _extract_f0(self, y: np.ndarray, sr: int) -> tuple[np.ndarray, str]:
        fmin = librosa.note_to_hz("C2")
        fmax = librosa.note_to_hz("C7")
        try:
            f0, _, _ = librosa.pyin(y, fmin=fmin, fmax=fmax, sr=sr)
            if f0 is not None and np.isfinite(f0).any():
                return f0.astype(np.float64), "librosa.pyin"
        except Exception:
            # Fallback is explicit: pyin can fail on noisy or very short input.
            pass

        try:
            f0 = librosa.yin(y, fmin=fmin, fmax=fmax, sr=sr)
            return f0.astype(np.float64), "librosa.yin"
        except Exception:
            return np.array([], dtype=np.float64), "fallback.default_root"

    def _estimate_valence_proxy(
        self,
        y: np.ndarray,
        sr: int,
        voiced: np.ndarray,
    ) -> tuple[float, dict[str, float]]:
        rms = librosa.feature.rms(y=y)[0]
        centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        zcr = librosa.feature.zero_crossing_rate(y)[0]

        mean_rms = float(np.mean(rms))
        mean_centroid = float(np.mean(centroid))
        mean_zcr = float(np.mean(zcr))
        f0_stability = float(1.0 / (1.0 + np.std(voiced) / max(np.mean(voiced), 1.0))) if voiced.size else 0.0

        # Transparent heuristic: brighter, stable, moderately energetic voices
        # score higher. The sigmoid keeps the output in [0, 1].
        brightness = np.clip(mean_centroid / 3_000.0, 0.0, 1.0)
        energy = np.clip(mean_rms / 0.20, 0.0, 1.0)
        noise_penalty = np.clip(mean_zcr / 0.20, 0.0, 1.0)
        raw = 0.35 * brightness + 0.35 * energy + 0.20 * f0_stability - 0.10 * noise_penalty
        valence = float(1.0 / (1.0 + np.exp(-6.0 * (raw - 0.5))))

        return valence, {
            "mean_rms": round(mean_rms, 6),
            "mean_spectral_centroid_hz": round(mean_centroid, 4),
            "mean_zero_crossing_rate": round(mean_zcr, 6),
            "f0_stability": round(f0_stability, 4),
            "valence_model": "transparent acoustic proxy, not clinical emotion recognition",
        }
