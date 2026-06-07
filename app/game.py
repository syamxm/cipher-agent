"""Single-player missions: encode, encrypt and decrypt with RSA.

Each mission's answer is computed from the real RSA functions. The player works it out
with the in-game tools (/api/rsa) and submits.
"""

import re

from app import rsa

MANDATORY = "I AM AN UNDERCOVER SPY AT UITM"
_D = rsa.derive_d()


def encode(text):
    return rsa.text_to_blocks(text)


def encrypt(text):
    return rsa.encrypt(rsa.text_to_blocks(text))


def input_blocks(text):
    """Letters get encoded first, plain numbers are used as-is.

    So both `encrypt hello` and `encrypt 72697676 79888888` work.
    """
    if any(c.isalpha() for c in text):
        return rsa.text_to_blocks(text)
    return _numbers(text)


def decrypt(blocks):
    return rsa.blocks_to_text(rsa.decrypt(blocks, _D))


def _cipher_str(text):
    return " ".join(str(c) for c in encrypt(text))


MISSIONS = [
    {
        "id": "encode",
        "level": 1,
        "title": "Tag the Letters",
        "brief": "Every letter is its ASCII code. Four letters join into one block.",
        "task": "Encode the codename UITM into a single number block.",
        "given": "UITM",
        "hint": "U=85, I=73, T=84, M=77 — joined into one number.",
        "kind": "number",
        "points": 100,
        "answer": "85738477",
    },
    {
        "id": "encrypt",
        "level": 2,
        "title": "Lock the Block",
        "brief": "Encrypt with the public key: c = m^e mod n.",
        "task": "Encrypt the codename UITM and give the cipher number.",
        "given": "UITM",
        "hint": "Encode it, then run the Encrypt tool.",
        "kind": "number",
        "points": 150,
        "answer": str(encrypt("UITM")[0]),
    },
    {
        "id": "decrypt",
        "level": 3,
        "title": "Crack the Intercept",
        "brief": "An enemy block was intercepted. Decrypt it: m = c^d mod n.",
        "task": "Decrypt the intercepted block back into letters.",
        "given": str(encrypt("CODE")[0]),
        "hint": "Run the Decrypt tool, then read the four letters.",
        "kind": "word",
        "points": 200,
        "answer": "CODE",
    },
    {
        "id": "mission",
        "level": 4,
        "title": "Send the Secret",
        "brief": "The core mission: get the full report to your partner, encrypted.",
        "task": "Encrypt the whole message and give every cipher block in order.",
        "given": MANDATORY,
        "hint": "Spaces are removed first. 24 letters = 6 blocks.",
        "kind": "number",
        "points": 300,
        "answer": _cipher_str(MANDATORY),
    },
]

_BY_ID = {m["id"]: m for m in MISSIONS}


def public_missions():
    """Missions without their answers, for the client."""
    return [{k: v for k, v in m.items() if k != "answer"} for m in MISSIONS]


def check(mission_id, answer):
    """Validate a submitted answer. Returns (correct, points_awarded)."""
    mission = _BY_ID.get(mission_id)
    if mission is None:
        raise KeyError(mission_id)
    correct = _matches(mission["kind"], answer, mission["answer"])
    return correct, mission["points"] if correct else 0


def _matches(kind, submitted, expected):
    if kind == "word":
        return _letters(submitted) == _letters(expected)
    return _numbers(submitted) == _numbers(expected)


def _letters(s):
    return "".join(c for c in s.upper() if c.isalpha())


def _numbers(s):
    return [int(x) for x in re.split(r"[^0-9]+", s) if x]
