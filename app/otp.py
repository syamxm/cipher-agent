"""One-time pad: XOR a message with random key bytes.

If the pad is truly random, secret, and never reused, XOR gives perfect secrecy.
Reusing any pad bytes breaks it, so each message must consume fresh bytes (see rooms.py).
"""

import secrets


def new_pad(size):
    """Random pad of `size` bytes from a cryptographically secure source."""
    return secrets.token_bytes(size)


def xor(data, pad):
    """XOR `data` with `pad`. Same function encrypts and decrypts."""
    if len(pad) < len(data):
        raise ValueError("pad slice shorter than data")
    return bytes(d ^ p for d, p in zip(data, pad))
