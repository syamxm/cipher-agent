# Cipher Agent

A spy game for learning **RSA public-key cryptography**, built for UiTM Cryptography
Lab 6. The whole thing runs as a fake in-browser terminal: type commands to encode,
encrypt, and crack intercepts, or open a secure channel and message a partner.

Live at **https://cipher-agent.syamxm.com**.

## Modes

- **Solo training** — RSA missions with scoring and levels. Encrypt and decrypt in
  blocks of 4 letters using the friend's public key `n = 1964556481, e = 456899`, with
  ASCII letter codes (`A=65 .. Z=90`). The private exponent `d` is recovered at runtime
  by factoring `n` (it is small) — see `app/rsa.py`.
- **Field channel (2-player)** — pair up in a room and chat through a one-time-pad
  channel. Each message consumes fresh pad bytes that are never reused.

## Commands

```
help              list commands
key               show public key n, e
missions          list missions + progress
mission <n>       show a mission
encode <letters>  letters -> number blocks
encrypt <letters> encrypt: m^e mod n
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
proxy fronted by a Cloudflare tunnel.

1. Build and start the container:

   ```bash
   docker compose up -d --build
   ```

2. Add the nginx server block for `cipher-agent.syamxm.com` from
   [`deploy/nginx-x.conf.example`](deploy/nginx-x.conf.example) to your proxy config and
   reload nginx. The `/ws` location carries the WebSocket upgrade headers the field
   channel needs.

3. Map `cipher-agent.syamxm.com` in your Cloudflare tunnel (DNS + tunnel ingress) so it
   routes to the nginx proxy.

## Security note

This is a teaching game, not a secure messenger:

- The lab RSA key is tiny and factorable in milliseconds — fine for learning, useless
  for real protection.
- The one-time pad gives perfect secrecy only when the pad is random, secret, and used
  once. Here the **server generates and hands the pad to both players**, so the channel
  is secure against other players and passive eavesdroppers, but **not against the
  server**. Pads and rooms are in memory and disappear on restart.
