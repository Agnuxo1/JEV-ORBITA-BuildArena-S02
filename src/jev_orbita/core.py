"""Deterministic utilities for BuildArena S02 engineering.

This module is deliberately mission-agnostic: it provides scoring, feasibility
gates, experiment bookkeeping, bounded parameter search, and a safe JEV adapter.
It does not contain a competition machine or a ready-to-run mission controller.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

AUTOPILOT_COEFFICIENT = 1.25
COPILOT_COEFFICIENT = 1.00
PAYLOAD_RADIUS_GATE = 1100.0
PAYLOAD_ORBITS_GATE = 3.0
RECOVERY_INTEGRITY_GATE = 0.90
RECOVERY_STABLE_SECONDS = 10.0


@dataclass(frozen=True)
class Recovery:
    """Evidence for one declared recovery machine."""
    dry_mass: float
    landing_distance: float
    structural_integrity: float
    stable_unpowered_seconds: float
    landed: bool = True

    @property
    def valid(self) -> bool:
        return (
            self.landed
            and self.dry_mass > 0.0
            and self.landing_distance >= 0.0
            and self.structural_integrity >= RECOVERY_INTEGRITY_GATE
            and self.stable_unpowered_seconds >= RECOVERY_STABLE_SECONDS
        )


@dataclass(frozen=True)
class MissionEvidence:
    """Minimal evidence needed to evaluate the published S02 score terms."""
    payload_mass: float
    payload_orbits: float
    payload_min_radius: float
    payload_unpowered: bool
    payload_independent: bool
    initial_propellant: float
    returned_unused_propellant: float
    initial_nonpayload_dry_mass: float
    recoveries: tuple[Recovery, ...] = ()

    @property
    def payload_qualifies(self) -> bool:
        return (
            self.payload_mass > 0.0
            and self.payload_orbits >= PAYLOAD_ORBITS_GATE
            and self.payload_min_radius > PAYLOAD_RADIUS_GATE
            and self.payload_unpowered
            and self.payload_independent
        )

    @property
    def fuel_expended(self) -> float:
        return max(0.0, self.initial_propellant - self.returned_unused_propellant)


@dataclass(frozen=True)
class ScoreBreakdown:
    payload: float | None
    efficiency: float | None
    recovery: float
    landing: float
    performance: float | None
    final: float | None
    payload_qualifies: bool


def landing_accuracy(distance: float) -> float:
    """Return the published S02 landing-accuracy kernel."""
    if distance < 0.0:
        raise ValueError("Landing distance cannot be negative.")
    raw = (1.0 - math.tanh((distance - 30.0) / 10.0)) / (1.0 + math.tanh(3.0))
    return 0.0 if raw < 0.001 else min(1.0, raw)


def _relative_score(value: float, best: float | None) -> float | None:
    """Return a 6..15 relative term; None means the global best is unknown."""
    if value <= 0.0:
        return 0.0
    if best is None:
        return None
    if best <= 0.0:
        return 15.0
    return 6.0 + 9.0 * min(1.0, value / best)


def evaluate_score(
    evidence: MissionEvidence,
    *,
    best_payload_mass: float | None = None,
    best_efficiency: float | None = None,
    mode: str = "autopilot",
) -> ScoreBreakdown:
    """Evaluate all S02 terms available from supplied mission evidence."""
    if evidence.initial_nonpayload_dry_mass <= 0.0:
        raise ValueError("Initial non-payload dry mass must be positive.")
    if evidence.initial_propellant < 0.0 or evidence.returned_unused_propellant < 0.0:
        raise ValueError("Propellant values cannot be negative.")

    qualifies = evidence.payload_qualifies
    payload = _relative_score(evidence.payload_mass, best_payload_mass) if qualifies else 0.0
    if not qualifies:
        efficiency = 0.0
    elif evidence.fuel_expended == 0.0:
        efficiency = 15.0
    else:
        eta = evidence.payload_mass / evidence.fuel_expended
        efficiency = _relative_score(eta, best_efficiency)

    valid = tuple(item for item in evidence.recoveries if item.valid)
    denominator = evidence.initial_nonpayload_dry_mass
    recovered_mass = sum(item.dry_mass for item in valid)
    recovery = 30.0 * min(1.0, recovered_mass / denominator)
    landing = 40.0 * min(
        1.0,
        sum(item.dry_mass * landing_accuracy(item.landing_distance) for item in valid)
        / denominator,
    )

    performance = None if payload is None or efficiency is None else (
        payload + efficiency + recovery + landing
    )
    normalized_mode = mode.casefold()
    if normalized_mode == "autopilot":
        coefficient = AUTOPILOT_COEFFICIENT
    elif normalized_mode == "copilot":
        coefficient = COPILOT_COEFFICIENT
    else:
        raise ValueError("Mode must be 'autopilot' or 'copilot'.")
    final = None if performance is None else performance * coefficient
    return ScoreBreakdown(
        payload=payload,
        efficiency=efficiency,
        recovery=recovery,
        landing=landing,
        performance=performance,
        final=final,
        payload_qualifies=qualifies,
    )


def _halton(index: int, base: int) -> float:
    """One deterministic element of a Halton low-discrepancy sequence."""
    result = 0.0
    factor = 1.0
    while index > 0:
        factor /= base
        result += factor * (index % base)
        index //= base
    return result


class AdaptiveSearch:
    """Bounded deterministic exploration followed by local exploitation."""

    PRIMES = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53)

    def __init__(self, bounds: Mapping[str, tuple[float, float]], seed: int = 0):
        if not bounds:
            raise ValueError("At least one bounded parameter is required.")
        if len(bounds) > len(self.PRIMES):
            raise ValueError("Too many parameters for the built-in sequence.")
        self.bounds = dict(bounds)
        for name, (low, high) in self.bounds.items():
            if not math.isfinite(low) or not math.isfinite(high) or low >= high:
                raise ValueError(f"Invalid bounds for {name}: {(low, high)}")
        self.seed = max(0, int(seed))
        self.observations: list[tuple[dict[str, float], float, bool]] = []

    def ask(self, count: int = 1) -> list[dict[str, float]]:
        """Return deterministic candidate parameter sets within every bound."""
        if count <= 0:
            raise ValueError("count must be positive.")
        feasible = [item for item in self.observations if item[2]]
        center = max(feasible, key=lambda item: item[1])[0] if feasible else None
        radius = max(0.03, 0.25 / math.sqrt(1.0 + len(feasible)))
        start = self.seed + len(self.observations) + 1
        proposals: list[dict[str, float]] = []
        for offset in range(count):
            index = start + offset
            point: dict[str, float] = {}
            for dim, (name, (low, high)) in enumerate(self.bounds.items()):
                unit = _halton(index, self.PRIMES[dim])
                if center is None:
                    value = low + unit * (high - low)
                else:
                    span = high - low
                    local_low = max(low, center[name] - radius * span)
                    local_high = min(high, center[name] + radius * span)
                    value = local_low + unit * (local_high - local_low)
                point[name] = value
            proposals.append(point)
        return proposals

    def tell(self, params: Mapping[str, float], objective: float, feasible: bool) -> None:
        """Record one measured experiment result."""
        canonical = {name: float(params[name]) for name in self.bounds}
        for name, value in canonical.items():
            low, high = self.bounds[name]
            if not low <= value <= high:
                raise ValueError(f"{name}={value} is outside {(low, high)}")
        if not math.isfinite(objective):
            raise ValueError("Objective must be finite.")
        self.observations.append((canonical, float(objective), bool(feasible)))


class ExperimentLedger:
    """Append-only JSONL ledger with deterministic experiment identifiers."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, record: Mapping[str, object]) -> str:
        payload = dict(record)
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        experiment_id = hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16]
        row = {"experiment_id": experiment_id, **payload}
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        return experiment_id

    def read_all(self) -> list[dict]:
        if not self.path.exists():
            return []
        return [
            json.loads(line)
            for line in self.path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]


class JevRouter:
    """Adapter to the installed JEV v4 router without exposing credentials."""

    def __init__(self, root: Path, profile: str = "agnuxo"):
        self.root = Path(root)
        self.profile = profile
        self.runner = self.root / "run.bat"
        if not self.runner.is_file():
            raise FileNotFoundError(self.runner)

    def route(self, task: str, timeout: float = 60.0) -> dict:
        """Send one compact semantic routing request to JEV."""
        if not task.strip():
            raise ValueError("JEV task cannot be empty.")
        env = os.environ.copy()
        env["TYPESAFE_PROFILE"] = self.profile
        command = subprocess.list2cmdline([str(self.runner), "route", task])
        result = subprocess.run(
            ["cmd.exe", "/d", "/s", "/c", command],
            cwd=self.root,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"JEV route failed with exit code {result.returncode}: {result.stderr.strip()}"
            )
        payload = json.loads(result.stdout)
        if payload.get("provenance") != "jev":
            raise RuntimeError("JEV did not return live remote provenance.")
        return payload
