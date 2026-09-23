"""Pre-start compliance and environment checks for JEV-ORBITA."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDARENA = Path(os.environ.get("ORBITA_BUILDARENA_ROOT", r"E:\Proyecto-concursos\BuildArena-S02"))
JEV = Path(os.environ.get("ORBITA_JEV_ROOT", r"E:\TartanIMU-Cognitive-Stack"))
PROFILE = os.environ.get("ORBITA_JEV_PROFILE", "agnuxo")


def setup_status() -> tuple[bool, str]:
    report = BUILDARENA / ".local" / "setup-report.json"
    if not report.is_file():
        return False, "BuildArena setup report is missing."
    try:
        payload = json.loads(report.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return False, f"BuildArena setup report is unreadable: {exc}"
    status = str(payload.get("status", "")).casefold()
    return status == "passed", f"BuildArena setup status: {status or 'unknown'}"


def jev_status() -> tuple[bool, str]:
    doctor = JEV / "connect_jev.bat"
    if not doctor.is_file():
        return False, "JEV v4 connector is missing."
    command = subprocess.list2cmdline([str(doctor), "doctor", "--profile", PROFILE])
    result = subprocess.run(
        ["cmd.exe", "/d", "/s", "/c", command],
        cwd=JEV,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
        check=False,
    )
    if result.returncode != 0:
        return False, f"JEV doctor failed with exit code {result.returncode}."
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return False, "JEV doctor returned non-JSON output."
    return payload.get("status") == "ready", f"JEV profile {PROFILE}: {payload.get('status', 'unknown')}"


def prebuilt_artifacts() -> list[str]:
    forbidden = {"trajectory.csv", "machine.bsg", "machine_raw.bsg", "machine_tuned.bsg"}
    return sorted(
        str(path.relative_to(ROOT))
        for path in ROOT.rglob("*")
        if path.is_file() and path.name.casefold() in forbidden
    )


def main() -> int:
    setup_ok, setup_note = setup_status()
    jev_ok, jev_note = jev_status()
    artifacts = prebuilt_artifacts()
    checks = [
        ("project_on_e", ROOT.drive.casefold() == "e:", str(ROOT)),
        ("buildarena_exists", BUILDARENA.is_dir(), str(BUILDARENA)),
        ("jev_exists", JEV.is_dir(), str(JEV)),
        ("uv_available", shutil.which("uv") is not None, shutil.which("uv") or "missing"),
        ("buildarena_setup", setup_ok, setup_note),
        ("jev_ready", jev_ok, jev_note),
        ("no_prebuilt_mission_artifacts", not artifacts, artifacts or "clean"),
    ]
    payload = {
        "schema": "jev-orbita.preflight.v1",
        "status": "passed" if all(item[1] for item in checks) else "blocked",
        "checks": [
            {"name": name, "ok": ok, "detail": detail}
            for name, ok, detail in checks
        ],
    }
    print(json.dumps(payload, indent=2))
    return 0 if payload["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
