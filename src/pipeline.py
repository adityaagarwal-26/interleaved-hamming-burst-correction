"""
Full pipeline: combines Hamming(7,4), block interleaving, and burst-error
injection into a single simulate-one-trial function.

Flow:
  random data bits
    -> split into 4-bit chunks, Hamming-encode each (7 bits each)
    -> interleave `depth` codewords together
    -> inject a fixed-length burst error (or use Gilbert-Elliott channel)
    -> de-interleave back into codewords
    -> Hamming-decode each codeword
    -> compare recovered data to original
"""

import random
from typing import List, Dict
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from hamming import encode, decode
from interleaver import interleave, deinterleave
from channel import inject_fixed_burst


def run_single_trial(depth: int, burst_length: int, burst_start: int = 0, seed: int = None) -> Dict:
    """
    Run one trial: generate `depth` random 4-bit data blocks, encode with
    Hamming(7,4), interleave at the given depth, inject a fixed burst error
    of the given length, de-interleave, decode, and check correctness.

    Args:
        depth: interleaving depth (number of codewords woven together)
        burst_length: length of the burst error to inject (in transmitted bits)
        burst_start: where in the transmitted stream the burst starts
        seed: random seed for reproducible data generation

    Returns:
        dict with keys:
            'success': True if ALL blocks decoded correctly, False otherwise
            'blocks_failed': how many of the `depth` blocks decoded wrong
            'depth': depth used
            'burst_length': burst length used
    """
    rng = random.Random(seed)

    # Generate `depth` random 4-bit data blocks
    original_data_blocks = [
        [rng.randint(0, 1) for _ in range(4)] for _ in range(depth)
    ]

    # Hamming-encode each block
    codewords = [encode(block) for block in original_data_blocks]

    # Interleave
    transmitted = interleave(codewords)

    # Inject burst error
    corrupted = inject_fixed_burst(transmitted, burst_start=burst_start, burst_length=burst_length)

    # De-interleave back into codewords
    received_codewords = deinterleave(corrupted, depth=depth, block_size=7)

    # Decode each and check correctness
    blocks_failed = 0
    for original_block, received_cw in zip(original_data_blocks, received_codewords):
        decoded_block, syndrome = decode(received_cw)
        if decoded_block != original_block:
            blocks_failed += 1

    return {
        "success": blocks_failed == 0,
        "blocks_failed": blocks_failed,
        "depth": depth,
        "burst_length": burst_length,
    }


def run_single_trial_no_interleaving(burst_length: int, burst_start: int = 0, seed: int = None) -> Dict:
    """
    Baseline comparison: same as run_single_trial but with depth=1
    (i.e. NO interleaving at all -- burst hits a single codeword directly).
    This is your "before" case to compare interleaving against.
    """
    return run_single_trial(depth=1, burst_length=burst_length, burst_start=burst_start, seed=seed)


def run_trials(depth: int, burst_length: int, num_trials: int = 1000, base_seed: int = 0) -> Dict:
    """
    Run many trials for a given (depth, burst_length) pair and compute
    the aggregate success rate.

    Returns:
        dict with 'success_rate', 'depth', 'burst_length', 'num_trials'
    """
    successes = 0
    for trial_num in range(num_trials):
        # Vary burst_start each trial so it's not always hitting the same
        # position relative to block boundaries -- more realistic average
        rng = random.Random(base_seed + trial_num)
        max_start = max(0, depth * 7 - burst_length)
        burst_start = rng.randint(0, max_start) if max_start > 0 else 0

        result = run_single_trial(
            depth=depth,
            burst_length=burst_length,
            burst_start=burst_start,
            seed=base_seed + trial_num,
        )
        if result["success"]:
            successes += 1

    return {
        "depth": depth,
        "burst_length": burst_length,
        "num_trials": num_trials,
        "success_rate": successes / num_trials,
    }