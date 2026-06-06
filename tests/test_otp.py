import pytest
from fastapi.testclient import TestClient

from app import otp
from app.main import app
from app.rooms import PadExhausted, Room, RoomFull, RoomManager


def test_xor_roundtrip():
    pad = otp.new_pad(16)
    msg = b"secret"
    cipher = otp.xor(msg, pad)
    assert cipher != msg
    assert otp.xor(cipher, pad) == msg


def test_xor_rejects_short_pad():
    with pytest.raises(ValueError):
        otp.xor(b"toolong", b"key")


def test_allocate_never_overlaps():
    room = Room("TEST01")
    half = room.half
    a1 = room.allocate(0, 10)
    a2 = room.allocate(0, 5)
    b1 = room.allocate(1, 8)
    assert a1 == 0
    assert a2 == 10                 # forward only, no reuse
    assert b1 == half               # other player draws from the second half
    assert a2 + 5 <= half           # players never share bytes


def test_allocate_raises_when_half_exhausted():
    room = Room("TEST02")
    room.allocate(0, room.half)
    with pytest.raises(PadExhausted):
        room.allocate(0, 1)


def test_room_full_after_two_members():
    room = Room("TEST03")
    room.add_member("a")
    room.add_member("b")
    with pytest.raises(RoomFull):
        room.add_member("c")


def test_manager_get_missing_raises():
    manager = RoomManager()
    with pytest.raises(KeyError):
        manager.get("NOPE00")


def test_two_players_exchange_message():
    client = TestClient(app)
    with client.websocket_connect("/ws") as a, client.websocket_connect("/ws") as b:
        a.send_json({"action": "create"})
        code = a.receive_json()["code"]

        b.send_json({"action": "join", "code": code})
        ready_a = a.receive_json()
        ready_b = b.receive_json()
        assert ready_a["pad"] == ready_b["pad"]

        pad = bytes.fromhex(ready_a["pad"])
        plaintext = b"MEET AT NOON"
        offset = ready_a["index"] * ready_a["half"]
        cipher = otp.xor(plaintext, pad[offset:offset + len(plaintext)])

        a.send_json({"action": "msg", "cipher": cipher.hex()})
        assert a.receive_json() == {"type": "sent", "offset": offset}

        msg = b.receive_json()
        assert msg["type"] == "msg"
        recovered = otp.xor(
            bytes.fromhex(msg["cipher"]),
            pad[msg["offset"]:msg["offset"] + len(plaintext)],
        )
        assert recovered == plaintext
