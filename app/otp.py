"""One-time pad: XOR the message with random key bytes.

Secure only if the pad is random, secret, and never reused. So each message has to use
fresh bytes (rooms.py handles that).
"""

import secrets


def new_pad(size):
    """Random pad of `size` bytes from a secure source."""
    return secrets.token_bytes(size)


def xor(data, pad):
    """XOR data with pad. Same function for encrypt and decrypt."""
    if len(pad) < len(data):
        raise ValueError("pad slice shorter than data")
    return bytes(d ^ p for d, p in zip(data, pad))
