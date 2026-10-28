"""Checks against the reference values printed in the official S02 Rules."""
from __future__ import annotations

import math
import unittest

from jev_orbita import MissionEvidence, Recovery, evaluate_score, landing_accuracy
from jev_orbita.geometry import angular_progress, great_circle_distance, min_radius, radius_gate_holds

# Rules 10.6 reference table: landing error d -> A(d), printed to 3 decimals.
RULES_A_TABLE = {0: 1.000, 10: 0.984, 20: 0.883, 30: 0.501, 40: 0.119, 50: 0.018}


class RulesReferenceTests(unittest.TestCase):
    def test_landing_table(self):
        for distance, expected in RULES_A_TABLE.items():
            self.assertAlmostEqual(landing_accuracy(distance), expected, delta=0.0006, msg=distance)

    def test_truncation_near_65(self):
        self.assertGreater(landing_accuracy(60.0), 0.0)
        self.assertEqual(landing_accuracy(66.0), 0.0)

    def test_worked_example_10_7(self):
        # 100 units of non-payload hardware; 60-unit stage lands on target; 40-unit stage crashes.
        evidence = MissionEvidence(
            payload_mass=5.0, payload_orbits=3.0, payload_min_radius=1200.0,
            payload_unpowered=True, payload_independent=True,
            initial_propellant=10.0, returned_unused_propellant=0.0,
            initial_nonpayload_dry_mass=100.0,
            recoveries=(Recovery(60.0, 0.0, 1.0, 10.0), Recovery(40.0, 0.0, 0.2, 0.0, landed=False)),
        )
        score = evaluate_score(evidence, best_payload_mass=5.0, best_efficiency=0.5)
        self.assertAlmostEqual(score.recovery, 18.0)
        self.assertAlmostEqual(score.landing, 24.0)

    def test_gate_failure_zeroes_everything_relative(self):
        evidence = MissionEvidence(
            payload_mass=5.0, payload_orbits=2.99, payload_min_radius=1200.0,
            payload_unpowered=True, payload_independent=True,
            initial_propellant=10.0, returned_unused_propellant=0.0,
            initial_nonpayload_dry_mass=100.0,
        )
        score = evaluate_score(evidence, best_payload_mass=5.0, best_efficiency=0.5)
        self.assertFalse(score.payload_qualifies)
        self.assertEqual(score.payload, 0.0)
        self.assertEqual(score.efficiency, 0.0)


class GeometryTests(unittest.TestCase):
    def test_great_circle_quarter_turn(self):
        d = great_circle_distance((0, 1000, 0), (1000, 0, 0), (0, 0, 0), 1000.0)
        self.assertAlmostEqual(d, 1000.0 * math.pi / 2)

    def test_three_revolutions(self):
        pts = [(1200 * math.cos(t), 0.0, 1200 * math.sin(t)) for t in (i * 0.05 for i in range(0, 380))]
        self.assertAlmostEqual(angular_progress(pts, (0, 0, 0)), 379 * 0.05, places=9)
        self.assertGreater(angular_progress(pts, (0, 0, 0)), 6 * math.pi)

    def test_back_and_forth_does_not_accumulate(self):
        pts = [(1200 * math.cos(t), 1200 * math.sin(t), 0.0) for t in (0.0, 0.5, 1.0, 0.5, 0.0, 0.5)]
        self.assertAlmostEqual(angular_progress(pts, (0, 0, 0), normal=(0, 0, 1)), 0.5)

    def test_radius_gate_strict(self):
        pts = [(1100.0, 0.0, 0.0), (0.0, 1300.0, 0.0)]
        self.assertEqual(min_radius(pts, (0, 0, 0)), 1100.0)
        self.assertFalse(radius_gate_holds(pts, (0, 0, 0)))


if __name__ == "__main__":
    unittest.main()
