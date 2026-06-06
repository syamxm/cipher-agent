# Cipher Agent

A spy mini-game for learning **RSA public-key cryptography**, built for UiTM
Cryptography Lab 6. Play solo missions to encrypt and decrypt secret messages, or
go online and exchange messages with a partner over a one-time-pad channel.

Live at **https://x.syamxm.com**.

## Modes

- **Single-player** — RSA training missions with scoring and levels. Encrypt and
  decrypt messages in blocks of 4 letters using the friend's public key
  `n = 1964556481, e = 456899`, with ASCII letter codes (`A=65 .. Z=90`).
- **Two-player** — pair up in a room and chat through a one-time-pad secured channel.

## Run locally

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
# open http://localhost:8000
```

## Tests

```bash
pytest
```

## Status

Scaffold. Game modes added in following phases.
