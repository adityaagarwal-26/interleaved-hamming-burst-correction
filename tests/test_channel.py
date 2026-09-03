"""
Unit tests for the Gilbert-Elliott channel model.
Run with: python tests/test_channel.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from channel import GilbertElliottChannel, inject_fixed_burst, measure_burst_lengths


def test_no_errors_when_probabilities_zero():
    """If both error probabilities are 0, no bits should ever flip."""
    channel = GilbertElliottChannel(p_error_in_good=0, p_error_in_bad=0, seed=42)
    original = [1, 0, 1, 1, 0, 0, 1, 0] * 10
    corrupted, states = channel.transmit(original)
    assert corrupted == original, "Expected no bit flips when error probs are 0"
    print("PASS: zero error probability produces no corruption")


def test_always_flips_when_probability_one():
    """If p_error_in_good = 1, every bit in GOOD state should flip."""
    channel = GilbertElliottChannel(
        p_good_to_bad=0,  # stay in GOOD forever
        p_error_in_good=1.0,
        seed=42,
    )
    original = [1, 0, 1, 1, 0, 0, 1, 0]
    corrupted, states = channel.transmit(original)
    expected = [b ^ 1 for b in original]
    assert corrupted == expected, "Expected every bit flipped"
    assert all(s == "GOOD" for s in states), "Expected channel to stay in GOOD state"
    print("PASS: p=1.0 error probability flips every bit")


def test_average_burst_length_roughly_matches_theory():
    """
    With p_bad_to_good = 0.3, average burst length should be roughly 1/0.3 ≈ 3.3.
    We run a long transmission and check it's in a sane ballpark (not exact,
    since it's probabilistic -- just a sanity check, not a strict equality).
    """
    channel = GilbertElliottChannel(
        p_good_to_bad=0.05,
        p_bad_to_good=0.3,
        p_error_in_good=0.0,
        p_error_in_bad=0.0,  # we only care about STATE bursts here, not bit flips
        seed=123,
    )
    dummy_bits = [0] * 5000
    _, states = channel.transmit(dummy_bits)
    bursts = measure_burst_lengths(states)

    assert len(bursts) > 10, "Expected multiple bursts over 5000 steps"
    avg_burst = sum(bursts) / len(bursts)
    expected_avg = 1 / 0.3  # ≈ 3.33

    print(f"INFO: measured {len(bursts)} bursts, avg length = {avg_burst:.2f} "
          f"(theoretical expectation ≈ {expected_avg:.2f})")

    # Loose sanity bound -- probabilistic, so allow decent margin
    assert 1.5 <= avg_burst <= 6.0, f"Average burst length {avg_burst:.2f} outside sane range"
    print("PASS: average burst length is in the expected ballpark")


def test_inject_fixed_burst():
    """inject_fixed_burst should flip EXACTLY the specified range, nothing else."""
    bits = [0] * 20
    corrupted = inject_fixed_burst(bits, burst_start=5, burst_length=4)

    for i in range(20):
        if 5 <= i < 9:
            assert corrupted[i] == 1, f"Expected bit {i} to be flipped"
        else:
            assert corrupted[i] == 0, f"Expected bit {i} to be untouched"

    print("PASS: inject_fixed_burst flips exactly the specified range")


def test_inject_fixed_burst_near_end():
    """Burst that would run past the end of the bit list should just truncate safely."""
    bits = [0] * 10
    corrupted = inject_fixed_burst(bits, burst_start=8, burst_length=5)
    assert len(corrupted) == 10, "Length should not change"
    assert corrupted[8] == 1 and corrupted[9] == 1, "Expected last 2 bits flipped"
    print("PASS: inject_fixed_burst handles overrun near end of list safely")


def test_reset():
    """After reset(), channel should be back in GOOD state."""
    channel = GilbertElliottChannel(p_good_to_bad=1.0, seed=1)  # forces flip to BAD fast
    channel.transmit_bit(0)  # this should push state to BAD
    assert channel.state == "BAD", "Expected state to have moved to BAD"
    channel.reset()
    assert channel.state == "GOOD", "Expected reset() to restore GOOD state"
    print("PASS: reset() restores GOOD state")


if __name__ == "__main__":
    test_no_errors_when_probabilities_zero()
    test_always_flips_when_probability_one()
    test_average_burst_length_roughly_matches_theory()
    test_inject_fixed_burst()
    test_inject_fixed_burst_near_end()
    test_reset()
    print("\nAll Gilbert-Elliott channel tests passed.")