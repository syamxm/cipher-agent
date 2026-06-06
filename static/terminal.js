const term = document.getElementById("terminal");
const screen = document.getElementById("screen");
const input = document.getElementById("cmd");

const scrollDown = () => { term.scrollTop = term.scrollHeight; };

const state = {
  missions: [],
  current: 0,
  score: 0,
  channel: null, // { ws, pad, index, half, cursor, ready }
};

// ---- screen helpers ----

function print(text = "", cls = "") {
  const line = document.createElement("div");
  line.className = "line " + cls;
  line.textContent = text;
  screen.appendChild(line);
  scrollDown();
}

function echo(raw) {
  const line = document.createElement("div");
  line.className = "line cmd";
  line.innerHTML = `<span class="ps1"><span class="user">user@cipher-agent</span> <span class="arrow">-&gt;</span></span> `;
  line.appendChild(document.createTextNode(raw));
  screen.appendChild(line);
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function typeLine(text, cls = "", speed = 16) {
  const line = document.createElement("div");
  line.className = "line " + cls;
  screen.appendChild(line);
  for (const ch of text) {
    line.textContent += ch;
    scrollDown();
    await sleep(speed);
  }
}

// ---- api + crypto helpers ----

async function api(path, body) {
  const res = await fetch(path, body
    ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }
    : undefined);
  return res.json();
}

const toHex = (bytes) => Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");
const fromHex = (hex) => new Uint8Array(hex.match(/../g).map((h) => parseInt(h, 16)));

function xor(data, pad, offset) {
  const out = new Uint8Array(data.length);
  for (let i = 0; i < data.length; i++) out[i] = data[i] ^ pad[offset + i];
  return out;
}

// ---- solo commands ----

const enc = new TextEncoder();
const dec = new TextDecoder();

async function cmdKey() {
  const k = await api("/api/key");
  print(`public key   n = ${k.n}   e = ${k.e}`);
}

function cmdMissions() {
  state.missions.forEach((m, i) => {
    const mark = i < state.current ? "[x]" : i === state.current ? "[>]" : "[ ]";
    print(`${mark} ${i + 1}. L${m.level}  ${m.title}`);
  });
}

function showMission(i) {
  const m = state.missions[i];
  if (!m) return print("no such mission", "bad");
  print(`Mission ${i + 1} — ${m.title}`, "accent");
  print(m.brief, "muted");
  print(m.task);
  print(`given: ${m.given}`);
  print(`hint:  ${m.hint}`, "muted");
}

async function cmdRsa(op, text) {
  if (!text) return print(`usage: ${op} <input>`, "bad");
  const out = await api("/api/rsa", { op, text });
  print(Array.isArray(out.result) ? out.result.join(" ") : out.result, "accent");
}

async function cmdSubmit(answer) {
  const m = state.missions[state.current];
  if (!m) return print("all missions complete, agent.", "accent");
  if (!answer) return print("usage: submit <answer>", "bad");
  const res = await api("/api/check", { mission_id: m.id, answer });
  if (!res.correct) return print("rejected. the enemy is listening — try again.", "bad");
  state.score += res.points;
  print(`accepted. +${res.points}  (score ${state.score})`, "accent");
  state.current += 1;
  if (state.current < state.missions.length) {
    print(`next: mission ${state.current + 1}. type "mission ${state.current + 1}".`, "muted");
  } else {
    print("all missions complete. the truth is delivered.", "accent");
  }
}

// ---- field channel (two-player OTP) ----

function openChannel(action, code) {
  if (state.channel) return print("already in a channel. type 'leave' first.", "bad");
  const proto = location.protocol === "https:" ? "wss" : "ws";
  const ws = new WebSocket(`${proto}://${location.host}/ws`);
  state.channel = { ws, pad: null, index: null, half: 0, cursor: 0, ready: false };

  ws.onopen = () => ws.send(JSON.stringify(action === "create" ? { action: "create" } : { action: "join", code }));
  ws.onmessage = (ev) => handleChannel(JSON.parse(ev.data));
  ws.onclose = () => { if (state.channel) { print("channel closed.", "muted"); state.channel = null; } };
}

function handleChannel(msg) {
  const ch = state.channel;
  if (msg.type === "created") {
    print(`room open. share this code with your partner: ${msg.code}`, "accent");
  } else if (msg.type === "ready") {
    ch.pad = fromHex(msg.pad);
    ch.index = msg.index;
    ch.half = msg.half;
    ch.cursor = 0;
    ch.ready = true;
    print("secure channel up. one-time pad shared. type 'send <message>'.", "accent");
  } else if (msg.type === "sent") {
    // server confirmed our pad offset; local echo already printed
  } else if (msg.type === "msg") {
    const cipher = fromHex(msg.cipher);
    const text = dec.decode(xor(cipher, ch.pad, msg.offset));
    print(`partner ▸ ${text}`, "partner");
    print(`          otp ${msg.cipher} @${msg.offset}`, "muted");
  } else if (msg.type === "partner_left") {
    print("partner left the channel.", "muted");
  } else if (msg.type === "error") {
    print(`channel error: ${msg.reason}`, "bad");
  }
}

function cmdSend(text) {
  const ch = state.channel;
  if (!ch || !ch.ready) return print("no secure channel. use 'connect' or 'join <code>'.", "bad");
  if (!text) return print("usage: send <message>", "bad");
  const data = enc.encode(text);
  const offset = ch.index * ch.half + ch.cursor;
  const cipher = xor(data, ch.pad, offset);
  ch.cursor += data.length;
  ch.ws.send(JSON.stringify({ action: "msg", cipher: toHex(cipher) }));
  print(`you ▸ ${text}`, "you");
  print(`      otp ${toHex(cipher)} @${offset}`, "muted");
}

function cmdLeave() {
  if (!state.channel) return print("not in a channel.", "muted");
  state.channel.ws.close();
  state.channel = null;
}

// ---- dispatch ----

const HELP = `SOLO
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

FIELD CHANNEL (2-player, one-time pad)
  connect           open a room, get a code
  join <code>       join your partner's room
  send <message>    encrypt with the pad and send
  leave             leave the channel`;

async function run(raw) {
  const line = raw.trim();
  if (!line) return;
  const [cmd, ...rest] = line.split(/\s+/);
  const arg = line.slice(cmd.length).trim();

  switch (cmd) {
    case "help": print(HELP); break;
    case "key": await cmdKey(); break;
    case "missions": cmdMissions(); break;
    case "mission": showMission(parseInt(arg, 10) - 1); break;
    case "encode": await cmdRsa("encode", arg); break;
    case "encrypt": await cmdRsa("encrypt", arg); break;
    case "decrypt": await cmdRsa("decrypt", arg); break;
    case "submit": await cmdSubmit(arg); break;
    case "score": print(`score ${state.score}`); break;
    case "clear": screen.replaceChildren(); break;
    case "connect": openChannel("create"); break;
    case "join": arg ? openChannel("join", arg) : print("usage: join <code>", "bad"); break;
    case "send": cmdSend(arg); break;
    case "leave": cmdLeave(); break;
    default: print(`command not found: ${cmd}`, "bad");
  }
}

input.addEventListener("keydown", (e) => {
  if (e.key !== "Enter") return;
  const raw = input.value;
  input.value = "";
  echo(raw);
  run(raw);
});

document.addEventListener("click", () => input.focus());

async function boot() {
  input.disabled = true;
  await typeLine("CIPHER AGENT // secure terminal", "accent");
  await typeLine("RSA field operations. type 'help' to begin.", "muted");
  print("");
  state.missions = await api("/api/missions");
  input.disabled = false;
  input.focus();
}

boot();
