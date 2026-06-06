from app import rsa

MANDATORY = "I AM AN UNDERCOVER SPY AT UITM"


def test_derive_d_matches_known_value():
    assert rsa.derive_d() == 1250832567


def test_uitm_known_vector():
    assert rsa.text_to_blocks("UITM") == [85738477]


def test_spaces_and_case_ignored():
    assert rsa.text_to_blocks("uitm") == rsa.text_to_blocks("U I T M")


def test_last_block_padded_with_x():
    # "SPY" -> S P Y X
    blocks = rsa.text_to_blocks("SPY")
    assert rsa.blocks_to_text(blocks) == "SPYX"


def test_block_roundtrip():
    blocks = rsa.text_to_blocks(MANDATORY)
    assert rsa.blocks_to_text(blocks) == "IAMANUNDERCOVERSPYATUITM"


def test_mandatory_message_encrypt_decrypt():
    d = rsa.derive_d()
    blocks = rsa.text_to_blocks(MANDATORY)
    cipher = rsa.encrypt(blocks)
    plain = rsa.decrypt(cipher, d)
    assert rsa.blocks_to_text(plain) == "IAMANUNDERCOVERSPYATUITM"


def test_all_blocks_below_modulus():
    blocks = rsa.text_to_blocks(MANDATORY)
    assert all(b < rsa.PUBLIC_N for b in blocks)
