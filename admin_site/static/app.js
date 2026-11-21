/* MULOQOT admin panel — bitta sahifali ilova (vanilla JS + Chart.js) */
"use strict";

const M = window.MLQ || { labels: {}, directions: [], sections: {}, levels: {} };
/* a'zolik darajasi: qo'lda (yetakchi/ekspert/faxriy) yoki davomatdan (nomzod/faol) */
const levelName = (s) => s.level_name || (M.levels || {})[s.member_level] || "A'zo";
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const fmtN = (n) => Number(n || 0).toLocaleString("en-US").replace(/,/g, " ");
const MONTHS = ["yan", "fev", "mar", "apr", "may", "iyn", "iyl", "avg", "sen", "okt", "noy", "dek"];
const parseD = (s) => (s ? new Date(String(s).replace(" ", "T")) : null);
const fmtDate = (s, time = false) => {
  const d = parseD(s); if (!d || isNaN(d)) return "—";
  const base = `${d.getDate()} ${MONTHS[d.getMonth()]} ${d.getFullYear()}`;
  return time ? `${base}, ${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}` : base;
};
const ago = (s) => {
  const d = parseD(s); if (!d) return "—";
  const m = Math.round((Date.now() - d) / 60000);
  if (m < 1) return "hozirgina";
  if (m < 60) return `${m} daq oldin`;
  if (m < 1440) return `${Math.round(m / 60)} soat oldin`;
  const days = Math.round(m / 1440);
  if (days === 1) return "kecha";
  if (days < 30) return `${days} kun oldin`;
  return fmtDate(s);
};
const isoLocal = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
const today = () => isoLocal(new Date());
const daysAgo = (n) => isoLocal(new Date(Date.now() - n * 86400000));
const cssVar = (n) => getComputedStyle(document.documentElement).getPropertyValue(n).trim();

/* ---------------- ikonlar ---------------- */
const ICONS = {
  users: '<circle cx="9" cy="8" r="4"/><path d="M2 21a7 7 0 0 1 14 0"/><path d="M16 4a4 4 0 0 1 0 8M22 21a7 7 0 0 0-4-6.3"/>',
  userPlus: '<circle cx="9" cy="8" r="4"/><path d="M2 21a7 7 0 0 1 14 0M19 8v6M16 11h6"/>',
  badge: '<rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="9" cy="11" r="2.5"/><path d="M5.5 16.5a4 4 0 0 1 7 0M15 10h3M15 13h3"/>',
  file: '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5M9 13h6M9 17h4"/>',
  chat: '<path d="M21 12a8 8 0 0 1-11.6 7.1L4 21l1.9-5.4A8 8 0 1 1 21 12z"/>',
  cal: '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
  ticket: '<path d="M3 8a2 2 0 0 0 2-2h14a2 2 0 0 0 2 2v2a2 2 0 0 0 0 4v2a2 2 0 0 0-2 2H5a2 2 0 0 0-2-2v-2a2 2 0 0 0 0-4z"/><path d="M13 6v2M13 11v2M13 16v2"/>',
  pulse: '<path d="M3 12h4l3 8 4-16 3 8h4"/>',
  star: '<path d="m12 3 2.8 5.7 6.2.9-4.5 4.4 1 6.2L12 17.3 6.5 20.2l1-6.2L3 9.6l6.2-.9z"/>',
  camOff: '<path d="M3 3l18 18M9 5h6l2 2h2a2 2 0 0 1 2 2v8M17 19H5a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2"/><path d="M9.5 10.5a3 3 0 0 0 4 4"/>',
  phone: '<path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2"/>',
  send: '<path d="m22 2-7 20-4-9-9-4z"/><path d="M22 2 11 13"/>',
  check: '<path d="m5 12 5 5L20 7"/>',
  x: '<path d="M18 6 6 18M6 6l12 12"/>',
  copy: '<rect x="9" y="9" width="12" height="12" rx="2"/><path d="M5 15V5a2 2 0 0 1 2-2h10"/>',
  dl: '<path d="M12 3v12M7 10l5 5 5-5M5 21h14"/>',
  grid: '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
  rows: '<path d="M3 6h18M3 12h18M3 18h18"/>',
  search: '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
  chev: '<path d="m6 9 6 6 6-6"/>',
  pin: '<path d="M12 21s-7-6.2-7-12a7 7 0 0 1 14 0c0 5.8-7 12-7 12z"/><circle cx="12" cy="9" r="2.5"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  award: '<circle cx="12" cy="9" r="6"/><path d="M8.5 14 7 22l5-3 5 3-1.5-8"/>',
  alert: '<path d="M12 3 2 21h20z"/><path d="M12 10v5M12 18h.01"/>',
  inbox: '<path d="M22 12h-6l-2 3h-4l-2-3H2"/><path d="M5.5 5h13L22 12v6a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2v-6z"/>',
  filterX: '<path d="M3 4h18l-7 8v6l-4 2v-8z"/><path d="m16 16 5 5M21 16l-5 5"/>',
  door: '<path d="M10 17l5-5-5-5M15 12H3M21 3v18"/>',
  shield: '<path d="M12 3 4 6v6c0 5 3.5 8 8 9 4.5-1 8-4 8-9V6z"/>',
};
const ic = (n, cls = "") => `<svg viewBox="0 0 24 24" class="${cls}">${ICONS[n] || ""}</svg>`;

/* ---------------- lug'atlar ---------------- */
const ST = {
  member: ["A'zo", "ok"], applicant: ["Ariza ko'rilmoqda", "warn"], registered: ["Ro'yxatdan o'tgan", "info"], guest: ["Ro'yxatdan o'tmagan", "mute"],
};
const APP_ST = { pending: ["Kutilmoqda", "warn"], returned: ["Qaytarilgan", "info"], accepted: ["Qabul qilingan", "ok"], rejected: ["Rad etilgan", "bad"] };
const AP_KIND = { question: ["Savol", "info", "chat"], suggestion: ["Taklif", "ok", "star"], complaint: ["Shikoyat", "bad", "alert"] };
const AP_ST = { new: ["Yangi", "warn"], in_review: ["Ko'rib chiqilmoqda", "info"], answered: ["Javob berilgan", "ok"], closed: ["Yopilgan", "mute"] };
const TK_ST = { active: ["Faol chipta", "info"], used: ["Keldi", "ok"], cancelled: ["Bekor qilingan", "mute"] };
const LANG = { uz: "O'zbekcha", ru: "Русский", en: "English", ko: "한국어" };
const KIND = { command: "Buyruq", button: "Menyu tugmasi", text: "Matn xabar", photo: "Surat", callback: "Inline tugma", contact: "Kontakt", document: "Fayl", voice: "Ovozli", video: "Video", sticker: "Stiker", other: "Boshqa" };
const CB = {
  lang: "Til tanlash", dir: "Yo'nalish tanlash", course: "Kurs tanlash", agree: "Rozilik berish", evreg: "Tadbirga yozilish",
  tkcancel: "Chiptani bekor qilish", about: "Klub haqida", faqlang: "FAQ tili", faq: "FAQ savoli", pf: "Profilni tahrirlash",
  app_submit: "Arizani yuborish", app_edit: "Arizani tahrirlash", appedit: "Javobni tahrirlash", rules_ok: "Qoidalarga rozilik",
  vol: "Ko'ngillilik", akind: "Murojaat turi", ureply: "Murojaatga javob", my_card: "Guvohnoma", delete_data: "Ma'lumot o'chirish",
  ap_ok: "Arizani qabul qilish (admin)", ap_no: "Arizani rad etish (admin)", ap_ret: "Arizani qaytarish (admin)", a_reply: "Admin javobi",
  cancel: "Bekor qilish", skip: "O'tkazib yuborish", m: "Ko'p tanlov", one: "Bitta tanlov", manydone: "Tanlovni tugatish",
};
const actLabel = (k) => M.labels[k] || CB[k] || k || "—";
const course = (c) => (c === "M" ? "Magistratura" : c ? `${c}-kurs` : "—");
const badge = (pair, extra = "") => (pair ? `<span class="badge ${pair[1]}">${esc(pair[0])}${extra}</span>` : "");
const initials = (n) => (n || "?").split(/\s+/).filter(Boolean).slice(0, 2).map((w) => w[0]).join("").toUpperCase();
const AV_COLORS = ["#5b6cff", "#0ea5a4", "#d97706", "#db2777", "#7c3aed", "#0891b2", "#16a34a", "#c2410c"];
const avColor = (id) => AV_COLORS[Math.abs(Number(id) || 0) % AV_COLORS.length];
const avatar = (r, cls = "") => `<span class="avatar ${cls}" style="background:${avColor(r.user_id)}">${r.has_photo
  ? `<img loading="lazy" src="/api/photo/${r.user_id}" alt="" onerror="this.remove()">` : ""}<span>${esc(initials(r.full_name))}</span></span>`;

/* ---------------- holat va API ---------------- */
const S = { cache: {}, charts: [], page: null, loadedAt: null };
async function api(path, fresh = false) {
  if (!fresh && S.cache[path]) return S.cache[path];
  const r = await fetch(path, { credentials: "same-origin" });
  if (r.status === 401) { location.href = "/"; throw new Error("auth"); }
  if (!r.ok) throw new Error(`${path}: ${r.status}`);
  const data = await r.json();
  S.cache[path] = data;
  return data;
}
async function send(method, path, body) {
  const r = await fetch(path, {
    method, credentials: "same-origin",
    headers: { "Content-Type": "application/json", "X-MLQ": "1" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (r.status === 401) { location.href = "/"; throw new Error("auth"); }
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.detail || `Xato: ${r.status}`);
  Object.keys(S.cache).filter((k) => k.startsWith("/api/site")).forEach((k) => delete S.cache[k]);
  return data;
}
const readFile = (file) => new Promise((ok, bad) => {
  if (file.size > 8 * 1024 * 1024) return bad(new Error("Rasm 8 MB dan katta"));
  const fr = new FileReader(); fr.onload = () => ok(fr.result); fr.onerror = () => bad(new Error("Faylni o'qib bo'lmadi")); fr.readAsDataURL(file);
});
function toast(msg) {
  const t = $("#toast"); t.textContent = msg; t.classList.add("on");
  clearTimeout(toast._t); toast._t = setTimeout(() => t.classList.remove("on"), 1800);
}
async function copy(text) {
  try { await navigator.clipboard.writeText(text); toast("Nusxa olindi: " + text); } catch { toast("Nusxa olinmadi"); }
}
document.addEventListener("click", (e) => { const b = e.target.closest("[data-copy]"); if (b) copy(b.dataset.copy); });

/* ---------------- matn qidiruvi (lotin/kirill, apostroflarsiz) ---------------- */
const CYR = { а: "a", б: "b", в: "v", г: "g", д: "d", е: "e", ё: "yo", ж: "j", з: "z", и: "i", й: "y", к: "k", л: "l", м: "m", н: "n", о: "o", п: "p", р: "r", с: "s", т: "t", у: "u", ф: "f", х: "x", ц: "ts", ч: "ch", ш: "sh", щ: "sh", ъ: "", ы: "i", ь: "", э: "e", ю: "yu", я: "ya", ў: "o", қ: "q", ғ: "g", ҳ: "h" };
const norm = (s) => String(s ?? "").toLowerCase().replace(/[ʻʼ'`’‘]/g, "").replace(/[а-яёўқғҳ]/g, (c) => CYR[c] ?? c);
const tokens = (q) => norm(q).split(/\s+/).filter(Boolean);
function hayOf(r) {
  if (!r._hay) {
    r._hay = norm([r.full_name, r.username, r.student_id, r.group_name, r.member_no, r.direction, r.user_id].join(" "));
    r._digits = String(r.phone || "").replace(/\D/g, "");
  }
  return r._hay;
}
function matchQ(r, toks) {
  if (!toks.length) return true;
  const h = hayOf(r);
  return toks.every((t) => h.includes(t) || (/^\+?\d{3,}$/.test(t) && r._digits.includes(t.replace(/\D/g, ""))));
}
function hl(text, q) {
  const s = esc(text);
  const toks = String(q || "").trim().split(/\s+/).filter((t) => t.length > 1);
  if (!toks.length) return s;
  const re = new RegExp("(" + toks.map((t) => esc(t).replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|") + ")", "gi");
  return s.replace(re, "<mark>$1</mark>");
}

/* ---------------- grafiklar ---------------- */
function killCharts() { S.charts.forEach((c) => c.destroy()); S.charts = []; }
function chartBase() {
  Chart.defaults.font.family = "Manrope, system-ui, sans-serif";
  Chart.defaults.font.weight = 600;
  Chart.defaults.color = cssVar("--muted");
  Chart.defaults.borderColor = cssVar("--line-2");
}
const palette = () => ["--c1", "--c2", "--c3", "--c4", "--c5", "--c6"].map(cssVar);
function tooltip() {
  return { backgroundColor: cssVar("--panel-solid"), titleColor: cssVar("--text"), bodyColor: cssVar("--muted"), borderColor: cssVar("--line"), borderWidth: 1, padding: 12, cornerRadius: 10, displayColors: true, boxPadding: 4 };
}
function lineChart(cv, labels, sets) {
  chartBase();
  const ctx = cv.getContext("2d");
  const c = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: sets.map((s, i) => {
        const col = s.color || palette()[i];
        const g = ctx.createLinearGradient(0, 0, 0, cv.parentElement.clientHeight || 290);
        g.addColorStop(0, col + "55"); g.addColorStop(1, col + "00");
        return { label: s.label, data: s.data, borderColor: col, backgroundColor: g, fill: i === 0, tension: .38, borderWidth: 2.5, pointRadius: 0, pointHoverRadius: 5, pointHoverBackgroundColor: col, pointHoverBorderColor: cssVar("--panel-solid"), pointHoverBorderWidth: 3 };
      }),
    },
    options: {
      responsive: true, maintainAspectRatio: false, interaction: { mode: "index", intersect: false },
      plugins: { legend: { display: sets.length > 1, align: "end", labels: { usePointStyle: true, boxWidth: 8 } }, tooltip: tooltip() },
      scales: { x: { grid: { display: false }, ticks: { maxTicksLimit: 8 } }, y: { beginAtZero: true, ticks: { precision: 0, maxTicksLimit: 5 }, border: { display: false } } },
    },
  });
  S.charts.push(c); return c;
}
function barChart(cv, labels, data, opts = {}) {
  chartBase();
  const cols = palette();
  const c = new Chart(cv, {
    type: "bar",
    data: { labels, datasets: [{ data, backgroundColor: opts.multi ? labels.map((_, i) => cols[i % cols.length]) : cols[0], borderRadius: 7, borderSkipped: false, maxBarThickness: 34 }] },
    options: {
      responsive: true, maintainAspectRatio: false, indexAxis: opts.horizontal ? "y" : "x",
      plugins: { legend: { display: false }, tooltip: tooltip() },
      scales: { x: { grid: { display: !!opts.horizontal }, ticks: { precision: 0 } }, y: { beginAtZero: true, grid: { display: !opts.horizontal }, ticks: { precision: 0, maxTicksLimit: 5 }, border: { display: false } } },
    },
  });
  S.charts.push(c); return c;
}
function doughnut(cv, labels, data, colors) {
  chartBase();
  const c = new Chart(cv, {
    type: "doughnut",
    data: { labels, datasets: [{ data, backgroundColor: colors || palette(), borderColor: cssVar("--panel-solid"), borderWidth: 3, hoverOffset: 6 }] },
    options: { responsive: true, maintainAspectRatio: false, cutout: "72%", plugins: { legend: { display: false }, tooltip: tooltip() } },
  });
  S.charts.push(c); return c;
}
function spark(values) {
  const v = values.length ? values : [0];
  const max = Math.max(...v, 1), w = 100, h = 40, step = w / Math.max(v.length - 1, 1);
  const pts = v.map((y, i) => [i * step, h - 4 - (y / max) * (h - 10)]);
  const d = pts.map((p, i) => (i ? "L" : "M") + p[0].toFixed(1) + " " + p[1].toFixed(1)).join(" ");
  return `<svg class="spark" viewBox="0 0 100 40" preserveAspectRatio="none"><path class="area" d="${d} L100 40 L0 40 Z"/><path d="${d}" vector-effect="non-scaling-stroke"/></svg>`;
}
const barRows = (items, label = (x) => x.k, total) => {
  const max = Math.max(...items.map((x) => x.n), 1);
  return items.length ? items.map((x) => `<div class="bar-row"><span title="${esc(label(x))}">${esc(label(x))}</span><b>${fmtN(x.n)}${total ? ` <small style="color:var(--faint);font-weight:600">· ${Math.round((x.n / total) * 100)}%</small>` : ""}</b><div class="bar"><i style="width:${(x.n / max) * 100}%"></i></div></div>`).join("") : emptyBox("Hozircha ma'lumot yo'q");
};
const emptyBox = (t, sub = "") => `<div class="empty">${ic("inbox")}<b>${esc(t)}</b>${esc(sub)}</div>`;

/* ================= SAHIFALAR ================= */
const PAGES = {};

/* ---------- umumiy ko'rinish ---------- */
PAGES.overview = {
  title: "Umumiy ko'rinish",
  sub: () => `${fmtDate(today())} · klub va bot holati`,
  async mount(el) {
    el.innerHTML = `<div class="grid g-kpi">${Array(8).fill('<div class="card kpi"><div class="skel" style="height:86px"></div></div>').join("")}</div>`;
    const d = await api("/api/overview", true);
    setBadges(d.kpi);
    const k = d.kpi, s = d.series, last14 = (a) => a.slice(-14);
    const kpi = (icon, label, val, foot, sp, go, cls = "") => `<div class="card kpi ${cls}" ${go ? `data-go="${go}"` : ""}>
      <div class="kpi-top"><span class="kpi-ico">${ic(icon)}</span>${label}</div>
      <div class="kpi-row"><div class="kpi-val">${fmtN(val)}</div>${sp ? spark(sp) : ""}</div><div class="kpi-foot">${foot}</div></div>`;
    const up = (n, t) => `<span class="delta ${n ? "up" : "zero"}">${n ? "+" : ""}${fmtN(n)}</span> ${t}`;
    const total = d.app_status.reduce((a, b) => a + b.n, 0);
    const stCols = { pending: cssVar("--warn"), returned: cssVar("--info"), accepted: cssVar("--ok"), rejected: cssVar("--bad") };
    el.innerHTML = `
    <div class="grid g-kpi">
      ${kpi("users", "Ro'yxatdan o'tganlar", k.registered, up(k.new_week, "shu hafta"), last14(s.registrations), "#/students?status=registered")}
      ${kpi("badge", "Faol a'zolar", k.members, `${k.registered ? Math.round((k.members / k.registered) * 100) : 0}% talabalardan`, null, "#/students?status=member")}
      ${kpi("file", "Kutilayotgan arizalar", k.apps_pending, k.apps_pending ? "ko'rib chiqish kerak" : "hammasi ko'rilgan", null, "#/applications?status=pending", k.apps_pending ? "alert-kpi" : "")}
      ${kpi("chat", "Ochiq murojaatlar", k.appeals_open, k.appeals_open ? "javob kutilmoqda" : "javobsiz murojaat yo'q", null, "#/appeals?status=open", k.appeals_open ? "alert-kpi" : "")}
      ${kpi("pulse", "Faol foydalanuvchilar · 24 soat", k.active_24h, `${fmtN(k.actions_24h)} ta amal`, last14(s.active_users), "#/activity")}
      ${kpi("cal", "Ochiq tadbirlar", k.events_open, "ro'yxat ochiq", null, "#/events?state=open")}
      ${kpi("ticket", "Tadbirga kelganlar", k.tickets_used, "QR orqali tasdiqlangan", null, "#/events")}
      ${kpi("camOff", "Suratsiz profillar", k.no_photo, k.no_photo ? "surat so'ralgan" : "hammada surat bor", null, "#/students?photo=no", k.no_photo ? "alert-kpi" : "")}
    </div>
    <div class="grid g-2">
      <div class="card fill"><div class="card-h"><h3>Faollik dinamikasi</h3>
        <div class="seg" id="trendSeg"><button data-k="registrations" class="on">Ro'yxatdan o'tish</button><button data-k="active_users">Faol foydalanuvchilar</button><button data-k="applications">Arizalar</button></div></div>
        <div class="card-b"><div class="chart-box"><canvas id="trend"></canvas></div></div></div>
      <div class="card"><div class="card-h"><h3>Arizalar holati</h3><span class="sub">jami ${fmtN(total)}</span></div>
        <div class="card-b"><div class="chart-box sm" style="height:190px"><canvas id="appDonut"></canvas></div>
        <div class="list" style="margin-top:10px">${d.app_status.map((x) => `<a class="li click" href="#/applications?status=${x.k}"><span class="dot-ico" style="background:${stCols[x.k]}22;color:${stCols[x.k]}">${ic("file")}</span><div class="grow"><b>${esc((APP_ST[x.k] || [x.k])[0])}</b></div><b>${fmtN(x.n)}</b></a>`).join("") || emptyBox("Arizalar yo'q")}</div></div></div>
    </div>
    <div class="grid g-3">
      <div class="card"><div class="card-h"><h3>Yo'nalishlar</h3><span class="sub">TOP 8</span></div><div class="card-b">${barRows(d.directions, (x) => x.k || "—", k.registered)}</div></div>
      <div class="card"><div class="card-h"><h3>Kurslar</h3></div><div class="card-b"><div class="chart-box sm"><canvas id="courses"></canvas></div></div></div>
      <div class="card"><div class="card-h"><h3>A'zolar bo'limlari</h3></div><div class="card-b">${barRows(d.sections, (x) => x.k, k.members)}</div></div>
    </div>
    <div class="grid g-3">
      <div class="card"><div class="card-h"><h3>So'nggi voqealar</h3><span class="sub">jonli</span></div><div class="card-b"><div class="list">${feedList(d.feed)}</div></div></div>
      <div class="card"><div class="card-h"><h3>Reyting · TOP</h3><a class="btn sm ghost" href="#/students?sort=points">Hammasi</a></div><div class="card-b"><div class="list">${d.top.map((t, i) => `<div class="li click" data-uid="${t.user_id}"><span class="rank r${i + 1}">${i + 1}</span>${avatar(t)}<div class="grow"><b>${esc(t.full_name)}</b><small>${esc(t.direction || "")}</small></div><span class="badge gold">${fmtN(t.pts)} ball</span></div>`).join("") || emptyBox("Hali ball berilmagan")}</div></div></div>
      <div class="card"><div class="card-h"><h3>Yaqin tadbirlar</h3><a class="btn sm ghost" href="#/events">Hammasi</a></div><div class="card-b"><div class="list">${d.upcoming.map((e) => `<a class="li click" href="#/events"><span class="dot-ico" style="background:var(--accent-soft);color:var(--accent)">${ic("cal")}</span><div class="grow"><b>${esc(e.title)}</b><small>${esc(e.date_text || "")}${e.place ? " · " + esc(e.place) : ""}</small></div><span class="badge info">${e.taken}${e.capacity ? "/" + e.capacity : ""}</span></a>`).join("") || emptyBox("Ochiq tadbir yo'q")}</div></div></div>
    </div>`;
    const labels = s.days.map((x) => { const d0 = parseD(x); return `${d0.getDate()} ${MONTHS[d0.getMonth()]}`; });
    const names = { registrations: "Ro'yxatdan o'tish", active_users: "Faol foydalanuvchilar", applications: "Arizalar" };
    let trend = lineChart($("#trend"), labels, [{ label: names.registrations, data: s.registrations }]);
    $$("#trendSeg button").forEach((b) => b.onclick = () => {
      $$("#trendSeg button").forEach((x) => x.classList.toggle("on", x === b));
      S.charts = S.charts.filter((c) => c !== trend); trend.destroy();
      const i = ["registrations", "active_users", "applications"].indexOf(b.dataset.k);
      trend = lineChart($("#trend"), labels, [{ label: names[b.dataset.k], data: s[b.dataset.k], color: palette()[i] }]);
    });
    doughnut($("#appDonut"), d.app_status.map((x) => (APP_ST[x.k] || [x.k])[0]), d.app_status.map((x) => x.n), d.app_status.map((x) => stCols[x.k] || cssVar("--c6")));
    barChart($("#courses"), d.courses.map((x) => course(x.k)), d.courses.map((x) => x.n), { multi: true });
    $$(".kpi[data-go]", el).forEach((c) => c.onclick = () => (location.hash = c.dataset.go));
  },
};

function feedList(items) {
  const T = {
    register: ["userPlus", "--info", (x) => `ro'yxatdan o'tdi · ${esc(x.info || "")}`],
    application: ["file", "--warn", (x) => `ariza topshirdi · ${esc((APP_ST[x.info] || [x.info])[0])}`],
    member: ["badge", "--ok", (x) => `klub a'zosi bo'ldi · ${esc(x.info)}`],
    appeal: ["chat", "--c5", (x) => `murojaat yubordi · ${esc((AP_KIND[x.info] || [x.info])[0])}`],
    checkin: ["ticket", "--accent", (x) => `tadbirga keldi · ${esc(x.info)}`],
  };
  return items.length ? items.map((x) => {
    const [icon, col, txt] = T[x.t] || ["pulse", "--muted", () => ""];
    return `<div class="li click" data-uid="${x.user_id}"><span class="dot-ico" style="background:color-mix(in srgb, var(${col}) 15%, transparent);color:var(${col})">${ic(icon)}</span><div class="grow"><b>${esc(x.full_name || "—")}</b><small>${txt(x)}</small></div><span class="time">${ago(x.ts)}</span></div>`;
  }).join("") : emptyBox("Hozircha voqealar yo'q");
}

/* ---------- ochiladigan ro'yxat (filtr) ---------- */
function makeDD({ label, icon, multi = true, get, set, searchable = false }) {
  const root = document.createElement("div");
  root.className = "dd";
  root.innerHTML = `<button class="dd-btn" type="button"></button><div class="dd-pop"></div>`;
  const btn = root.firstChild, pop = root.lastChild;
  let q = "";
  const sync = () => {
    const { value } = get();
    const n = multi ? value.length : value ? 1 : 0;
    const cur = !multi && value ? get().options.find((o) => o.v === value) : null;
    btn.className = "dd-btn" + (n ? " set" : "");
    btn.innerHTML = `${icon ? ic(icon) : ""}${esc(cur ? cur.label : label)}${multi && n ? `<em>${n}</em>` : ""}${ic("chev")}`;
  };
  const draw = () => {
    const { options, value } = get();
    const qq = norm(q);
    const opts = options.filter((o) => !qq || norm(o.label).includes(qq));
    pop.innerHTML = `${searchable ? `<input class="dd-q" placeholder="Qidirish…" value="${esc(q)}">` : ""}
      <div class="dd-opts">${opts.map((o) => {
        const on = multi ? value.includes(o.v) : value === o.v;
        return `<div class="dd-opt ${on ? "on" : ""} ${o.count === 0 && !on ? "zero" : ""}" data-v="${esc(o.v)}"><span class="ck" style="${multi ? "" : "border-radius:50%"}"></span><span>${esc(o.label)}</span>${o.count != null ? `<i>${fmtN(o.count)}</i>` : ""}</div>`;
      }).join("") || '<div class="empty" style="padding:20px">Topilmadi</div>'}</div>
      ${multi ? `<div class="dd-foot"><button data-a="clear">Tozalash</button><button data-a="close">Tayyor</button></div>` : ""}`;
    const inp = $(".dd-q", pop);
    if (inp) { inp.oninput = () => { q = inp.value; draw(); const i2 = $(".dd-q", pop); i2.focus(); i2.setSelectionRange(q.length, q.length); }; }
  };
  btn.onclick = (e) => {
    e.stopPropagation();
    const open = !root.classList.contains("open");
    $$(".dd.open").forEach((d) => d.classList.remove("open"));
    if (open) { q = ""; draw(); root.classList.add("open"); const i = $(".dd-q", pop); if (i) i.focus(); }
  };
  pop.onclick = (e) => {
    e.stopPropagation();
    const a = e.target.closest("[data-a]");
    if (a) { if (a.dataset.a === "clear") { set(multi ? [] : ""); draw(); } else root.classList.remove("open"); return sync(); }
    const o = e.target.closest(".dd-opt"); if (!o) return;
    const v = o.dataset.v, { value } = get();
    if (multi) set(value.includes(v) ? value.filter((x) => x !== v) : [...value, v]);
    else { set(value === v ? "" : v); root.classList.remove("open"); }
    draw(); sync();
  };
  root.sync = sync;
  sync();
  return root;
}
document.addEventListener("click", () => $$(".dd.open").forEach((d) => d.classList.remove("open")));

/* ---------- talabalar ---------- */
const SF_DEFAULT = { q: "", status: "", dirs: [], course: [], group: [], section: [], lang: [], photo: "", act: "", minPts: "", from: "", to: "", sort: "created_at", desc: "1", view: "table", per: "25", page: "1" };
const DIMS = { dirs: (r) => r.direction || "", course: (r) => r.course || "", group: (r) => r.group_name || "", section: (r) => r.section || "", lang: (r) => r.lang || "" };
const ARR_KEYS = ["dirs", "course", "group", "section", "lang"];
function readParams(params, defaults) {
  const f = JSON.parse(JSON.stringify(defaults));
  for (const k of Object.keys(defaults)) {
    if (!params.has(k)) continue;
    f[k] = Array.isArray(defaults[k]) ? params.get(k).split("|").filter(Boolean) : params.get(k);
  }
  return f;
}
function writeParams(page, f, defaults) {
  const qs = new URLSearchParams();
  for (const [k, v] of Object.entries(f)) {
    const dv = defaults[k];
    if (Array.isArray(v) ? v.length : v !== dv && v !== "") qs.set(k, Array.isArray(v) ? v.join("|") : v);
  }
  const s = qs.toString();
  history.replaceState(null, "", `#/${page}${s ? "?" + s : ""}`);
}
function matchStudent(r, f, skip, toks) {
  if (skip !== "status" && f.status && r.status !== f.status) return false;
  for (const k of ARR_KEYS) if (skip !== k && f[k].length && !f[k].includes(DIMS[k](r))) return false;
  if (f.photo === "yes" && !r.has_photo) return false;
  if (f.photo === "no" && r.has_photo) return false;
  if (f.act === "yes" && !r.actions_30d) return false;
  if (f.act === "no" && r.actions_30d) return false;
  if (f.minPts !== "" && r.points < Number(f.minPts)) return false;
  const day = (r.created_at || "").slice(0, 10);
  if (f.from && day < f.from) return false;
  if (f.to && day > f.to) return false;
  return matchQ(r, toks);
}
const SORTS = {
  created_at: ["Ro'yxatdan o'tgan sana", (r) => r.created_at || ""], full_name: ["Ism", (r) => r.full_name || ""],
  points: ["Ball", (r) => r.points], attended: ["Davomat", (r) => r.attended], last_seen: ["Oxirgi faollik", (r) => r.last_seen || ""],
  course: ["Kurs", (r) => r.course || ""], group_name: ["Guruh", (r) => r.group_name || ""], direction: ["Yo'nalish", (r) => r.direction || ""],
  status: ["Holat", (r) => ["member", "applicant", "registered", "guest"].indexOf(r.status)],
};
const PRESETS = [
  ["week", "Shu hafta qo'shilganlar", { from: () => daysAgo(7) }],
  ["active_members", "Faol a'zolar", { status: "member", act: "yes" }],
  ["pending", "Arizasi kutilmoqda", { status: "applicant" }],
  ["nophoto", "Suratsiz", { photo: "no" }],
  ["top", "Eng ko'p ball", { sort: "points", desc: "1", minPts: "1" }],
  ["sleep", "30 kun faol emas", { status: "registered", act: "no" }],
];

PAGES.students = {
  title: "Talabalar",
  sub: () => "Qidiruv, filtrlar va talaba kartochkasi",
  async mount(el, params) {
    el.innerHTML = `<div class="card"><div class="filters"><div class="skel" style="height:46px"></div><div class="skel" style="height:38px;width:60%"></div></div></div><div class="card"><div class="skel" style="height:420px;margin:16px"></div></div>`;
    S.students = await api("/api/students", true);
    const f = readParams(params, SF_DEFAULT);
    if (!params.toString()) Object.assign(f, readParams(new URLSearchParams(localStorage.getItem("mlq_sf") || ""), SF_DEFAULT), { q: "", page: "1" });
    this.f = f; this.preset = null;
    el.innerHTML = `
      <div class="card"><div class="filters">
        <div class="f-row">
          <label class="f-search">${ic("search")}<input id="sq" placeholder="Ism, @username, telefon, talaba ID, guruh, MLQ-raqam…" value="${esc(f.q)}" autocomplete="off"><button class="clear" id="sqx" title="Tozalash" ${f.q ? "" : "hidden"}>${ic("x")}</button></label>
          <div class="seg" id="viewSeg"><button data-v="table">${ic("rows")}Jadval</button><button data-v="cards">${ic("grid")}Kartalar</button></div>
          <button class="btn" id="exportBtn">${ic("dl")}Excel (CSV)</button>
        </div>
        <div class="f-row"><div class="seg" id="stSeg"></div></div>
        <div class="f-row" id="ddRow"></div>
        <div class="f-row"><span style="color:var(--faint);font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.1em">Tezkor:</span><div class="presets" id="presets"></div></div>
      </div></div>
      <div class="card" id="resCard">
        <div class="card-h res-bar" style="padding-bottom:12px;border-bottom:1px solid var(--line-2)"><div class="res-count" id="resCount"></div><div class="chips" id="chips"></div>
          <select class="sel" id="perSel"><option value="25">25 ta</option><option value="50">50 ta</option><option value="100">100 ta</option></select></div>
        <div id="results"></div>
      </div>`;
    const rows = S.students, self = this;
    const opts = (k, labelFn = (v) => v || "—") => {
      const counts = {}; const toks = tokens(f.q);
      rows.forEach((r) => { if (matchStudent(r, f, k, toks)) { const v = DIMS[k](r); counts[v] = (counts[v] || 0) + 1; } });
      const all = [...new Set(rows.map(DIMS[k]))];
      return all.map((v) => ({ v, label: labelFn(v), count: counts[v] || 0 }));
    };
    const ddRow = $("#ddRow");
    const mk = (k, label, icon, labelFn, sorter, searchable) => {
      const d = makeDD({ label, icon, searchable, get: () => ({ options: sorter ? opts(k, labelFn).sort(sorter) : opts(k, labelFn).sort((a, b) => b.count - a.count || a.label.localeCompare(b.label)), value: f[k] }), set: (v) => { f[k] = v; self.changed(); } });
      ddRow.appendChild(d); return d;
    };
    this.dds = [
      mk("dirs", "Yo'nalish", "award", (v) => v || "Ko'rsatilmagan", null, true),
      mk("course", "Kurs", null, course, (a, b) => a.v.localeCompare(b.v)),
      mk("group", "Guruh", null, (v) => v || "—", (a, b) => a.label.localeCompare(b.label, undefined, { numeric: true }), true),
      mk("section", "Bo'lim", null, (v) => (v ? M.sections[v] || v : "Bo'limsiz")),
      mk("lang", "Bot tili", null, (v) => LANG[v] || v),
    ];
    const single = (k, label, options) => {
      const d = makeDD({ label, multi: false, get: () => ({ options, value: f[k] }), set: (v) => { f[k] = v; self.changed(); } });
      ddRow.appendChild(d); this.dds.push(d);
    };
    single("photo", "Surat", [{ v: "yes", label: "Surati bor" }, { v: "no", label: "Surati yo'q" }]);
    single("act", "Faollik", [{ v: "yes", label: "30 kunda faol" }, { v: "no", label: "30 kun faol emas" }]);
    ddRow.insertAdjacentHTML("beforeend", `
      <label class="num-in" title="Kamida shuncha ball">${ic("star")}Ball ≥<input type="number" min="0" id="minPts" value="${esc(f.minPts)}" placeholder="0"></label>
      <label class="num-in" title="Ro'yxatdan o'tgan sana">${ic("cal")}<input type="date" id="dFrom" value="${esc(f.from)}">—<input type="date" id="dTo" value="${esc(f.to)}"></label>
      <select class="sel" id="sortSel">${Object.entries(SORTS).map(([k, v]) => `<option value="${k}">↕ ${v[0]}</option>`).join("")}</select>
      <button class="btn ghost sm" id="resetBtn">${ic("filterX")}Tozalash</button>`);
    $("#presets").innerHTML = PRESETS.map(([id, label]) => `<button class="preset" data-p="${id}">${label}</button>`).join("");

    let tmr;
    $("#sq").oninput = (e) => { clearTimeout(tmr); tmr = setTimeout(() => { f.q = e.target.value; $("#sqx").hidden = !f.q; self.changed(); }, 120); };
    $("#sqx").onclick = (e) => { e.preventDefault(); $("#sq").value = ""; f.q = ""; $("#sqx").hidden = true; self.changed(); $("#sq").focus(); };
    $("#minPts").oninput = (e) => { f.minPts = e.target.value; self.changed(); };
    $("#dFrom").onchange = (e) => { f.from = e.target.value; self.changed(); };
    $("#dTo").onchange = (e) => { f.to = e.target.value; self.changed(); };
    $("#sortSel").onchange = (e) => { f.sort = e.target.value; f.desc = ["full_name", "group_name", "direction", "course", "status"].includes(f.sort) ? "" : "1"; self.changed(); };
    $("#perSel").onchange = (e) => { f.per = e.target.value; f.page = "1"; self.update(); };
    $("#resetBtn").onclick = () => { Object.assign(f, JSON.parse(JSON.stringify(SF_DEFAULT)), { view: f.view }); self.syncInputs(); self.changed(); };
    $$("#viewSeg button").forEach((b) => b.onclick = () => { f.view = b.dataset.v; self.update(); });
    $$("#presets .preset").forEach((b) => b.onclick = () => {
      const p = PRESETS.find((x) => x[0] === b.dataset.p);
      const was = self.preset === p[0];
      Object.assign(f, JSON.parse(JSON.stringify(SF_DEFAULT)), { view: f.view, per: f.per });
      if (!was) for (const [k, v] of Object.entries(p[2])) f[k] = typeof v === "function" ? v() : v;
      self.syncInputs(); self.changed(was ? null : p[0]);
    });
    $("#exportBtn").onclick = () => exportCSV(self.filtered || []);
    this.syncInputs();
    this.update();
    setTimeout(() => $("#sq") && $("#sq").focus(), 50);
  },
  syncInputs() {
    const f = this.f;
    $("#sq").value = f.q; $("#sqx").hidden = !f.q;
    $("#minPts").value = f.minPts; $("#dFrom").value = f.from; $("#dTo").value = f.to;
    $("#sortSel").value = f.sort; $("#perSel").value = f.per;
  },
  changed(preset = null) { this.preset = preset; this.f.page = "1"; this.update(); },
  async refresh() { S.students = await api("/api/students", true); this.update(); },
  update() {
    const f = this.f, rows = S.students, toks = tokens(f.q);
    writeParams("students", f, SF_DEFAULT);
    try { const p = new URLSearchParams(location.hash.split("?")[1] || ""); p.delete("q"); p.delete("page"); localStorage.setItem("mlq_sf", p.toString()); } catch {}
    // holat bo'yicha sonlar (boshqa filtrlar hisobga olingan)
    const sc = { "": 0, member: 0, applicant: 0, registered: 0, guest: 0 };
    rows.forEach((r) => { if (matchStudent(r, f, "status", toks)) { sc[""]++; sc[r.status]++; } });
    $("#stSeg").innerHTML = [["", "Hammasi"], ["member", "A'zolar"], ["applicant", "Ariza ko'rilmoqda"], ["registered", "Ro'yxatdan o'tgan"], ["guest", "Ro'yxatdan o'tmagan"]]
      .map(([k, l]) => `<button data-s="${k}" class="${f.status === k ? "on" : ""}">${l}<i>${fmtN(sc[k])}</i></button>`).join("");
    $$("#stSeg button").forEach((b) => b.onclick = () => { f.status = b.dataset.s; this.changed(); });
    $$("#viewSeg button").forEach((b) => b.classList.toggle("on", b.dataset.v === f.view));
    $$("#presets .preset").forEach((b) => b.classList.toggle("on", b.dataset.p === this.preset));
    this.dds.forEach((d) => d.sync());
    $("#sortSel").value = f.sort;

    const [, keyFn] = SORTS[f.sort] || SORTS.created_at;
    const dir = f.desc ? -1 : 1;
    const list = rows.filter((r) => matchStudent(r, f, null, toks)).sort((a, b) => {
      const x = keyFn(a), y = keyFn(b);
      if (x === y) return 0;
      if (x === "" || x == null) return 1;
      if (y === "" || y == null) return -1;
      return (typeof x === "number" ? x - y : String(x).localeCompare(String(y), undefined, { numeric: true })) * dir;
    });
    this.filtered = list;
    $("#resCount").innerHTML = `<b>${fmtN(list.length)}</b> ta talaba topildi${list.length !== rows.length ? ` · jami ${fmtN(rows.length)}` : ""}`;

    // faol filtrlar «chip»lari
    const chips = [];
    const chip = (label, clear) => chips.push([label, clear]);
    if (f.q) chip(`«${f.q}»`, () => { f.q = ""; });
    if (f.status) chip(ST[f.status][0], () => { f.status = ""; });
    ARR_KEYS.forEach((k) => f[k].forEach((v) => chip(k === "course" ? course(v) : k === "section" ? (v ? M.sections[v] || v : "Bo'limsiz") : k === "lang" ? LANG[v] || v : v || "—", () => { f[k] = f[k].filter((x) => x !== v); })));
    if (f.photo) chip(f.photo === "yes" ? "Surati bor" : "Surati yo'q", () => { f.photo = ""; });
    if (f.act) chip(f.act === "yes" ? "30 kunda faol" : "30 kun faol emas", () => { f.act = ""; });
    if (f.minPts !== "") chip(`Ball ≥ ${f.minPts}`, () => { f.minPts = ""; });
    if (f.from || f.to) chip(`${f.from ? fmtDate(f.from) : "…"} — ${f.to ? fmtDate(f.to) : "…"}`, () => { f.from = ""; f.to = ""; });
    $("#chips").innerHTML = chips.map(([l], i) => `<span class="chip">${esc(l)}<button data-i="${i}" title="Olib tashlash">${ic("x")}</button></span>`).join("");
    $$("#chips button").forEach((b) => b.onclick = () => { chips[b.dataset.i][1](); this.syncInputs(); this.changed(); });

    const per = Number(f.per) || 25, pages = Math.max(1, Math.ceil(list.length / per));
    let page = Math.min(Math.max(1, Number(f.page) || 1), pages);
    const slice = list.slice((page - 1) * per, page * per);
    const box = $("#results");
    if (!list.length) {
      box.innerHTML = emptyBox("Hech kim topilmadi", " Filtrlarni o'zgartiring yoki tozalang.");
      return;
    }
    const sortTh = (k, label) => `<th data-k="${k}" class="${f.sort === k ? "sorted" : ""}">${label}${f.sort === k ? `<span class="arr">${f.desc ? "▼" : "▲"}</span>` : ""}</th>`;
    box.innerHTML = (f.view === "cards" ? `<div class="cards-grid">${slice.map((r) => `
      <div class="s-card" data-uid="${r.user_id}"><div class="top">${avatar(r)}<div><b>${hl(r.full_name || "—", f.q)}</b><small>${esc(r.direction || "")}</small></div></div>
        <div style="display:flex;gap:6px;flex-wrap:wrap">${badge(ST[r.status])}${r.member_no ? `<span class="badge gold">${esc(r.member_no)}</span>` : ""}<span class="badge mute">${course(r.course)} · ${esc(r.group_name || "—")}</span></div>
        <div class="stats"><div><b>${r.points}</b><small>ball</small></div><div><b>${r.attended}</b><small>davomat</small></div><div><b>${r.actions_30d}</b><small>amal/30k</small></div></div></div>`).join("")}</div>`
      : `<div class="tbl-wrap"><table class="tbl"><thead><tr>${sortTh("full_name", "Talaba")}${sortTh("status", "Holat")}${sortTh("direction", "Yo'nalish")}${sortTh("group_name", "Kurs · guruh")}<th>Talaba ID</th><th>Telefon</th>${sortTh("points", "Ball")}${sortTh("attended", "Davomat")}${sortTh("last_seen", "Oxirgi faollik")}${sortTh("created_at", "Qo'shilgan")}</tr></thead><tbody>
        ${slice.map((r) => `<tr data-uid="${r.user_id}"><td><div class="who">${avatar(r)}<div><b>${hl(r.full_name || "—", f.q)}</b><small>${r.username ? hl(r.username, f.q) : "ID " + r.user_id}${r.member_no ? " · " + esc(r.member_no) : ""}</small></div></div></td>
          <td>${badge(ST[r.status])}</td><td class="mut" style="max-width:190px;overflow:hidden;text-overflow:ellipsis" title="${esc(r.direction || "")}">${esc(r.direction || "—")}</td><td>${hl(r.group_name || "—", f.q)}<small class="mut" style="display:block;font-size:11.5px">${course(r.course)}</small></td>
          <td class="mut">${hl(r.student_id || "—", f.q)}</td><td class="mut">${esc(r.phone || "—")}</td><td class="num">${r.points}</td><td class="num">${r.attended}</td><td class="mut">${r.last_seen ? ago(r.last_seen) : "—"}</td><td class="mut">${fmtDate(r.created_at)}</td></tr>`).join("")}
      </tbody></table></div>`)
      + `<div class="pager"><span class="info">${(page - 1) * per + 1}–${Math.min(page * per, list.length)} / ${fmtN(list.length)}</span>${pagerBtns(page, pages)}</div>`;
    $$("th[data-k]", box).forEach((th) => th.onclick = () => { if (f.sort === th.dataset.k) f.desc = f.desc ? "" : "1"; else { f.sort = th.dataset.k; f.desc = ["full_name", "group_name", "direction", "course", "status"].includes(f.sort) ? "" : "1"; } this.update(); });
    $$(".pager button[data-p]", box).forEach((b) => b.onclick = () => { f.page = b.dataset.p; this.update(); $("#resCard").scrollIntoView({ behavior: "smooth", block: "start" }); });
  },
};
function pagerBtns(page, pages) {
  const set = new Set([1, pages, page - 1, page, page + 1].filter((p) => p >= 1 && p <= pages));
  const arr = [...set].sort((a, b) => a - b);
  let out = `<button data-p="${page - 1}" ${page <= 1 ? "disabled" : ""}>‹</button>`, prev = 0;
  for (const p of arr) { if (p - prev > 1) out += `<span style="color:var(--faint)">…</span>`; out += `<button data-p="${p}" class="${p === page ? "on" : ""}">${p}</button>`; prev = p; }
  return out + `<button data-p="${page + 1}" ${page >= pages ? "disabled" : ""}>›</button>`;
}
function exportCSV(rows) {
  if (!rows.length) return toast("Eksport uchun ma'lumot yo'q");
  const cols = [["full_name", "F.I.Sh."], ["status", "Holat"], ["member_no", "A'zolik raqami"], ["direction", "Yo'nalish"], ["course", "Kurs"], ["group_name", "Guruh"], ["student_id", "Talaba ID"], ["phone", "Telefon"], ["username", "Telegram"], ["section_name", "Bo'lim"], ["points", "Ball"], ["points_sem", "Semestr bali"], ["attended", "Davomat"], ["created_at", "Ro'yxatdan o'tgan"], ["last_seen", "Oxirgi faollik"], ["user_id", "Telegram ID"]];
  const cell = (v) => { const s = String(v ?? ""); return /[;"\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s; };
  const val = (r, k) => (k === "status" ? ST[r.status][0] : k === "course" ? course(r.course) : r[k]);
  const csv = "\ufeff" + [cols.map((c) => c[1]).join(";"), ...rows.map((r) => cols.map(([k]) => cell(val(r, k))).join(";"))].join("\r\n");
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
  a.download = `muloqot_talabalar_${today()}.csv`; a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 2000);
  toast(`${fmtN(rows.length)} ta talaba eksport qilindi`);
}

/* ---------- arizalar ---------- */
PAGES.applications = {
  title: "Arizalar",
  sub: () => "A'zolik arizalari (Ustav 4.6)",
  async mount(el, params) {
    const rows = await api("/api/applications", true);
    const f = readParams(params, { status: "", type: "", q: "" });
    el.innerHTML = `<div class="card"><div class="filters"><div class="f-row">
      <label class="f-search">${ic("search")}<input id="aq" placeholder="Ism, yo'nalish, guruh…" value="${esc(f.q)}"></label>
      <div class="seg" id="atype"><button data-t="">Barchasi</button><button data-t="new">Yangi a'zolik</button><button data-t="renew">Yangilash</button></div></div>
      <div class="f-row"><div class="seg" id="aseg"></div></div></div></div><div class="card" id="ares"></div>`;
    const draw = () => {
      writeParams("applications", f, { status: "", type: "", q: "" });
      const toks = tokens(f.q);
      const base = rows.filter((r) => (!f.type || r.app_type === f.type) && (!toks.length || toks.every((t) => norm([r.full_name, r.direction, r.group_name, r.id].join(" ")).includes(t))));
      const cnt = (s) => base.filter((r) => !s || r.status === s).length;
      $("#aseg").innerHTML = [["", "Hammasi"], ...Object.entries(APP_ST).map(([k, v]) => [k, v[0]])].map(([k, l]) => `<button data-s="${k}" class="${f.status === k ? "on" : ""}">${l}<i>${cnt(k)}</i></button>`).join("");
      $$("#aseg button").forEach((b) => b.onclick = () => { f.status = b.dataset.s; draw(); });
      $$("#atype button").forEach((b) => { b.classList.toggle("on", b.dataset.t === f.type); b.onclick = () => { f.type = b.dataset.t; draw(); }; });
      const list = base.filter((r) => !f.status || r.status === f.status);
      $("#ares").innerHTML = list.length ? `<div class="tbl-wrap"><table class="tbl"><thead><tr><th>№</th><th>Talaba</th><th>Yo'nalish</th><th>Kurs · guruh</th><th>Turi</th><th>Holat</th><th>Bo'lim</th><th>Topshirilgan</th><th>Qaror</th></tr></thead><tbody>
        ${list.map((r) => `<tr data-uid="${r.user_id}" data-tab="app"><td class="num mut">#${r.id}</td><td><div class="who">${avatar(r)}<div><b>${hl(r.full_name, f.q)}</b></div></div></td><td class="mut">${esc(r.direction || "—")}</td><td>${course(r.course)} · ${esc(r.group_name || "—")}</td>
        <td>${r.app_type === "renew" ? '<span class="badge mute">Yangilash</span>' : '<span class="badge gold">Yangi</span>'}</td><td>${badge(APP_ST[r.status])}</td><td class="mut">${esc(r.section_name || "—")}</td><td class="mut">${fmtDate(r.created_at, true)}</td>
        <td class="mut" style="max-width:260px;overflow:hidden;text-overflow:ellipsis" title="${esc(r.reason || "")}">${r.decided_at ? fmtDate(r.decided_at) : "—"}${r.reason ? " · " + esc(r.reason) : ""}</td></tr>`).join("")}</tbody></table></div>` : emptyBox("Bu filtr bo'yicha ariza yo'q");
    };
    let t; $("#aq").oninput = (e) => { clearTimeout(t); t = setTimeout(() => { f.q = e.target.value; draw(); }, 120); };
    draw();
  },
};

/* ---------- tadbirlar ---------- */
PAGES.events = {
  title: "Tadbirlar",
  sub: () => "Ro'yxat, chiptalar va QR davomat",
  async mount(el, params) {
    const rows = await api("/api/events", true);
    const f = readParams(params, { state: "", kind: "" });
    const stOf = (e) => (e.finished ? "done" : e.active ? "open" : "closed");
    el.innerHTML = `<div class="card"><div class="filters"><div class="f-row"><div class="seg" id="eseg"></div><div class="seg" id="kseg"><button data-k="">Barchasi</button><button data-k="event">Tadbirlar</button><button data-k="session">Mashg'ulotlar</button></div></div></div></div><div id="eres"></div>`;
    const draw = () => {
      writeParams("events", f, { state: "", kind: "" });
      const base = rows.filter((e) => !f.kind || e.kind === f.kind);
      const c = (s) => base.filter((e) => !s || stOf(e) === s).length;
      $("#eseg").innerHTML = [["", "Hammasi"], ["open", "Ro'yxat ochiq"], ["closed", "Ro'yxat yopiq"], ["done", "O'tkazilgan"]].map(([k, l]) => `<button data-s="${k}" class="${f.state === k ? "on" : ""}">${l}<i>${c(k)}</i></button>`).join("");
      $$("#eseg button").forEach((b) => b.onclick = () => { f.state = b.dataset.s; draw(); });
      $$("#kseg button").forEach((b) => { b.classList.toggle("on", b.dataset.k === f.kind); b.onclick = () => { f.kind = b.dataset.k; draw(); }; });
      const list = base.filter((e) => !f.state || stOf(e) === f.state);
      const stB = { open: ["Ro'yxat ochiq", "ok"], closed: ["Ro'yxat yopiq", "warn"], done: ["O'tkazilgan", "mute"] };
      $("#eres").innerHTML = list.length ? `<div class="ev-grid">${list.map((e) => {
        const cap = e.capacity || Math.max(e.taken, 1);
        const rate = e.taken ? Math.round((e.used / e.taken) * 100) : 0;
        return `<div class="card ev"><div style="display:flex;gap:8px;align-items:center">${badge(stB[stOf(e)])}<span class="badge ${e.kind === "session" ? "info" : "gold"}">${e.kind === "session" ? "Mashg'ulot" : "Tadbir"}</span><span style="margin-left:auto;color:var(--faint);font-size:12px">#${e.id}</span></div>
          <h4>${esc(e.title)}</h4>
          <div class="meta"><span>${ic("clock")}${esc(e.date_text || fmtDate(e.starts_at, true))}</span>${e.place ? `<span>${ic("pin")}${esc(e.place)}</span>` : ""}<span>${ic("star")}${e.points} ball</span></div>
          <div><div style="display:flex;justify-content:space-between;font-size:12px;color:var(--muted);margin-bottom:6px"><span>Joylar: ${e.taken}${e.capacity ? " / " + e.capacity : " (cheklanmagan)"}</span><span>Keldi: ${e.used}</span></div>
          <div class="prog"><i style="width:${Math.min(100, ((e.taken - e.used) / cap) * 100)}%;opacity:.55"></i><i style="width:${Math.min(100, (e.used / cap) * 100)}%"></i></div></div>
          <div class="nums"><div><b>${e.taken}</b><small>yozilgan</small></div><div><b>${e.used}</b><small>kelgan</small></div><div><b>${e.finished || e.used ? rate + "%" : "—"}</b><small>davomat</small></div></div></div>`;
      }).join("")}</div>` : `<div class="card">${emptyBox("Tadbirlar topilmadi", " Bot orqali /addevent buyrug'i bilan qo'shiladi.")}</div>`;
    };
    draw();
  },
};

/* ---------- murojaatlar ---------- */
PAGES.appeals = {
  title: "Murojaatlar",
  sub: () => "Savollar, takliflar va shikoyatlar",
  async mount(el, params) {
    const rows = await api("/api/appeals", true);
    const f = readParams(params, { kind: "", status: "", q: "" });
    el.innerHTML = `<div class="card"><div class="filters"><div class="f-row"><label class="f-search">${ic("search")}<input id="pq" placeholder="Ism yoki xabar matni…" value="${esc(f.q)}"></label><div class="seg" id="pk"></div></div><div class="f-row"><div class="seg" id="ps"></div></div></div></div><div class="card"><div class="card-b" id="pres"></div></div>`;
    const isOpen = (r) => r.status === "new" || r.status === "in_review";
    const draw = () => {
      writeParams("appeals", f, { kind: "", status: "", q: "" });
      const toks = tokens(f.q);
      const base = rows.filter((r) => !toks.length || toks.every((t) => norm([r.full_name, r.username, r.first_text].join(" ")).includes(t)));
      const byKind = base.filter((r) => !f.kind || r.kind === f.kind);
      $("#pk").innerHTML = [["", "Barchasi"], ...Object.entries(AP_KIND).map(([k, v]) => [k, v[0]])].map(([k, l]) => `<button data-k="${k}" class="${f.kind === k ? "on" : ""}">${l}<i>${base.filter((r) => !k || r.kind === k).length}</i></button>`).join("");
      $("#ps").innerHTML = [["", "Hammasi"], ["open", "Ochiq"], ...Object.entries(AP_ST).map(([k, v]) => [k, v[0]])].map(([k, l]) => `<button data-s="${k}" class="${f.status === k ? "on" : ""}">${l}<i>${byKind.filter((r) => !k || (k === "open" ? isOpen(r) : r.status === k)).length}</i></button>`).join("");
      $$("#pk button").forEach((b) => b.onclick = () => { f.kind = b.dataset.k; draw(); });
      $$("#ps button").forEach((b) => b.onclick = () => { f.status = b.dataset.s; draw(); });
      const list = byKind.filter((r) => !f.status || (f.status === "open" ? isOpen(r) : r.status === f.status));
      $("#pres").innerHTML = list.length ? `<div class="list">${list.map((r) => {
        const k = AP_KIND[r.kind] || ["?", "mute", "chat"];
        return `<div class="li click" data-uid="${r.user_id}" data-tab="appeals"><span class="dot-ico" style="background:color-mix(in srgb, var(--${k[1] === "mute" ? "muted" : k[1]}) 15%, transparent);color:var(--${k[1]})">${ic(k[2])}</span>
          <div class="grow"><b>${hl(r.full_name, f.q)} <span style="color:var(--faint);font-weight:600">#${r.id} · ${k[0]}</span></b><small>${hl((r.first_text || "(fayl)").slice(0, 140), f.q)}</small></div>
          <span class="badge mute">${r.messages} xabar</span>${badge(AP_ST[r.status])}<span class="time">${ago(r.last_at || r.created_at)}</span></div>`;
      }).join("")}</div>` : emptyBox("Murojaatlar topilmadi");
    };
    let t; $("#pq").oninput = (e) => { clearTimeout(t); t = setTimeout(() => { f.q = e.target.value; draw(); }, 120); };
    draw();
  },
};

/* ---------- bot faolligi ---------- */
PAGES.activity = {
  title: "Bot faolligi",
  sub: () => "Kim, qachon va qaysi bo'limlardan foydalanmoqda",
  async mount(el, params) {
    const days = params.get("days") || "30";
    const d = await api(`/api/activity?days=${days}`, true);
    const t = d.totals;
    const max = Math.max(...d.heatmap.map((x) => x.n), 1);
    const H = {}; d.heatmap.forEach((x) => (H[`${x.dow}-${x.h}`] = x.n));
    const DOW = ["Du", "Se", "Ch", "Pa", "Ju", "Sh", "Ya"];
    const kindTotal = d.kinds.reduce((a, b) => a + b.n, 0);
    el.innerHTML = `
      <div class="f-row"><div class="seg" id="dseg">${[["1", "24 soat"], ["7", "7 kun"], ["30", "30 kun"], ["90", "90 kun"]].map(([k, l]) => `<button data-d="${k}" class="${days === k ? "on" : ""}">${l}</button>`).join("")}</div></div>
      <div class="grid g-kpi">
        ${[["pulse", "Faol · 24 soat (DAU)", t.dau], ["users", "Faol · 7 kun (WAU)", t.wau], ["send", "Amallar soni", t.actions], ["userPlus", "Noyob foydalanuvchilar", t.users]].map(([i, l, v]) => `<div class="card kpi"><div class="kpi-top"><span class="kpi-ico">${ic(i)}</span>${l}</div><div class="kpi-val">${fmtN(v)}</div><div class="kpi-foot">tanlangan davr</div></div>`).join("")}
      </div>
      <div class="grid g-2">
        <div class="card"><div class="card-h"><h3>Haftalik issiqlik xaritasi</h3><span class="sub">hafta kuni × soat</span></div><div class="card-b">
          <div class="heat"><span></span>${Array.from({ length: 24 }, (_, h) => `<span class="hl">${h % 3 === 0 ? h : ""}</span>`).join("")}
          ${DOW.map((n, i) => `<span class="lbl">${n}</span>` + Array.from({ length: 24 }, (_, h) => { const v = H[`${i + 1}-${h}`] || 0; return `<span class="c" title="${n}, ${h}:00 — ${v} ta amal" style="opacity:${v ? 0.15 + (v / max) * 0.85 : 0.06}"></span>`; }).join("")).join("")}
          </div></div></div>
        <div class="card"><div class="card-h"><h3>Xabar turlari</h3></div><div class="card-b"><div class="chart-box sm" style="height:180px"><canvas id="kinds"></canvas></div>
          <div style="margin-top:10px">${barRows(d.kinds, (x) => KIND[x.k] || x.k, kindTotal)}</div></div></div>
      </div>
      <div class="grid g-11">
        <div class="card"><div class="card-h"><h3>Eng ko'p bosilgan bo'limlar</h3></div><div class="card-b">${d.actions.length ? d.actions.map((x) => { const mx = d.actions[0].n; return `<div class="bar-row"><span>${esc(actLabel(x.k))}</span><b>${fmtN(x.n)} <small style="color:var(--faint);font-weight:600">· ${fmtN(x.u)} kishi</small></b><div class="bar"><i style="width:${(x.n / mx) * 100}%"></i></div></div>`; }).join("") : emptyBox("Hali ma'lumot yo'q", " Bot ishlagan sari to'planadi.")}</div></div>
        <div class="card"><div class="card-h"><h3>Soatlar kesimida</h3></div><div class="card-b"><div class="chart-box"><canvas id="hours"></canvas></div></div></div>
      </div>
      <div class="card"><div class="card-h"><h3>Jonli lenta</h3><span class="sub">oxirgi 40 ta amal · har 30 soniyada yangilanadi</span></div><div class="card-b"><div class="list">
        ${d.recent.map((x) => `<div class="li click" data-uid="${x.user_id}"><span class="dot-ico" style="background:var(--accent-soft);color:var(--accent)">${ic(x.kind === "command" ? "send" : x.kind === "photo" ? "camOff" : x.kind === "text" ? "chat" : "pulse")}</span><div class="grow"><b>${esc(x.full_name || "ID " + x.user_id)}</b><small>${esc(KIND[x.kind] || x.kind)}${x.action ? " · " + esc(actLabel(x.action)) : ""}</small></div><span class="time">${ago(x.created_at)}</span></div>`).join("") || emptyBox("Hali faollik yo'q")}
      </div></div></div>`;
    $$("#dseg button").forEach((b) => b.onclick = () => (location.hash = `#/activity?days=${b.dataset.d}`));
    if (d.kinds.length) doughnut($("#kinds"), d.kinds.map((x) => KIND[x.k] || x.k), d.kinds.map((x) => x.n));
    const hours = Array(24).fill(0); d.hours.forEach((x) => (hours[x.h] = x.n));
    barChart($("#hours"), hours.map((_, h) => `${h}:00`), hours);
  },
};

/* ================= TALABA KARTOCHKASI ================= */
async function openStudent(uid, tab = "app") {
  const dr = $("#drawer");
  dr.innerHTML = `<div class="dr-head"><div class="skel" style="width:96px;height:120px;border-radius:16px"></div><div class="dr-id" style="flex:1"><div class="skel" style="height:26px;width:70%"></div><div class="skel" style="height:14px;width:50%"></div></div></div><div class="dr-body"><div class="skel" style="height:80px"></div><div class="skel" style="height:220px"></div></div>`;
  dr.classList.add("on"); $("#drawerScrim").classList.add("on"); dr.setAttribute("aria-hidden", "false");
  let s;
  try { s = await api(`/api/students/${uid}`, true); } catch { dr.innerHTML = emptyBox("Talaba topilmadi"); return; }
  const cp = (v) => (v ? `<button class="copy" title="Nusxa olish" data-copy="${esc(v)}">${ic("copy")}</button>` : "");
  const app = s.applications[0];
  dr.innerHTML = `
    <div class="dr-head">
      ${avatar(s, "lg")}
      <div class="dr-id"><h2>${esc(s.full_name || "—")}</h2>
        <p>${s.username ? `<a href="https://t.me/${esc(s.username.replace("@", ""))}" target="_blank" rel="noopener">${esc(s.username)}</a> · ` : ""}ID ${s.user_id}</p>
        <div class="dr-tags">${badge(ST[s.status])}${s.member_no ? `<span class="badge gold">${esc(s.member_no)}</span>` : ""}${s.section_name ? `<span class="badge mute">${esc(s.section_name)}</span>` : ""}${s.member_no ? `<span class="badge">${esc(levelName(s))}</span>` : ""}</div>
      </div>
      <button class="icon-btn x" id="drClose" title="Yopish (Esc)">${ic("x")}</button>
    </div>
    <div class="dr-body">
      <div class="dr-stats"><div><b>${s.points}</b><small>jami ball</small></div><div><b>${s.points_sem}</b><small>semestr</small></div><div><b>${s.attended}</b><small>davomat</small></div><div><b>${s.actions_30d}</b><small>amal / 30 kun</small></div></div>
      <dl class="kv">
        <dt>Yo'nalish</dt><dd>${esc(s.direction || "—")}</dd>
        <dt>Kurs · guruh</dt><dd>${course(s.course)} · ${esc(s.group_name || "—")}</dd>
        <dt>Talaba ID</dt><dd>${esc(s.student_id || "—")}${cp(s.student_id)}</dd>
        <dt>Telefon</dt><dd>${s.phone ? `<a href="tel:${esc(s.phone)}">${esc(s.phone)}</a>` : "—"}${cp(s.phone)}</dd>
        <dt>Bot tili</dt><dd>${LANG[s.lang] || s.lang}</dd>
        <dt>Ro'yxatdan o'tgan</dt><dd>${fmtDate(s.created_at, true)}</dd>
        <dt>A'zo bo'lgan</dt><dd>${s.joined_at ? fmtDate(s.joined_at) : "—"}</dd>
        <dt>Oxirgi faollik</dt><dd>${s.last_seen ? `${ago(s.last_seen)} <span style="color:var(--faint)">(${fmtDate(s.last_seen, true)})</span>` : "—"}</dd>
      </dl>
      <div class="tabs" id="drTabs">
        <button data-t="app">Ariza${s.applications.length ? ` (${s.applications.length})` : ""}</button>
        <button data-t="points">Ballar (${s.points_log.length})</button>
        <button data-t="events">Tadbirlar (${s.tickets_log.length})</button>
        <button data-t="appeals">Murojaatlar (${s.appeals.length})</button>
        <button data-t="act">Faollik</button>
      </div>
      <div id="drTab"></div>
    </div>`;
  const tabs = {
    app: () => app ? `<div style="display:flex;gap:8px;align-items:center;margin-bottom:12px;flex-wrap:wrap">${badge(APP_ST[app.status])}<span class="badge mute">#${app.id} · ${app.app_type === "renew" ? "Yangilash" : "Yangi a'zolik"}</span><span style="color:var(--muted);font-size:12px">${fmtDate(app.created_at, true)}</span></div>
      ${app.reason ? `<div class="alert warn" style="margin-bottom:12px"><b>Sabab:</b> ${esc(app.reason)}</div>` : ""}
      <div class="qa">${app.answers.map((a) => `<div><small>${esc(a.k)}</small><p>${esc(a.v)}</p></div>`).join("")}</div>
      ${s.applications.length > 1 ? `<div style="margin-top:14px;color:var(--muted);font-size:12.5px">Oldingi arizalar: ${s.applications.slice(1).map((a) => `#${a.id} ${(APP_ST[a.status] || [a.status])[0]} (${fmtDate(a.created_at)})`).join(", ")}</div>` : ""}` : emptyBox("Ariza topshirilmagan"),
    points: () => s.points_log.length ? `<div class="list">${s.points_log.map((p) => `<div class="li"><span class="dot-ico" style="background:var(--accent-soft);color:var(--accent)">${ic("star")}</span><div class="grow"><b>${esc(p.reason || "Ball")}</b><small>${fmtDate(p.created_at, true)}</small></div><span class="badge ${p.amount >= 0 ? "ok" : "bad"}">${p.amount > 0 ? "+" : ""}${p.amount}</span></div>`).join("")}</div>` : emptyBox("Ball berilmagan"),
    events: () => s.tickets_log.length ? `<div class="list">${s.tickets_log.map((t) => `<div class="li"><span class="dot-ico" style="background:var(--accent-soft);color:var(--accent)">${ic("ticket")}</span><div class="grow"><b>${esc(t.title)}</b><small>${esc(t.date_text || "")}${t.used_at ? " · keldi " + fmtDate(t.used_at, true) : ""}</small></div>${badge(TK_ST[t.status])}</div>`).join("")}</div>` : emptyBox("Tadbirlarga yozilmagan"),
    appeals: () => s.appeals.length ? `<div class="list">${s.appeals.map((a) => `<div class="li"><span class="dot-ico" style="background:var(--accent-soft);color:var(--accent)">${ic((AP_KIND[a.kind] || [, , "chat"])[2])}</span><div class="grow"><b>#${a.id} · ${esc((AP_KIND[a.kind] || [a.kind])[0])}</b><small>${esc((a.first_text || "(fayl)").slice(0, 160))}</small></div>${badge(AP_ST[a.status])}</div>`).join("")}</div>` : emptyBox("Murojaat yo'q"),
    act: () => s.activity.length ? `<div class="list">${s.activity.map((x) => `<div class="li"><div class="grow"><b style="font-weight:600">${esc(KIND[x.kind] || x.kind)}${x.action ? " · " + esc(actLabel(x.action)) : ""}</b></div><span class="time">${fmtDate(x.created_at, true)}</span></div>`).join("")}</div>` : emptyBox("Faollik qayd etilmagan"),
  };
  const show = (t) => { $$("#drTabs button").forEach((b) => b.classList.toggle("on", b.dataset.t === t)); $("#drTab").innerHTML = tabs[t](); };
  $$("#drTabs button").forEach((b) => b.onclick = () => show(b.dataset.t));
  show(tabs[tab] ? tab : "app");
  $("#drClose").onclick = closeDrawer;
}
function closeDrawer() { $("#drawer").classList.remove("on"); $("#drawerScrim").classList.remove("on"); $("#drawer").setAttribute("aria-hidden", "true"); }
$("#drawerScrim").onclick = closeDrawer;
document.addEventListener("click", (e) => {
  const el = e.target.closest("[data-uid]");
  if (el && !e.target.closest("a[href], button, .copy") && $("#view").contains(el)) openStudent(el.dataset.uid, el.dataset.tab);
});

/* ================= Ctrl+K ================= */
/* ---------- ochiq sayt: e'lon va reklamalar ---------- */
const POST_KIND = { ad: ["Reklama", "gold"], news: ["E'lon", "info"] };
PAGES.siteposts = {
  refresh: async () => {},           // avtomatik yangilanish tahrirni buzmasin
  title: "E'lon va reklamalar",
  sub: () => "Asosiy saytda hammaga ko'rinadi",
  async mount(el) {
    let rows = await api("/api/site/posts", true);
    let edit = null;                      // tahrirlanayotgan e'lon (yoki yangi)
    const blank = () => ({ kind: "ad", title: "", body: "", image_id: null, image_url: null, link_url: "", link_label: "", pinned: false, active: true });
    const form = () => {
      const p = edit;
      return `<div class="card"><div class="card-h"><h3>${p.id ? "E'lonni tahrirlash" : "Yangi e'lon yoki reklama"}</h3></div><div class="card-b">
        <div class="fgrid">
          <div class="fld full"><span>Turi</span><div class="seg" id="pkind"><button type="button" data-k="ad" class="${p.kind === "ad" ? "on" : ""}">Reklama</button><button type="button" data-k="news" class="${p.kind === "news" ? "on" : ""}">E'lon / yangilik</button></div></div>
          <label class="fld full"><span>Sarlavha *</span><input class="inp" id="ptitle" maxlength="200" value="${esc(p.title)}" placeholder="Masalan: Model UN 2026 — ro'yxatdan o'tish boshlandi"></label>
          <label class="fld full"><span>Matn</span><textarea class="inp" id="pbody" rows="5" maxlength="4000" placeholder="Batafsil ma'lumot, sana, joy…">${esc(p.body || "")}</textarea></label>
          <div class="fld full"><span>Rasm</span><div class="img-pick">
            ${p.image_url ? `<img class="thumb" src="${esc(p.image_url)}" alt="">` : `<div class="thumb empty-thumb">${ic("camOff")}<small>Rasm tanlanmagan</small></div>`}
            <div class="img-act"><label class="btn sm">${ic("dl")}Rasm yuklash<input type="file" id="pimg" accept="image/*" hidden></label>${p.image_url ? `<button type="button" class="btn sm ghost" id="pimgx">${ic("x")}Rasmni olib tashlash</button>` : ""}<small class="hint">JPG, PNG yoki WEBP, 8 MB gacha</small></div></div></div>
          <label class="fld"><span>Havola (ixtiyoriy)</span><input class="inp" id="plink" maxlength="500" value="${esc(p.link_url || "")}" placeholder="https://t.me/…"></label>
          <label class="fld"><span>Tugma matni</span><input class="inp" id="plabel" maxlength="60" value="${esc(p.link_label || "")}" placeholder="Batafsil"></label>
          <div class="fld full f-row"><span class="tog ${p.pinned ? "on" : ""}" id="ppin" role="switch" tabindex="0" aria-checked="${p.pinned}"><span class="sw"></span>Muhim (tepada turadi)</span><span class="tog ${p.active ? "on" : ""}" id="pact" role="switch" tabindex="0" aria-checked="${p.active}"><span class="sw"></span>Saytda ko'rinsin</span></div>
        </div>
        <div class="f-row" style="margin-top:16px"><button class="btn primary" id="psave">${ic("check")}Saqlash</button><button class="btn ghost" id="pcancel">Bekor qilish</button></div>
      </div></div>`;
    };
    const list = () => rows.length ? `<div class="card"><div class="card-h"><h3>Barcha e'lonlar</h3><span class="sub">${rows.length} ta</span></div><div class="card-b"><div class="list">${rows.map((p) => `
        <div class="post-row">${p.image_url ? `<img src="${esc(p.image_url)}" alt="">` : `<span class="post-noimg">${ic("file")}</span>`}
          <div class="grow"><b>${esc(p.title)}</b><small>${badge(POST_KIND[p.kind])} ${p.pinned ? badge(["Muhim", "warn"]) : ""} ${p.active ? "" : badge(["Yashirin", "mute"])} · ${fmtDate(p.created_at)}</small></div>
          <div class="row-act"><button class="btn sm" data-edit="${p.id}">Tahrirlash</button><button class="btn sm ghost" data-hide="${p.id}">${p.active ? "Yashirish" : "Ko'rsatish"}</button><button class="btn sm ghost danger" data-del="${p.id}" aria-label="O'chirish">${ic("x")}</button></div></div>`).join("")}</div></div></div>`
      : `<div class="card">${emptyBox("Hali e'lon yo'q", " «Yangi e'lon» tugmasi bilan birinchisini qo'shing — u darhol saytda chiqadi.")}</div>`;
    const draw = () => {
      el.innerHTML = `<div class="res-bar"><span class="res-count">Saytda ko'rinadigan: <b>${rows.filter((p) => p.active).length}</b></span><div class="f-row"><a class="btn" href="/" target="_blank" rel="noopener">${ic("door")}Saytni ochish</a>${edit ? "" : `<button class="btn primary" id="pnew">+ Yangi e'lon</button>`}</div></div>${edit ? form() : ""}${list()}`;
      const nb = $("#pnew"); if (nb) nb.onclick = () => { edit = blank(); draw(); };
      if (edit) bindForm();
      $$("[data-edit]", el).forEach((b) => b.onclick = () => { edit = { ...rows.find((p) => p.id == b.dataset.edit) }; draw(); scrollTo({ top: 0, behavior: "smooth" }); });
      $$("[data-hide]", el).forEach((b) => b.onclick = async () => {
        const p = rows.find((x) => x.id == b.dataset.hide);
        try { await send("PUT", `/api/site/posts/${p.id}`, { ...p, active: !p.active }); toast(p.active ? "Saytdan yashirildi" : "Saytda ko'rsatildi"); rows = await api("/api/site/posts", true); draw(); } catch (e) { toast(e.message); }
      });
      $$("[data-del]", el).forEach((b) => b.onclick = async () => {
        const p = rows.find((x) => x.id == b.dataset.del);
        if (!confirm(`«${p.title}» o'chirilsinmi? Buni qaytarib bo'lmaydi.`)) return;
        try { await send("DELETE", `/api/site/posts/${p.id}`); toast("O'chirildi"); rows = await api("/api/site/posts", true); draw(); } catch (e) { toast(e.message); }
      });
    };
    const bindForm = () => {
      const keep = () => Object.assign(edit, { title: $("#ptitle").value, body: $("#pbody").value, link_url: $("#plink").value, link_label: $("#plabel").value });
      $$("#pkind button").forEach((b) => b.onclick = () => { keep(); edit.kind = b.dataset.k; draw(); });
      const tg = (id, key) => { const t = $(id); const flip = () => { keep(); edit[key] = !edit[key]; draw(); }; t.onclick = flip; t.onkeydown = (e) => { if (e.key === " " || e.key === "Enter") { e.preventDefault(); flip(); } }; };
      tg("#ppin", "pinned"); tg("#pact", "active");
      $("#pimg").onchange = async (e) => {
        const f = e.target.files[0]; if (!f) return; keep();
        try { toast("Rasm yuklanmoqda…"); const m = await send("POST", "/api/site/media", { data: await readFile(f) }); edit.image_id = m.id; edit.image_url = m.url; draw(); } catch (err) { toast(err.message); }
      };
      const x = $("#pimgx"); if (x) x.onclick = () => { keep(); edit.image_id = null; edit.image_url = null; draw(); };
      $("#pcancel").onclick = () => { edit = null; draw(); };
      $("#psave").onclick = async () => {
        keep();
        if (!edit.title.trim()) { toast("Sarlavhani yozing"); $("#ptitle").focus(); return; }
        try {
          if (edit.id) await send("PUT", `/api/site/posts/${edit.id}`, edit); else await send("POST", "/api/site/posts", edit);
          toast("Saqlandi — saytda yangilandi"); edit = null; rows = await api("/api/site/posts", true); draw();
        } catch (e) { toast(e.message); }
      };
    };
    draw();
  },
};

/* ---------- ochiq sayt: galereya ---------- */
PAGES.sitegallery = {
  refresh: async () => {},           // avtomatik yangilanish tahrirni buzmasin
  title: "Galereya",
  sub: () => "Saytdagi rasmlar bo'limi",
  async mount(el) {
    let rows = await api("/api/site/gallery", true);
    const draw = () => {
      el.innerHTML = `<div class="card"><div class="card-b" style="padding-top:20px"><div class="f-row"><label class="btn primary">${ic("dl")}Rasm qo'shish<input type="file" id="gup" accept="image/*" multiple hidden></label><span class="hint">Bir nechta rasmni birdaniga tanlash mumkin · JPG, PNG, WEBP · 8 MB gacha</span><a class="btn" style="margin-left:auto" href="/#galereya" target="_blank" rel="noopener">${ic("door")}Saytda ko'rish</a></div></div></div>
        ${rows.length ? `<div class="g-grid">${rows.map((g) => `<div class="card g-cell"><img src="${esc(g.url)}" alt="" loading="lazy"><input class="inp" data-cap="${g.id}" maxlength="300" value="${esc(g.caption || "")}" placeholder="Izoh (ixtiyoriy)" aria-label="Rasm izohi"><div class="f-row"><small class="hint">${fmtDate(g.created_at)}</small><button class="btn sm ghost danger" style="margin-left:auto" data-gdel="${g.id}">${ic("x")}O'chirish</button></div></div>`).join("")}</div>`
          : `<div class="card">${emptyBox("Galereya bo'sh", " Rasm qo'shsangiz, saytda «Galereya» bo'limi paydo bo'ladi.")}</div>`}`;
      $("#gup").onchange = async (e) => {
        const files = [...e.target.files]; if (!files.length) return;
        let n = 0;
        for (const f of files) {
          try { toast(`Yuklanmoqda: ${++n}/${files.length}`); await send("POST", "/api/site/media", { data: await readFile(f), in_gallery: true }); } catch (err) { toast(`${f.name}: ${err.message}`); }
        }
        rows = await api("/api/site/gallery", true); draw(); toast("Galereya yangilandi");
      };
      $$("[data-cap]", el).forEach((i) => i.onchange = async () => { try { await send("PUT", `/api/site/media/${i.dataset.cap}`, { caption: i.value }); toast("Izoh saqlandi"); } catch (e) { toast(e.message); } });
      $$("[data-gdel]", el).forEach((b) => b.onclick = async () => {
        if (!confirm("Rasm o'chirilsinmi? Buni qaytarib bo'lmaydi.")) return;
        try { await send("DELETE", `/api/site/media/${b.dataset.gdel}`); rows = await api("/api/site/gallery", true); draw(); toast("O'chirildi"); } catch (e) { toast(e.message); }
      });
    };
    draw();
  },
};

/* ---------- ochiq sayt: ma'lumotlar ---------- */
const SITE_FIELDS = [
  ["hero_title", "Sayt nomi", "input"], ["hero_subtitle", "Qisqa tavsif (bosh sahifa)", "input"], ["motto", "Shior", "input"],
  ["about", "Biz haqimizda", "textarea"], ["phone", "Telefon", "input"], ["email", "Email (ixtiyoriy)", "input"],
  ["address", "Manzil", "input"], ["map_query", "Xaritada qidirish so'zi", "input"], ["hours", "Ish vaqti", "input"],
  ["telegram", "Telegram kanal havolasi", "input"], ["instagram", "Instagram havolasi", "input"], ["bot", "Telegram bot havolasi", "input"],
];
PAGES.siteinfo = {
  refresh: async () => {},           // avtomatik yangilanish tahrirni buzmasin
  title: "Sayt ma'lumotlari",
  sub: () => "Manzil, telefon, ijtimoiy tarmoqlar va matnlar",
  async mount(el) {
    const s = await api("/api/site/settings", true);
    el.innerHTML = `<div class="card"><div class="card-h"><h3>Asosiy sahifadagi ma'lumotlar</h3><a class="btn sm" href="/" target="_blank" rel="noopener">${ic("door")}Saytni ochish</a></div><div class="card-b">
      <div class="fgrid">${SITE_FIELDS.map(([k, l, t]) => `<label class="fld ${t === "textarea" || k === "address" ? "full" : ""}"><span>${l}</span>${t === "textarea"
        ? `<textarea class="inp" data-k="${k}" rows="4" maxlength="2000">${esc(s[k] || "")}</textarea>` : `<input class="inp" data-k="${k}" maxlength="2000" value="${esc(s[k] || "")}">`}</label>`).join("")}</div>
      <div class="f-row" style="margin-top:16px"><button class="btn primary" id="ssave">${ic("check")}Saqlash</button><span class="hint">O'zgarishlar saytda darhol ko'rinadi</span></div></div></div>`;
    $("#ssave").onclick = async () => {
      const data = {}; $$("[data-k]", el).forEach((i) => (data[i.dataset.k] = i.value));
      try { await send("PUT", "/api/site/settings", data); toast("Saqlandi — saytda yangilandi"); } catch (e) { toast(e.message); }
    };
  },
};

const NAV = [["overview", "Umumiy ko'rinish", "grid"], ["students", "Talabalar", "users"], ["applications", "Arizalar", "file"], ["events", "Tadbirlar", "cal"], ["appeals", "Murojaatlar", "chat"], ["activity", "Bot faolligi", "pulse"], ["siteposts", "E'lon va reklamalar", "send"], ["sitegallery", "Galereya", "grid"], ["siteinfo", "Sayt ma'lumotlari", "pin"]];
let cmdSel = 0, cmdItems = [];
async function openCmd() {
  $("#cmdk").hidden = false; const inp = $("#cmdInput"); inp.value = ""; inp.focus();
  if (!S.students) { try { S.students = await api("/api/students"); } catch { S.students = []; } }
  drawCmd();
}
function drawCmd() {
  const q = $("#cmdInput").value, toks = tokens(q);
  const studs = toks.length ? (S.students || []).filter((r) => matchQ(r, toks)).slice(0, 8) : (S.students || []).slice(0, 5);
  const navs = NAV.filter((n) => !toks.length || toks.every((t) => norm(n[1]).includes(t)));
  cmdItems = [...studs.map((r) => ({ t: "s", r })), ...navs.map((n) => ({ t: "n", n }))];
  cmdSel = Math.min(cmdSel, Math.max(cmdItems.length - 1, 0));
  let i = -1;
  $("#cmdList").innerHTML = (studs.length ? `<div class="cmdk-sec">${toks.length ? "Talabalar" : "Yangi qo'shilganlar"}</div>` + studs.map((r) => { i++; return `<div class="cmdk-item ${i === cmdSel ? "sel" : ""}" data-i="${i}">${avatar(r)}<div class="grow"><b>${hl(r.full_name || "—", q)}</b><small>${esc(r.direction || "")} · ${course(r.course)} · ${esc(r.group_name || "")}${r.phone ? " · " + esc(r.phone) : ""}</small></div>${badge(ST[r.status])}</div>`; }).join("") : toks.length ? '<div class="empty" style="padding:24px">Talaba topilmadi</div>' : "")
    + (navs.length ? `<div class="cmdk-sec">Sahifalar</div>` + navs.map((n) => { i++; return `<div class="cmdk-item ${i === cmdSel ? "sel" : ""}" data-i="${i}"><span class="dot-ico" style="background:var(--accent-soft);color:var(--accent)">${ic(n[2])}</span><div class="grow"><b>${n[1]}</b></div></div>`; }).join("") : "");
  $$(".cmdk-item").forEach((el) => el.onclick = () => runCmd(Number(el.dataset.i)));
}
function runCmd(i) {
  const it = cmdItems[i]; if (!it) return;
  $("#cmdk").hidden = true;
  if (it.t === "s") openStudent(it.r.user_id); else location.hash = `#/${it.n[0]}`;
}
$("#cmdInput").addEventListener("input", () => { cmdSel = 0; drawCmd(); });
$("#cmdInput").addEventListener("keydown", (e) => {
  if (e.key === "ArrowDown") { cmdSel = Math.min(cmdSel + 1, cmdItems.length - 1); drawCmd(); e.preventDefault(); }
  if (e.key === "ArrowUp") { cmdSel = Math.max(cmdSel - 1, 0); drawCmd(); e.preventDefault(); }
  if (e.key === "Enter") runCmd(cmdSel);
});
$("#cmdk").addEventListener("click", (e) => { if (e.target.id === "cmdk") $("#cmdk").hidden = true; });
$("#cmdBtn").onclick = openCmd;
document.addEventListener("keydown", (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") { e.preventDefault(); openCmd(); }
  else if (e.key === "/" && !/INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName)) { e.preventDefault(); const s = $("#sq"); s ? s.focus() : openCmd(); }
  else if (e.key === "Escape") { $("#cmdk").hidden = true; closeDrawer(); $$(".dd.open").forEach((d) => d.classList.remove("open")); }
});

/* ================= marshrutlash, mavzu, yangilash ================= */
function setBadges(k) {
  $("#navStudents").textContent = k.registered ? fmtN(k.registered) : "";
  $("#navApps").textContent = k.apps_pending || "";
  $("#navAppeals").textContent = k.appeals_open || "";
}
async function route() {
  const raw = location.hash.replace(/^#\/?/, "") || "overview";
  const [name, qs] = raw.split("?");
  const page = PAGES[name] ? name : "overview";
  const params = new URLSearchParams(qs || "");
  S.page = page;
  $$(".nav a").forEach((a) => a.classList.toggle("active", a.dataset.page === page));
  $("#pageTitle").textContent = PAGES[page].title;
  $("#pageSub").textContent = PAGES[page].sub();
  document.title = `${PAGES[page].title} · MULOQOT`;
  $("#sidebar").classList.remove("on"); $("#scrim").classList.remove("on");
  killCharts();
  const view = $("#view");
  view.style.animation = "none"; void view.offsetWidth; view.style.animation = "";
  try { await PAGES[page].mount(view, params); S.loadedAt = new Date(); }
  catch (err) { if (err.message !== "auth") view.innerHTML = `<div class="card">${emptyBox("Ma'lumot yuklanmadi", " " + err.message)}</div>`; }
}
let skipRoute = false;
window.addEventListener("hashchange", () => { if (!skipRoute) route(); });

function applyTheme(t) {
  document.documentElement.dataset.theme = t;
  try { localStorage.setItem("mlq_theme", t); } catch {}
  if (S.page === "students") { /* grafik yo'q — qayta chizish shart emas */ } else route();
}
$$(".theme-switch button").forEach((b) => b.onclick = () => applyTheme(b.dataset.t));
$("#menuBtn").onclick = () => { $("#sidebar").classList.add("on"); $("#scrim").classList.add("on"); };
$("#scrim").onclick = () => { $("#sidebar").classList.remove("on"); $("#scrim").classList.remove("on"); };

async function refresh(manual) {
  const btn = $("#refreshBtn"); btn.classList.remove("spin"); void btn.offsetWidth; btn.classList.add("spin");
  const busy = $("#drawer").classList.contains("on") || $(".dd.open") || !$("#cmdk").hidden;
  if (!manual && busy) return;
  const p = PAGES[S.page];
  if (p.refresh) await p.refresh(); else await route();
  api("/api/overview", true).then((d) => setBadges(d.kpi)).catch(() => {});
  if (manual) toast("Ma'lumotlar yangilandi");
}
$("#refreshBtn").onclick = () => refresh(true);
// jonli yangilanish: faollik sahifasi har 30 soniyada, qolganlari har daqiqada
let tick = 0;
setInterval(() => { tick++; if (!document.hidden && (S.page === "activity" || tick % 2 === 0)) refresh(false); }, 30000);

api("/api/overview").then((d) => setBadges(d.kpi)).catch(() => {});
route();
