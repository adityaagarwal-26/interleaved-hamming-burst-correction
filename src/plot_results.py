"""
Reads results/experiment_results.csv and generates plots:
  1. Success rate vs burst length, one line per interleaving depth
  2. Theory vs actual: overlay showing the theoretical max burst length
     matches where success rate actually drops

Run with: python src/plot_results.py
Requires: pip install matplotlib
"""

import csv
import os
import sys

import matplotlib.pyplot as plt

CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "results", "experiment_results.csv")
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "results")


def load_results():
    """Load the CSV into a list of dicts, with proper types."""
    rows = []
    with open(CSV_PATH, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                "depth": int(row["depth"]),
                "burst_length": int(row["burst_length"]),
                "num_trials": int(row["num_trials"]),
                "success_rate": float(row["success_rate"]),
                "theoretical_max_burst": int(row["theoretical_max_burst"]),
                "theory_predicts_success": row["theory_predicts_success"] == "True",
            })
    return rows


def plot_success_vs_burst_length(rows):
    """
    Plot 1: Success rate (y) vs burst length (x), one line per depth.
    This is your main result graph.
    """
    depths = sorted(set(r["depth"] for r in rows))

    plt.figure(figsize=(9, 6))

    for depth in depths:
        depth_rows = sorted(
            [r for r in rows if r["depth"] == depth],
            key=lambda r: r["burst_length"]
        )
        x = [r["burst_length"] for r in depth_rows]
        y = [r["success_rate"] * 100 for r in depth_rows]
        plt.plot(x, y, marker="o", markersize=3, label=f"Depth = {depth}")

    plt.xlabel("Burst Error Length (bits)")
    plt.ylabel("Correction Success Rate (%)")
    plt.title("Interleaved Hamming(7,4): Success Rate vs Burst Length, by Interleaving Depth")
    plt.legend(title="Interleaving Depth")
    plt.grid(True, alpha=0.3)
    plt.ylim(-5, 105)

    out_path = os.path.join(RESULTS_DIR, "success_vs_burstlen.png")
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    print(f"Saved: {out_path}")
    plt.close()


def plot_theory_vs_actual(rows):
    """
    Plot 2: For each depth, show the point where success rate drops
    (actual) vs. the theoretical max burst length (predicted).
    This is your validation graph -- proves simulation matches theory.
    """
    depths = sorted(set(r["depth"] for r in rows))

    actual_breakpoints = []
    theoretical_breakpoints = []

    for depth in depths:
        depth_rows = sorted(
            [r for r in rows if r["depth"] == depth],
            key=lambda r: r["burst_length"]
        )
        # Find the last burst_length where success_rate is still high (>= 95%)
        last_success = 0
        for r in depth_rows:
            if r["success_rate"] >= 0.95:
                last_success = r["burst_length"]
        actual_breakpoints.append(last_success)
        theoretical_breakpoints.append(depth_rows[0]["theoretical_max_burst"])

    plt.figure(figsize=(8, 6))
    x = range(len(depths))
    width = 0.35

    plt.bar([i - width / 2 for i in x], theoretical_breakpoints, width,
            label="Theoretical Max Burst Length", color="#4C72B0")
    plt.bar([i + width / 2 for i in x], actual_breakpoints, width,
            label="Actual (Simulated) Max Burst Survived", color="#DD8452")

    plt.xlabel("Interleaving Depth")
    plt.ylabel("Max Burst Length Survived (bits)")
    plt.title("Theoretical Prediction vs Simulated Result")
    plt.xticks(list(x), [str(d) for d in depths])
    plt.legend()
    plt.grid(True, alpha=0.3, axis="y")

    out_path = os.path.join(RESULTS_DIR, "theory_vs_actual.png")
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    print(f"Saved: {out_path}")
    plt.close()

    # Print the comparison as text too, useful for the report
    print("\nTheory vs Actual breakdown:")
    print(f"{'Depth':<8}{'Theoretical Max Burst':<25}{'Actual Max Burst Survived':<25}")
    for d, t, a in zip(depths, theoretical_breakpoints, actual_breakpoints):
        match = "MATCH" if t == a else "DIFFERS"
        print(f"{d:<8}{t:<25}{a:<25}{match}")


def plot_delay_vs_depth(rows):
    """
    Plot 3: Decode delay vs interleaving depth.
    Delay here = depth (in block units), since the receiver must buffer
    `depth` blocks before it can start de-interleaving. This is the
    COST side of the tradeoff -- higher depth = more protection but
    more buffering delay.
    """
    depths = sorted(set(r["depth"] for r in rows))
    delay_in_blocks = depths  # decode delay = depth, by construction
    delay_in_bits = [d * 7 for d in depths]  # each block is 7 bits

    plt.figure(figsize=(8, 6))
    plt.plot(depths, delay_in_bits, marker="o", color="#C44E52")
    plt.xlabel("Interleaving Depth")
    plt.ylabel("Decode Delay (bits that must be buffered)")
    plt.title("Decoding Delay vs Interleaving Depth (the cost of protection)")
    plt.grid(True, alpha=0.3)
    plt.xticks(depths)

    out_path = os.path.join(RESULTS_DIR, "delay_vs_depth.png")
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    print(f"Saved: {out_path}")
    plt.close()


if __name__ == "__main__":
    if not os.path.exists(CSV_PATH):
        print(f"ERROR: {CSV_PATH} not found. Run src/experiment.py first.")
        sys.exit(1)

    rows = load_results()
    print(f"Loaded {len(rows)} result rows from {CSV_PATH}\n")

    plot_success_vs_burst_length(rows)
    plot_theory_vs_actual(rows)
    plot_delay_vs_depth(rows)

    print("\nAll plots generated in results/ folder.")