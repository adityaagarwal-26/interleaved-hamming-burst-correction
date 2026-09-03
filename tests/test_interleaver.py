"""
Unit tests for the block interleaver.
Run with: python tests/test_interleaver.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from interleaver import interleave, deinterleave, theoretical_max_burst_length
from hamming import encode, decode


def test_interleave_deinterleave_roundtrip():
    """Interleaving then de-interleaving with NO corruption should return
    the exact original codewords."""
    codewords = [
        [1, 0, 1, 0, 1, 0, 1],
        [0, 1, 0, 1, 0, 1, 0],
        [1, 1, 1, 0, 0, 0, 1],
        [0, 0, 1, 1, 0, 1, 0],
    ]
    flat = interleave(codewords)
    assert len(flat) == 4 * 7, f"Expected 28 bits, got {len(flat)}"

    recovered = deinterleave(flat, depth=4, block_size=7)
    assert recovered == codewords, f"Roundtrip failed: {recovered} != {codewords}"
    print("PASS: interleave -> deinterleave roundtrip returns original codewords")


def test_interleave_order_is_column_by_column():
    """Manually check the interleaved order matches the expected pattern."""
    codewords = [
        ['a1', 'a2', 'a3'],
        ['b1', 'b2', 'b3'],
    ]
    flat = interleave(codewords)
    expected = ['a1', 'b1', 'a2', 'b2', 'a3', 'b3']
    assert flat == expected, f"Expected {expected}, got {flat}"
    print("PASS: interleaved bit order is correct (column-by-column)")


def test_burst_spread_across_blocks():
    """
    THE KEY TEST: inject a burst of consecutive TRANSMITTED bit errors,
    confirm it spreads to only 1 bit per codeword when depth >= burst length,
    and that each codeword can then self-correct via Hamming.
    """
    # 4 Hamming-encoded blocks (depth = 4)
    data_blocks = [[1, 0, 1, 1], [0, 1, 0, 0], [1, 1, 0, 1], [0, 0, 1, 0]]
    codewords = [encode(d) for d in data_blocks]

    # Interleave them
    transmitted = interleave(codewords)

    # Inject a burst of length 4 (= depth) starting at position 0
    corrupted = transmitted.copy()
    for i in range(4):
        corrupted[i] ^= 1

    # De-interleave back into codewords
    received_codewords = deinterleave(corrupted, depth=4, block_size=7)

    # Each codeword should have exactly 1 bit corrupted (since burst
    # length == depth, spread evenly), and Hamming should fix each one
    for i, (original_data, received_cw) in enumerate(zip(data_blocks, received_codewords)):
        decoded_data, syndrome = decode(received_cw)
        assert decoded_data == original_data, (
            f"Block {i}: expected {original_data}, got {decoded_data} -- "
            f"interleaving+Hamming failed to recover from burst"
        )
        assert syndrome != 0, f"Block {i}: expected a correction to have been applied"

    print("PASS: burst of length=depth is fully corrected after de-interleaving "
          "(1 bit error spread to each of 4 blocks, each self-corrected)")


def test_burst_exceeding_depth_breaks_some_blocks():
    """
    Sanity check the flip side: a burst LONGER than depth should overload
    at least one block with 2+ errors, which Hamming(7,4) cannot fix.
    This demonstrates the theoretical_max_burst_length boundary.
    """
    depth = 4
    data_blocks = [[1, 0, 1, 1], [0, 1, 0, 0], [1, 1, 0, 1], [0, 0, 1, 0]]
    codewords = [encode(d) for d in data_blocks]
    transmitted = interleave(codewords)

    # Burst length = depth + 1 = 5 -- one block will get 2 errors
    burst_length = depth + 1
    corrupted = transmitted.copy()
    for i in range(burst_length):
        corrupted[i] ^= 1

    received_codewords = deinterleave(corrupted, depth=depth, block_size=7)

    failures = 0
    for original_data, received_cw in zip(data_blocks, received_codewords):
        decoded_data, syndrome = decode(received_cw)
        if decoded_data != original_data:
            failures += 1

    assert failures > 0, (
        "Expected at least one block to fail when burst length exceeds depth, "
        "but all blocks recovered -- check test assumptions"
    )
    print(f"PASS: burst length ({burst_length}) > depth ({depth}) causes "
          f"{failures} block(s) to fail, as theory predicts")


def test_theoretical_max_burst_length():
    assert theoretical_max_burst_length(4) == 4
    assert theoretical_max_burst_length(8) == 8
    assert theoretical_max_burst_length(1) == 1
    print("PASS: theoretical_max_burst_length returns depth as expected")


if __name__ == "__main__":
    test_interleave_deinterleave_roundtrip()
    test_interleave_order_is_column_by_column()
    test_burst_spread_across_blocks()
    test_burst_exceeding_depth_breaks_some_blocks()
    test_theoretical_max_burst_length()
    print("\nAll interleaver tests passed.")