"""
recommend.py -- given a channel's expected burst length and a target
correction success rate, recommend the minimum interleaving depth needed.

This reads results/experiment_results.csv (produced by experiment.py)
and looks up, for the requested burst length, the smallest depth that
achieves at least the target success rate.

Usage:
    python src/recommend.py --avg-burst-length 5 --target-success-rate 0.95
"""

import argparse
import csv
import os
import sys

CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "results", "experiment_results.csv")


def load_results():
    rows = []
    with open(CSV_PATH, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                "depth": int(row["depth"]),
                "burst_length": int(row["burst_length"]),
                "success_rate": float(row["success_rate"]),
            })
    return rows


def recommend_depth(avg_burst_length: int, target_success_rate: float, rows):
    """
    Find the smallest interleaving depth that achieves >= target_success_rate
    at the given burst length, using the experiment results.

    Returns a dict with the recommendation, or None if no tested depth
    meets the target (caller should suggest going higher than what was tested).
    """
    # Filter to rows matching (or nearest to) the requested burst length
    matching = [r for r in rows if r["burst_length"] == avg_burst_length]

    if not matching:
        # Burst length wasn't directly tested -- find the closest tested value
        available_bursts = sorted(set(r["burst_length"] for r in rows))
        closest = min(available_bursts, key=lambda b: abs(b - avg_burst_length))
        print(f"Note: burst length {avg_burst_length} wasn't directly tested; "
              f"using closest tested value ({closest}) instead.")
        matching = [r for r in rows if r["burst_length"] == closest]

    # Sort by depth ascending, find smallest depth meeting the target
    matching.sort(key=lambda r: r["depth"])

    for r in matching:
        if r["success_rate"] >= target_success_rate:
            return {
                "recommended_depth": r["depth"],
                "expected_success_rate": r["success_rate"],
                "burst_length_used": r["burst_length"],
                "decode_delay_bits": r["depth"] * 7,
            }

    # No tested depth met the target
    max_tested_depth = max(r["depth"] for r in matching)
    return {
        "recommended_depth": None,
        "max_tested_depth": max_tested_depth,
        "burst_length_used": matching[0]["burst_length"] if matching else avg_burst_length,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Recommend minimum interleaving depth for a target burst-error correction rate."
    )
    parser.add_argument(
        "--avg-burst-length", type=int, required=True,
        help="Expected/average burst error length of your channel, in bits"
    )
    parser.add_argument(
        "--target-success-rate", type=float, default=0.95,
        help="Desired correction success rate (0.0 to 1.0), default 0.95"
    )
    args = parser.parse_args()

    if not os.path.exists(CSV_PATH):
        print(f"ERROR: {CSV_PATH} not found. Run src/experiment.py first.")
        sys.exit(1)

    rows = load_results()

    print(f"Analyzing simulated results for burst length ~{args.avg_burst_length}, "
          f"target success rate {args.target_success_rate:.0%}...\n")

    result = recommend_depth(args.avg_burst_length, args.target_success_rate, rows)

    if result["recommended_depth"] is None:
        print(f"No tested interleaving depth (up to {result['max_tested_depth']}) "
              f"achieves {args.target_success_rate:.0%} success rate at burst length "
              f"{args.avg_burst_length}.")
        print(f"Recommendation: use a depth >= burst length "
              f"(theoretical requirement), i.e. try depth >= {args.avg_burst_length}, "
              f"or re-run experiment.py with larger DEPTHS values.")
    else:
        print(f"Recommended interleaving depth: {result['recommended_depth']}")
        print(f"Expected success rate at this depth: {result['expected_success_rate']:.1%}")
        print(f"Expected decode delay: {result['recommended_depth']} blocks "
              f"(~{result['decode_delay_bits']} bits buffered)")


if __name__ == "__main__":
    main()