# Karpathy-style note:
# Geometry is a translation layer: intent comes in as words and measurable
# signals, then deterministic math turns it into points. Keep every symbol as a
# small, inspectable function so PhiVox can grow a visual language without
# hiding the rules behind magic.

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

import numpy as np

from config import PHI

GeometryName = Literal[
    "phi_spiral",
    "archimedean_spiral",
    "fermat_spiral",
    "concentric_mandala",
    "flower_of_life",
    "torus_field",
]

FIBONACCI_LAYERS = (5, 8, 13, 21, 34)
GOLDEN_ANGLE = np.pi * (3.0 - np.sqrt(5.0))


@dataclass(frozen=True)
class GeometryProfile:
    """A symbolic contract between sound intention and visible form."""

    geometry: GeometryName
    layers: int
    source: str
    intention: str
    desired_state: str
    meaning: str

    def to_dict(self) -> dict[str, str | int]:
        return asdict(self)


STATE_GEOMETRY: dict[str, tuple[GeometryName, int, str]] = {
    "delta": (
        "concentric_mandala",
        5,
        "reposo profundo: círculos lentos que protegen el centro",
    ),
    "theta": (
        "phi_spiral",
        8,
        "imaginación y memoria: expansión orgánica desde la voz",
    ),
    "schumann": (
        "flower_of_life",
        13,
        "campo terrestre: interconexión entre cuerpo, paisaje y biodiversidad",
    ),
    "alpha": (
        "fermat_spiral",
        21,
        "claridad suave: distribución vegetal tipo semilla o flor",
    ),
    "beta": (
        "archimedean_spiral",
        13,
        "atención activa: ritmo ordenado y distancia constante",
    ),
}


class SacredGeometryEngine:
    """Generate deterministic 2D geometry paths for PhiVox frames."""

    def resolve_profile(
        self,
        desired_state: str = "theta",
        requested_geometry: str | None = None,
        source: str = "voice",
        intention: str = "calma",
    ) -> GeometryProfile:
        state = str(desired_state or "theta").lower().strip()
        geometry, layers, meaning = STATE_GEOMETRY.get(
            state,
            ("phi_spiral", 8, "intención libre: forma abierta basada en proporción"),
        )
        if requested_geometry:
            requested = requested_geometry.lower().strip()
            if requested not in GeometryName.__args__:  # type: ignore[attr-defined]
                allowed = ", ".join(GeometryName.__args__)  # type: ignore[attr-defined]
                raise ValueError(f"geometry must be one of: {allowed}")
            geometry = requested  # type: ignore[assignment]

        return GeometryProfile(
            geometry=geometry,
            layers=layers,
            source=str(source or "voice"),
            intention=str(intention or "calma"),
            desired_state=state,
            meaning=meaning,
        )

    def generate(
        self,
        profile: GeometryProfile,
        phase: float = 0.0,
        points: int = 1_600,
        amplitude: float = 0.0,
    ) -> dict[str, object]:
        """Return renderable coordinates and metadata for a geometry profile."""
        amplitude = float(np.clip(amplitude, 0.0, 1.0))
        layers = max(1, int(profile.layers))
        geometry = profile.geometry

        if geometry == "phi_spiral":
            return self._phi_spiral(layers, phase, points, amplitude)
        if geometry == "archimedean_spiral":
            return self._archimedean_spiral(layers, phase, points, amplitude)
        if geometry == "fermat_spiral":
            return self._fermat_spiral(layers, phase, points, amplitude)
        if geometry == "concentric_mandala":
            return self._concentric_mandala(layers, phase, points, amplitude)
        if geometry == "flower_of_life":
            return self._flower_of_life(layers, phase, points, amplitude)
        if geometry == "torus_field":
            return self._torus_field(layers, phase, points, amplitude)
        raise ValueError(f"Unsupported geometry: {geometry}")

    def _phi_spiral(self, layers: int, phase: float, points: int, amplitude: float) -> dict[str, object]:
        theta = np.linspace(0.0, layers * 2.0 * np.pi, points)
        growth = np.power(PHI, theta / (np.pi / 2.0) / 4.0)
        radius = growth / np.max(growth)
        radius *= 0.82 + 0.18 * amplitude
        x = radius * np.cos(theta + phase)
        y = radius * np.sin(theta + phase)
        return {"x": x, "y": y, "mode": "line"}

    def _archimedean_spiral(self, layers: int, phase: float, points: int, amplitude: float) -> dict[str, object]:
        theta = np.linspace(0.0, layers * 2.0 * np.pi, points)
        radius = np.linspace(0.0, 0.95, points) * (0.9 + 0.1 * amplitude)
        x = radius * np.cos(theta + phase)
        y = radius * np.sin(theta + phase)
        return {"x": x, "y": y, "mode": "line"}

    def _fermat_spiral(self, layers: int, phase: float, points: int, amplitude: float) -> dict[str, object]:
        seeds = max(points, layers * 144)
        n = np.arange(seeds)
        radius = np.sqrt(n / max(seeds - 1, 1)) * (0.92 + 0.08 * amplitude)
        theta = n * GOLDEN_ANGLE + phase
        x = radius * np.cos(theta)
        y = radius * np.sin(theta)
        sizes = 3.0 + 18.0 * np.sqrt(n / max(seeds - 1, 1))
        return {"x": x, "y": y, "mode": "scatter", "sizes": sizes}

    def _concentric_mandala(self, layers: int, phase: float, points: int, amplitude: float) -> dict[str, object]:
        per_ring = max(80, points // layers)
        xs: list[np.ndarray] = []
        ys: list[np.ndarray] = []
        theta = np.linspace(0.0, 2.0 * np.pi, per_ring)
        for index in range(1, layers + 1):
            radius = index / layers * (0.88 + 0.1 * amplitude)
            petal = 1.0 + 0.035 * np.sin(theta * (index + 2) + phase)
            xs.append(radius * petal * np.cos(theta + phase / (index + 1)))
            ys.append(radius * petal * np.sin(theta + phase / (index + 1)))
            xs.append(np.array([np.nan]))
            ys.append(np.array([np.nan]))
        return {"x": np.concatenate(xs), "y": np.concatenate(ys), "mode": "line"}

    def _flower_of_life(self, layers: int, phase: float, points: int, amplitude: float) -> dict[str, object]:
        circles = min(layers, 21)
        per_circle = max(80, points // max(circles, 1))
        theta = np.linspace(0.0, 2.0 * np.pi, per_circle)
        base_radius = 0.18 + 0.015 * amplitude
        centers = [(0.0, 0.0)]
        rings = int(np.ceil((circles - 1) / 6))
        for ring in range(1, rings + 1):
            for k in range(6 * ring):
                angle = phase * 0.05 + k * 2.0 * np.pi / (6 * ring)
                centers.append((ring * base_radius * np.cos(angle), ring * base_radius * np.sin(angle)))
                if len(centers) >= circles:
                    break
            if len(centers) >= circles:
                break

        xs: list[np.ndarray] = []
        ys: list[np.ndarray] = []
        scale = max(1.0, rings * base_radius + base_radius)
        for cx, cy in centers:
            xs.append((cx + base_radius * np.cos(theta)) / scale * 0.9)
            ys.append((cy + base_radius * np.sin(theta)) / scale * 0.9)
            xs.append(np.array([np.nan]))
            ys.append(np.array([np.nan]))
        return {"x": np.concatenate(xs), "y": np.concatenate(ys), "mode": "line"}

    def _torus_field(self, layers: int, phase: float, points: int, amplitude: float) -> dict[str, object]:
        t = np.linspace(0.0, layers * 2.0 * np.pi, points)
        major = 0.58
        minor = 0.28 + 0.05 * amplitude
        x = (major + minor * np.cos(PHI * t + phase)) * np.cos(t)
        y = (major + minor * np.cos(PHI * t + phase)) * np.sin(t)
        y += 0.20 * np.sin(PHI * t + phase)
        norm = max(np.max(np.abs(x)), np.max(np.abs(y)), 1e-9)
        return {"x": x / norm * 0.94, "y": y / norm * 0.94, "mode": "line"}
