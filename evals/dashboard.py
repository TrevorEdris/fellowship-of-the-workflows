#!/usr/bin/env python3
"""Generate a visual dashboard for autoresearch results.

Usage:
    ./evals/dashboard.py <target_name>           # Generate + open PNG
    ./evals/dashboard.py <target_name> --all      # Show all targets side by side
    ./evals/dashboard.py --list                   # List targets with scores

Requires: pandas, matplotlib (pip install pandas matplotlib)
"""

import os
import subprocess
import sys
from pathlib import Path

EVALS_DIR = Path(__file__).parent
TARGETS_DIR = EVALS_DIR / "targets"


def load_results(target_name: str):
    """Load results.tsv for a target, return pandas DataFrame."""
    import pandas as pd

    tsv = TARGETS_DIR / target_name / "results.tsv"
    if not tsv.exists():
        return None
    df = pd.read_csv(tsv, sep="\t")
    df["pass_rate"] = df["pass_rate"].str.rstrip("%").astype(float)
    return df


def list_targets():
    """Print a summary table of all targets with results."""
    targets = sorted(d.name for d in TARGETS_DIR.iterdir() if d.is_dir())
    if not targets:
        print("No targets found.")
        return

    print(f"{'Target':<25} {'Experiments':>11} {'Best':>8} {'Latest':>8} {'Status'}")
    print("-" * 70)

    for name in targets:
        df = load_results(name)
        if df is None or df.empty:
            print(f"{name:<25} {'no results':>11}")
            continue

        total = len(df)
        kept = df[df["status"] == "keep"]
        best = kept["pass_rate"].max() if not kept.empty else 0
        latest = df.iloc[-1]["pass_rate"]
        latest_status = df.iloc[-1]["status"]
        print(f"{name:<25} {total:>11} {best:>7.1f}% {latest:>7.1f}% {latest_status}")


def plot_target(target_name: str, ax=None):
    """Plot autoresearch progress for a single target."""
    import matplotlib.pyplot as plt

    df = load_results(target_name)
    if df is None or df.empty:
        print(f"No results for {target_name}")
        return None

    standalone = ax is None
    if standalone:
        fig, ax = plt.subplots(figsize=(14, 7))

    # Experiment index
    df = df.reset_index(drop=True)
    baseline_rate = df.iloc[0]["pass_rate"]

    # Discarded experiments: gray dots
    disc = df[df["status"] == "discard"]
    if not disc.empty:
        ax.scatter(disc.index, disc["pass_rate"],
                   c="#cccccc", s=20, alpha=0.6, zorder=2, label="Discarded")

    # Crashed/skipped
    crash = df[df["status"] == "crash"]
    if not crash.empty:
        ax.scatter(crash.index, crash["pass_rate"],
                   c="#e74c3c", s=20, alpha=0.6, zorder=2, marker="x", label="Crashed")

    # Pending (not yet decided)
    pending = df[df["status"] == "pending"]
    if not pending.empty:
        ax.scatter(pending.index, pending["pass_rate"],
                   c="#f39c12", s=30, alpha=0.7, zorder=3, marker="D", label="Pending")

    # Kept experiments: green dots
    kept = df[df["status"] == "keep"]
    if not kept.empty:
        ax.scatter(kept.index, kept["pass_rate"],
                   c="#2ecc71", s=60, zorder=4, label="Kept",
                   edgecolors="black", linewidths=0.5)

        # Running maximum line
        running_max = kept["pass_rate"].cummax()
        ax.step(kept.index, running_max, where="post", color="#27ae60",
                linewidth=2, alpha=0.7, zorder=3, label="Running best")

        # Label kept experiments
        for idx, row in kept.iterrows():
            desc = str(row["description"]).strip()
            if len(desc) > 40:
                desc = desc[:37] + "..."
            ax.annotate(desc, (idx, row["pass_rate"]),
                        textcoords="offset points", xytext=(6, 6),
                        fontsize=7.5, color="#1a7a3a", alpha=0.85,
                        rotation=20, ha="left", va="bottom")

    # Baseline reference line
    ax.axhline(y=baseline_rate, color="#3498db", linewidth=1, linestyle="--",
               alpha=0.5, label=f"Baseline ({baseline_rate:.1f}%)")

    # Labels
    n_total = len(df)
    n_kept = len(kept)
    best_rate = kept["pass_rate"].max() if not kept.empty else baseline_rate
    improvement = best_rate - baseline_rate

    ax.set_xlabel("Experiment #", fontsize=11)
    ax.set_ylabel("Pass Rate %", fontsize=11)
    ax.set_title(
        f"{target_name}: {n_total} experiments, {n_kept} kept, "
        f"best {best_rate:.1f}% ({improvement:+.1f}% vs baseline)",
        fontsize=13,
    )
    ax.legend(loc="lower right", fontsize=8)
    ax.grid(True, alpha=0.15)
    ax.set_ylim(max(0, baseline_rate - 15), min(100, best_rate + 15))

    if standalone:
        return fig
    return ax


def plot_all_targets():
    """Plot all targets that have results, side by side."""
    import matplotlib.pyplot as plt

    targets = sorted(
        d.name for d in TARGETS_DIR.iterdir()
        if d.is_dir() and (d / "results.tsv").exists()
    )
    if not targets:
        print("No targets with results found.")
        return None

    n = len(targets)
    cols = min(n, 2)
    rows = (n + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(14 * cols, 7 * rows), squeeze=False)

    for i, name in enumerate(targets):
        r, c = divmod(i, cols)
        plot_target(name, ax=axes[r][c])

    # Hide unused subplots
    for i in range(n, rows * cols):
        r, c = divmod(i, cols)
        axes[r][c].set_visible(False)

    fig.tight_layout()
    return fig


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    # Check deps
    try:
        import pandas  # noqa: F401
        import matplotlib  # noqa: F401
        matplotlib.use("Agg")  # Non-interactive backend
    except ImportError:
        print("Missing dependencies. Install with:")
        print("  cd cli && .venv/bin/python -m pip install pandas matplotlib")
        sys.exit(1)

    import matplotlib.pyplot as plt

    if sys.argv[1] == "--list":
        list_targets()
        return

    if sys.argv[1] == "--all" or (len(sys.argv) > 2 and sys.argv[2] == "--all"):
        fig = plot_all_targets()
        if fig is None:
            return
        out = EVALS_DIR / "dashboard-all.png"
    else:
        target_name = sys.argv[1]
        if not (TARGETS_DIR / target_name).is_dir():
            print(f"Target not found: {target_name}")
            print(f"Available: {', '.join(d.name for d in TARGETS_DIR.iterdir() if d.is_dir())}")
            sys.exit(1)
        fig = plot_target(target_name)
        if fig is None:
            return
        out = TARGETS_DIR / target_name / "dashboard.png"

    fig.tight_layout()
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved to {out}")

    # Open on macOS
    if sys.platform == "darwin":
        subprocess.run(["open", str(out)], check=False)


if __name__ == "__main__":
    main()
