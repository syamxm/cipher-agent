"""In-memory two-player rooms, each with one shared one-time pad.

State is lost on restart, which is fine for a game. The pad is split in half, one half
per player, and each half is used strictly front-to-back. So no byte is ever reused and
the one-time-pad rule holds.
"""

import secrets
import string

from app.otp import new_pad

PAD_SIZE = 4096
CODE_LENGTH = 6
CODE_ALPHABET = string.ascii_uppercase + string.digits
MAX_MEMBERS = 2


class PadExhausted(Exception):
    pass


class RoomFull(Exception):
    pass


class Room:
    def __init__(self, code):
        self.code = code
        self.pad = new_pad(PAD_SIZE)
        self.members = []          # connection handles, index 0 and 1 = the two players
        self.used = [0, 0]         # bytes consumed in each player's half

    @property
    def half(self):
        return len(self.pad) // 2

    @property
    def ready(self):
        return len(self.members) == MAX_MEMBERS

    def add_member(self, handle):
        if len(self.members) >= MAX_MEMBERS:
            raise RoomFull()
        self.members.append(handle)
        return len(self.members) - 1   # the player's index

    def allocate(self, index, length):
        """Reserve `length` fresh pad bytes for player `index`, return the offset.

        Only moves forward inside that player's half, so ranges never overlap.
        """
        if self.used[index] + length > self.half:
            raise PadExhausted()
        offset = index * self.half + self.used[index]
        self.used[index] += length
        return offset


class RoomManager:
    def __init__(self):
        self.rooms = {}

    def create(self):
        code = self._new_code()
        room = Room(code)
        self.rooms[code] = room
        return room

    def get(self, code):
        room = self.rooms.get(code)
        if room is None:
            raise KeyError(code)
        return room

    def remove(self, code):
        self.rooms.pop(code, None)

    def _new_code(self):
        while True:
            code = "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))
            if code not in self.rooms:
                return code
