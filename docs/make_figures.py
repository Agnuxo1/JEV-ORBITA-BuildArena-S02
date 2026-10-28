"""Render the animated README figures from the real jev_orbita code.

    PYTHONPATH=src python docs/make_figures.py

Every number drawn comes from jev_orbita (scorer, geometry, AdaptiveSearch).
The orbit animation uses a synthetic two-body test trajectory to illustrate the
gate checker; it is not a flight result.
"""
from __future__ import annotations

import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.patches import Circle, FancyBboxPatch

from jev_orbita import AdaptiveSearch, MissionEvidence, Recovery, evaluate_score, landing_accuracy
from jev_orbita.geometry import angular_progress, min_radius

OUT = Path(__file__).resolve().parent / "assets"
BG, PANEL, FG, MUTED = "#0d1117", "#161b22", "#e6edf3", "#8b949e"
CYAN, ORANGE, VIOLET, GREEN, RED = "#22d3ee", "#f97316", "#a78bfa", "#34d399", "#f43f5e"
plt.rcParams.update({
    "figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG,
    "text.color": FG, "axes.labelcolor": FG, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.edgecolor": "#30363d", "font.family": "DejaVu Sans", "font.size": 11,
})


def save(anim: FuncAnimation, name: str, fps: int = 20) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    anim.save(OUT / name, writer=PillowWriter(fps=fps), dpi=80)
    plt.close("all")
    print(name, round((OUT / name).stat().st_size / 1e6, 2), "MB")


def pipeline() -> None:
    steps = ["Design", "Build\n(MCP)", "Fly\n(Besiege)", "Observe\n(telemetry)", "Diagnose", "Improve"]
    fig, ax = plt.subplots(figsize=(9, 4.6))
    ax.set_xlim(-1.6, 1.6); ax.set_ylim(-1.25, 1.25); ax.set_aspect("equal"); ax.axis("off")
    pos = [(math.cos(math.pi / 2 - i * 2 * math.pi / 6), math.sin(math.pi / 2 - i * 2 * math.pi / 6)) for i in range(6)]
    boxes = []
    for (x, y), label in zip(pos, steps):
        box = FancyBboxPatch((x - 0.32, y - 0.17), 0.64, 0.34, boxstyle="round,pad=0.02,rounding_size=0.08",
                             fc=PANEL, ec="#30363d", lw=2)
        ax.add_patch(box); boxes.append(box)
        ax.text(x, y, label, ha="center", va="center", fontsize=10, color=FG, weight="bold")
    ax.text(0, 0.12, "JEV-ORBITA", ha="center", fontsize=17, weight="bold", color=CYAN)
    ax.text(0, -0.12, "closed-loop engineering", ha="center", fontsize=10, color=MUTED)
    status = ax.text(0, -0.36, "", ha="center", fontsize=9, color=VIOLET)
    notes = ["hypothesis written first", "official BuildArena MCP only", "official simulator, >=3 repeats",
             "scorer + gates on CSV", "JEV semantic checkpoint", "one causal change, regression flight"]
    dot, = ax.plot([], [], "o", ms=12, color=ORANGE)

    def frame(k):
        t = k / 12.0
        i = int(t) % 6
        for j, b in enumerate(boxes):
            b.set_edgecolor(ORANGE if j == i else "#30363d"); b.set_linewidth(3 if j == i else 2)
        a0 = math.pi / 2 - i * 2 * math.pi / 6
        a = a0 - (t - int(t)) * 2 * math.pi / 6
        dot.set_data([0.78 * math.cos(a)], [0.78 * math.sin(a)])
        status.set_text(notes[i])
        return boxes + [dot, status]

    save(FuncAnimation(fig, frame, frames=72, blit=False), "pipeline.gif", fps=12)


def orbit_gate() -> None:
    # Synthetic Keplerian test orbit (illustration of the gate checker only).
    center, gm, a, e = (0.0, 0.0, 0.0), 1.0, 1250.0, 0.06
    n = math.sqrt(gm / a ** 3)
    pts = []
    for k in range(0, 3 * 240 + 30):
        m = n * k * (2 * math.pi / n) / 240
        ecc = m
        for _ in range(8):
            ecc = ecc - (ecc - e * math.sin(ecc) - m) / (1 - e * math.cos(ecc))
        x, y = a * (math.cos(ecc) - e), a * math.sqrt(1 - e * e) * math.sin(ecc)
        pts.append((x, 0.0, y))
    fig, ax = plt.subplots(figsize=(6.4, 6.4))
    ax.set_aspect("equal"); ax.axis("off"); ax.set_xlim(-1500, 1500); ax.set_ylim(-1500, 1500)
    ax.add_patch(Circle((0, 0), 1000, fc="#1f3b57", ec="#2f6690", lw=2))
    ax.add_patch(Circle((0, 0), 1100, fc="none", ec=RED, lw=1.5, ls="--"))
    ax.text(0, -1135, "gate r > 1100", ha="center", va="top", color=RED, fontsize=9)
    trail, = ax.plot([], [], color=CYAN, lw=1.6, alpha=0.9)
    head, = ax.plot([], [], "o", color=ORANGE, ms=9)
    label = ax.text(0, 60, "", ha="center", fontsize=15, weight="bold")
    sub = ax.text(0, -110, "", ha="center", fontsize=10, color=MUTED)
    ax.text(0, 1440, "Three-orbit gate checker (synthetic test orbit)", ha="center", fontsize=11, color=FG)

    def frame(k):
        i = min(len(pts) - 1, k * 6)
        seg = pts[: i + 1]
        trail.set_data([p[0] for p in seg], [p[2] for p in seg]); head.set_data([seg[-1][0]], [seg[-1][2]])
        deg = math.degrees(angular_progress(seg, center)) if i else 0.0
        ok = deg >= 1080.0
        label.set_text(f"{deg:6.0f}° / 1080°"); label.set_color(GREEN if ok else FG)
        sub.set_text(f"r_min = {min_radius(seg, center):.0f}   " + ("GATE PASSED" if ok else "in progress"))
        return trail, head, label, sub

    save(FuncAnimation(fig, frame, frames=len(pts) // 6 + 12), "orbit_gate.gif", fps=20)


def landing_curve() -> None:
    d = [x * 0.25 for x in range(0, 321)]
    a = [landing_accuracy(x) for x in d]
    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.plot(d, a, color=CYAN, lw=2.5)
    ax.fill_between(d, a, color=CYAN, alpha=0.08)
    for ref, val in {0: 1.0, 10: 0.984, 20: 0.883, 30: 0.501, 40: 0.119, 50: 0.018}.items():
        ax.plot(ref, val, "o", color=VIOLET, ms=5)
    ax.set_xlabel("great-circle landing error d (game units)"); ax.set_ylabel("A(d)")
    ax.set_title("S02 landing accuracy — 40 points  (violet: Rules reference table)", color=FG, fontsize=11)
    ax.grid(color="#21262d"); ax.set_ylim(-0.05, 1.1)
    m, = ax.plot([], [], "o", color=ORANGE, ms=11)
    txt = ax.text(48, 0.85, "", fontsize=12, weight="bold")

    def frame(k):
        x = 70 * (0.5 - 0.5 * math.cos(math.pi * k / 60))
        y = landing_accuracy(x)
        m.set_data([x], [y]); txt.set_text(f"d = {x:5.1f}\nscore = {40 * y:5.1f} / 40")
        return m, txt

    save(FuncAnimation(fig, frame, frames=120), "landing_curve.gif", fps=20)


def score_stack() -> None:
    ev = MissionEvidence(5.0, 3.0, 1200.0, True, True, 10.0, 0.0, 100.0,
                         (Recovery(60.0, 0.0, 1.0, 10.0), Recovery(40.0, 0.0, 0.2, 0.0, landed=False)))
    worked = evaluate_score(ev, best_payload_mass=5.0, best_efficiency=0.5)
    ideal = evaluate_score(MissionEvidence(5.0, 3.0, 1200.0, True, True, 10.0, 0.0, 100.0,
                                           (Recovery(100.0, 0.0, 1.0, 10.0),)), best_payload_mass=5.0, best_efficiency=0.5)
    cases = [("Rules §10.7 example\n(60 % stage recovered)", worked), ("Full recovery\non target", ideal)]
    terms = [("payload", ORANGE), ("efficiency", VIOLET), ("recovery", CYAN), ("landing", GREEN)]
    fig, ax = plt.subplots(figsize=(8.6, 4.4))
    fig.subplots_adjust(left=0.25, right=0.97)

    def frame(k):
        ax.clear(); ax.set_xlim(0, 130); ax.set_ylim(-0.7, 1.7); ax.grid(axis="x", color="#21262d")
        ax.set_yticks([0, 1]); ax.set_yticklabels([c[0] for c in cases])
        ax.set_title("FinalScore = (payload + efficiency + recovery + landing) × 1.25 (Autopilot)", fontsize=10.5)
        f = min(1.0, k / 40)
        for row, (_, s) in enumerate(cases):
            left = 0.0
            for name, color in terms:
                w = getattr(s, name) * f
                ax.barh(row, w, left=left, color=color, height=0.5)
                left += w
            ax.barh(row, s.performance * 0.25 * f, left=left, color="#30363d", height=0.5, hatch="//")
            ax.text(left + s.performance * 0.25 * f + 2, row, f"{s.final * f:5.1f}", va="center", weight="bold")
        for i, (name, color) in enumerate(terms):
            ax.text(2 + 26 * i, -0.55, f"■ {name}", color=color, fontsize=10)
        ax.text(106, -0.55, "▨ ×1.25", color=MUTED, fontsize=10)

    save(FuncAnimation(fig, frame, frames=60), "score_stack.gif", fps=20)


def adaptive_search() -> None:
    def branin(x, y):
        return (y - 5.1 / (4 * math.pi ** 2) * x ** 2 + 5 / math.pi * x - 6) ** 2 + 10 * (1 - 1 / (8 * math.pi)) * math.cos(x) + 10

    search = AdaptiveSearch({"x": (-5.0, 10.0), "y": (0.0, 15.0)}, seed=7)
    history = []
    for _ in range(60):
        p = search.ask(1)[0]
        val = branin(p["x"], p["y"])
        search.tell(p, -val, feasible=True)
        history.append((p["x"], p["y"], val))
    xs = [-5 + 15 * i / 120 for i in range(121)]; ys = [15 * j / 120 for j in range(121)]
    z = [[math.log(branin(x, y)) for x in xs] for y in ys]
    fig, ax = plt.subplots(figsize=(6.6, 5.4))
    ax.contourf(xs, ys, z, levels=24, cmap="mako" if "mako" in plt.colormaps() else "viridis", alpha=0.85)
    ax.set_title("AdaptiveSearch: Halton exploration → local exploitation\n(Branin test function, minima ≈ 0.398)", fontsize=10)
    sc = ax.scatter([], [], s=28, c=[], cmap="plasma", vmin=0, vmax=60, edgecolors="white", linewidths=0.4)
    best, = ax.plot([], [], "*", color=ORANGE, ms=18)
    txt = ax.text(-4.6, 14.0, "", fontsize=11, weight="bold", color="white")

    def frame(k):
        n = min(len(history), k + 1)
        pts = history[:n]
        sc.set_offsets([(p[0], p[1]) for p in pts]); sc.set_array(list(range(n)))
        b = min(pts, key=lambda p: p[2])
        best.set_data([b[0]], [b[1]]); txt.set_text(f"trial {n:2d}   best f = {b[2]:.3f}")
        return sc, best, txt

    save(FuncAnimation(fig, frame, frames=len(history) + 15), "adaptive_search.gif", fps=8)


if __name__ == "__main__":
    pipeline(); orbit_gate(); landing_curve(); score_stack(); adaptive_search()
