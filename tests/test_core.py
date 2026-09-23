from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from jev_orbita import AdaptiveSearch, ExperimentLedger
from jev_orbita import MissionEvidence, Recovery, evaluate_score, landing_accuracy


class ScoringTests(unittest.TestCase):
    def test_landing_kernel(self):
        self.assertAlmostEqual(landing_accuracy(0.0), 1.0, places=12)
        self.assertGreater(landing_accuracy(20.0), landing_accuracy(30.0))
        self.assertGreater(landing_accuracy(30.0), landing_accuracy(40.0))
        self.assertEqual(landing_accuracy(100.0), 0.0)

    def test_full_recovery_and_exact_site(self):
        evidence = MissionEvidence(
            payload_mass=10.0,
            payload_orbits=3.0,
            payload_min_radius=1100.001,
            payload_unpowered=True,
            payload_independent=True,
            initial_propellant=20.0,
            returned_unused_propellant=10.0,
            initial_nonpayload_dry_mass=100.0,
            recoveries=(Recovery(100.0, 0.0, 0.95, 10.0),),
        )
        score = evaluate_score(
            evidence,
            best_payload_mass=10.0,
            best_efficiency=1.0,
            mode="autopilot",
        )
        self.assertTrue(score.payload_qualifies)
        self.assertAlmostEqual(score.performance, 100.0)
        self.assertAlmostEqual(score.final, 125.0)

    def test_radius_gate_is_strict(self):
        evidence = MissionEvidence(
            payload_mass=1.0,
            payload_orbits=3.0,
            payload_min_radius=1100.0,
            payload_unpowered=True,
            payload_independent=True,
            initial_propellant=0.0,
            returned_unused_propellant=0.0,
            initial_nonpayload_dry_mass=1.0,
        )
        score = evaluate_score(evidence, best_payload_mass=1.0, best_efficiency=1.0)
        self.assertFalse(score.payload_qualifies)
        self.assertEqual(score.payload, 0.0)
        self.assertEqual(score.efficiency, 0.0)

    def test_invalid_recovery_scores_zero(self):
        evidence = MissionEvidence(
            payload_mass=0.0,
            payload_orbits=0.0,
            payload_min_radius=0.0,
            payload_unpowered=False,
            payload_independent=False,
            initial_propellant=1.0,
            returned_unused_propellant=0.0,
            initial_nonpayload_dry_mass=10.0,
            recoveries=(Recovery(10.0, 0.0, 0.899, 20.0),),
        )
        score = evaluate_score(evidence)
        self.assertEqual(score.recovery, 0.0)
        self.assertEqual(score.landing, 0.0)


class SearchAndLedgerTests(unittest.TestCase):
    def test_search_is_bounded_and_deterministic(self):
        left = AdaptiveSearch({"x": (0.0, 1.0), "y": (-2.0, 2.0)}, seed=7)
        right = AdaptiveSearch({"x": (0.0, 1.0), "y": (-2.0, 2.0)}, seed=7)
        first = left.ask(4)
        self.assertEqual(first, right.ask(4))
        for point in first:
            self.assertTrue(0.0 <= point["x"] <= 1.0)
            self.assertTrue(-2.0 <= point["y"] <= 2.0)
        left.tell(first[0], objective=1.0, feasible=True)
        self.assertEqual(len(left.ask(3)), 3)

    def test_ledger_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = ExperimentLedger(Path(tmp) / "experiments.jsonl")
            first = ledger.append({"score": 12.5, "gate": True})
            second = ledger.append({"score": 10.0, "gate": False})
            self.assertNotEqual(first, second)
            rows = ledger.read_all()
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["score"], 12.5)


if __name__ == "__main__":
    unittest.main()
