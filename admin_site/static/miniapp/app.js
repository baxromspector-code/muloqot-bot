/* MULOQOT Mini App — botdagi barcha imkoniyatlar bitta ilovada */
"use strict";
const TG = window.Telegram && window.Telegram.WebApp;
/* Rejim: ☀️ kunduzgi («Rasmiy» ranglar) va 🌙 tungi («Diplomat tungi»).
   Tanlov telefonda saqlanadi; tanlanmagan bo'lsa Telegram'ning o'z rejimiga (yorug'/qorong'i) moslanadi.
   Sinov uchun: /app?theme=oq|bmt (boshqa variantlar). */
const THEMES = ["rasmiy", "tun", "oq", "bmt"];
const MODE_KEY = "mlq-mode";
const storeGet = (k) => { try { return localStorage.getItem(k); } catch { return null; } };
const storeSet = (k, v) => { try { localStorage.setItem(k, v); } catch {} };
function applyTheme(theme, animate) {
  const root = document.documentElement;
  if (animate) { root.classList.add("mode-anim"); setTimeout(() => root.classList.remove("mode-anim"), 450); }
  if (theme === "rasmiy") delete root.dataset.theme; else root.dataset.theme = theme;
  try {
    const bgc = getComputedStyle(root).getPropertyValue("--bg").trim();
    TG.setHeaderColor(bgc); TG.setBackgroundColor(bgc);
    TG.setBottomBarColor(getComputedStyle(root).getPropertyValue("--solid").trim() || bgc);
  } catch {}
  const b = document.getElementById("modeBtn");
  if (b) { b.innerHTML = ic(theme === "tun" ? "sun" : "moon"); b.setAttribute("aria-label", theme === "tun" ? "Kunduzgi rejim" : "Tungi rejim"); }
}
const THEME = (() => {
  const q = new URLSearchParams(location.search).get("theme");
  if (THEMES.includes(q)) return q;
  const saved = storeGet(MODE_KEY);
  if (saved === "night") return "tun";
  if (saved === "day") return "rasmiy";
  return TG && TG.colorScheme === "dark" ? "tun" : "rasmiy";
})();
let CUR_THEME = THEME;
if (THEME !== "rasmiy") document.documentElement.dataset.theme = THEME;
function toggleMode() {
  CUR_THEME = CUR_THEME === "tun" ? "rasmiy" : "tun";
  storeSet(MODE_KEY, CUR_THEME === "tun" ? "night" : "day");
  applyTheme(CUR_THEME, true);
  try { TG.HapticFeedback.selectionChanged(); } catch {}
}
const INIT = (TG && TG.initData) || "";
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const haptic = (k = "light") => { try { TG.HapticFeedback.impactOccurred(k); } catch {} };
const notifyH = (k) => { try { TG.HapticFeedback.notificationOccurred(k); } catch {} };

const I = {
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>', pin: '<path d="M12 21s-7-6.2-7-12a7 7 0 0 1 14 0c0 5.8-7 12-7 12z"/><circle cx="12" cy="9" r="2.5"/>',
  users: '<circle cx="9" cy="8" r="4"/><path d="M2 21a7 7 0 0 1 14 0M16 4a4 4 0 0 1 0 8M22 21a7 7 0 0 0-4-6.3"/>', check: '<path d="m5 12 5 5L20 7"/>',
  ticket: '<path d="M3 8a2 2 0 0 0 2-2h14a2 2 0 0 0 2 2v2a2 2 0 0 0 0 4v2a2 2 0 0 0-2 2H5a2 2 0 0 0-2-2v-2a2 2 0 0 0 0-4z"/><path d="M13 6v2M13 11v2M13 16v2"/>',
  file: '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5M9 13h6M9 17h4"/>', chat: '<path d="M21 12a8 8 0 0 1-11.6 7.1L4 21l1.9-5.4A8 8 0 1 1 21 12z"/>',
  hand: '<path d="M18 11V6a2 2 0 0 0-4 0v5M14 10V4a2 2 0 0 0-4 0v6M10 10.5V6a2 2 0 0 0-4 0v8a8 8 0 0 0 16 0v-3a2 2 0 0 0-4 0"/>',
  card: '<rect x="3" y="5" width="18" height="14" rx="2.5"/><circle cx="9" cy="11" r="2.5"/><path d="M5.5 16.5a4 4 0 0 1 7 0M15 10h3M15 13h3"/>',
  star: '<path d="m12 3 2.8 5.7 6.2.9-4.5 4.4 1 6.2L12 17.3 6.5 20.2l1-6.2L3 9.6l6.2-.9z"/>', info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7.5h.01"/>',
  help: '<circle cx="12" cy="12" r="9"/><path d="M9.5 9a2.5 2.5 0 1 1 3.5 2.3c-.6.3-1 .9-1 1.7M12 17h.01"/>', doc: '<path d="M6 3h9l4 4v14H6z"/><path d="M15 3v4h4"/>',
  globe: '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/>', edit: '<path d="M4 20h4L19 9l-4-4L4 16z"/><path d="m13.5 6.5 4 4"/>',
  trash: '<path d="M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3"/>', chev: '<path d="m9 6 6 6-6 6"/>', search: '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
  gear: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 0 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 0 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 0 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 0 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/>',
  sun: '<circle cx="12" cy="12" r="4.2"/><path d="M12 2.5v2M12 19.5v2M4.6 4.6l1.4 1.4M18 18l1.4 1.4M2.5 12h2M19.5 12h2M4.6 19.4 6 18M18 6l1.4-1.4"/>',
  moon: '<path d="M20.5 14.2A8.5 8.5 0 1 1 9.8 3.5a7 7 0 0 0 10.7 10.7z"/>',
  inbox: '<path d="M22 12h-6l-2 3h-4l-2-3H2"/><path d="M5.5 5h13L22 12v6a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2v-6z"/>', send: '<path d="m22 2-7 20-4-9-9-4z"/><path d="M22 2 11 13"/>',
};
const ic = (n, cls = "") => `<svg viewBox="0 0 24 24" class="${cls}" aria-hidden="true">${I[n] || ""}</svg>`;
const COLORS = ["#1b2f55", "#a8844a", "#2f5d62", "#5b4a7a", "#3d5a80", "#7a4b3a"];  // sokin, rasmiy ranglar
const initials = (n) => (n || "?").split(/\s+/).filter(Boolean).slice(0, 2).map((w) => w[0]).join("").toUpperCase();
const COURSE = (c) => (c === "M" ? "Magistratura" : c ? `${c}-kurs` : "—");
const KIND = { question: "Savol", suggestion: "Taklif / loyiha", complaint: "Shikoyat (maxfiy)" };
const AP_ST = { new: ["Yangi", "warn"], in_review: ["Ko'rib chiqilmoqda", "blue"], answered: ["Javob berilgan", "ok"], closed: ["Yopilgan", ""] };
const APP_ST = { pending: ["Ko'rib chiqilmoqda", "warn"], returned: ["Qaytarilgan", "bad"], accepted: ["Qabul qilingan", "ok"], rejected: ["Rad etilgan", "bad"] };
const WD = ["Yak", "Dush", "Sesh", "Chor", "Pay", "Jum", "Shan"];
const MONTHS = ["yan", "fev", "mar", "apr", "may", "iyn", "iyl", "avg", "sen", "okt", "noy", "dek"];
const fmtDate = (s) => { if (!s) return ""; const d = new Date(String(s).replace(" ", "T")); return isNaN(d) ? s : `${d.getDate()} ${MONTHS[d.getMonth()]}, ${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`; };

/* ---------------- yangi alifbo (2026): Sh→Ş, Ch→Ç, O'→Ö, G'→Ğ ---------------- */
const KEEP = /(LinkedIn|Instagram|Telegram|Model UN|MUN|Excel|Word|Google)/;
const PROT = /(https?:\/\/\S+|@\w+|[\w.+-]+@[\w-]+\.[\w.]+|#\w*\d\w*|EVT-\d+|MLQ-[\w-]+)/;
function toNewPlain(x) {
  return x.replace(/O['‘`ʻ’]/g, "Ö").replace(/o['‘`ʻ’]/g, "ö").replace(/G['‘`ʻ’]/g, "Ğ").replace(/g['‘`ʻ’]/g, "ğ")
    .replace(/SH/g, "Ş").replace(/Sh/g, "Ş").replace(/sh/g, "ş").replace(/CH/g, "Ç").replace(/Ch/g, "Ç").replace(/ch/g, "ç");
}
function toNew(text) {
  return String(text).split(PROT).map((part, i) => (i % 2 ? part : part.split(KEEP).map((p, j) => (j % 2 ? p : toNewPlain(p))).join(""))).join("");
}
const isNew = () => S.me && S.me.lang === "un";
function localize(root) {
  if (!isNew() || !root) return;
  const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
    acceptNode: (n) => (n.parentElement && n.parentElement.closest("[data-raw],input,textarea,script,style") ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT),
  });
  const nodes = []; while (w.nextNode()) nodes.push(w.currentNode);
  nodes.forEach((n) => { const v = toNew(n.nodeValue); if (v !== n.nodeValue) n.nodeValue = v; });
  $$("[placeholder],[aria-label]", root.nodeType === 1 ? root : document).forEach((el) => {
    ["placeholder", "aria-label"].forEach((a) => { const v = el.getAttribute(a); if (v) el.setAttribute(a, toNew(v)); });
  });
}
new MutationObserver((muts) => { if (!isNew()) return; muts.forEach((m) => m.addedNodes.forEach((n) => localize(n.nodeType === 3 ? n.parentElement : n))); })
  .observe(document.body, { childList: true, subtree: true });

/* ---------------- API ---------------- */
const S = { me: null, events: null, info: null, tab: "home", blobs: [] };
async function api(path, opts = {}) {
  const r = await fetch(`/api/app${path}`, {
    method: opts.method || "GET",
    headers: { "X-Tg-Init": INIT, ...(opts.body ? { "Content-Type": "application/json" } : {}) },
    body: opts.body ? JSON.stringify(opts.body) : undefined,
  });
  if (opts.blob) { if (!r.ok) throw new Error("Rasm yuklanmadi"); return URL.createObjectURL(await r.blob()); }
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.detail || `Xato (${r.status})`);
  return data;
}
/* Kesh: tab almashtirish darhol (ma'lumot xotirada), eskirsa fonda yangilanadi */
const CACHE = new Map();
function get(path, ttl = 30000) {
  const c = CACHE.get(path);
  if (c && Date.now() - c.t < ttl) return c.p;
  const p = api(path).catch((e) => { CACHE.delete(path); throw e; });
  CACHE.set(path, { t: Date.now(), p });
  return p;
}
const invalidate = (...paths) => paths.forEach((x) => CACHE.delete(x));
function prefetch() { ["/tickets", "/rating", "/info", "/volunteer"].forEach((x) => get(x, 60000).catch(() => {})); }
let AVATAR = null;   // profil surati bir marta yuklanadi
const loadAvatar = () => (AVATAR = AVATAR || api("/photo", { blob: true }));
function setAvatar() { if (S.me.has_photo) loadAvatar().then((u) => { const im = $("#avaImg"); if (im) im.src = u; }).catch(() => {}); }
function toast(msg, ok = true) {
  const t = $("#toast"); t.textContent = msg; t.classList.add("on"); notifyH(ok ? "success" : "error");
  clearTimeout(toast._t); toast._t = setTimeout(() => t.classList.remove("on"), 2400);
}
const safe = (fn) => async (...a) => { try { await fn(...a); } catch (e) { toast(e.message, false); } };

/* ---------------- pastdan chiquvchi oyna ---------------- */
function openSheet(html, onMount) {
  const sh = $("#sheet"); sh.innerHTML = html; sh.scrollTop = 0;
  $("#scrim").classList.add("on"); sh.classList.add("on"); haptic();
  try { TG.BackButton.show(); } catch {}
  if (onMount) onMount(sh);
}
function closeSheet() {
  $("#sheet").classList.remove("on"); $("#scrim").classList.remove("on");
  try { TG.BackButton.hide(); } catch {}
  S.blobs.forEach((u) => URL.revokeObjectURL(u)); S.blobs = [];
}
$("#scrim").onclick = closeSheet;
try { TG.BackButton.onClick(closeSheet); } catch {}
const openLink = (url) => { try { url.startsWith("https://t.me/") ? TG.openTelegramLink(url) : TG.openLink(url); } catch { window.open(url, "_blank"); } };

/* ---------------- ro'yxatdan o'tmaganlar ---------------- */
function gate(me) {
  $("#tabbar").hidden = true;
  $("#view").innerHTML = `<div class="gate fade"><img src="/static/logo.png" alt=""><h1>MULOQOT</h1>
    <p>${INIT ? "Ilovadan foydalanish uchun avval botda ro'yxatdan o'ting: ism, yo'nalish, guruh, talaba ID, surat va telefon raqami so'raladi." : "Bu ilova Telegram ichida ishlaydi. Botni oching va «Ilova» tugmasini bosing."}</p>
    <button class="btn primary w press" id="goBot" style="max-width:320px">Botda ro'yxatdan o'tish</button></div>`;
  $("#goBot").onclick = () => { openLink(me.links.bot); try { TG.close(); } catch {} };
}

/* ---------------- effektlar ---------------- */
const REDUCED = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
function countUp(root) {
  $$("[data-count]", root).forEach((el) => {
    const to = +el.dataset.count || 0;
    if (REDUCED || to === 0) { el.textContent = to; return; }
    const t0 = performance.now(), dur = 900;
    const step = (t) => { const k = Math.min(1, (t - t0) / dur); el.textContent = Math.round(to * (1 - Math.pow(1 - k, 3))); if (k < 1) requestAnimationFrame(step); };
    requestAnimationFrame(step);
  });
}

/* ---------------- BOSH SAHIFA ---------------- */
function weekDays() {
  const now = new Date(); const day = (now.getDay() + 6) % 7; const mon = new Date(now); mon.setDate(now.getDate() - day);
  return [0, 1, 2, 3, 4].map((i) => { const d = new Date(mon); d.setDate(mon.getDate() + i); return d; });
}
const sameDay = (a, b) => a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();
const evDate = (e) => {
  if (e.starts_at) return new Date(String(e.starts_at).replace(" ", "T"));
  const m = /(\d{1,2})[./](\d{1,2})/.exec(e.date_text || "");     // «20.11 16:00» kabi matndan
  return m ? new Date(new Date().getFullYear(), +m[2] - 1, +m[1]) : null;
};

function eventCard(e, i) {
  const left = e.capacity ? Math.max(0, e.capacity - e.taken) : null;
  return `<button class="ecard glass press c${i % 4}" data-ev="${e.id}">
    <div class="bar"><i></i><h3>${esc(e.title)}</h3></div>
    <div class="meta"><span>${ic("clock")}${esc(e.date_text || "Sana e'lon qilinadi")}</span>
      <span>${e.ticket ? ic("check") + "Siz yozilgansiz" : ic("users") + (left === null ? `${e.taken} kishi yozilgan` : `${left} ta joy qoldi`)}</span></div></button>`;
}

async function renderHome() {
  const me = S.me; const u = me.user;
  const [events, rating] = await Promise.all([get("/events"), get("/rating").catch(() => ({ month: [], total: [] }))]);
  S.events = events;
  const days = weekDays(); const today = new Date();
  S.daySel = S.daySel ?? Math.max(0, days.findIndex((d) => sameDay(d, today)));
  const hour = today.getHours();
  const hello = hour < 11 ? "Xayrli tong" : hour < 18 ? "Xayrli kun" : "Xayrli kech";
  const top = (rating.total.length ? rating.total : rating.month).slice(0, 5);
  const m = me.member;
  const pct = me.held ? Math.min(1, me.went / me.held) : 0;
  const RING = 2 * Math.PI * 46;
  $("#view").innerHTML = `<div class="stagger">
    <header class="top"><div class="ava">${me.has_photo ? `<img src="" alt="" id="avaImg">` : `<span>${esc(initials(u.full_name))}</span>`}</div>
      <div class="hello"><small>${hello}</small><h1 class="grad" data-raw>${esc((u.full_name || "").split(" ")[0] || "Talaba")}</h1></div>
      <button class="ibtn press" id="modeBtn" aria-label="${CUR_THEME === "tun" ? "Kunduzgi rejim" : "Tungi rejim"}">${ic(CUR_THEME === "tun" ? "sun" : "moon")}</button>
      <button class="ibtn press" id="gear" aria-label="Sozlamalar">${ic("gear")}</button></header>
    <section class="pass press" id="pass" role="button" tabindex="0" aria-label="Reyting">
      <i class="sheen" aria-hidden="true"></i>
      <div class="pass-top"><span class="pass-chip">MULOQOT · KIUT</span><span class="pass-st">${esc(me.level || "Kuzatuvchi")}${m && m.active ? ` · ${esc(m.number)}` : ""}</span></div>
      <div class="pass-main">
        <div class="ring"><svg viewBox="0 0 108 108" aria-hidden="true"><circle class="trk" cx="54" cy="54" r="46"/><circle class="val" cx="54" cy="54" r="46" style="stroke-dasharray:${RING.toFixed(1)};stroke-dashoffset:${(RING * (1 - pct)).toFixed(1)}"/></svg>
          <div class="ring-c"><b><span data-count="${Math.round(pct * 100)}">0</span>%</b><small>davomat</small></div></div>
        <div class="pass-stats">
          <div><b data-count="${me.points}">0</b><small>jami ball</small></div>
          <div><b data-count="${me.rank}">0</b><small>o'rin</small></div>
          <div><b data-count="${me.month_points}">0</b><small>bu oy</small></div>
        </div>
      </div>
      <div class="pass-foot">${pct >= 2 / 3 && me.held ? "Faol a'zo talabi bajarilmoqda" : `Faol a'zo uchun 2/3 qatnashish kerak · ${me.went}/${me.held}`}</div>
    </section>
    <label class="search glass">${ic("search")}<input id="q" type="search" placeholder="Tadbir yoki savol qidirish…" aria-label="Qidirish"></label>
    <div id="searchRes"></div>
    <div id="homeMain">
      <div class="sec-h"><h2>Tadbirlar</h2><button data-go="events">Hammasi</button></div>
      ${events.length ? `<div class="hscroll">${events.map(eventCard).join("")}</div>` : `<div class="glass empty">${ic("inbox")}<div>Hozircha ochiq tadbir yo'q</div></div>`}
      <div class="sec-h"><h2>Haftalik reja</h2><button data-go="events">Tadbirlar</button></div>
      <section class="sheetcard glass">
        <h2>Bu hafta nima bor?</h2>
        <p>Kunni tanlang — o'sha kundagi tadbirlar shu yerda chiqadi</p>
        <div class="week">${days.map((d, i) => `<button class="day press ${i === S.daySel ? "on" : ""} ${events.some((e) => evDate(e) && sameDay(evDate(e), d)) ? "has" : ""}" data-day="${i}"><small>${WD[d.getDay()]}</small><b>${d.getDate()}</b></button>`).join("")}</div>
        <div class="dayev" id="dayev"></div>
        ${top.length ? `<div class="people">${top.map((r, i) => `<span style="background:${COLORS[i % COLORS.length]}" title="${esc(r.name)}">${esc(initials(r.name))}</span>`).join("")}</div>` : ""}
      </section>
      <div class="sec-h"><h2>Tezkor amallar</h2></div>
      <div class="tiles">
        <button class="tile press" data-act="card"><span class="ic">${ic("card")}</span><b>Guvohnoma</b><small>${m ? esc(m.number) : "A'zo bo'lgach beriladi"}</small></button>
        <button class="tile press" data-act="tickets"><span class="ic">${ic("ticket")}</span><b>Chiptalarim</b><small>QR orqali kirish</small></button>
        <button class="tile press" data-act="apply"><span class="ic">${ic("file")}</span><b>A'zo bo'lish</b><small>${me.application ? APP_ST[me.application.status]?.[0] || "" : "Ariza topshirish"}</small></button>
        <button class="tile press" data-act="appeal"><span class="ic">${ic("chat")}</span><b>Murojaat</b><small>Savol, taklif, shikoyat</small></button>
      </div>
    </div></div>`;
  setAvatar();
  countUp($("#view"));
  $("#pass").onclick = () => go("rating");
  const drawDay = () => {
    const d = days[S.daySel]; const list = events.filter((e) => evDate(e) && sameDay(evDate(e), d));
    $("#dayev").innerHTML = list.length ? list.map((e) => `<button class="row press" data-ev="${e.id}"><span class="ic">${ic("clock")}</span><span class="grow"><b>${esc(e.title)}</b><small>${esc(e.date_text || "")}${e.place ? " · " + esc(e.place) : ""}</small></span>${ic("chev", "chev")}</button>`).join("")
      : `<div class="empty" style="padding:10px 0 0">Bu kunda tadbir yo'q</div>`;
    $$("#dayev [data-ev]").forEach((b) => (b.onclick = () => openEvent(+b.dataset.ev)));
  };
  drawDay();
  $$(".day").forEach((b) => (b.onclick = () => { S.daySel = +b.dataset.day; $$(".day").forEach((x) => x.classList.toggle("on", x === b)); haptic(); drawDay(); }));
  $$("[data-ev]", $("#homeMain")).forEach((b) => (b.onclick = () => openEvent(+b.dataset.ev)));
  $$("[data-go]").forEach((b) => (b.onclick = () => go(b.dataset.go)));
  $("#gear").onclick = () => go("profile");
  $("#modeBtn").onclick = toggleMode;
  $$("[data-act]").forEach((b) => (b.onclick = () => ACTIONS[b.dataset.act]()));
  $("#q").oninput = safe(async (e) => {
    const q = e.target.value.trim().toLowerCase();
    $("#homeMain").hidden = !!q;
    if (!q) return ($("#searchRes").innerHTML = "");
    const info = S.info || (S.info = await get("/info", 600000));
    const ev = events.filter((x) => (x.title + " " + (x.place || "") + " " + (x.description || "")).toLowerCase().includes(q));
    const fq = info.faq.filter((x) => (x.q + " " + x.a).toLowerCase().includes(q));
    $("#searchRes").innerHTML = (ev.length || fq.length) ? `<div class="list">${ev.map((x) => `<button class="row press" data-ev="${x.id}"><span class="ic">${ic("ticket")}</span><span class="grow"><b>${esc(x.title)}</b><small>${esc(x.date_text || "Tadbir")}</small></span></button>`).join("")}
      ${fq.map((x) => `<details class="faq"><summary>${esc(x.q)}${ic("chev")}</summary><div class="rich">${x.a}</div></details>`).join("")}</div>` : `<div class="glass empty">Hech narsa topilmadi</div>`;
    $$("#searchRes [data-ev]").forEach((b) => (b.onclick = () => openEvent(+b.dataset.ev)));
  });
}

/* ---------------- TADBIRLAR ---------------- */
async function renderEvents() {
  S.evTab = S.evTab || "open";
  $("#view").innerHTML = `<div class="stagger"><header class="top"><div class="hello"><small>MULOQOT</small><h1>Tadbirlar</h1></div></header>
    <div class="seg" role="tablist"><button data-t="open">Ochiq</button><button data-t="tickets">Chiptalarim</button><button data-t="vol">Ko'ngillilik</button></div><div id="evbody"><div class="skel" style="height:140px"></div></div></div>`;
  $$(".seg button").forEach((b) => { b.classList.toggle("on", b.dataset.t === S.evTab); b.onclick = () => { S.evTab = b.dataset.t; haptic(); renderEvents(); }; });
  const body = $("#evbody");
  if (S.evTab === "open") {
    const events = S.events = await get("/events");
    body.innerHTML = events.length ? `<div class="list">${events.map((e, i) => `<button class="row press" data-ev="${e.id}"><span class="ic" style="color:${COLORS[i % 4]}">${ic(e.kind === "session" ? "users" : "star")}</span><span class="grow"><b>${esc(e.title)}</b><small>${esc(e.date_text || "")}${e.place ? " · " + esc(e.place) : ""}</small></span>${e.ticket ? `<span class="badge ok">Yozilgan</span>` : ic("chev", "chev")}</button>`).join("")}</div>`
      : `<div class="glass empty">${ic("inbox")}<div>Hozircha ochiq tadbir yo'q. Yangi tadbirlar haqida bot xabar beradi.</div></div>`;
    $$("[data-ev]", body).forEach((b) => (b.onclick = () => openEvent(+b.dataset.ev)));
  } else if (S.evTab === "tickets") {
    const tk = await get("/tickets");
    body.innerHTML = tk.length ? `<div class="list">${tk.map((t) => `<button class="row press" data-tk="${t.id}"><span class="ic">${ic("ticket")}</span><span class="grow"><b>${esc(t.title)}</b><small>${t.code} · ${esc(t.date_text || "")}</small></span><span class="badge ${t.status === "used" ? "ok" : "blue"}">${t.status === "used" ? "Keldingiz" : "Faol"}</span></button>`).join("")}</div>`
      : `<div class="glass empty">${ic("ticket")}<div>Hali chiptangiz yo'q. Tadbirga yozilsangiz, QR-chipta shu yerda chiqadi.</div></div>`;
    $$("[data-tk]", body).forEach((b) => (b.onclick = () => openTicket(+b.dataset.tk)));
  } else {
    const vol = await get("/volunteer");
    body.innerHTML = vol.length ? `<div class="list">${vol.map((v) => `<div class="row"><span class="ic">${ic("hand")}</span><span class="grow"><b>${esc(v.title)}</b><small>${esc(v.date_text || "")} · ${v.volunteers} ta ko'ngilli kerak</small></span>${v.applied ? `<span class="badge ok">Ariza berilgan</span>` : `<button class="btn press" style="min-height:40px;padding:0 14px" data-vol="${v.id}">Qo'shilish</button>`}</div>`).join("")}</div>`
      : `<div class="glass empty">${ic("hand")}<div>Hozircha ko'ngillilar kerak bo'lgan tadbir yo'q.</div></div>`;
    $$("[data-vol]", body).forEach((b) => (b.onclick = safe(async () => { b.disabled = true; await api(`/volunteer/${b.dataset.vol}`, { method: "POST" }); invalidate("/volunteer"); toast("Ariza yuborildi. Kengash siz bilan bog'lanadi."); renderEvents(); })));
  }
}

async function openEvent(id) {
  const ev = (S.events || []).find((e) => e.id === id) || (S.events = await get("/events")).find((e) => e.id === id);
  if (!ev) return toast("Tadbir topilmadi", false);
  const seats = ev.capacity ? `${ev.taken} / ${ev.capacity}` : `${ev.taken} (cheklanmagan)`;
  openSheet(`<span class="badge ${ev.kind === "session" ? "blue" : "warn"}">${ev.kind === "session" ? "Mashg'ulot" : "Tadbir"}</span>
    <h2 style="margin-top:10px">${esc(ev.title)}</h2>
    <div class="kv"><div><span>Sana</span><b>${esc(ev.date_text || "—")}</b></div><div><span>Joy</span><b>${esc(ev.place || "—")}</b></div><div><span>Yozilganlar</span><b>${seats}</b></div><div><span>Ball</span><b>+${ev.points}</b></div></div>
    ${ev.description ? `<div class="rich" style="margin-bottom:18px;white-space:pre-line">${esc(ev.description)}</div>` : ""}
    <div id="evAct"></div>`, (sh) => {
    const act = $("#evAct", sh);
    if (ev.ticket) {
      act.innerHTML = `<button class="btn primary w press" id="showTk">${ic("ticket")}Chiptamni ko'rish · ${ev.ticket.code}</button>`;
      $("#showTk").onclick = () => openTicket(ev.ticket.id);
    } else if (ev.active) {
      const full = ev.capacity && ev.taken >= ev.capacity;
      act.innerHTML = `<button class="btn primary w press" id="reg" ${full ? "disabled" : ""}>${full ? "Joylar to'lgan" : "Ro'yxatdan o'tish"}</button>`;
      $("#reg").onclick = safe(async () => {
        $("#reg").disabled = true; const tk = await api(`/events/${ev.id}/register`, { method: "POST" });
        toast("Siz yozildingiz! QR-chipta tayyor."); invalidate("/events", "/tickets"); S.events = null; openTicket(tk.id); if (S.tab !== "rating") render();
      });
    } else act.innerHTML = `<div class="note">Ro'yxatga olish yopilgan.</div>`;
  });
}

async function openTicket(id) {
  openSheet(`<h2>QR-chipta</h2><p class="sub">Kirishda shu QR-kodni ko'rsating.</p><div class="skel img" id="tkImg"></div><div id="tkAct" style="margin-top:14px"></div>`, safe(async (sh) => {
    const url = await api(`/tickets/${id}.png`, { blob: true }); S.blobs.push(url);
    $("#tkImg", sh).outerHTML = `<img class="img" src="${url}" alt="QR-chipta">`;
    const tks = await get("/tickets"); const tk = tks.find((t) => t.id === id);
    if (tk && tk.status === "active" && !tk.finished) {
      $("#tkAct", sh).innerHTML = `<button class="btn danger w press" id="tkCancel">Chiptani bekor qilish</button>`;
      $("#tkCancel").onclick = safe(async () => {
        if (!(await confirmBox("Chiptani bekor qilasizmi? Joyingiz boshqaga beriladi."))) return;
        await api(`/tickets/${id}/cancel`, { method: "POST" }); toast("Chipta bekor qilindi"); invalidate("/events", "/tickets"); S.events = null; closeSheet(); render();
      });
    }
  }));
}

function confirmBox(text) {
  return new Promise((ok) => { try { TG.showConfirm(text, ok); } catch { ok(confirm(text)); } });
}

/* ---------------- REYTING ---------------- */
async function renderRating() {
  S.rtTab = S.rtTab || "month";
  const r = await get("/rating"); const me = S.me;
  const rows = r[S.rtTab];
  $("#view").innerHTML = `<div class="stagger"><header class="top"><div class="hello"><small>MULOQOT</small><h1>Reyting</h1></div></header>
    <section class="glass stat"><div><b>${r.mine}</b><small>jami ball</small></div><div><b>${r.rank}</b><small>o'rin</small></div><div><b>${me.went}/${me.held}</b><small>davomat</small></div></section>
    <div class="seg" style="margin-top:16px"><button data-t="month">Shu oy</button><button data-t="total">Umumiy</button></div>
    ${rows.length ? `<div class="list">${rows.map((x, i) => `<div class="rank ${x.me ? "me" : ""}"><span class="n ${i < 3 ? "g" + (i + 1) : ""}">${i + 1}</span><span class="grow"><span data-raw>${esc(x.name)}</span>${x.me ? " (siz)" : ""}</span><b>${x.total}</b></div>`).join("")}</div>`
      : `<div class="glass empty">${ic("star")}<div>Hali ball berilmagan. Tadbirlarda qatnashib ball to'plang.</div></div>`}
    <p style="color:var(--faint);font-size:12.5px;margin:16px 4px">Ball: mashg'ulot 1 · ko'ngilli yordam 2 · tahliliy matn 3 · debat/MUN 3 · loyihaga mas'ul 5</p></div>`;
  $$(".seg button").forEach((b) => { b.classList.toggle("on", b.dataset.t === S.rtTab); b.onclick = () => { S.rtTab = b.dataset.t; haptic(); renderRating(); }; });
}

/* ---------------- PROFIL ---------------- */
async function renderProfile() {
  const me = S.me; const u = me.user; const m = me.member;
  $("#view").innerHTML = `<div class="stagger">
    <header class="top"><div class="ava">${me.has_photo ? `<img src="" alt="" id="avaImg">` : `<span>${esc(initials(u.full_name))}</span>`}</div>
      <div class="hello"><small>${m && m.active ? `A'zo · ${esc(m.number)}` : "Ishtirokchi"}</small><h1 data-raw>${esc(u.full_name || "")}</h1></div></header>
    <div class="kv glass" style="margin-top:0"><div><span>Yo'nalish</span><b>${esc(u.direction || "—")}</b></div><div><span>Kurs · guruh</span><b>${COURSE(u.course)} · ${esc(u.group_name || "—")}</b></div>
      <div><span>Talaba ID</span><b>${esc(u.student_id || "—")}</b></div><div><span>Telefon</span><b>${esc(u.phone || "—")}</b></div>
      ${m ? `<div><span>Bo'lim</span><b>${esc(m.section)}</b></div><div><span>A'zolik yili</span><b>${esc(m.year)}${m.expired ? " (yangilash kerak)" : ""}</b></div>` : ""}</div>
    <div class="list">
      ${row("edit", "Profilni tahrirlash", "Ism, yo'nalish, kurs, guruh, ID", "edit")}
      ${row("card", "Guvohnoma", m ? "Elektron a'zolik guvohnomasi" : "A'zo bo'lgach beriladi", "card")}
      ${row("file", "A'zolik arizasi", me.application ? `#${me.application.id} · ${APP_ST[me.application.status]?.[0] || ""}` : "Klubga a'zo bo'lish", "apply")}
      ${row("chat", "Murojaatlarim", "Savol, taklif, shikoyat va javoblar", "appeals")}
      ${row("info", "Klub haqida", "Maqsad, yo'nalishlar, boshqaruv", "about")}
      ${row("help", "Savol-javob", "Ko'p beriladigan savollar", "faq")}
      ${row("doc", "Hujjatlar", "Ustav, nizom, blanka, taqdimot", "docs")}
      ${row("globe", "Til", (me.langs.find((l) => l.key === me.lang) || {}).label || "", "lang")}
      ${row("trash", "Ma'lumotlarimni o'chirish", "Rozilikni qaytarib olish", "delete")}
    </div>
    <p style="color:var(--faint);font-size:12.5px;text-align:center;margin:20px 0 0">Telefon raqami va suratni botdagi «Sozlamalar» orqali o'zgartirasiz.</p></div>`;
  setAvatar();
  $$("[data-act]").forEach((b) => (b.onclick = () => ACTIONS[b.dataset.act]()));
}
const row = (icn, title, sub, act) => `<button class="row press" data-act="${act}"><span class="ic">${ic(icn)}</span><span class="grow"><b>${title}</b><small>${esc(sub)}</small></span>${ic("chev", "chev")}</button>`;

/* ---------------- AMALLAR ---------------- */
const ACTIONS = {
  plus() {
    openSheet(`<h2>Yangi</h2><p class="sub">Nima qilmoqchisiz?</p><div class="list">
      ${row("file", "A'zo bo'lish", "Elektron a'zolik blankasi", "apply")}${row("chat", "Murojaat yuborish", "Savol, taklif yoki shikoyat", "appeal")}
      ${row("ticket", "Tadbirga yozilish", "Ochiq tadbirlar ro'yxati", "goEvents")}${row("hand", "Ko'ngilli bo'lish", "Tadbirlarda yordam berish", "goVol")}</div>`,
    (sh) => $$("[data-act]", sh).forEach((b) => (b.onclick = () => ACTIONS[b.dataset.act]())));
  },
  goEvents() { closeSheet(); S.evTab = "open"; go("events"); },
  goVol() { closeSheet(); S.evTab = "vol"; go("events"); },
  tickets() { S.evTab = "tickets"; go("events"); },
  card: safe(async () => {
    if (!S.me.member) return toast("Guvohnoma a'zolik arizangiz qabul qilingach beriladi", false);
    openSheet(`<h2>Guvohnoma</h2><p class="sub">${esc(S.me.member.number)} · ${esc(S.me.member.year)}</p><div class="skel img" id="cardImg" style="min-height:420px"></div>`, safe(async (sh) => {
      const url = await api("/card.png", { blob: true }); S.blobs.push(url); $("#cardImg", sh).outerHTML = `<img class="img" src="${url}" alt="A'zolik guvohnomasi">`;
    }));
  }),
  edit() {
    const u = S.me.user;
    openSheet(`<h2>Profilni tahrirlash</h2><p class="sub">O'zgarishlar bot va saytda ham yangilanadi.</p>
      <label class="field"><span>Ism-familiya</span><input class="inp" id="fName" maxlength="80" value="${esc(u.full_name || "")}"></label>
      <label class="field"><span>Yo'nalish</span><select class="inp" id="fDir">${S.me.directions.map((d) => `<option ${d === u.direction ? "selected" : ""}>${esc(d)}</option>`).join("")}</select></label>
      <div class="field"><span>Kurs</span><div class="opts" id="fCourse">${["1", "2", "3", "4", "M"].map((c) => `<button type="button" class="opt ${c === u.course ? "on" : ""}" data-v="${c}">${c === "M" ? "Magistratura" : c + "-kurs"}</button>`).join("")}</div></div>
      <label class="field"><span>Guruh</span><input class="inp" id="fGroup" maxlength="20" value="${esc(u.group_name || "")}"></label>
      <label class="field"><span>Talaba ID</span><input class="inp" id="fSid" maxlength="30" value="${esc(u.student_id || "")}"></label>
      <button class="btn primary w press" id="fSave">Saqlash</button>`, (sh) => {
      let course = u.course;
      $$("#fCourse .opt", sh).forEach((b) => (b.onclick = () => { course = b.dataset.v; $$("#fCourse .opt", sh).forEach((x) => x.classList.toggle("on", x === b)); haptic(); }));
      $("#fSave", sh).onclick = safe(async () => {
        await api("/profile", { method: "PUT", body: { full_name: $("#fName").value, direction: $("#fDir").value, course, group_name: $("#fGroup").value, student_id: $("#fSid").value } });
        toast("Profil saqlandi"); S.me = await api("/me"); closeSheet(); render();
      });
    });
  },
  appeal() {
    let kind = "question";
    openSheet(`<h2>Murojaat</h2><p class="sub">Kengash ko'rib chiqadi va javob shu yerda hamda botda keladi.</p>
      <div class="seg" id="aKind"><button data-k="question" class="on">Savol</button><button data-k="suggestion">Taklif</button><button data-k="complaint">Shikoyat</button></div>
      <div class="note" id="aNote" hidden>Shikoyat Etika va intizom komissiyasiga yuboriladi va maxfiy saqlanadi.</div>
      <label class="field"><span>Matn</span><textarea class="inp" id="aText" maxlength="2000" placeholder="Murojaatingizni batafsil yozing (kamida 10 belgi)"></textarea><div class="counter" id="aCnt">0 / 2000</div></label>
      <button class="btn primary w press" id="aSend">${ic("send")}Yuborish</button>
      <p style="color:var(--faint);font-size:12.5px;margin:12px 2px 0">Fayl yoki rasm biriktirish kerak bo'lsa, murojaatni botdan yuboring.</p>`, (sh) => {
      $$("#aKind button", sh).forEach((b) => (b.onclick = () => { kind = b.dataset.k; $$("#aKind button", sh).forEach((x) => x.classList.toggle("on", x === b)); $("#aNote", sh).hidden = kind !== "complaint"; haptic(); }));
      $("#aText", sh).oninput = (e) => ($("#aCnt", sh).textContent = `${e.target.value.length} / 2000`);
      $("#aSend", sh).onclick = safe(async () => {
        const text = $("#aText", sh).value.trim();
        if (text.length < 10) return toast("Kamida 10 belgi yozing", false);
        $("#aSend", sh).disabled = true;
        const r = await api("/appeals", { method: "POST", body: { kind, text } });
        toast(`Murojaat #${r.id} yuborildi`); closeSheet();
      });
    });
  },
  appeals: safe(async () => {
    const list = await api("/appeals");
    openSheet(`<h2>Murojaatlarim</h2><p class="sub">Javoblar shu yerda va botda keladi.</p>${list.length ? `<div class="list">${list.map((a) => `<button class="row press" data-ap="${a.id}"><span class="ic">${ic("chat")}</span><span class="grow"><b>#${a.id} · ${KIND[a.kind] || a.kind}</b><small>${esc((a.messages[0] || {}).text || "")}</small></span><span class="badge ${AP_ST[a.status]?.[1] || ""}">${AP_ST[a.status]?.[0] || a.status}</span></button>`).join("")}</div>` : `<div class="empty">${ic("inbox")}<div>Hali murojaat yubormagansiz</div></div>`}
      <button class="btn primary w press" id="newAp" style="margin-top:16px">Yangi murojaat</button>`, (sh) => {
      $("#newAp", sh).onclick = () => ACTIONS.appeal();
      $$("[data-ap]", sh).forEach((b) => (b.onclick = () => openAppeal(list.find((a) => a.id === +b.dataset.ap))));
    });
  }),
  apply: safe(async () => {
    const f = await api("/form");
    if (f.blocked) return openSheet(`<h2>A'zolik arizasi</h2><div class="note" style="margin-top:12px">${esc(f.blocked)}</div>`);
    applyWizard(f);
  }),
  about: safe(async () => {
    const info = S.info || (S.info = await get("/info", 600000));
    openSheet(`<h2>Klub haqida</h2><p class="sub">«${esc(info.motto)}»</p><div class="list">${info.about.map((a, i) => `<button class="row press" data-ab="${i}"><span class="ic">${ic("info")}</span><span class="grow"><b>${esc(a.title)}</b></span>${ic("chev", "chev")}</button>`).join("")}</div>`, (sh) =>
      $$("[data-ab]", sh).forEach((b) => (b.onclick = () => { const a = info.about[+b.dataset.ab]; openSheet(`<h2>${esc(a.title)}</h2><div class="rich" style="margin-top:12px">${a.html}</div>`); })));
  }),
  faq: safe(async () => {
    const info = S.info || (S.info = await get("/info", 600000));
    openSheet(`<h2>Savol-javob</h2><p class="sub">Ko'p beriladigan savollar</p>${info.faq.length ? `<div class="stack">${info.faq.map((x) => `<details class="faq"><summary>${esc(x.q)}${ic("chev")}</summary><div class="rich">${x.a}</div></details>`).join("")}</div>` : `<div class="empty">Hozircha savollar qo'shilmagan</div>`}
      <button class="btn w press" id="askQ" style="margin-top:16px">Savolingiz bormi? Murojaat yuboring</button>`, (sh) => ($("#askQ", sh).onclick = () => ACTIONS.appeal()));
  }),
  docs: safe(async () => {
    const info = S.info || (S.info = await get("/info", 600000));
    openSheet(`<h2>Hujjatlar</h2><p class="sub">Klubning rasmiy hujjatlari</p>${info.docs.length ? `<div class="list">${info.docs.map((d) => `<button class="row press" data-doc="${d.url}"><span class="ic">${ic("doc")}</span><span class="grow"><b>${esc(d.name)}</b><small>Yuklab olish</small></span>${ic("chev", "chev")}</button>`).join("")}</div>` : `<div class="empty">Hujjatlar topilmadi</div>`}`, (sh) =>
      $$("[data-doc]", sh).forEach((b) => (b.onclick = () => openLink(location.origin + b.dataset.doc))));
  }),
  lang() {
    openSheet(`<h2>Til</h2><p class="sub">Bot xabarlari, savollar va «Klub haqida» shu tilda bo'ladi.</p><div class="list">${S.me.langs.map((l) => `<button class="row press" data-l="${l.key}"><span class="grow"><b>${esc(l.label)}</b></span>${l.key === S.me.lang ? ic("check") : ""}</button>`).join("")}</div>`, (sh) =>
      $$("[data-l]", sh).forEach((b) => (b.onclick = safe(async () => { await api("/lang", { method: "PUT", body: { lang: b.dataset.l } }); S.me = await api("/me"); S.info = null; invalidate("/info"); toast("Til o'zgartirildi"); closeSheet(); render(); }))));
  },
  delete: safe(async () => {
    if (!(await confirmBox("Roziligingizni qaytarib olib, barcha ma'lumotlaringizni o'chirishni so'raysizmi? Kengash 5 ish kuni ichida o'chiradi."))) return;
    const r = await api("/delete", { method: "POST" }); toast(r.message || "So'rov yuborildi");
  }),
};

function openAppeal(a) {
  openSheet(`<h2>#${a.id} · ${KIND[a.kind] || ""}</h2><span class="badge ${AP_ST[a.status]?.[1] || ""}">${AP_ST[a.status]?.[0] || a.status}</span>
    <div class="thread">${a.messages.map((m) => `<div class="msg ${m.from === "user" ? "user" : "club"}" data-raw>${m.text ? esc(m.text) : "(fayl)"}<time>${m.from === "user" ? "Siz" : "Klub"} · ${fmtDate(m.at)}</time></div>`).join("")}</div>
    ${a.status === "closed" ? `<div class="note">Murojaat yopilgan.</div>` : `<label class="field"><span>Javob yozish</span><textarea class="inp" id="rText" maxlength="2000" style="min-height:90px"></textarea></label><button class="btn primary w press" id="rSend">${ic("send")}Yuborish</button>`}`, (sh) => {
    const b = $("#rSend", sh);
    if (b) b.onclick = safe(async () => {
      const text = $("#rText", sh).value.trim(); if (!text) return toast("Javob matnini yozing", false);
      b.disabled = true; await api(`/appeals/${a.id}/reply`, { method: "POST", body: { text } }); toast("Javob yuborildi"); closeSheet();
    });
  });
}

/* ---------------- A'ZOLIK ARIZASI (bosqichma-bosqich) ---------------- */
function applyWizard(f) {
  const ans = { ...(f.answers || {}) }; let appType = ans.app_type || (f.renew_default ? "renew" : "new");
  const steps = f.steps; let i = -1;
  const label = (st) => (st.options.length ? st.options : []);
  const draw = () => {
    const sh = $("#sheet");
    if (i === -1) {
      sh.innerHTML = `<h2>A'zolik arizasi</h2><p class="sub">${steps.length} ta savol · taxminan 5 daqiqa</p>
        ${f.returned_reason ? `<div class="note">Arizangiz qaytarilgan: ${esc(f.returned_reason)}. Avvalgi javoblaringiz saqlangan — kerakli joyini tuzating.</div>` : ""}
        <div class="field"><span>Ariza turi</span><div class="opts">${f.types.map((t) => `<button type="button" class="opt ${t.key === appType ? "on" : ""}" data-t="${t.key}">${esc(t.label)}</button>`).join("")}</div></div>
        <button class="btn primary w press" id="wNext">Boshlash</button>`;
      $$("[data-t]", sh).forEach((b) => (b.onclick = () => { appType = b.dataset.t; $$("[data-t]", sh).forEach((x) => x.classList.toggle("on", x === b)); haptic(); }));
      $("#wNext").onclick = () => { i = 0; draw(); };
      return;
    }
    if (i >= steps.length) {
      const filled = steps.filter((s) => ans[s.field] && ans[s.field].length !== 0).length;
      sh.innerHTML = `<h2>Tekshirish</h2><p class="sub">${filled} / ${steps.length} savolga javob berildi</p>
        <div class="list">${steps.map((s, k) => `<button class="row press" data-k="${k}"><span class="grow"><b>${k + 1}. ${esc(s.question.replace(/<[^>]+>/g, " ").slice(0, 60))}</b><small>${esc(showAns(s, ans[s.field]))}</small></span>${ic("edit")}</button>`).join("")}</div>
        <div class="btnrow" style="margin-top:16px"><button class="btn press" id="wBack">Orqaga</button><button class="btn primary press" id="wSend">Yuborish</button></div>`;
      $$("[data-k]", sh).forEach((b) => (b.onclick = () => { i = +b.dataset.k; draw(); }));
      $("#wBack").onclick = () => { i = steps.length - 1; draw(); };
      $("#wSend").onclick = safe(async () => {
        $("#wSend").disabled = true;
        try { const r = await api("/apply", { method: "POST", body: { app_type: appType, answers: ans } });
          toast(`Ariza #${r.id} yuborildi`); S.me = await api("/me"); closeSheet(); render();
        } finally { const b = $("#wSend"); if (b) b.disabled = false; }
      });
      sh.scrollTop = 0; return;
    }
    const st = steps[i]; const v = ans[st.field];
    let input = "";
    if (st.kind === "one") input = `<div class="opts">${label(st).map((o) => `<button type="button" class="opt ${v === o.key ? "on" : ""}" data-o="${o.key}">${esc(o.label)}</button>`).join("")}</div>`;
    else if (st.kind === "many") input = `<div class="opts">${label(st).map((o) => `<button type="button" class="opt ${(v || []).includes(o.key) ? "on" : ""}" data-m="${o.key}">${esc(o.label)}</button>`).join("")}</div>`;
    else if (st.kind === "yesno") input = `<div class="opts"><button type="button" class="opt ${v === "yes" ? "on" : ""}" data-o="yes">Ha</button><button type="button" class="opt ${v === "no" ? "on" : ""}" data-o="no">Yo'q</button></div>`;
    else if (st.kind === "rules") input = `<button type="button" class="opt ${v === "yes" ? "on" : ""}" data-o="yes" style="width:100%">Barcha qoidalarga roziman</button>`;
    else input = `<textarea class="inp" id="wText" maxlength="${st.kind === "motivation" ? 1500 : 1000}" ${st.kind === "email" ? 'inputmode="email" style="min-height:50px"' : ""}>${esc(v || "")}</textarea>`;
    sh.innerHTML = `<div class="progress"><i style="width:${((i + 1) / steps.length) * 100}%"></i></div>
      <p class="sub">${i + 1} / ${steps.length}${st.optional ? " · ixtiyoriy" : ""}</p><div class="qtext rich">${st.question}</div>${input}
      <div class="btnrow" style="margin-top:18px"><button class="btn press" id="wBack">Orqaga</button>${st.optional ? `<button class="btn press" id="wSkip">O'tkazish</button>` : ""}<button class="btn primary press" id="wNext">Keyingi</button></div>`;
    sh.scrollTop = 0;
    $$("[data-o]", sh).forEach((b) => (b.onclick = () => { ans[st.field] = b.dataset.o; haptic(); i++; draw(); }));
    $$("[data-m]", sh).forEach((b) => (b.onclick = () => { const set = new Set(ans[st.field] || []); set.has(b.dataset.m) ? set.delete(b.dataset.m) : set.add(b.dataset.m); ans[st.field] = [...set]; b.classList.toggle("on"); haptic(); }));
    $("#wBack").onclick = () => { saveText(); i--; draw(); };
    const sk = $("#wSkip"); if (sk) sk.onclick = () => { ans[st.field] = null; i++; draw(); };
    $("#wNext").onclick = () => {
      saveText(); const val = ans[st.field];
      const err = validate(st, val); if (err) return toast(err, false);
      i++; draw();
    };
    function saveText() { const t = $("#wText"); if (t) ans[st.field] = t.value.trim(); }
  };
  openSheet("", () => draw());
}
function validate(st, v) {
  const empty = v == null || v === "" || (Array.isArray(v) && !v.length);
  if (empty) return st.optional ? "" : "Bu savolga javob bering";
  if (st.kind === "email" && !/^[\w.+-]+@[\w-]+(\.[\w-]+)+$/.test(v)) return "Email noto'g'ri";
  if (st.kind === "motivation" && (v.length < 20 || v.length > 1500)) return "Javob 20–1500 belgi bo'lsin";
  if (st.kind === "text" && (v.length < 2 || v.length > 1000)) return "Javob 2–1000 belgi bo'lsin";
  return "";
}
function showAns(st, v) {
  if (v == null || v === "" || (Array.isArray(v) && !v.length)) return "—";
  if (st.kind === "yesno" || st.kind === "rules") return v === "yes" ? "Ha" : "Yo'q";
  if (st.options.length) { const m = Object.fromEntries(st.options.map((o) => [o.key, o.label])); return (Array.isArray(v) ? v : [v]).map((x) => m[x] || x).join(", "); }
  return String(v);
}

/* ---------------- yo'naltirish ---------------- */
const VIEWS = { home: renderHome, events: renderEvents, rating: renderRating, profile: renderProfile };
function go(tab) {
  if (tab === "plus") return ACTIONS.plus();
  S.tab = tab; haptic("soft");
  $$("#tabbar [data-tab]").forEach((b) => b.classList.toggle("on", b.dataset.tab === tab));
  moveInd(tab);
  window.scrollTo(0, 0); render();
}
const render = safe(async () => { await VIEWS[S.tab](); });
/* pastki menyu: faol bo'lim ikonkasi yashil shisha sharga ko'tariladi, shar va o'yiq birga sirpanadi */
function moveInd(tab) {
  const btns = $$("#tabbar [data-tab]"), i = btns.findIndex((b) => b.dataset.tab === tab), orb = $("#tabInd");
  if (i < 0 || !orb) return;
  $("#tabbar").style.setProperty("--i", i);
  orb.innerHTML = btns[i].querySelector("svg").outerHTML;
  orb.classList.remove("bump"); void orb.offsetWidth; orb.classList.add("bump");
}

/* tablar (.seg): ostidagi ko'k shisha «pill» faol tabga sirpanadi — qayta chizilganda ham oldingi joyidan */
const SEG_LAST = {};
function segSync(seg) {
  const bs = $$(":scope > button", seg); if (!bs.length) return;
  const key = bs.map((b) => b.dataset.t || b.dataset.k || b.textContent).join("|");
  const k = Math.max(0, bs.findIndex((b) => b.classList.contains("on")));
  seg.style.setProperty("--n", bs.length);
  let ind = $(":scope > .seg-ind", seg);
  if (!ind) {
    ind = document.createElement("i"); ind.className = "seg-ind"; ind.setAttribute("aria-hidden", "true"); seg.prepend(ind);
    ind.style.transition = "none"; ind.style.setProperty("--k", SEG_LAST[key] ?? k); void ind.offsetWidth; ind.style.transition = "";
  }
  if (ind.style.getPropertyValue("--k") !== String(k)) ind.style.setProperty("--k", k);
  SEG_LAST[key] = k;
}
new MutationObserver(() => $$(".seg").forEach(segSync))
  .observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ["class"] });
$$("#tabbar [data-tab]").forEach((b) => (b.onclick = () => go(b.dataset.tab)));

(async function start() {
  try { TG.ready(); TG.expand(); applyTheme(CUR_THEME, false); } catch {}
  $("#view").innerHTML = `<div class="splash"><div class="splash-logo"><img src="/static/logo.png" alt=""></div><b>MULOQOT</b></div>`;
  try {
    S.me = await api("/me");
  } catch (e) {
    return gate({ links: { bot: "https://t.me/KIUT_muloqotbot" } });
  }
  if (!S.me.registered) return gate(S.me);
  $("#tabbar").hidden = false; moveInd("home");
  await render();
  (window.requestIdleCallback || setTimeout)(prefetch, { timeout: 1500 });   // boshqa tablar oldindan yuklanadi
})();
