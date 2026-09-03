"""
Block interleaver / de-interleaver.

Takes multiple Hamming(7,4) codewords (each 7 bits) and interleaves them
so that a burst error spread across consecutive TRANSMITTED bits ends up
touching only 1 bit in each of several codewords, instead of many bits
in a single codeword.

Matrix analogy:
  - Write `depth` codewords into a matrix, ROW by ROW (each row = 1 codeword)
  - Read the matrix OUT, COLUMN by COLUMN -- that's the transmitted bit order
  - De-interleaving reverses this: read the received bits back into the
    matrix column by column, then read rows back out to recover codewords
"""

from typing import List


def interleave(codewords: List[List[int]]) -> List[int]:
    """
    Interleave a list of codewords (each of equal length, e.g. 7 bits
    for Hamming(7,4)) into a single flat transmission order.

    Args:
        codewords: list of `depth` codewords, each a list of `n` bits
                   (all codewords must be the same length)

    Returns:
        Flat list of bits in interleaved (column-by-column) order,
        length = depth * n
    """
    if not codewords:
        return []

    depth = len(codewords)
    n = len(codewords[0])
    for cw in codewords:
        if len(cw) != n:
            raise ValueError("All codewords must be the same length to interleave")

    interleaved = []
    for col in range(n):
        for row in range(depth):
            interleaved.append(codewords[row][col])

    return interleaved


def deinterleave(bits: List[int], depth: int, block_size: int = 7) -> List[List[int]]:
    """
    Reverse the interleaving process: take the flat received bit stream
    and reconstruct the original `depth` codewords (each `block_size` bits).

    Args:
        bits: flat list of bits, length must equal depth * block_size
        depth: how many codewords were interleaved together
        block_size: length of each codeword (7 for Hamming(7,4))

    Returns:
        list of `depth` codewords, each `block_size` bits, in original order
    """
    expected_len = depth * block_size
    if len(bits) != expected_len:
        raise ValueError(
            f"Expected {expected_len} bits (depth={depth} x block_size={block_size}), "
            f"got {len(bits)}"
        )

    # Reconstruct: codewords[row][col] = bits[col * depth + row]
    codewords = [[0] * block_size for _ in range(depth)]
    idx = 0
    for col in range(block_size):
        for row in range(depth):
            codewords[row][col] = bits[idx]
            idx += 1

    return codewords


def theoretical_max_burst_length(depth: int) -> int:
    """
    The theoretical maximum burst length (in transmitted bits) that
    interleaving at a given depth can survive, assuming each individual
    Hamming(7,4) block can fix at most 1 bit error.

    With interleaving depth D, a burst of length D (in transmitted-bit
    order) spreads out to at most 1 bit per codeword -- which Hamming(7,4)
    can still fix. A burst of length D+1 guarantees at least one codeword
    receives 2 errors, which Hamming(7,4) cannot reliably fix.

    Returns:
        Maximum survivable burst length = depth
    """
    return depth