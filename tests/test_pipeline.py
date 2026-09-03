"""
Unit tests for the full pipeline (Hamming + interleaving + burst injection).
Run with: python tests/test_pipeline.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from pipeline import run_single_trial, run_single_trial_no_interleaving, run_trials


def test_no_burst_always_succeeds():
    """With burst_length=0, nothing should ever fail regardless of depth."""
    for depth in [1, 2, 4, 8]:
        result = run_single_trial(depth=depth, burst_length=0, seed=1)
        assert result["success"] is True, f"Expected success with no burst at depth {depth}"
    print("PASS: burst_length=0 always succeeds")


def test_burst_at_depth_succeeds():
    """Burst length == depth should (by design) fully recover, burst_start=0."""
    for depth in [2, 4, 8, 16]:
        result = run_single_trial(depth=depth, burst_length=depth, burst_start=0, seed=1)
        assert result["success"] is True, (
            f"Expected success when burst_length == depth ({depth}), got {result}"
        )
    print("PASS: burst_length == depth succeeds at multiple depths")


def test_burst_exceeding_depth_can_fail():
    """Burst length > depth should cause failures (at least sometimes)."""
    depth = 4
    result = run_single_trial(depth=depth, burst_length=depth + 1, burst_start=0, seed=1)
    assert result["success"] is False, (
        f"Expected failure when burst_length > depth, got {result}"
    )
    assert result["blocks_failed"] > 0
    print(f"PASS: burst_length > depth causes failure (blocks_failed={result['blocks_failed']})")


def test_no_interleaving_worse_than_interleaving():
    """
    Sanity check the whole point of the project: at the same burst length,
    no interleaving (depth=1) should fail more often than interleaving
    (depth >= burst_length).
    """
    burst_length = 4

    # No interleaving: burst of length 4 hits a single 7-bit block directly
    no_il_result = run_single_trial_no_interleaving(burst_length=burst_length, burst_start=0, seed=1)

    # With interleaving at depth=4: burst spreads to 1 bit per block
    il_result = run_single_trial(depth=4, burst_length=burst_length, burst_start=0, seed=1)

    assert no_il_result["success"] is False, "Expected no-interleaving to fail with burst=4"
    assert il_result["success"] is True, "Expected interleaving depth=4 to succeed with burst=4"
    print("PASS: interleaving succeeds where no-interleaving fails, same burst length")


def test_run_trials_success_rate_sane():
    """
    Run many trials at a setting we know should mostly succeed
    (burst_length well below depth) and confirm success rate is high.
    """
    result = run_trials(depth=8, burst_length=2, num_trials=200, base_seed=0)
    assert result["success_rate"] > 0.9, (
        f"Expected high success rate for burst << depth, got {result['success_rate']}"
    )
    print(f"PASS: run_trials gives high success rate ({result['success_rate']:.2%}) "
          f"for burst_length=2, depth=8")


def test_run_trials_low_success_when_no_interleaving_and_big_burst():
    """Opposite case: depth=1, large burst -> should mostly fail."""
    result = run_trials(depth=1, burst_length=5, num_trials=200, base_seed=0)
    assert result["success_rate"] < 0.3, (
        f"Expected low success rate for depth=1, burst=5, got {result['success_rate']}"
    )
    print(f"PASS: run_trials gives low success rate ({result['success_rate']:.2%}) "
          f"for depth=1, burst_length=5")


if __name__ == "__main__":
    test_no_burst_always_succeeds()
    test_burst_at_depth_succeeds()
    test_burst_exceeding_depth_can_fail()
    test_no_interleaving_worse_than_interleaving()
    test_run_trials_success_rate_sane()
    test_run_trials_low_success_when_no_interleaving_and_big_burst()
    print("\nAll pipeline tests passed.")