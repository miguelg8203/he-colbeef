// ── API base ──────────────────────────────────────────────────────────────────
const API = {
  base: window.location.origin === "null" || window.location.hostname === "127.0.0.1" 
    ? "http://127.0.0.1:8000" 
    : window.location.origin,

  async get(path) {
    const r = await fetch(this.base + path);
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  },

  async post(path, body) {
    const r = await fetch(this.base + path, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  },

  async put(path, body) {
    const r = await fetch(this.base + path, {
      method: "PUT", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  },

  async del(path) {
    const r = await fetch(this.base + path, { method: "DELETE" });
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  },

  pdfUrl(path) { return this.base + path; },
};

// ── Helpers ───────────────────────────────────────────────────────────────────
const MESES = ["","Enero","Febrero","Marzo","Abril","Mayo","Junio",
               "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"];
const DIAS  = ["Dom","Lun","Mar","Mié","Jue","Vie","Sáb"];

function periodLabel(y, m) {
  const em = m === 12 ? 1 : m + 1;
  const ey = m === 12 ? y + 1 : y;
  return `21 ${MESES[m].slice(0,3)} → 20 ${MESES[em].slice(0,3)} ${ey}`;
}

function currPeriod() {
  const n = new Date();
  const d = n.getDate(), mo = n.getMonth() + 1, y = n.getFullYear();
  if (d >= 21) return { y, m: mo };
  return mo === 1 ? { y: y - 1, m: 12 } : { y, m: mo - 1 };
}

function fmt(v) {
  if (v === null || v === undefined || v === 0) return "";
  return Number(v).toFixed(1);
}

function fmtCop(v) {
  return "$" + Number(v).toLocaleString("es-CO", { maximumFractionDigits: 0 });
}

function fmtOT(v) {
  if (v === 0) return "";
  return (v > 0 ? "+" : "") + Number(v).toFixed(1) + "h";
}

// ── UI utilities ──────────────────────────────────────────────────────────────
const UI = {
  openModal(id)  { document.getElementById(id).classList.add("open"); },
  closeModal(id) { document.getElementById(id).classList.remove("open"); },

  toast(msg, type = "ok") {
    const t = document.getElementById("toast");
    t.textContent = msg;
    t.className = `toast show ${type}`;
    setTimeout(() => { t.className = "toast"; }, 2800);
  },

  confirm(msg, cb) {
    document.getElementById("confirm-msg").textContent = msg;
    const btn = document.getElementById("confirm-ok");
    btn.onclick = () => { UI.closeModal("modal-confirm"); cb(); };
    UI.openModal("modal-confirm");
  },
};

// ── Global state ──────────────────────────────────────────────────────────────
const STATE = {
  tecnicos:     [],
  observaciones:[],
  config:       {},
  planPeriod:   currPeriod(),
  resPeriod:    currPeriod(),
  planTecId:    null,
};

// ── Navigation ────────────────────────────────────────────────────────────────
document.querySelectorAll(".nv").forEach(btn => {
  btn.addEventListener("click", () => {
    const v = btn.dataset.view;
    document.querySelectorAll(".nv").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".view").forEach(s => s.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById("view-" + v).classList.add("active");
    if (v === "planilla") PLAN.init();
    if (v === "resumen")  RES.init();
    if (v === "config")   CFG.init();
  });
});

// ── Boot ──────────────────────────────────────────────────────────────────────
async function boot() {
  try {
    STATE.tecnicos      = await API.get("/tecnicos/");
    STATE.observaciones = await API.get("/observaciones");
    STATE.config        = await API.get("/config");
    TEC.render();
    PLAN.initSelects();
  } catch(e) {
    UI.toast("⚠️ No se pudo conectar al servidor. ¿Está corriendo Python?", "err");
  }
}

boot();
