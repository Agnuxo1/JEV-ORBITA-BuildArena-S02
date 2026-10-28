# Experiment log — JEV-ORBITA / BuildArena S02

Every experiment: hypothesis → design → control → execution (fixed seeds / ≥3 repeats) → official metric → decision.
Negative results are recorded exactly like positive ones. Machine-readable copy: `experiments.csv`.

## E000 — Scorer fidelity against the official Rules (2026-10-28)
- **Hypothesis:** `jev_orbita.evaluate_score` and `landing_accuracy` reproduce the reference values printed in Rules §10.6 and the worked example §10.7.
- **Control:** the Rules themselves (official S02 scorer not yet published; Kaggle discussion 748404 unanswered).
- **Design:** deterministic unit tests (`tests/test_rules_reference.py`); tolerance 0.0006 because the table is printed to 3 decimals.
- **Result:** A(0,10,20,30,40,50) = 1.000, 0.984, 0.883, 0.501, 0.119, 0.018 — all within tolerance; truncation to 0 between 60 and 66 units; worked example gives Recovery 18.000 and Landing 24.000 exactly. 14/14 tests pass. Deterministic, so seed repetition is not applicable.
- **Decision:** accepted. Second validation (official `rocket_orbit_return` telemetry) is pending until the game is installed.

## E001 — Official environment readiness (2026-10-28)
- **Hypothesis:** the local PC satisfies Rules §5.2 (Windows, Besiege build 25434581, both DLC, ToolKit, setup passed).
- **Result:** blocked. Steam present; Besiege, The Splintered Sea, The Broken Beyond and ToolKit absent; `.local/setup-report.json` missing. JEV v4 profile ready; uv present; no prebuilt mission artefacts.
- **Decision:** rejected → consolidated single action in `PENDIENTE_FRAN.md`.
