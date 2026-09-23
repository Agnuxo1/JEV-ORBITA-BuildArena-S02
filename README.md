# JEV-ORBITA

JEV-ORBITA is the pre-start engineering harness for BuildArena S02. It combines the official BuildArena 2.0 control stack with JEV v4 deterministic-first orchestration while preserving the Autopilot rule that the final competition machine and ready-to-run mission controller must be created during Engineering Start.

## Purpose

The project provides reusable engineering infrastructure, not a prebuilt mission answer:

- published S02 score terms and qualification gates;
- mass-weighted recovery and landing evaluation;
- deterministic low-discrepancy parameter search with bounded local exploitation;
- append-only experiment records with stable identifiers;
- a safe adapter to the existing JEV v4 router;
- a preflight that blocks accidental pre-start mission artifacts;
- an initial Autopilot instruction for the official engineering run.

No final machine, trajectory, tuned mission controller, or claimed leaderboard score is included.

## Canonical paths

- Official BuildArena checkout: E:\Proyecto-concursos\BuildArena-S02
- JEV-ORBITA: E:\Proyecto-concursos\BuildArena-S02-JEV-ORBITA
- JEV v4: E:\TartanIMU-Cognitive-Stack
- uv and pip caches: E:\Proyecto-concursos\_cache
- temporary files: E:\Proyecto-concursos\_tmp

Project data and caches are deliberately kept off C:.

## Environment

Open PowerShell:

    cd E:\Proyecto-concursos\BuildArena-S02-JEV-ORBITA
    .\scripts\env.ps1
    $env:PYTHONPATH = "$PWD\src"

Run the preflight:

    python .\scripts\preflight.py

A blocked BuildArena setup check is expected until a licensed Besiege installation, required DLC, official BuildArena ToolKit, and the official one-command setup are present and .local/setup-report.json reports status=passed.

## Tests

    python -m unittest discover -s tests -v

The suite checks the strict radius gate, landing kernel, perfect-score reference case, recovery validity, deterministic adaptive search, and experiment-ledger persistence.

## Evidence scoring

Save measured mission evidence as JSON and run:

    python .\scripts\score_evidence.py evidence.json --best-payload-mass 10 --best-efficiency 1.0

Relative payload and efficiency terms require the relevant best value from the comparison pool. If those values are unknown, JEV-ORBITA deliberately returns null for those terms rather than inventing a score.

## Engineering Start

Before Engineering Start, maintain only this harness, the official tools, rules, skills, and the initial instruction. Do not create the competition mission machine or a ready-to-run mission controller.

At Engineering Start, use prompts\autopilot_initial.md as the initial human instruction and preserve the complete transcript. The autonomous agent then builds through the official MCP, writes its controller during the run, executes telemetry-driven experiments, diagnoses failures, and improves the system.

JEV is a semantic supervisor, not a frame-by-frame pilot. Use it after meaningful state changes and follow LUNA-FIRST. Deterministic code owns exact scoring, validation, experiment bookkeeping, budgets, and compliance.

The final controller should stay CPU-light. Optional offline surrogate work follows the compute policy TPU, then Colab, then local RTX 3090.
