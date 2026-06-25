const API = {
  base: window.location.hostname === "127.0.0.1" || window.location.hostname === "localhost"
    ? "http://127.0.0.1:8000" : window.location.origin,
  _eid: () => STATE.empresa?.empresa_id || "",
  async get(path) {
    const r = await fetch(this.base + path);
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  },
  async post(path, body) {
    const r = await fetch(this.base + path, {
      method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(body)
    });
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  },
  async put(path, body) {
    const r = await fetch(this.base + path, {
      method:"PUT", headers:{"Content-Type":"application/json"}, body:JSON.stringify(body)
    });
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  },
  async del(path) {
    const r = await fetch(this.base + path, {method:"DELETE"});
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  },
  pdfUrl(path) { return this.base + path + "?empresa_id=" + this._eid(); },
};

const MESES = ["","Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"];
const DIAS  = ["Dom","Lun","Mar","Mié","Jue","Vie","Sáb"];

function periodLabel(y,m) {
  const em=m===12?1:m+1, ey=m===12?y+1:y;
  return `21 ${MESES[m].slice(0,3)} → 20 ${MESES[em].slice(0,3)} ${ey}`;
}
function currPeriod() {
  const n=new Date(), d=n.getDate(), mo=n.getMonth()+1, y=n.getFullYear();
  if(d>=21) return {y,m:mo};
  return mo===1?{y:y-1,m:12}:{y,m:mo-1};
}
function fmt(v) { if(v===null||v===undefined||v===0) return ""; return Number(v).toFixed(1); }
function fmtCop(v) { return "$"+Number(v).toLocaleString("es-CO",{minimumFractionDigits:2,maximumFractionDigits:2}); }
function fmtOT(v) { if(v===0) return ""; return (v>0?"+":"")+Number(v).toFixed(1)+"h"; }

const UI = {
  openModal(id)  { document.getElementById(id).classList.add("open"); },
  closeModal(id) { document.getElementById(id).classList.remove("open"); },
  toast(msg, type="ok") {
    const t=document.getElementById("toast");
    t.textContent=msg; t.className=`toast show ${type}`;
    setTimeout(()=>{t.className="toast";},2800);
  },
  confirm(msg, cb) {
    document.getElementById("confirm-msg").textContent=msg;
    const btn=document.getElementById("confirm-ok");
    btn.onclick=()=>{UI.closeModal("modal-confirm");cb();};
    UI.openModal("modal-confirm");
  },
};

const STATE = {
  empresa: null,
  tecnicos:[], observaciones:[], config:{},
  planPeriod: currPeriod(), resPeriod: currPeriod(), planTecId: null,
};

// Nav
document.querySelectorAll(".nv").forEach(btn => {
  btn.addEventListener("click", () => {
    const v = btn.dataset.view;
    document.querySelectorAll(".nv").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".view").forEach(s => s.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById("view-"+v).classList.add("active");
    if(v==="planilla")   PLAN.init();
    if(v==="resumen")    RES.init();
    if(v==="dashboard")  DASH.init();
    if(v==="dashboard2") DASH2.init();
    if(v==="config")     CFG.init();
  });
});

// Login
let _loginEmpresa = "colbeef";

function selectEmpresa(slug) {
  _loginEmpresa = slug;
  document.querySelectorAll(".emp-btn").forEach(b => {
    b.classList.toggle("active", b.dataset.slug === slug);
  });
  document.getElementById("login-error").style.display = "none";
}

document.getElementById("login-pwd").addEventListener("keydown", e => {
  if(e.key === "Enter") doLogin();
});

// Caducidad
async function cargarDiasUso() {
  try {
    const r = await API.get("/auth/caducidad");
    const el = document.getElementById("dias-uso-msg");
    if(!el) return;
    if(r.dias === null) { el.style.display="none"; return; }
    el.style.display = "block";
    if(r.vencida) {
      el.textContent = "⛔ Licencia vencida";
      el.style.color = "#ff4444";
      const renovar = document.getElementById("login-renovar");
      const btnMain = document.getElementById("btn-login-main");
      if(renovar) renovar.style.display = "block";
      if(btnMain) btnMain.style.display = "none";
    } else if(r.dias <= 5) {
      el.textContent = `⚠️ Tienes ${r.dias} día${r.dias!==1?'s':''} de uso`;
      el.style.color = "#ffaa00";
    } else {
      el.textContent = `✅ Tienes ${r.dias} días de uso`;
      el.style.color = "#00c885";
    }
  } catch(e) {}
}

cargarDiasUso();

async function renovarLicencia() {
  const clave = document.getElementById("renovar-clave").value;
  const fecha = document.getElementById("renovar-fecha").value;
  if(!clave || !fecha) { alert("Ingrese clave y fecha"); return; }
  try {
    await API.post("/auth/caducidad", {clave, fecha});
    document.getElementById("login-renovar").style.display = "none";
    document.getElementById("btn-login-main").style.display = "block";
    document.getElementById("dias-uso-msg").style.display = "none";
    alert("✅ Licencia renovada. Ya puede ingresar.");
    cargarDiasUso();
  } catch(e) {
    alert("Clave incorrecta");
  }
}

async function doLogin() {
  const pwd = document.getElementById("login-pwd").value;
  const errEl = document.getElementById("login-error");
  try {
    const res = await API.post("/auth/login", {empresa: _loginEmpresa, password: pwd});
    STATE.empresa = res;
    document.getElementById("empresa-nombre").textContent = `Time Xtra · ${res.empresa_nombre}`;
    document.title = `Time Xtra · ${res.empresa_nombre}`;
    document.getElementById("view-login").style.display = "none";
    document.getElementById("app-container").style.display = "block";
    await boot();
  } catch(e) {
    const msg = e.message || "";
    const msg2 = e.message || "";
    if(msg2.includes("Licencia vencida")) {
      document.getElementById("login-renovar").style.display = "block";
      document.getElementById("btn-login-main").style.display = "none";
      errEl.style.display = "none";
    } else {
      errEl.textContent = "Empresa o contraseña incorrecta";
      errEl.style.display = "block";
    }
  }
}

function cerrarSesion() {
  STATE.empresa = null;
  document.getElementById("app-container").style.display = "none";
  document.getElementById("view-login").style.display = "flex";
  document.getElementById("login-pwd").value = "";
  selectEmpresa("colbeef");
  cargarDiasUso();

async function renovarLicencia() {
  const clave = document.getElementById("renovar-clave").value;
  const fecha = document.getElementById("renovar-fecha").value;
  if(!clave || !fecha) { alert("Ingrese clave y fecha"); return; }
  try {
    await API.post("/auth/caducidad", {clave, fecha});
    document.getElementById("login-renovar").style.display = "none";
    document.getElementById("btn-login-main").style.display = "block";
    document.getElementById("dias-uso-msg").style.display = "none";
    alert("✅ Licencia renovada. Ya puede ingresar.");
    cargarDiasUso();
  } catch(e) {
    alert("Clave incorrecta");
  }
}
}

async function boot() {
  const eid = STATE.empresa.empresa_id;
  try {
    STATE.tecnicos      = await API.get(`/tecnicos/?empresa_id=${eid}`);
    STATE.observaciones = await API.get(`/observaciones?empresa_id=${eid}`);
    STATE.config        = await API.get(`/config?empresa_id=${eid}`);
    TEC.render();
    PLAN.initSelects();
  } catch(e) {
    UI.toast("Error al conectar con el servidor", "err");
  }
}