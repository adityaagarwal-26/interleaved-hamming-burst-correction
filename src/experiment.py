"""
Experiment runner: sweeps interleaving depth x burst length, running many
trials for each combination, and saves the results to a CSV file for
plotting (Day 5) and for the recommend.py tool (Day 6).

Run with: python src/experiment.py
"""

import csv
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from pipeline import run_trials
from interleaver import theoretical_max_burst_length


# ---- Experiment configuration ----
DEPTHS = [1, 2, 4, 8, 16]
BURST_LENGTHS = list(range(1, 21))  # burst lengths 1 through 20
NUM_TRIALS = 500  # trials per (depth, burst_length) combination

OUTPUT_CSV = os.path.join(os.path.dirname(__file__), "..", "results", "experiment_results.csv")


def run_full_sweep():
    """
    Run run_trials() for every (depth, burst_length) combination in the
    configured grid, and write results to a CSV file.
    """
    results = []
    total_combinations = len(DEPTHS) * len(BURST_LENGTHS)
    combo_num = 0

    start_time = time.time()

    for depth in DEPTHS:
        for burst_length in BURST_LENGTHS:
            combo_num += 1
            result = run_trials(
                depth=depth,
                burst_length=burst_length,
                num_trials=NUM_TRIALS,
                base_seed=depth * 1000 + burst_length,  # unique seed per combo
            )

            # Add theoretical prediction: does theory say this should succeed?
            max_survivable = theoretical_max_burst_length(depth)
            theory_predicts_success = burst_length <= max_survivable

            result["theoretical_max_burst"] = max_survivable
            result["theory_predicts_success"] = theory_predicts_success

            results.append(result)

            print(
                f"[{combo_num}/{total_combinations}] depth={depth:2d}  "
                f"burst_length={burst_length:2d}  "
                f"success_rate={result['success_rate']:.1%}  "
                f"(theory: {'survive' if theory_predicts_success else 'fail'})"
            )

    elapsed = time.time() - start_time
    print(f"\nSweep complete in {elapsed:.1f}s. Writing results to {OUTPUT_CSV}")

    # Ensure results directory exists
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)

    with open(OUTPUT_CSV, "w", newline="") as f:
        fieldnames = [
            "depth", "burst_length", "num_trials", "success_rate",
            "theoretical_max_burst", "theory_predicts_success",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow(row)

    print(f"Saved {len(results)} rows to {OUTPUT_CSV}")
    return results


def validate_theory_match(results):
    """
    Quick check: for cases where burst_length is well below the theoretical
    max, success rate should be ~100%. For cases well above, it should be
    much lower. This is a sanity check, not a strict pass/fail test.
    """
    print("\n--- Theory vs Actual sanity check ---")
    mismatches = 0
    for r in results:
        if r["theory_predicts_success"] and r["success_rate"] < 0.95:
            print(
                f"  NOTE: depth={r['depth']}, burst={r['burst_length']} -- "
                f"theory predicts survival but success_rate={r['success_rate']:.1%}"
            )
            mismatches += 1
        elif not r["theory_predicts_success"] and r["burst_length"] > r["theoretical_max_burst"] + 2 \
                and r["success_rate"] > 0.5:
            print(
                f"  NOTE: depth={r['depth']}, burst={r['burst_length']} -- "
                f"theory predicts failure but success_rate={r['success_rate']:.1%}"
            )
            mismatches += 1

    if mismatches == 0:
        print("  All results align well with theoretical predictions.")
    else:
        print(f"  {mismatches} combinations show notable theory/practice divergence "
              f"(worth discussing in your report -- likely due to burst position "
              f"relative to block boundaries).")


if __name__ == "__main__":
    results = run_full_sweep()
    validate_theory_match(results)