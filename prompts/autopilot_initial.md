# JEV-ORBITA BuildArena S02 Initial Autopilot Instruction

This message marks Engineering Start. Work autonomously from this point until a submission-ready engineering package is produced. Do not request human engineering guidance, manual parameter tuning, manual piloting, or manual machine edits.

Use only legal BuildArena S02 mechanisms. Build the competition machine through the official BuildArena MCP and create the mission controller during this engineering run. Do not load, copy, or submit a prebuilt mission machine or a ready-to-run mission controller. Official examples may be studied for API contracts, telemetry semantics, and general control techniques, but the competition machine and controller must be engineered in this run.

Primary objective: maximize the official S02 FinalScore in Autopilot mode while preserving reproducibility and eligibility. Treat the payload qualification gate as mandatory: the separated payload must be independent, unpowered, complete at least three revolutions, and remain strictly above radius 1100 throughout the qualifying interval.

Optimize in this order until evidence supports moving on:

1. Establish a repeatable qualifying payload orbit.
2. Recover the largest possible fraction of non-payload dry mass with at least 90 percent structural integrity and at least 10 seconds of stable unpowered post-landing state.
3. Minimize landing distance because landing accuracy carries 40 points.
4. Improve fuel efficiency without weakening recovery; returned unused propellant must be measured explicitly.
5. Increase qualifying payload mass only after the recovery solution is robust.

Prefer simple, symmetric, low-degree-of-freedom hardware. Add complexity only after a recorded failure proves it is needed. Use closed-loop telemetry, explicit state machines, feedback control, online calibration or system identification where useful, and physics-based forecasts. Never infer physical success from command acknowledgement alone; verify the response in telemetry.

For every experiment, record configuration, code revision, telemetry path, mission gates, score terms, failure signature, and the single hypothesis being tested. Make one causal change at a time unless a structural redesign is explicitly selected at a semantic checkpoint. Retain the best known feasible configuration and run regression flights after every improvement.

Use JEV v4 only at meaningful semantic checkpoints: initial routing, a changed failure mode, model-tier escalation, major architecture change, and the final completion gate. Follow LUNA-FIRST. Escalate to Sol only after observable Luna insufficiency and to Astra only after an attempted but insufficient Sol result. Keep deterministic calculations, scoring, safety gates, and exact validation outside the language model.

The final real-time controller should remain lightweight and accelerator-independent. Simulations run in the official Windows environment; offline analysis of exported telemetry (fits, sweeps, statistics) is plain Python. Repeat every candidate configuration at least three times and report mean and standard deviation; keep experiments/LOG.md and experiments/experiments.csv up to date, including negative results.

Before completion, reproduce the final mission from a clean start using the required one-command control workflow, verify every required submission artifact, and run a compliance audit. Do not claim an official score or rank until the organizer has accepted and scored the submission.
