# Karpathy-style note:
# The visualizer is pure geometry: given a phase, return pixels. The golden
# spiral grows by powers of Phi, so each turn visually mirrors the same scaling
# principle used by the audio engine.

from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from config import PHI, VISUAL_DIR


class GoldenSpiralVisualizer:
    """Generate real-time frames of a Phi spiral as PNG bytes or files."""

    def __init__(self, output_dir: str | Path = VISUAL_DIR) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_frame(
        self,
        phase: float = 0.0,
        turns: float = 5.0,
        points: int = 1_200,
        size: tuple[float, float] = (6.0, 6.0),
    ) -> bytes:
        """Return one PNG frame of a golden spiral."""
        theta = np.linspace(0.0, turns * 2.0 * np.pi, points)
        growth = np.power(PHI, theta / (np.pi / 2.0) / 4.0)
        radius = growth / np.max(growth)
        x = radius * np.cos(theta + phase)
        y = radius * np.sin(theta + phase)

        fig, ax = plt.subplots(figsize=size, dpi=120)
        ax.plot(x, y, linewidth=2.0)
        ax.scatter([x[-1]], [y[-1]], s=40)
        ax.set_aspect("equal", adjustable="box")
        ax.axis("off")
        ax.set_xlim(-1.05, 1.05)
        ax.set_ylim(-1.05, 1.05)
        fig.tight_layout(pad=0)

        buffer = BytesIO()
        fig.savefig(buffer, format="png", transparent=True)
        plt.close(fig)
        return buffer.getvalue()

    def generate_frame_base64(self, phase: float = 0.0) -> str:
        """Return a base64 PNG frame suitable for Socket.IO JSON payloads."""
        return base64.b64encode(self.generate_frame(phase=phase)).decode("ascii")

    def save_frame(self, filename: str = "golden_spiral.png", phase: float = 0.0) -> Path:
        """Persist one spiral frame for debugging or static previews."""
        path = self.output_dir / filename
        path.write_bytes(self.generate_frame(phase=phase))
        return path
