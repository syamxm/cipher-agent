# Cipher Agent

A small spy game for learning RSA, built for UiTM Cryptography Lab 6. The whole site is
a fake terminal in the browser: you type commands to encode, encrypt and crack messages,
or open a secure channel and chat with a partner.

Live at **https://cipher-agent.syamxm.com**.

## Modes

- **Solo training** — RSA missions with a score and levels. You encrypt and decrypt in
  blocks of 4 letters using the friend's public key `n = 1964556481, e = 456899`, where
  each letter is its ASCII code (`A=65 .. Z=90`). We aren't given `d`, so the game gets it
  at runtime by factoring `n` (it's small). See `app/rsa.py`.
- **Field channel (2-player)** — pair up in a room and chat over a one-time pad. Every
  message eats fresh pad bytes that are never reused.

## Commands

```
help              list commands
key               show public key n, e
missions          list missions + progress
mission <n>       show a mission
encode <letters>  letters -> number blocks
encrypt <input>   encrypt letters or blocks: m^e mod n
decrypt <nums>    decrypt: c^d mod n
submit <answer>   answer the current mission
score             show score
clear             clear the screen

connect           open a room, get a code
join <code>       join your partner's room
send <message>    encrypt with the pad and send
leave             leave the channel
```

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

## Deploy

The app runs as a container on the shared `proxy-net` network, behind an nginx reverse
proxy and a Cloudflare tunnel.

1. Build and start it:

   ```bash
   docker compose up -d --build
   ```

2. Copy the server block from [`deploy/nginx-x.conf.example`](deploy/nginx-x.conf.example)
   into your nginx config and reload. The `/ws` block carries the WebSocket upgrade
   headers the field channel needs.

3. Point `cipher-agent.syamxm.com` at the nginx proxy in your Cloudflare tunnel (DNS +
   ingress).

## Security note

This is a learning game, not a real secure messenger:

- The lab RSA key is tiny and factors in milliseconds. Good for learning, useless for
  real protection.
- A one-time pad is only safe if the pad is random, secret, and used once. Here the
  **server makes the pad and hands it to both players**, so the channel is safe against
  other players and someone just sniffing traffic, but **not against the server itself**.
- Pads and rooms live in memory and are gone on restart.
