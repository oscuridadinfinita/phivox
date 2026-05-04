# Karpathy-style note:
# Audio should be a collection of tiny deterministic transforms: make a time
# axis, make frequencies, apply an envelope, normalize. No hidden global state,
# no hand-written sample loops, and every Phi operation has a traceable reason.

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile

from config import MAX_FREQ_HZ, MIN_FREQ_HZ, PHI, PHI_SCALE, SAMPLE_RATE, SCHUMANN_BASE


@dataclass(frozen=True)
class AudioRender:
    """Small immutable container for a generated stereo audio buffer."""

    samples: np.ndarray
    sample_rate: int

    @property
    def duration_seconds(self) -> float:
        return float(len(self.samples) / self.sample_rate)


class AcousticEngine:
    """Deterministic generator for Phi-based sonic material."""

    def __init__(self, sample_rate: int = SAMPLE_RATE) -> None:
        self.sample_rate = int(sample_rate)

    def generate_golden_sequence(self, root_freq: float, length: int) -> np.ndarray:
        """
        Generate a frequency sequence where each step is root * PHI^n.

        Phi is used here as a proportional interval generator. Unlike equal
        temperament, every new frequency is derived from a single irrational
        scaling rule, which produces non-repeating relationships useful for
        meditative drones and evolving harmonic beds.
        """
        root = self._validate_frequency(root_freq)
        if length <= 0:
            raise ValueError("length must be a positive integer")

        sequence = root * np.power(PHI, np.arange(length, dtype=np.float64))
        return np.array([self._fold_to_audible(freq) for freq in sequence], dtype=np.float64)

    def create_binaural_beats(
        self,
        base_freq: float,
        beat_freq: float,
        duration: float,
        sample_rate: int | None = None,
    ) -> AudioRender:
        """
        Generate a stereo binaural tone.

        The left ear receives base_freq and the right ear receives
        base_freq + beat_freq. The perceived beat equals the difference between
        both channels. Vectorized NumPy synthesis keeps the function predictable.
        """
        sr = int(sample_rate or self.sample_rate)
        base = self._validate_frequency(base_freq)
        beat = float(beat_freq)
        if beat < 0:
            raise ValueError("beat_freq must be non-negative")
        self._validate_duration(duration)

        right_freq = self._fold_to_audible(base + beat)
        t = self._time_axis(duration, sr)
        left = np.sin(2.0 * np.pi * base * t)
        right = np.sin(2.0 * np.pi * right_freq * t)
        stereo = np.column_stack((left, right))
        stereo = self._apply_soft_envelope(stereo, sr)
        return AudioRender(samples=self._normalize(stereo), sample_rate=sr)

    def synthesize_om(self, human_base_freq: float, duration: float) -> AudioRender:
        """
        Synthesize an OM-like drone with Phi-spaced harmonics.

        A classical harmonic stack uses integer ratios. Phi harmonics use
        root * PHI^n, which avoids a perfectly repeating overtone ladder and
        makes the sound slowly evolving. A Schumann-rate amplitude modulation
        is included as a low-frequency texture, not as a medical intervention.
        """
        root = self._validate_frequency(human_base_freq)
        self._validate_duration(duration)

        t = self._time_axis(duration, self.sample_rate)
        phi_harmonics = np.array([self._fold_to_audible(root * scale) for scale in PHI_SCALE[:6]])
        amplitudes = 1.0 / np.power(PHI, np.arange(len(phi_harmonics), dtype=np.float64))

        phases = 2.0 * np.pi * phi_harmonics[:, None] * t[None, :]
        mono = np.sum(amplitudes[:, None] * np.sin(phases), axis=0) / np.sum(amplitudes)

        # Add a breath-like Phi modulation. The modulation depth is intentionally
        # modest so the root identity remains stable.
        mod_rate = SCHUMANN_BASE / PHI
        modulation = 0.82 + 0.18 * signal.sawtooth(2.0 * np.pi * mod_rate * t, width=0.5)
        mono *= modulation

        # Smooth harsh edges and duplicate to stereo.
        mono = self._apply_soft_envelope(mono, self.sample_rate)
        stereo = np.column_stack((mono, mono))
        return AudioRender(samples=self._normalize(stereo), sample_rate=self.sample_rate)

    def mix_layers(self, layers: list[AudioRender], weights: list[float] | None = None) -> AudioRender:
        """Mix same-sample-rate audio layers into one normalized stereo render."""
        if not layers:
            raise ValueError("At least one layer is required")
        sample_rate = layers[0].sample_rate
        if any(layer.sample_rate != sample_rate for layer in layers):
            raise ValueError("All layers must share the same sample rate")

        max_len = max(layer.samples.shape[0] for layer in layers)
        weights = weights or [1.0] * len(layers)
        if len(weights) != len(layers):
            raise ValueError("weights length must match layers length")

        mix = np.zeros((max_len, 2), dtype=np.float64)
        for layer, weight in zip(layers, weights):
            padded = np.zeros_like(mix)
            data = self._ensure_stereo(layer.samples)
            padded[: data.shape[0], :] = data
            mix += float(weight) * padded
        return AudioRender(samples=self._normalize(mix), sample_rate=sample_rate)

    def write_wav(self, render: AudioRender, output_path: str | Path) -> Path:
        """Write a stereo float render as 16-bit PCM WAV."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        pcm = np.clip(render.samples, -1.0, 1.0)
        wavfile.write(path, render.sample_rate, (pcm * np.iinfo(np.int16).max).astype(np.int16))
        return path

    def _time_axis(self, duration: float, sample_rate: int) -> np.ndarray:
        samples = int(round(float(duration) * sample_rate))
        if samples <= 0:
            raise ValueError("duration produced no samples")
        return np.arange(samples, dtype=np.float64) / sample_rate

    def _apply_soft_envelope(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        # Tukey avoids clicks at boundaries without custom loops.
        length = audio.shape[0]
        alpha = min(0.25, max(0.02, (2.0 * sample_rate) / max(length, 1)))
        envelope = signal.windows.tukey(length, alpha=alpha)
        if audio.ndim == 2:
            envelope = envelope[:, None]
        return audio * envelope

    def _ensure_stereo(self, samples: np.ndarray) -> np.ndarray:
        data = np.asarray(samples, dtype=np.float64)
        if data.ndim == 1:
            return np.column_stack((data, data))
        if data.ndim == 2 and data.shape[1] == 2:
            return data
        raise ValueError("Audio must be mono or stereo")

    def _normalize(self, audio: np.ndarray, peak: float = 0.92) -> np.ndarray:
        data = self._ensure_stereo(audio)
        max_abs = np.max(np.abs(data))
        if max_abs <= 1e-12:
            return data.astype(np.float32)
        return (peak * data / max_abs).astype(np.float32)

    def _validate_frequency(self, freq: float) -> float:
        value = float(freq)
        if not np.isfinite(value) or value <= 0:
            raise ValueError("frequency must be a positive finite number")
        return self._fold_to_audible(value)

    def _fold_to_audible(self, freq: float) -> float:
        value = float(freq)
        while value < MIN_FREQ_HZ:
            value *= PHI
        while value > MAX_FREQ_HZ:
            value /= PHI
        return value

    def _validate_duration(self, duration: float) -> None:
        if not np.isfinite(duration) or duration <= 0:
            raise ValueError("duration must be a positive finite number")
