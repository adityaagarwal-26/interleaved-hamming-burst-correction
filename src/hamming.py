"""
Hamming(7,4) code implementation.

Encodes 4 data bits into a 7-bit codeword using 3 parity bits.
Can detect and correct any single-bit error within a 7-bit block.

Bit positions (1-indexed, as is standard for Hamming codes):
  1  2  3  4  5  6  7
  p1 p2 d1 p3 d2 d3 d4

  p1 covers positions 1,3,5,7
  p2 covers positions 2,3,6,7
  p3 covers positions 4,5,6,7
"""

from typing import List, Tuple


def encode(data_bits: List[int]) -> List[int]:
    """
    Encode 4 data bits into a 7-bit Hamming codeword.

    Args:
        data_bits: list of 4 bits (0/1), e.g. [1, 0, 1, 1]

    Returns:
        list of 7 bits (the codeword)
    """
    if len(data_bits) != 4:
        raise ValueError(f"Expected 4 data bits, got {len(data_bits)}")

    d1, d2, d3, d4 = data_bits

    # Compute parity bits using even parity
    p1 = d1 ^ d2 ^ d4
    p2 = d1 ^ d3 ^ d4
    p3 = d2 ^ d3 ^ d4

    # Assemble codeword in position order: p1 p2 d1 p3 d2 d3 d4
    codeword = [p1, p2, d1, p3, d2, d3, d4]
    return codeword


def decode(codeword: List[int]) -> Tuple[List[int], int]:
    """
    Decode a 7-bit Hamming codeword, correcting a single-bit error if present.

    Args:
        codeword: list of 7 bits (possibly with 1 bit flipped)

    Returns:
        (data_bits, error_position)
        data_bits: the recovered 4 data bits
        error_position: 0 if no error detected, else 1-7 indicating which
                         bit position was corrected (1-indexed).
    """
    if len(codeword) != 7:
        raise ValueError(f"Expected 7 bits, got {len(codeword)}")

    # Work on a mutable copy; convert to 1-indexed access via offset
    c = [None] + list(codeword)  # c[1..7] now valid

    # Recompute parity checks
    s1 = c[1] ^ c[3] ^ c[5] ^ c[7]
    s2 = c[2] ^ c[3] ^ c[6] ^ c[7]
    s3 = c[4] ^ c[5] ^ c[6] ^ c[7]

    syndrome = s1 + (s2 << 1) + (s3 << 2)  # value 0-7, gives error bit position

    if syndrome != 0:
        # Flip the erroneous bit (syndrome directly gives 1-indexed position)
        c[syndrome] ^= 1

    # Extract data bits from corrected codeword: positions 3,5,6,7 -> d1,d2,d3,d4
    data_bits = [c[3], c[5], c[6], c[7]]
    return data_bits, syndrome


def encode_bytes(data: bytes) -> List[int]:
    """
    Encode a bytes object into a flat list of Hamming-coded bits.
    Each byte (8 bits) is split into two 4-bit nibbles, each nibble
    is Hamming(7,4) encoded, producing 14 bits per input byte.
    """
    all_codeword_bits: List[int] = []
    for byte in data:
        high_nibble = [(byte >> 7) & 1, (byte >> 6) & 1, (byte >> 5) & 1, (byte >> 4) & 1]
        low_nibble = [(byte >> 3) & 1, (byte >> 2) & 1, (byte >> 1) & 1, byte & 1]
        all_codeword_bits.extend(encode(high_nibble))
        all_codeword_bits.extend(encode(low_nibble))
    return all_codeword_bits


def decode_bits(bits: List[int]) -> Tuple[bytes, int]:
    """
    Decode a flat list of Hamming-coded bits (length must be multiple of 14)
    back into bytes. Returns (recovered_bytes, num_blocks_corrected).

    Note: if 2+ bits flip in one 7-bit block, Hamming(7,4) will "correct"
    the wrong bit -- this will NOT be flagged as a failure here. Those
    blocks just decode WRONG. That's exactly the motivation for interleaving.
    """
    if len(bits) % 14 != 0:
        raise ValueError("Bit stream length must be a multiple of 14 (2 nibbles/byte)")

    recovered_bytes = bytearray()
    blocks_corrected = 0

    for i in range(0, len(bits), 14):
        high_codeword = bits[i:i + 7]
        low_codeword = bits[i + 7:i + 14]

        high_data, err1 = decode(high_codeword)
        low_data, err2 = decode(low_codeword)

        if err1 != 0:
            blocks_corrected += 1
        if err2 != 0:
            blocks_corrected += 1

        byte_val = 0
        for bit in high_data + low_data:
            byte_val = (byte_val << 1) | bit
        recovered_bytes.append(byte_val)

    return bytes(recovered_bytes), blocks_corrected