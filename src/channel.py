"""
Gilbert-Elliott channel model.

A 2-state Markov chain that simulates a bursty communication channel:
- Good state: low bit-error probability (clean channel)
- Bad state: high bit-error probability (noisy channel, causes bursts)

The channel transitions between states based on fixed probabilities,
so when it lands in the Bad state and stays there for a few steps,
you get a burst of consecutive bit errors -- much more realistic
than flipping bits independently at random.
"""

import random
from typing import List, Tuple


class GilbertElliottChannel:
    def __init__(
        self,
        p_good_to_bad: float = 0.02,
        p_bad_to_good: float = 0.3,
        p_error_in_good: float = 0.001,
        p_error_in_bad: float = 0.5,
        seed: int = None,
    ):
        """
        Args:
            p_good_to_bad: probability of transitioning Good -> Bad each step
            p_bad_to_good: probability of transitioning Bad -> Good each step
                           (smaller value = longer average bursts, since
                           avg burst length ~= 1 / p_bad_to_good)
            p_error_in_good: bit-error probability while in Good state
            p_error_in_bad: bit-error probability while in Bad state
            seed: optional random seed for reproducible experiments
        """
        self.p_good_to_bad = p_good_to_bad
        self.p_bad_to_good = p_bad_to_good
        self.p_error_in_good = p_error_in_good
        self.p_error_in_bad = p_error_in_bad
        self.state = "GOOD"  # start clean
        self.rng = random.Random(seed)

    def _step_state(self):
        """Possibly transition to the other state based on current state."""
        if self.state == "GOOD":
            if self.rng.random() < self.p_good_to_bad:
                self.state = "BAD"
        else:  # BAD
            if self.rng.random() < self.p_bad_to_good:
                self.state = "GOOD"

    def transmit_bit(self, bit: int) -> Tuple[int, str]:
        """
        Pass a single bit through the channel. May flip it, based on
        the current state's error probability. Returns (possibly_flipped_bit,
        state_used).
        """
        error_prob = self.p_error_in_good if self.state == "GOOD" else self.p_error_in_bad
        state_used = self.state

        if self.rng.random() < error_prob:
            bit = bit ^ 1  # flip

        self._step_state()  # move to next state for the following bit
        return bit, state_used

    def transmit(self, bits: List[int]) -> Tuple[List[int], List[str]]:
        """
        Pass a full list of bits through the channel.

        Returns:
            (corrupted_bits, states) -- states[i] tells you which state
            the channel was in when bit i was transmitted, useful for
            debugging/visualizing where bursts happened.
        """
        corrupted = []
        states = []
        for bit in bits:
            out_bit, state = self.transmit_bit(bit)
            corrupted.append(out_bit)
            states.append(state)
        return corrupted, states

    def reset(self):
        """Reset channel to Good state (call between independent trials)."""
        self.state = "GOOD"


def inject_fixed_burst(bits: List[int], burst_start: int, burst_length: int) -> List[int]:
    """
    Utility for controlled experiments: instead of using the probabilistic
    Gilbert-Elliott model, flip a FIXED, exact-length run of consecutive
    bits starting at burst_start. Used in the depth-sweep experiments
    where we want to test "exactly a burst of length N" rather than a
    random one, to get clean, reproducible curves.
    """
    corrupted = bits.copy()
    for i in range(burst_start, min(burst_start + burst_length, len(bits))):
        corrupted[i] ^= 1
    return corrupted


def measure_burst_lengths(states: List[str]) -> List[int]:
    """
    Given a list of per-bit states (output of transmit()), measure the
    lengths of consecutive BAD runs (bursts). Useful for verifying the
    channel produces the average burst length you expect from your
    chosen p_bad_to_good.
    """
    burst_lengths = []
    current_burst = 0

    for state in states:
        if state == "BAD":
            current_burst += 1
        else:
            if current_burst > 0:
                burst_lengths.append(current_burst)
                current_burst = 0

    if current_burst > 0:
        burst_lengths.append(current_burst)

    return burst_lengths