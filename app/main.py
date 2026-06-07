from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app import game, rsa
from app.rooms import PadExhausted, RoomFull, RoomManager

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

app = FastAPI(title="Cipher Agent")
rooms = RoomManager()


@app.api_route("/health", methods=["GET", "HEAD"])
def health():
    return {"status": "ok"}


@app.get("/api/key")
def key():
    return {"n": rsa.PUBLIC_N, "e": rsa.PUBLIC_E}


@app.get("/api/missions")
def missions():
    return game.public_missions()


class CheckRequest(BaseModel):
    mission_id: str
    answer: str


@app.post("/api/check")
def check(req: CheckRequest):
    correct, points = game.check(req.mission_id, req.answer)
    return {"correct": correct, "points": points}


class RsaRequest(BaseModel):
    op: str
    text: str = ""


@app.post("/api/rsa")
def rsa_tool(req: RsaRequest):
    """RSA tool the player uses to solve missions."""
    if req.op == "encode":
        blocks = rsa.text_to_blocks(req.text)
        return {"result": blocks} if blocks else {"error": "no letters to encode"}
    if req.op == "encrypt":
        blocks = game.input_blocks(req.text)
        return {"result": rsa.encrypt(blocks)} if blocks else {"error": "give letters or number blocks"}
    if req.op == "decrypt":
        blocks = game._numbers(req.text)
        return {"result": game.decrypt(blocks)} if blocks else {"error": "give number blocks"}
    return {"error": "unknown op"}


@app.websocket("/ws")
async def ws(socket: WebSocket):
    """Relay one-time-pad messages between the two players in a room.

    First client message is {"action":"create"} or {"action":"join","code":...}. Once
    both are in, each side gets the shared pad. After that {"action":"msg","cipher":hex}
    messages are passed to the partner with the pad offset the server reserved.
    """
    await socket.accept()
    room = None
    index = None
    try:
        room, index = await _enter_room(socket)
        if room is None:
            return
        while True:
            data = await socket.receive_json()
            if data.get("action") != "msg":
                continue
            cipher = data["cipher"]
            length = len(bytes.fromhex(cipher))
            try:
                offset = room.allocate(index, length)
            except PadExhausted:
                await socket.send_json({"type": "error", "reason": "pad exhausted"})
                continue
            await socket.send_json({"type": "sent", "offset": offset})
            await _partner_of(room, index).send_json(
                {"type": "msg", "offset": offset, "cipher": cipher}
            )
    except WebSocketDisconnect:
        pass
    finally:
        if room is not None:
            await _on_leave(room, index)


async def _enter_room(socket):
    """Handle the create/join handshake. Returns (room, index) or (None, None)."""
    data = await socket.receive_json()
    action = data.get("action")

    if action == "create":
        room = rooms.create()
        index = room.add_member(socket)
        await socket.send_json({"type": "created", "code": room.code})
        return room, index

    if action == "join":
        try:
            room = rooms.get(data.get("code", ""))
            index = room.add_member(socket)
        except KeyError:
            await socket.send_json({"type": "error", "reason": "no such room"})
            return None, None
        except RoomFull:
            await socket.send_json({"type": "error", "reason": "room full"})
            return None, None
        await _send_ready(room)
        return room, index

    await socket.send_json({"type": "error", "reason": "expected create or join"})
    return None, None


async def _send_ready(room):
    """Both players are in: hand each the shared pad and their own half."""
    pad_hex = room.pad.hex()
    for i, member in enumerate(room.members):
        await member.send_json(
            {"type": "ready", "pad": pad_hex, "index": i, "half": room.half}
        )


def _partner_of(room, index):
    return room.members[1 - index]


async def _on_leave(room, index):
    partner = room.members[1 - index] if room.ready else None
    rooms.remove(room.code)
    if partner is not None:
        try:
            await partner.send_json({"type": "partner_left"})
        except RuntimeError:
            pass


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
