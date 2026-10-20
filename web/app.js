// Touchline web client: renders the live synthetic feed and the agents' overlay cues.
const $ = (id) => document.getElementById(id);
const PITCH = { L: 105, W: 68 };

const store = {
  get(k, d) { try { const v = localStorage.getItem(k); return v ? JSON.parse(v) : d; } catch { return d; } },
  set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch { /* private mode */ } },
};

const params = new URLSearchParams(location.search);
const state = {
  ws: null,
  meta: null,
  players: {},
  colors: { home: "#1f6feb", away: "#e5484d" },
  profile: Object.assign({ mode: "fan", language: "en", favourite_side: null, focus_player_id: null, metric: null }, store.get("tl.profile", {})),
  speed: Number(params.get("speed")) || store.get("tl.speed", 8),
  paused: false,
  prev: null,
  cur: null,
  curWall: 0,
  stats: null,
  playerStats: {},
  series: [],
  goals: [],
  arrows: [],
  tags: new Map(),
  slots: {},
  cues: new Map(),
  cueLog: [],
  opsCount: {},
  latency: [],
  model: "",
  directed: 0,
  counters: {},
};
if (params.get("mode")) state.profile.mode = params.get("mode");
if (params.get("lang")) state.profile.language = params.get("lang");

// ------------------------------------------------------------------ connection
function connect(seed) {
  if (state.ws) { state.ws.onclose = null; state.ws.close(); }
  resetMatch();
  const q = new URLSearchParams({ speed: state.speed, profile: JSON.stringify(state.profile) });
  if (seed) q.set("seed", seed);
  if (params.get("home") && params.get("away")) { q.set("home", params.get("home")); q.set("away", params.get("away")); }
  const proto = location.protocol === "https:" ? "wss" : "ws";
  const ws = new WebSocket(`${proto}://${location.host}/ws/match?${q}`);
  state.ws = ws;
  ws.onmessage = (e) => handle(JSON.parse(e.data));
  ws.onclose = () => { $("matchTitle").textContent = "Disconnected · press New match"; };
}

function send(msg) { if (state.ws && state.ws.readyState === 1) state.ws.send(JSON.stringify(msg)); }

function resetMatch() {
  Object.assign(state, { prev: null, cur: null, series: [], goals: [], arrows: [], cueLog: [], opsCount: {}, latency: [], directed: 0, counters: {} });
  state.cues.clear();
  state.tags.forEach((el) => el.remove());
  state.tags.clear();
  for (const k of Object.keys(state.slots)) clearSlot(k);
  $("feed").innerHTML = "";
  $("traces").innerHTML = "";
  $("cueJson").textContent = "No cues yet.";
}

function handle(m) {
  switch (m.type) {
    case "hello": return onHello(m);
    case "frame": state.prev = state.cur; state.cur = m; state.curWall = performance.now(); return onFrame(m);
    case "cue": return onCue(m.cue, m.replay);
    case "stats": state.stats = m.stats; state.playerStats = m.players; state.counters = m.counters || {}; renderPipeline(); return onStats();
    case "traces": return onTraces(m);
    case "events": return onEvents(m.events);
    case "profile": return;
    case "end": $("tickerText").textContent = "Full-time · press New match for another synthetic fixture"; return;
    case "error": $("matchTitle").textContent = m.message; return;
  }
}

function onHello(m) {
  state.meta = m.meta;
  state.model = m.model;
  state.players = Object.fromEntries(m.meta.players.map((p) => [p.id, p]));
  state.colors = { home: m.meta.home.colors[0], away: m.meta.away.colors[0] };
  if (state.colors.home.toLowerCase() === state.colors.away.toLowerCase()) state.colors.away = m.meta.away.colors[1];
  document.documentElement.style.setProperty("--home", state.colors.home);
  document.documentElement.style.setProperty("--away", state.colors.away);
  $("matchTitle").textContent = `${m.meta.home.name} vs ${m.meta.away.name} · ${m.meta.venue}`;
  $("seedLabel").textContent = m.seed;
  $("sbHome").querySelector("b").textContent = m.meta.home.short;
  $("sbAway").querySelector("b").textContent = m.meta.away.short;
  $("sbHome").querySelector("i").style.background = state.colors.home;
  $("sbAway").querySelector("i").style.background = state.colors.away;
  $("tlHome").textContent = m.meta.home.name;
  $("tlAway").textContent = m.meta.away.name;
  const badge = $("modelBadge");
  const offline = m.model.startsWith("touchline-offline");
  badge.textContent = offline ? "Agents: offline templates" : `Agents: ${m.model}`;
  badge.classList.toggle("offline", offline);
  badge.title = offline
    ? "Language agents are running on the deterministic offline backend (no keys needed). Set FOUNDRY_PROJECT_ENDPOINT and FOUNDRY_MODEL to run them on Microsoft Foundry."
    : "Language agents are running on Microsoft Foundry";
  const sel = $("speedSel");
  sel.innerHTML = m.speeds.map((s) => `<option value="${s}">${s}×</option>`).join("");
  sel.value = String(state.speed);
  fillProfileControls();
  history.replaceState(null, "", `?seed=${m.seed}`);
}

// ------------------------------------------------------------------ profile
function fillProfileControls() {
  const { meta, profile } = state;
  $("favSel").innerHTML = `<option value="">Neutral</option><option value="home">${meta.home.name}</option><option value="away">${meta.away.name}</option>`;
  const group = (side, club) =>
    `<optgroup label="${club.name}">` +
    meta.players.filter((p) => p.side === side).map((p) => `<option value="${p.id}">${p.number} · ${p.name} (${p.position})</option>`).join("") +
    "</optgroup>";
  $("focusSel").innerHTML = `<option value="">Nobody</option>` + group("home", meta.home) + group("away", meta.away);
  if (profile.focus_player_id && !state.players[profile.focus_player_id]) profile.focus_player_id = null;
  $("favSel").value = profile.favourite_side || "";
  $("focusSel").value = profile.focus_player_id || "";
  $("langSel").value = profile.language;
  $("metricSel").value = profile.metric || "";
  paintMode();
}

function paintMode() {
  document.querySelectorAll("#modeSeg button").forEach((b) => b.classList.toggle("on", b.dataset.mode === state.profile.mode));
  document.body.classList.toggle("mode-analyst", state.profile.mode === "analyst");
  document.body.classList.toggle("mode-fan", state.profile.mode === "fan");
}

function updateProfile(patch) {
  Object.assign(state.profile, patch);
  store.set("tl.profile", state.profile);
  paintMode();
  send({ type: "profile", profile: state.profile });
  onStats();
}

document.querySelectorAll("#modeSeg button").forEach((b) => b.addEventListener("click", () => updateProfile({ mode: b.dataset.mode })));
$("langSel").addEventListener("change", (e) => updateProfile({ language: e.target.value }));
$("favSel").addEventListener("change", (e) => updateProfile({ favourite_side: e.target.value || null }));
$("focusSel").addEventListener("change", (e) => updateProfile({ focus_player_id: e.target.value || null }));
$("metricSel").addEventListener("change", (e) => updateProfile({ metric: e.target.value || null }));
$("speedSel").addEventListener("change", (e) => { state.speed = Number(e.target.value); store.set("tl.speed", state.speed); send({ type: "speed", speed: state.speed }); });
$("pauseBtn").addEventListener("click", togglePause);
$("newMatchBtn").addEventListener("click", () => { history.replaceState(null, "", location.pathname); connect(null); });
document.querySelectorAll(".chaos-grid button").forEach((b) => b.addEventListener("click", () => send({ type: "chaos", fault: b.dataset.fault })));
document.querySelectorAll(".tab").forEach((t) => t.addEventListener("click", () => {
  document.querySelectorAll(".tab").forEach((x) => x.classList.toggle("active", x === t));
  document.querySelectorAll(".panel").forEach((p) => p.classList.toggle("active", p.id === `panel-${t.dataset.tab}`));
}));
document.addEventListener("keydown", (e) => {
  if (e.target.tagName === "SELECT") return;
  if (e.code === "Space") { e.preventDefault(); togglePause(); }
  if (e.key === "a") updateProfile({ mode: "analyst" });
  if (e.key === "f") updateProfile({ mode: "fan" });
});
function togglePause() { state.paused = !state.paused; $("pauseBtn").textContent = state.paused ? "▶" : "❚❚"; send({ type: "pause", paused: state.paused }); }

// ------------------------------------------------------------------ pitch rendering
const canvas = $("pitch");
const ctx = canvas.getContext("2d");
let geom = { w: 0, h: 0, ox: 0, oy: 0, s: 1 };

function resize() {
  const r = canvas.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  canvas.width = Math.round(r.width * dpr);
  canvas.height = Math.round(r.height * dpr);
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  const pad = Math.max(16, r.width * 0.035);
  const s = Math.min((r.width - 2 * pad) / PITCH.L, (r.height - 2 * pad - 30) / PITCH.W);
  geom = { w: r.width, h: r.height, s, ox: (r.width - PITCH.L * s) / 2, oy: (r.height - 30 - PITCH.W * s) / 2 + 4 };
  const tc = $("timelineCanvas");
  const tr = tc.getBoundingClientRect();
  tc.width = Math.round(tr.width * dpr);
  tc.height = Math.round(90 * dpr);
}
window.addEventListener("resize", resize);

// pitch y=0 is the bottom touchline on the broadcast view
const px = (x) => geom.ox + x * geom.s;
const py = (y) => geom.oy + (PITCH.W - y) * geom.s;

function drawPitch() {
  const { w, h, s } = geom;
  ctx.fillStyle = "#0f4a26";
  ctx.fillRect(0, 0, w, h);
  for (let i = 0; i < 14; i++) {
    if (i % 2) continue;
    ctx.fillStyle = "rgba(255,255,255,0.035)";
    ctx.fillRect(px((i * PITCH.L) / 14), py(PITCH.W), (PITCH.L / 14) * s, PITCH.W * s);
  }
  ctx.strokeStyle = "rgba(255,255,255,0.75)";
  ctx.lineWidth = Math.max(1.2, s * 0.15);
  ctx.strokeRect(px(0), py(PITCH.W), PITCH.L * s, PITCH.W * s);
  line(52.5, 0, 52.5, 68);
  circle(52.5, 34, 9.15);
  dot(52.5, 34, 0.35);
  for (const g of [0, 105]) {
    const d = g === 0 ? 1 : -1;
    ctx.strokeRect(px(Math.min(g, g + d * 16.5)), py(34 + 20.16), 16.5 * s, 40.32 * s);
    ctx.strokeRect(px(Math.min(g, g + d * 5.5)), py(34 + 9.16), 5.5 * s, 18.32 * s);
    dot(g + d * 11, 34, 0.3);
    ctx.save();
    ctx.lineWidth = Math.max(2, s * 0.3);
    line(g, 34 - 3.66, g, 34 + 3.66);
    ctx.restore();
    ctx.beginPath();
    const a0 = d === 1 ? -0.93 : Math.PI - 0.93;
    ctx.arc(px(g + d * 11), py(34), 9.15 * s, a0, a0 + 1.86);
    ctx.stroke();
  }
}
function line(x1, y1, x2, y2) { ctx.beginPath(); ctx.moveTo(px(x1), py(y1)); ctx.lineTo(px(x2), py(y2)); ctx.stroke(); }
function circle(x, y, r) { ctx.beginPath(); ctx.arc(px(x), py(y), r * geom.s, 0, Math.PI * 2); ctx.stroke(); }
function dot(x, y, r) { ctx.beginPath(); ctx.arc(px(x), py(y), r * geom.s, 0, Math.PI * 2); ctx.fillStyle = "rgba(255,255,255,.8)"; ctx.fill(); }

function lerpPos(id) {
  const { prev, cur } = state;
  if (!cur) return null;
  const b = id === "ball" ? cur.ball : cur.players[id];
  if (!b) return null;
  if (!prev || state.paused) return b;
  const a = id === "ball" ? prev.ball : prev.players[id];
  if (!a) return b;
  const k = Math.min(1, (performance.now() - state.curWall) / 100);
  return [a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k];
}

function render() {
  if (geom.w === 0) resize();
  drawPitch();
  const now = performance.now();
  state.arrows = state.arrows.filter((a) => a.until > now);
  for (const a of state.arrows) drawArrow(a);
  if (state.cur) {
    const r = Math.max(5, geom.s * 1.05);
    const focus = state.profile.focus_player_id;
    for (const id of Object.keys(state.cur.players)) {
      const p = state.players[id];
      const pos = lerpPos(id);
      if (!p || !pos) continue;
      const x = px(pos[0]);
      const y = py(pos[1]);
      ctx.beginPath();
      ctx.arc(x, y + r * 0.35, r, 0, Math.PI * 2);
      ctx.fillStyle = "rgba(0,0,0,.25)";
      ctx.fill();
      ctx.beginPath();
      ctx.arc(x, y, r, 0, Math.PI * 2);
      ctx.fillStyle = p.position === "GK" ? "#facc15" : state.colors[p.side];
      ctx.fill();
      ctx.lineWidth = id === focus ? 3 : 1.4;
      ctx.strokeStyle = id === focus ? "#facc15" : "rgba(255,255,255,.85)";
      ctx.stroke();
      if (id === focus) {
        ctx.beginPath();
        ctx.arc(x, y, r + 5 + 2 * Math.sin(now / 200), 0, Math.PI * 2);
        ctx.strokeStyle = "rgba(250,204,21,.6)";
        ctx.lineWidth = 2;
        ctx.stroke();
      }
      ctx.fillStyle = p.position === "GK" ? "#111" : "#fff";
      ctx.font = `700 ${Math.round(r * 1.05)}px "Barlow Condensed", sans-serif`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(p.number, x, y + 0.5);
    }
    const b = lerpPos("ball");
    if (b) {
      ctx.beginPath();
      ctx.arc(px(b[0]), py(b[1]), Math.max(3, geom.s * 0.55), 0, Math.PI * 2);
      ctx.fillStyle = "#fff";
      ctx.shadowColor = "rgba(0,0,0,.6)";
      ctx.shadowBlur = 6;
      ctx.fill();
      ctx.shadowBlur = 0;
    }
  }
  placeTags();
  requestAnimationFrame(render);
}

function drawArrow(a) {
  const [x1, y1, x2, y2] = [px(a.x), py(a.y), px(a.end_x), py(a.end_y)];
  const life = Math.min(1, (a.until - performance.now()) / 800);
  ctx.save();
  ctx.globalAlpha = Math.max(0, life);
  ctx.strokeStyle = "#facc15";
  ctx.fillStyle = "#facc15";
  ctx.lineWidth = 3;
  ctx.setLineDash([8, 6]);
  ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
  ctx.setLineDash([]);
  const ang = Math.atan2(y2 - y1, x2 - x1);
  ctx.beginPath();
  ctx.moveTo(x2, y2);
  ctx.lineTo(x2 - 12 * Math.cos(ang - 0.4), y2 - 12 * Math.sin(ang - 0.4));
  ctx.lineTo(x2 - 12 * Math.cos(ang + 0.4), y2 - 12 * Math.sin(ang + 0.4));
  ctx.fill();
  if (a.label) {
    ctx.font = '700 14px "Barlow Condensed", sans-serif';
    const mx = (x1 + x2) / 2;
    const my = (y1 + y2) / 2 - 12;
    const tw = ctx.measureText(a.label).width + 12;
    ctx.fillStyle = "rgba(8,12,18,.9)";
    ctx.fillRect(mx - tw / 2, my - 11, tw, 20);
    ctx.fillStyle = "#facc15";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(a.label, mx, my);
  }
  ctx.restore();
}

// ------------------------------------------------------------------ overlays
function wallDuration(cue) {
  if (cue.slot === "full_panel") return cue.headline.match(/FULL|FINAL|FIN/) ? 20000 : 7000;
  const d = ((cue.t_out - cue.t_in) / state.speed) * 1000;
  return Math.max(3500, Math.min(d, cue.slot === "corner_bug" ? 12000 : 9000));
}

function sideColor(side) { return side ? state.colors[side] : "var(--accent)"; }

function chipsHtml(chips) {
  return (chips || []).map((c) => `<span class="chip${c.pinned ? " pinned-chip" : ""}"><em>${esc(c.label)}</em>${esc(String(c.value))}${esc(c.unit || "")}</span>`).join("");
}

function whyHtml(cue, cls) {
  if (cue.why) return `<div class="${cls}">${esc(cue.why)}</div>`;
  return `<div class="${cls} pending">${pendingText()}</div>`;
}
function pendingText() { return state.model.startsWith("foundry") ? "Analyst agent is writing…" : "Agents enriching…"; }

function onCue(cue, replay) {
  const prev = state.cues.get(cue.id);
  state.cues.set(cue.id, cue);
  state.cueLog.unshift(cue);
  state.cueLog.length = Math.min(state.cueLog.length, 6);
  $("cueJson").textContent = JSON.stringify(state.cueLog, null, 2);
  feedItem(cue, prev);
  if (!prev) state.directed += 1;
  if (cue.slot !== "ticker" && cue.why && cue.kind !== "sprint") {
    const minute = state.cur ? clock(state.cur.period, state.cur.minute) : "";
    $("tickerText").textContent = `${minute}  ${cue.headline} — ${cue.why}`;
  }
  if (prev && !replay) return refreshOnAir(cue);
  showCue(cue);
}

function showCue(cue) {
  switch (cue.slot) {
    case "full_panel": {
      const el = $("fullPanel");
      const kicker = cue.anchor.side ? (state.meta[cue.anchor.side] || {}).name || "" : state.meta.competition;
      el.innerHTML = `<div class="fp-kicker">${esc(kicker)}</div><div class="fp-head">${esc(cue.headline)}</div>${whyHtml(cue, "fp-why")}<div class="chips">${chipsHtml(cue.chips)}</div>`;
      return putSlot("full_panel", el, cue);
    }
    case "lower_third": {
      const el = $("lowerThird");
      el.innerHTML = `<div class="lt-head"><span class="stripe" style="background:${sideColor(cue.anchor.side)}"></span>${esc(cue.headline)}</div>${whyHtml(cue, "lt-why")}<div class="chips">${chipsHtml(cue.chips)}</div>`;
      return putSlot("lower_third", el, cue);
    }
    case "corner_bug": {
      const el = $("cornerBug");
      el.style.borderLeftColor = sideColor(cue.anchor.side);
      el.innerHTML = `<div class="h">${esc(cue.headline)}</div>${cue.why ? `<div class="w">${esc(cue.why)}</div>` : ""}<div class="chips" style="padding:6px 0 0">${chipsHtml(cue.chips)}</div>`;
      return putSlot("corner_bug", el, cue);
    }
    case "ticker": {
      $("tickerText").textContent = cue.headline + (cue.why ? ` — ${cue.why}` : "");
      return;
    }
    case "player_tag":
      return addTag(cue);
    case "pitch_arrow": {
      const a = cue.anchor;
      if (a.end_x !== undefined) {
        const diff = (cue.chips.find((c) => c.label === "Difficulty") || {}).value;
        state.arrows.push({ ...a, until: performance.now() + wallDuration(cue), label: diff !== undefined ? `Difficulty ${diff}/10` : "" });
      }
      if (state.profile.mode === "analyst") {
        const el = $("lowerThird");
        if (!state.slots.lower_third || state.slots.lower_third.cue.priority <= cue.priority) {
          el.innerHTML = `<div class="lt-head"><span class="stripe" style="background:${sideColor(a.side)}"></span>${esc(cue.headline)}</div>${whyHtml(cue, "lt-why")}<div class="chips">${chipsHtml(cue.chips)}</div>`;
          putSlot("lower_third", el, cue);
        }
      }
      return;
    }
  }
}

function putSlot(slot, el, cue) {
  clearSlot(slot);
  el.classList.remove("hidden");
  el.style.animation = "none";
  void el.offsetWidth;
  el.style.animation = "";
  const timer = setTimeout(() => clearSlot(slot), wallDuration(cue));
  state.slots[slot] = { el, cue, timer };
}

function clearSlot(slot) {
  const s = state.slots[slot];
  if (!s) return;
  clearTimeout(s.timer);
  s.el.classList.add("hidden");
  delete state.slots[slot];
}

function refreshOnAir(cue) {
  for (const s of Object.values(state.slots)) {
    if (s.cue.id !== cue.id) continue;
    s.cue = cue;
    const why = s.el.querySelector(".lt-why, .fp-why, .w");
    if (why) { why.textContent = cue.why || ""; why.classList.remove("pending"); }
    else if (cue.slot === "corner_bug" && cue.why) s.el.querySelector(".h").insertAdjacentHTML("afterend", `<div class="w">${esc(cue.why)}</div>`);
  }
  if (cue.slot === "ticker") $("tickerText").textContent = cue.headline + (cue.why ? ` — ${cue.why}` : "");
}

function addTag(cue) {
  const pid = cue.anchor.player_id;
  if (!pid) return;
  const key = `${pid}`;
  let el = state.tags.get(key);
  if (!el) {
    el = document.createElement("div");
    el.className = "ptag";
    $("tags").appendChild(el);
    state.tags.set(key, el);
  }
  el.classList.toggle("focus", pid === state.profile.focus_player_id);
  el.innerHTML = esc(cue.headline);
  el.dataset.pid = pid;
  clearTimeout(el._t);
  el._t = setTimeout(() => { el.remove(); state.tags.delete(key); }, wallDuration(cue));
}

function placeTags() {
  const focus = state.profile.focus_player_id;
  if (focus && state.cur && !state.tags.has(focus)) {
    const el = document.createElement("div");
    el.className = "ptag focus";
    el.dataset.pid = focus;
    el.dataset.persistent = "1";
    $("tags").appendChild(el);
    state.tags.set(focus, el);
  }
  for (const [key, el] of state.tags) {
    if (el.dataset.persistent && key !== focus) { el.remove(); state.tags.delete(key); continue; }
    const pos = lerpPos(el.dataset.pid);
    if (!pos) continue;
    if (el.dataset.persistent) {
      const ps = state.playerStats[key];
      const p = state.players[key];
      el.innerHTML = `${esc(p ? p.short_name : key)}${ps ? `<small>${ps.distance_km} km</small>` : ""}`;
    }
    el.style.left = `${px(pos[0])}px`;
    el.style.top = `${py(pos[1])}px`;
  }
}

// ------------------------------------------------------------------ frame + events
function onFrame(f) {
  $("sbScore").textContent = `${f.score[0]} – ${f.score[1]}`;
  $("sbClock").textContent = clock(f.period, f.minute);
  $("sbHome").classList.toggle("poss", f.possession === "home");
  $("sbAway").classList.toggle("poss", f.possession === "away");
}

function clock(period, minute) {
  const m = Math.floor(minute);
  const cap = period === 1 ? 45 : 90;
  return m >= cap ? `${cap}+${m - cap + 1}'` : `${m + 1}'`;
}

function onEvents(events) {
  for (const e of events) if (e.type === "goal") state.goals.push({ minute: e.data.minute, side: e.side });
}

// ------------------------------------------------------------------ feed
function feedItem(cue, prev) {
  if (cue.slot === "player_tag" && state.profile.mode === "fan" && !prev) return;
  let li = document.querySelector(`#feed li[data-id="${cue.id}"]`);
  const kind = cue.kind;
  if (!li) {
    li = document.createElement("li");
    li.dataset.id = cue.id;
    $("feed").prepend(li);
    while ($("feed").children.length > 80) $("feed").lastChild.remove();
  }
  li.className = `k-${kind}`;
  const minute = state.cur ? clock(state.cur.period, state.cur.minute) : "";
  const at = li.dataset.minute || minute;
  li.dataset.minute = at;
  li.innerHTML = `<div class="meta"><span>${esc(at)} · ${esc(cue.slot.replace("_", " "))}</span><span class="rev">${cue.revision ? `rev ${cue.revision} · ${esc(cue.source)}` : "director"}</span></div>
    <div class="h">${esc(cue.headline)}</div>${cue.why ? `<div class="w">${esc(cue.why)}</div>` : `<div class="w pending">${pendingText()}</div>`}`;
}

// ------------------------------------------------------------------ stats + metric
function onStats() {
  const s = state.stats;
  if (!s || !state.meta) return;
  state.series.push({ m: s.minute, mom: s.momentum, chaos: s.control.chaos });
  drawTimeline();
  renderStats(s);
  renderPinned(s);
  renderFocus();
}

function bar(h, a) {
  const tot = (Number(h) || 0) + (Number(a) || 0) || 1;
  return `<div class="bar"><span style="width:${(100 * (Number(h) || 0)) / tot}%;background:var(--home)"></span><span style="width:${(100 * (Number(a) || 0)) / tot}%;background:var(--away)"></span></div>`;
}

function renderStats(s) {
  const analyst = state.profile.mode === "analyst";
  const rows = analyst
    ? [["possession", "Possession %"], ["xg", "Expected goals (xG)"], ["shots", "Shots"], ["shots_on_target", "On target"], ["passes", "Passes"], ["pass_accuracy", "Pass accuracy %"], ["final_third_entries", "Final-third entries"], ["pressures", "Pressures"], ["tackles_won", "Tackles won"], ["interceptions", "Interceptions"], ["fouls", "Fouls"], ["corners", "Corners"]]
    : [["possession", "Possession %"], ["shots", "Shots"], ["xg", "Chance quality (xG)"], ["corners", "Corners"], ["fouls", "Fouls"]];
  let html = `<div class="stat-head"><span style="color:var(--home)">${esc(state.meta.home.name)}</span><span style="color:var(--away)">${esc(state.meta.away.name)}</span></div>`;
  for (const [k, label] of rows) {
    html += `<div class="stat-row"><span class="v">${s.home[k] ?? "–"}</span><div><div class="lbl">${label}</div>${bar(s.home[k], s.away[k])}</div><span class="v">${s.away[k] ?? "–"}</span></div>`;
  }
  if (analyst) {
    html += `<div class="stat-sub">Game state</div>
      <div class="stat-row"><span class="v">${s.pressure.home}</span><div><div class="lbl">Pressures / min (2')</div>${bar(s.pressure.home, s.pressure.away)}</div><span class="v">${s.pressure.away}</span></div>
      <div class="ops-kpis" style="margin-top:8px">
        <div class="kpi"><div class="k">Chaos index</div><div class="v">${s.control.chaos}/100</div></div>
        <div class="kpi"><div class="k">Turnovers / min</div><div class="v">${s.control.turnovers_per_min}</div></div>
        <div class="kpi"><div class="k">Passes / move</div><div class="v">${s.control.avg_chain}</div></div>
        <div class="kpi"><div class="k">Actions / min</div><div class="v">${s.rhythm.actions_per_min}</div></div>
        <div class="kpi"><div class="k">Avg pass speed</div><div class="v">${s.rhythm.avg_pass_speed_kmh ?? "–"} km/h</div></div>
        <div class="kpi"><div class="k">Momentum</div><div class="v">${s.momentum > 0 ? "+" : ""}${s.momentum}</div></div>
      </div>`;
  }
  const ps = Object.entries(state.playerStats).map(([id, v]) => ({ id, ...v, p: state.players[id] })).filter((x) => x.p);
  ps.sort((a, b) => (b.goals * 3 + b.xg * 2 + b.progressive_passes * 0.1) - (a.goals * 3 + a.xg * 2 + a.progressive_passes * 0.1) || b.distance_km - a.distance_km);
  const top = ps.slice(0, analyst ? 12 : 6);
  const focus = state.profile.focus_player_id;
  if (focus && !top.some((x) => x.id === focus)) { const f = ps.find((x) => x.id === focus); if (f) top.push(f); }
  html += `<div class="stat-sub">Players</div><table class="players"><tr><th>Player</th><th>km</th><th>Top</th>${analyst ? "<th>Pass%</th><th>xG</th><th>Prs</th>" : "<th>G</th>"}</tr>`;
  for (const x of top) {
    html += `<tr class="${x.id === focus ? "focus" : ""}"><td><span style="color:${state.colors[x.p.side]}">●</span> ${esc(x.p.short_name)}</td><td>${x.distance_km}</td><td>${x.top_speed_kmh}</td>${analyst ? `<td>${x.pass_accuracy ?? "–"}</td><td>${x.xg}</td><td>${x.pressures}</td>` : `<td>${x.goals}</td>`}</tr>`;
  }
  $("statsBox").innerHTML = html + "</table>";
}

function renderPinned(s) {
  const el = $("pinned");
  const m = state.profile.metric;
  if (!m) return el.classList.add("hidden");
  el.classList.remove("hidden");
  const H = state.meta.home.short;
  const A = state.meta.away.short;
  let label = "";
  let val = "";
  let barHtml = "";
  if (m === "xg") { label = "Expected goals"; val = `${H} ${s.home.xg} – ${s.away.xg} ${A}`; barHtml = bar(s.home.xg, s.away.xg); }
  if (m === "possession") { label = "Possession"; val = `${H} ${s.home.possession}% – ${s.away.possession}% ${A}`; barHtml = bar(s.home.possession, s.away.possession); }
  if (m === "momentum") { label = "Momentum (5')"; const h = Math.round(50 + 50 * s.momentum); val = `${H} ${h}% – ${100 - h}% ${A}`; barHtml = bar(h, 100 - h); }
  if (m === "chaos") { label = "Control ↔ chaos"; val = `${s.control.chaos}/100 ${s.control.chaos > 60 ? "chaotic" : s.control.chaos < 40 ? "controlled" : "balanced"}`; barHtml = `<div class="bar"><span style="width:${s.control.chaos}%;background:linear-gradient(90deg,#38bdf8,#f59e0b)"></span></div>`; }
  if (m === "pressure") { label = "Pressures per minute"; val = `${H} ${s.pressure.home} – ${s.pressure.away} ${A}`; barHtml = bar(s.pressure.home, s.pressure.away); }
  el.innerHTML = `<div class="lbl">${label}</div><div>${esc(val)}</div>${barHtml}`;
}

function renderFocus() {
  const el = $("focusCard");
  const id = state.profile.focus_player_id;
  const ps = id && state.playerStats[id];
  if (!ps) return el.classList.add("hidden");
  const p = state.players[id];
  el.classList.remove("hidden");
  el.style.borderColor = state.colors[p.side];
  const cells = state.profile.mode === "analyst"
    ? [["Distance", `${ps.distance_km} km`], ["Top speed", `${ps.top_speed_kmh}`], ["Sprints", ps.sprints], ["Passes", ps.passes], ["Pass %", ps.pass_accuracy ?? "–"], ["xG", ps.xg], ["Shots", ps.shots], ["Tackles", ps.tackles_won], ["Pressures", ps.pressures]]
    : [["Distance", `${ps.distance_km} km`], ["Top speed", `${ps.top_speed_kmh}`], ["Goals", ps.goals]];
  el.innerHTML = `<div class="k">Following</div><div class="nm">${p.number} · ${esc(p.name)}</div><div class="grid">${cells.map(([k, v]) => `<div><div class="k">${k}</div><div class="v">${v}</div></div>`).join("")}</div>`;
}

function drawTimeline() {
  const c = $("timelineCanvas");
  const g = c.getContext("2d");
  const dpr = window.devicePixelRatio || 1;
  const w = c.width / dpr;
  const h = c.height / dpr;
  g.setTransform(dpr, 0, 0, dpr, 0, 0);
  g.clearRect(0, 0, w, h);
  const X = (m) => (Math.min(m, 96) / 96) * w;
  const mid = h / 2;
  g.strokeStyle = "#233041";
  g.lineWidth = 1;
  g.beginPath(); g.moveTo(0, mid); g.lineTo(w, mid); g.stroke();
  for (const m of [15, 30, 45, 60, 75, 90]) {
    g.fillStyle = "#3a4a60"; g.fillRect(X(m), 0, 1, h);
    g.fillStyle = "#5b6b80"; g.font = "10px Inter, sans-serif"; g.fillText(`${m}'`, X(m) + 3, h - 3);
  }
  const pts = state.series;
  for (const side of ["home", "away"]) {
    g.beginPath();
    g.moveTo(X(pts.length ? pts[0].m : 0), mid);
    for (const p of pts) {
      const v = side === "home" ? Math.max(0, p.mom) : Math.min(0, p.mom);
      g.lineTo(X(p.m), mid - v * (mid - 6));
    }
    g.lineTo(X(pts.length ? pts[pts.length - 1].m : 0), mid);
    g.closePath();
    g.fillStyle = side === "home" ? hexA(state.colors.home, 0.55) : hexA(state.colors.away, 0.55);
    g.fill();
  }
  g.setLineDash([4, 4]);
  g.strokeStyle = "rgba(245,158,11,.8)";
  g.beginPath();
  pts.forEach((p, i) => { const y = h - 4 - (p.chaos / 100) * (h - 8); if (i) g.lineTo(X(p.m), y); else g.moveTo(X(p.m), y); });
  g.stroke();
  g.setLineDash([]);
  for (const goal of state.goals) {
    const x = X(goal.minute);
    g.fillStyle = state.colors[goal.side];
    g.beginPath(); g.arc(x, goal.side === "home" ? 8 : h - 8, 5, 0, Math.PI * 2); g.fill();
    g.strokeStyle = "#fff"; g.lineWidth = 1.5; g.stroke();
  }
}

function hexA(hex, a) {
  const n = parseInt(hex.slice(1), 16);
  return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${a})`;
}

// ------------------------------------------------------------------ ops
const NODES = [
  ["ingest", "Ingest"], ["interpret", "Interpret"], ["director", "Director"],
  ["analyst", "Analyst"], ["personalizer", "Personalizer"], ["narrator", "Narrator"], ["verifier", "Verifier"], ["supervisor", "Supervisor"],
];
function renderPipeline() {
  $("pipelineViz").innerHTML = NODES.map(([id, label], i) => {
    const n = { ingest: state.counters.events, interpret: state.counters.insights, director: state.counters.cues }[id] ?? state.opsCount[id] ?? 0;
    const sep = i === 3 || i === 6 ? '<span class="arrow" style="flex-basis:100%;height:0"></span>' : i ? '<span class="arrow">→</span>' : "";
    return `${sep}<span class="node" id="node-${id}">${label}<span class="n">${n || ""}</span></span>`;
  }).join("");
}
renderPipeline();

function flash(id, bad) {
  const el = $(`node-${id}`);
  if (!el) return;
  el.classList.remove("flash-ok", "flash-bad");
  void el.offsetWidth;
  el.classList.add(bad ? "flash-bad" : "flash-ok");
  clearTimeout(el._t);
  el._t = setTimeout(() => el.classList.remove("flash-ok", "flash-bad"), 700);
}

function onTraces(m) {
  const list = $("traces");
  for (const t of m.traces) {
    state.opsCount[t.agent] = (state.opsCount[t.agent] || 0) + 1;
    const bad = !["ok", "skipped"].includes(t.status);
    if (t.status === "rejected") state.opsCount.verifier = (state.opsCount.verifier || 0) + 1;
    if (bad && t.agent !== "chaos") state.opsCount.supervisor = (state.opsCount.supervisor || 0) + 1;
    if (t.latency_ms) { state.latency.push(t.latency_ms); if (state.latency.length > 50) state.latency.shift(); }
    state.opsCount[`st_${t.status}`] = (state.opsCount[`st_${t.status}`] || 0) + 1;
    if (t.status === "ok" && t.agent !== "analyst" && t.agent !== "personalizer" && t.agent !== "narrator") continue;
    if (t.status === "ok" && Math.random() > 0.25) { flash(t.agent); continue; }
    const li = document.createElement("li");
    li.innerHTML = `<span>${esc(t.agent)}</span><span class="st-${esc(t.status)}">${esc(t.status)}</span><span class="note">${esc(t.note || (t.latency_ms ? `${t.latency_ms} ms · ${t.model}` : t.model))}</span>`;
    list.prepend(li);
    while (list.children.length > 120) list.lastChild.remove();
  }
  for (const t of m.traces.slice(-6)) {
    flash(t.agent, !["ok", "skipped"].includes(t.status));
    if (t.status === "rejected") flash("verifier", true);
    if (["fallback", "timeout", "error", "breaker_open", "rejected"].includes(t.status)) flash("supervisor", true);
  }
  renderPipeline();
  const lat = state.latency.length ? Math.round(state.latency.reduce((a, b) => a + b, 0) / state.latency.length) : 0;
  const c = state.opsCount;
  $("opsKpis").innerHTML = [
    ["Model calls", m.calls],
    ["Avg latency", `${lat} ms`],
    ["Circuit", m.breaker_open ? "OPEN" : "closed"],
    ["Verifier rejects", c.st_rejected || 0],
    ["Fallbacks", (c.st_timeout || 0) + (c.st_error || 0) + (c.st_breaker_open || 0) + (c.st_rejected || 0)],
    ["Feed repairs", (c.st_repaired || 0) + (c.st_quarantined || 0) + (c.st_dropped || 0)],
  ].map(([k, v]) => `<div class="kpi"><div class="k">${k}</div><div class="v">${v}</div></div>`).join("");
}

function esc(s) { return String(s ?? "").replace(/[&<>"']/g, (ch) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[ch]); }

// ------------------------------------------------------------------ boot
resize();
requestAnimationFrame(render);
connect(params.get("seed"));
