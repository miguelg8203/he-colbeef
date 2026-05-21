// ── Resumen HE ────────────────────────────────────────────────────────────────
const fmtCol = v => {
  if (!v && v !== 0) return "";
  return "$" + Number(v).toLocaleString("es-CO", {minimumFractionDigits:2, maximumFractionDigits:2});
};

const RES = {
  init() { this._updateLabel(); this.cargar(); },

  _updateLabel() {
    const { y, m } = STATE.resPeriod;
    const lbl = periodLabel(y, m);
    document.getElementById("res-period-lbl").textContent = lbl;
    document.getElementById("res-periodo").textContent    = "Periodo: " + lbl;
  },

  cambiarPeriodo(delta) {
    let { y, m } = STATE.resPeriod;
    m += delta;
    if (m > 12) { m = 1; y++; }
    if (m < 1)  { m = 12; y--; }
    STATE.resPeriod = { y, m };
    this._updateLabel();
    this.cargar();
  },

  async cargar() {
    const { y, m } = STATE.resPeriod;
    try {
      const data = await API.get(`/calculos/resumen/${y}/${m}`);
      this.render(data);
    } catch(e) { UI.toast("Error al cargar resumen", "err"); }
  },

  render(data) {
    const body = document.getElementById("res-body");
    const foot = document.getElementById("res-foot");
    let totalNeto = 0;
    const totSub = { hed:0, hen:0, rno:0, hefd:0, hefn:0, rfd:0, rfn:0 };
    const totVal = { hed:0, hen:0, rno:0, hefd:0, hefn:0, rfd:0, rfn:0 };
    const fv = v => v ? fmtCol(v) : "";
    body.innerHTML = data.map((t, i) => {
      totalNeto += t.neto || 0;
      ["hed","hen","rno","hefd","hefn","rfd","rfn"].forEach(k => {
        totSub[k] += t[k] || 0;
        totVal[k] += t["val_"+k] || 0;
      });
      return `<tr>
        <td class="num">${i+1}</td>
        <td>${t.nombre}</td>
        <td style="color:var(--text2)">${t.cargo}</td>
        <td class="num">${fmtCol(t.sueldo)}</td>
        <td class="num">${fmt(t.hed)}</td>
        <td class="num">${fv(t.val_hed)}</td>
        <td class="num">${fmt(t.hen)}</td>
        <td class="num">${fv(t.val_hen)}</td>
        <td class="num">${fmt(t.rno)}</td>
        <td class="num">${fv(t.val_rno)}</td>
        <td class="num">${fmt(t.hefd)}</td>
        <td class="num">${fv(t.val_hefd)}</td>
        <td class="num">${fmt(t.hefn)}</td>
        <td class="num">${fv(t.val_hefn)}</td>
        <td class="num">${fmt(t.rfd)}</td>
        <td class="num">${fv(t.val_rfd)}</td>
        <td class="num">${fmt(t.rfn)}</td>
        <td class="num">${fv(t.val_rfn)}</td>
        <td class="neto">${fmtCol(t.neto || 0)}</td>
      </tr>`;
    }).join("");
    foot.innerHTML = `<tr>
      <td colspan="3" style="text-align:right;padding-right:12px">TOTAL</td>
      <td></td>
      <td class="num">${fmt(totSub.hed)}</td><td class="num">${fv(totVal.hed)}</td>
      <td class="num">${fmt(totSub.hen)}</td><td class="num">${fv(totVal.hen)}</td>
      <td class="num">${fmt(totSub.rno)}</td><td class="num">${fv(totVal.rno)}</td>
      <td class="num">${fmt(totSub.hefd)}</td><td class="num">${fv(totVal.hefd)}</td>
      <td class="num">${fmt(totSub.hefn)}</td><td class="num">${fv(totVal.hefn)}</td>
      <td class="num">${fmt(totSub.rfd)}</td><td class="num">${fv(totVal.rfd)}</td>
      <td class="num">${fmt(totSub.rfn)}</td><td class="num">${fv(totVal.rfn)}</td>
      <td class="neto">${fmtCol(totalNeto)}</td>
    </tr>`;
  },

  exportarPDF() {
    const { y, m } = STATE.resPeriod;
    window.open(API.pdfUrl(`/exportar/resumen/${y}/${m}`), "_blank");
  },
};

// ── Config ────────────────────────────────────────────────────────────────────
const CFG = {
  init() {
    const c = STATE.config;
    document.getElementById("cfg-horas").value  = c.horas_sem    || 44;
    document.getElementById("cfg-inicio").value = c.inicio_diurno || "06:00";
    document.getElementById("cfg-fin").value    = c.fin_diurno   || "19:00";
    this._updateHint();
    this.renderObs();
  },

  _updateHint() {
    const h  = +document.getElementById("cfg-horas").value || 44;
    const jd = +(h / 6).toFixed(2);
    const jm = Math.round(jd * 30);
    const dEl = document.getElementById("cfg-jornada-dia");
    const mEl = document.getElementById("cfg-jornada-mes");
    if (dEl) dEl.textContent = jd;
    if (mEl) mEl.textContent = jm;
  },

  async guardar() {
    const cfg = {
      horas_sem:     +document.getElementById("cfg-horas").value,
      inicio_diurno:  document.getElementById("cfg-inicio").value,
      fin_diurno:     document.getElementById("cfg-fin").value,
    };
    this._updateHint();
    try {
      STATE.config = await API.put("/config", cfg);
      UI.toast("✅ Configuración guardada");
    } catch(e) { UI.toast("Error al guardar config", "err"); }
  },

  renderObs() {
    const list = document.getElementById("obs-list");
    list.innerHTML = STATE.observaciones.map(o => `
      <div class="obs-row">
        <input type="text" value="${o.nombre}" onchange="CFG.updObs(${o.id},'nombre',this.value)">
        <input type="number" value="${o.horas_fijas}" min="0" max="24" step="0.5"
          onchange="CFG.updObs(${o.id},'horas_fijas',+this.value)">
        <div style="text-align:center">
          <input type="checkbox" ${o.cuenta_ot?"checked":""}
            onchange="CFG.updObs(${o.id},'cuenta_ot',this.checked)">
        </div>
        <button class="btn-x" onclick="CFG.delObs(${o.id})">✕</button>
      </div>`).join("");
  },

  async updObs(id, field, val) {
    const o = STATE.observaciones.find(x => x.id === id);
    if (!o) return;
    const upd = { ...o, [field]: val };
    try {
      const res = await API.put(`/observaciones/${id}`, upd);
      STATE.observaciones = STATE.observaciones.map(x => x.id === id ? res : x);
    } catch(e) { UI.toast("Error al actualizar", "err"); }
  },

  async addObs() {
    const nombre = document.getElementById("obs-nombre").value.trim();
    const horas  = +document.getElementById("obs-horas").value || 0;
    const ot     = document.getElementById("obs-ot").checked;
    if (!nombre) { UI.toast("Escribe el nombre de la observación", "err"); return; }
    try {
      const nueva = await API.post("/observaciones", { nombre, horas_fijas: horas, cuenta_ot: ot });
      STATE.observaciones.push(nueva);
      this.renderObs();
      document.getElementById("obs-nombre").value = "";
      document.getElementById("obs-horas").value  = "";
      document.getElementById("obs-ot").checked   = false;
      UI.toast("✅ Observación agregada");
    } catch(e) { UI.toast("Error al agregar", "err"); }
  },

  async delObs(id) {
    const o = STATE.observaciones.find(x => x.id === id);
    UI.confirm(`¿Eliminar observación "${o.nombre}"?`, async () => {
      try {
        await API.del(`/observaciones/${id}`);
        STATE.observaciones = STATE.observaciones.filter(x => x.id !== id);
        this.renderObs();
        UI.toast("✅ Observación eliminada");
      } catch(e) { UI.toast("Error al eliminar", "err"); }
    });
  },
};

document.getElementById("cfg-horas").addEventListener("input",  () => CFG._updateHint());
document.getElementById("cfg-horas").addEventListener("change", () => CFG._updateHint());
