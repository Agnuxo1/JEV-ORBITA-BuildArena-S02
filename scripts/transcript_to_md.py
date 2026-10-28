"""Convert a Claude Code stream-json run transcript into chat_transcript.md.

Keeps the initial human instruction, administrative resume messages and the
agent's own reasoning text; tool calls are listed by name and tool results are
omitted (the organiser removes machine-produced text before token counting).

    python scripts/transcript_to_md.py runs/<stamp>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def convert(run: Path) -> Path:
    lines = [
        "# chat_transcript.md — JEV-ORBITA Autopilot engineering run",
        "",
        "## Initial human instruction (complete)",
        "",
        (run / "initial_instruction.md").read_text(encoding="utf-8").strip(),
        "",
    ]
    admin = run / "admin_messages.log"
    if admin.is_file():
        lines += ["## Administrative resume messages", ""]
        lines += [f"- {row}" for row in admin.read_text(encoding="utf-8").splitlines() if row.strip()]
        lines.append("")
    lines += ["## Agent record", ""]
    for raw in (run / "transcript.jsonl").read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            event = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if event.get("type") != "assistant":
            continue
        for block in event.get("message", {}).get("content", []):
            if block.get("type") == "text" and block.get("text", "").strip():
                lines += ["**Agent:** " + block["text"].strip(), ""]
            elif block.get("type") == "tool_use":
                lines.append(f"- tool call: `{block.get('name')}`")
    out = run / "chat_transcript.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


if __name__ == "__main__":
    print(convert(Path(sys.argv[1])))
