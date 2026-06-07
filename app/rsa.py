"""RSA on blocks of 4 letters using ASCII codes (A=65..Z=90).

Public key is from the lab. We aren't given d, so we just factor n (it's small) to get it.
"""

PUBLIC_N = 1964556481
PUBLIC_E = 456899

BLOCK_LETTERS = 4          # letters per block
PAD_LETTER = "X"           # used to fill the last block
CODE_DIGITS = 2            # each ASCII code 65..90 is exactly 2 digits


def modexp(base, exp, mod):
    """(base ** exp) % mod by square-and-multiply, so the numbers stay small."""
    result = 1
    base %= mod
    while exp > 0:
        if exp & 1:
            result = (result * base) % mod
        base = (base * base) % mod
        exp >>= 1
    return result


def derive_d(n=PUBLIC_N, e=PUBLIC_E):
    """Get the private key d. Factor n into p*q, then d = e^-1 mod phi."""
    p = _smallest_factor(n)
    q = n // p
    phi = (p - 1) * (q - 1)
    return pow(e, -1, phi)


def _smallest_factor(n):
    i = 2
    while i * i <= n:
        if n % i == 0:
            return i
        i += 1
    raise ValueError(f"{n} is prime; not a valid RSA modulus")


def text_to_blocks(text):
    """Text -> integer blocks. Keep A-Z, pad last group with X, join 2-digit ASCII codes.

    e.g. UITM -> 85 73 84 77 -> 85738477.
    """
    letters = [c for c in text.upper() if "A" <= c <= "Z"]
    while len(letters) % BLOCK_LETTERS != 0:
        letters.append(PAD_LETTER)

    blocks = []
    for i in range(0, len(letters), BLOCK_LETTERS):
        group = letters[i:i + BLOCK_LETTERS]
        block = 0
        for c in group:
            block = block * (10 ** CODE_DIGITS) + ord(c)
        blocks.append(block)
    return blocks


def blocks_to_text(blocks):
    """Reverse of text_to_blocks: integer blocks back into letters."""
    digits = CODE_DIGITS * BLOCK_LETTERS  # 8 digits per block
    chars = []
    for block in blocks:
        s = str(block).zfill(digits)      # pad back to 8 in case a leading digit was dropped
        for i in range(0, digits, CODE_DIGITS):
            chars.append(chr(int(s[i:i + CODE_DIGITS])))
    return "".join(chars)


def encrypt(blocks, e=PUBLIC_E, n=PUBLIC_N):
    """Encrypt each block: c = m^e mod n."""
    return [modexp(m, e, n) for m in blocks]


def decrypt(blocks, d, n=PUBLIC_N):
    """Decrypt each block: m = c^d mod n."""
    return [modexp(c, d, n) for c in blocks]
