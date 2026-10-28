"""Assemble and check the six required S02 Build-with-Agent items for one run.

    python scripts/package_submission.py runs/<stamp> [--out <dir>]

Copies nothing that the agent did not produce; it only gathers the run's
`workspace/submission/` items and the converted chat transcript, verifies that
all six items exist, that `control/` has CONTROL.md and a reproduce entry
point, scans the package for credential-like strings, and writes
MANIFEST.json with SHA-256 hashes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path

REQUIRED_FILES = ("machine.bsg", "build_history.json", "build_history_full.json", "trajectory.csv")
SECRET = re.compile(r"(sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9]{20,}|ANTHROPIC_API_KEY\s*=\s*\S+|KGAT_[A-Za-z0-9]+)")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    source = args.run / "workspace" / "submission"
    out = args.out or (args.run / "package")
    problems: list[str] = []

    out.mkdir(parents=True, exist_ok=True)
    for name in REQUIRED_FILES:
        if (source / name).is_file():
            shutil.copy2(source / name, out / name)
        else:
            problems.append(f"missing {name}")
    control = source / "control"
    if control.is_dir():
        shutil.copytree(control, out / "control", dirs_exist_ok=True)
        if not (control / "CONTROL.md").is_file():
            problems.append("control/CONTROL.md missing")
        if not any((control / n).is_file() for n in ("reproduce.py", "reproduce.ps1")):
            problems.append("control/ has no reproduce entry point")
    else:
        problems.append("missing control/")
    transcript = args.run / "chat_transcript.md"
    if transcript.is_file():
        shutil.copy2(transcript, out / "chat_transcript.md")
    else:
        problems.append("missing chat_transcript.md (run transcript_to_md.py first)")

    files = sorted(p for p in out.rglob("*") if p.is_file() and p.name != "MANIFEST.json")
    for path in files:
        if path.suffix.lower() in {".py", ".md", ".json", ".toml", ".ps1", ".txt", ".csv"}:
            if SECRET.search(path.read_text(encoding="utf-8", errors="replace")):
                problems.append(f"credential-like string in {path.relative_to(out)}")
    manifest = {
        "schema": "jev-orbita.submission.v1",
        "run": str(args.run),
        "status": "complete" if not problems else "incomplete",
        "problems": problems,
        "files": {str(p.relative_to(out)).replace("\\", "/"): sha256(p) for p in files},
    }
    (out / "MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({k: manifest[k] for k in ("status", "problems")}, indent=2))
    return 0 if not problems else 2


if __name__ == "__main__":
    raise SystemExit(main())
