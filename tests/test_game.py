from app import game


def test_public_missions_hide_answers():
    for m in game.public_missions():
        assert "answer" not in m
    assert len(game.public_missions()) == len(game.MISSIONS)


def test_encode_mission_checks():
    correct, points = game.check("encode", "85738477")
    assert correct and points == 100
    assert game.check("encode", "12345678") == (False, 0)


def test_word_mission_ignores_case_and_spaces():
    assert game.check("decrypt", " c o d e ")[0] is True


def test_mandatory_mission_round_trips():
    cipher = game._cipher_str(game.MANDATORY)
    assert game.check("mission", cipher) == (True, 300)
    assert len(cipher.split()) == 6


def test_decrypt_helper_recovers_word():
    blocks = game.encrypt("CODE")
    assert game.decrypt(blocks) == "CODE"


def test_unknown_mission_raises():
    try:
        game.check("nope", "x")
        assert False
    except KeyError:
        pass
