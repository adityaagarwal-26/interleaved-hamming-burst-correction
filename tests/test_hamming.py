"""
Unit tests for Hamming(7,4) encode/decode.
Run with: python tests/test_hamming.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from hamming import encode, decode, encode_bytes, decode_bits


def test_encode_length():
    codeword = encode([1, 0, 1, 1])
    assert len(codeword) == 7, f"Expected 7 bits, got {len(codeword)}"
    print("PASS: encode produces 7 bits")


def test_no_error_roundtrip():
    test_cases = [
        [0, 0, 0, 0],
        [1, 1, 1, 1],
        [1, 0, 1, 1],
        [0, 1, 0, 1],
        [1, 0, 0, 0],
    ]
    for data in test_cases:
        codeword = encode(data)
        decoded, syndrome = decode(codeword)
        assert decoded == data, f"Failed roundtrip for {data}: got {decoded}"
        assert syndrome == 0, f"Expected no error, got syndrome {syndrome}"
    print("PASS: no-error roundtrip works for all test cases")


def test_single_bit_correction():
    data = [1, 0, 1, 1]
    codeword = encode(data)

    for flip_pos in range(7):
        corrupted = codeword.copy()
        corrupted[flip_pos] ^= 1

        decoded, syndrome = decode(corrupted)
        assert decoded == data, (
            f"Failed to correct bit flip at position {flip_pos}: "
            f"original={data}, decoded={decoded}"
        )
        assert syndrome != 0, "Expected syndrome to indicate an error"

    print("PASS: single-bit error correction works for all 7 positions")


def test_double_bit_error_fails_as_expected():
    """
    Sanity check: Hamming(7,4) CANNOT reliably fix 2-bit errors.
    This documents the known limitation -- it's the whole motivation
    for interleaving later.
    """
    data = [1, 0, 1, 1]
    codeword = encode(data)
    corrupted = codeword.copy()
    corrupted[0] ^= 1
    corrupted[1] ^= 1

    decoded, syndrome = decode(corrupted)
    status = "matched original (lucky)" if decoded == data else "WRONG (expected for 2-bit error)"
    print(f"INFO: 2-bit error decode result: {status} (decoded={decoded}, original={data})")


def test_encode_decode_bytes():
    original = b"HI"
    bits = encode_bytes(original)
    assert len(bits) == len(original) * 14, "Expected 14 bits per input byte"

    recovered, corrections = decode_bits(bits)
    assert recovered == original, f"Expected {original}, got {recovered}"
    assert corrections == 0, "Expected no corrections needed on clean channel"
    print(f"PASS: byte-level roundtrip works, '{original.decode()}' -> {len(bits)} bits -> '{recovered.decode()}'")


def test_encode_decode_bytes_with_single_errors():
    original = b"HELLO"
    bits = encode_bytes(original)

    corrupted = bits.copy()
    for block_start in range(0, len(corrupted), 7):
        corrupted[block_start] ^= 1

    recovered, corrections = decode_bits(corrupted)
    assert recovered == original, f"Expected {original}, got {recovered}"
    expected_corrections = len(bits) // 7
    assert corrections == expected_corrections, (
        f"Expected {expected_corrections} corrections, got {corrections}"
    )
    print(f"PASS: recovered '{original.decode()}' correctly with 1 bit error per block "
          f"({corrections} blocks corrected)")


if __name__ == "__main__":
    test_encode_length()
    test_no_error_roundtrip()
    test_single_bit_correction()
    test_double_bit_error_fails_as_expected()
    test_encode_decode_bytes()
    test_encode_decode_bytes_with_single_errors()
    print("\nAll Hamming(7,4) tests passed.")