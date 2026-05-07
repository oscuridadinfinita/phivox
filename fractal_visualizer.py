# Karpathy-style note:
# The visualizer is a renderer, not the source of truth. Symbolic intention is
# resolved by geometry_engine.py; this file only turns generated coordinates into
# pixels so the same geometry can later be rendered by WebGL, LEDs or hardware.

from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from config import VISUAL_DIR
from geometry_engine import GeometryProfile, SacredGeometryEngine


class GoldenSpiralVisualizer:
    """Generate real-time sacred-geometry frames as PNG bytes or files."""

    def __init__(self, output_dir: str | Path = VISUAL_DIR) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.geometry_engine = SacredGeometryEngine()

    def generate_frame(
        self,
        phase: float = 0.0,
        turns: float = 5.0,
        points: int = 1_600,
        size: tuple[float, float] = (6.0, 6.0),
        geometry: str | None = None,
        desired_state: str = "theta",
        source: str = "voice",
        intention: str = "calma",
        amplitude: float = 0.0,
    ) -> bytes:
        """Return one PNG frame for the selected geometry language."""
        profile = self.geometry_engine.resolve_profile(
            desired_state=desired_state,
            requested_geometry=geometry,
            source=source,
            intention=intention,
        )
        # Backward compatibility: old callers used turns=5.0 for a Phi spiral.
        if geometry is None and desired_state == "theta" and turns != 5.0:
            profile = GeometryProfile(
                geometry=profile.geometry,
                layers=max(1, int(round(turns))),
                source=profile.source,
                intention=profile.intention,
                desired_state=profile.desired_state,
                meaning=profile.meaning,
            )

        coordinates = self.geometry_engine.generate(
            profile=profile,
            phase=phase,
            points=points,
            amplitude=amplitude,
        )
        x = np.asarray(coordinates["x"], dtype=float)
        y = np.asarray(coordinates["y"], dtype=float)
        mode = str(coordinates.get("mode", "line"))

        fig, ax = plt.subplots(figsize=size, dpi=120)
        if mode == "scatter":
            sizes = np.asarray(coordinates.get("sizes", np.full_like(x, 10.0)), dtype=float)
            ax.scatter(x, y, s=sizes, alpha=0.78)
        else:
            line_width = 1.4 + 1.8 * float(np.clip(amplitude, 0.0, 1.0))
            ax.plot(x, y, linewidth=line_width, alpha=0.95)
            finite = np.isfinite(x) & np.isfinite(y)
            if np.any(finite):
                ax.scatter([x[finite][-1]], [y[finite][-1]], s=36 + 90 * amplitude)

        ax.set_aspect("equal", adjustable="box")
        ax.axis("off")
        ax.set_xlim(-1.05, 1.05)
        ax.set_ylim(-1.05, 1.05)
        fig.tight_layout(pad=0)

        buffer = BytesIO()
        fig.savefig(buffer, format="png", transparent=True)
        plt.close(fig)
        return buffer.getvalue()

    def generate_frame_base64(
        self,
        phase: float = 0.0,
        geometry: str | None = None,
        desired_state: str = "theta",
        source: str = "voice",
        intention: str = "calma",
        amplitude: float = 0.0,
    ) -> str:
        """Return a base64 PNG frame suitable for Socket.IO JSON payloads."""
        return base64.b64encode(
            self.generate_frame(
                phase=phase,
                geometry=geometry,
                desired_state=desired_state,
                source=source,
                intention=intention,
                amplitude=amplitude,
            )
        ).decode("ascii")

    def save_frame(
        self,
        filename: str = "sacred_geometry.png",
        phase: float = 0.0,
        geometry: str | None = None,
        desired_state: str = "theta",
        source: str = "voice",
        intention: str = "calma",
        amplitude: float = 0.0,
    ) -> Path:
        """Persist one frame for debugging or static previews."""
        path = self.output_dir / filename
        path.write_bytes(
            self.generate_frame(
                phase=phase,
                geometry=geometry,
                desired_state=desired_state,
                source=source,
                intention=intention,
                amplitude=amplitude,
            )
        )
        return path
