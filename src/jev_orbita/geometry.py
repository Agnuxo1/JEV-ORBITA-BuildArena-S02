"""Mission-agnostic geometry for S02 evidence checks.

Implements the published S02 definitions (Rules 7.3, 7.4 and 10.6): the
great-circle landing error on the official spherical planet, continuous
angular progress about the planet centre on one orbital plane, and the strict
minimum-radius gate. Planet centre and surface radius are explicit inputs; the
engineering agent measures them in the official environment.
"""
from __future__ import annotations

import math
from typing import Iterable, Sequence

Vector = Sequence[float]


def _sub(a: Vector, b: Vector) -> tuple[float, float, float]:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _dot(a: Vector, b: Vector) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a: Vector, b: Vector) -> tuple[float, float, float]:
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _norm(a: Vector) -> float:
    return math.sqrt(_dot(a, a))


def great_circle_distance(position: Vector, target: Vector, center: Vector, surface_radius: float) -> float:
    """Rule 10.6 landing error: R_surface * arccos(clamp(cos angle, -1, 1))."""
    if surface_radius <= 0.0:
        raise ValueError("Surface radius must be positive.")
    p, t = _sub(position, center), _sub(target, center)
    denom = _norm(p) * _norm(t)
    if denom == 0.0:
        raise ValueError("Positions must differ from the planet centre.")
    return surface_radius * math.acos(max(-1.0, min(1.0, _dot(p, t) / denom)))


def orbit_plane_normal(points: Iterable[Vector], center: Vector) -> tuple[float, float, float]:
    """Unit normal of the dominant orbital plane (sum of consecutive cross products)."""
    total = [0.0, 0.0, 0.0]
    previous = None
    for point in points:
        rel = _sub(point, center)
        if previous is not None:
            c = _cross(previous, rel)
            total = [total[0] + c[0], total[1] + c[1], total[2] + c[2]]
        previous = rel
    length = _norm(total)
    if length == 0.0:
        raise ValueError("Trajectory does not define an orbital plane.")
    return (total[0] / length, total[1] / length, total[2] / length)


def angular_progress(points: Sequence[Vector], center: Vector, normal: Vector | None = None) -> float:
    """Continuous signed angle (radians) swept about the centre on one plane.

    Each step adds the wrapped angle between consecutive projected radius
    vectors, so the result keeps counting beyond 2*pi. The magnitude is
    returned; 6*pi is the S02 three-revolution gate.
    """
    if len(points) < 2:
        return 0.0
    n = orbit_plane_normal(points, center) if normal is None else normal
    swept = 0.0
    previous = None
    for point in points:
        rel = _sub(point, center)
        k = _dot(rel, n)
        proj = (rel[0] - k * n[0], rel[1] - k * n[1], rel[2] - k * n[2])
        if previous is not None:
            swept += math.atan2(_dot(_cross(previous, proj), n), _dot(previous, proj))
        previous = proj
    return abs(swept)


def min_radius(points: Iterable[Vector], center: Vector) -> float:
    """Smallest planet-centred distance over the supplied points."""
    return min(_norm(_sub(p, center)) for p in points)


def radius_gate_holds(points: Iterable[Vector], center: Vector, gate: float = 1100.0) -> bool:
    """Rule 7.4: every point strictly above the gate radius."""
    return min_radius(points, center) > gate
