"""Score a JSON mission-evidence record with the published S02 formulas."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from jev_orbita import MissionEvidence, Recovery, evaluate_score


def load_evidence(path: Path) -> MissionEvidence:
    payload = json.loads(path.read_text(encoding="utf-8"))
    recoveries = tuple(Recovery(**item) for item in payload.pop("recoveries", []))
    return MissionEvidence(recoveries=recoveries, **payload)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--best-payload-mass", type=float)
    parser.add_argument("--best-efficiency", type=float)
    parser.add_argument("--mode", choices=("autopilot", "copilot"), default="autopilot")
    args = parser.parse_args()
    score = evaluate_score(
        load_evidence(args.evidence),
        best_payload_mass=args.best_payload_mass,
        best_efficiency=args.best_efficiency,
        mode=args.mode,
    )
    print(json.dumps(score.__dict__, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
