// ── Planilla ──────────────────────────────────────────────────────────────────
const PLAN = {
  data: null,
  saving: {},

  initSelects() {
    const sel = document.getElementById("plan-tec-select");
    const cur = sel.value;
    sel.innerHTML = `<option value="">— Seleccionar técnico —</option>` +
      STATE.tecnicos.map(t => `<option value="${t.id}">${t.nombre}</option>`).join("");
    if (cur) sel.value = cur;
    this._updatePeriodLabel();
  },

  init() {
    this.initSelects();
    this._updatePeriodLabel();
    if (STATE.planTecId) {
      document.getElementById("plan-tec-select").value = STATE.planTecId;
      this.cargar();
    }
  },

  _updatePeriodLabel() {
    const { y, m } = STATE.planPeriod;
    document.getElementById("plan-period-lbl").textContent = periodLabel(y, m);
    document.getElementById("plan-periodo").textContent    = "Periodo: " + periodLabel(y, m);
  },

  cambiarPeriodo(delta) {
    let { y, m } = STATE.planPeriod;
    m += delta;
    if (m > 12) { m = 1; y++; }
    if (m < 1)  { m = 12; y--; }
    STATE.planPeriod = { y, m };
    this._updatePeriodLabel();
    if (document.getElementById("plan-tec-select").value) this.cargar();
  },

  async cargar() {
    const tecId = document.getElementById("plan-tec-select").value;
    if (!tecId) {
      document.getElementById("plan-empty").style.display = "block";
      document.getElementById("plan-table-wrap").style.display = "none";
      document.getElementById("btn-pdf-tec").style.display = "none";
      return;
    }
    STATE.planTecId = +tecId;
    const tec = STATE.tecnicos.find(t => t.id === +tecId);
    document.getElementById("plan-titulo").textContent = tec ? tec.nombre : "Planilla";

    const { y, m } = STATE.planPeriod;
    try {
      this.data = await API.get(`/calculos/periodo/${tecId}?year=${y}&month=${m}`);
      this.render();
      document.getElementById("plan-empty").style.display = "none";
      document.getElementById("plan-table-wrap").style.display = "block";
      document.getElementById("btn-pdf-tec").style.display = "inline-block";
    } catch(e) { UI.toast("Error al cargar planilla", "err"); }
  },

  render() {
    const body = document.getElementById("plan-body");
    const foot = document.getElementById("plan-foot");
    const obs  = STATE.observaciones;
    const obsOpts = `<option value=""></option>` +
      obs.map(o => `<option value="${o.nombre}">${o.nombre}</option>`).join("");

    let html = "";
    let rowNum = 0;

    this.data.semanas.forEach((sem, si) => {
      sem.rows.forEach(item => {
        rowNum++;
        const f   = new Date(item.fecha + "T00:00:00");
        const dow = f.getDay(); // 0=Dom
        const reg = item.registro;
        const res = item.resultado;
        const isDom  = dow === 0;
        const isFest = reg.es_festivo;
        const cls    = isDom ? "row-dom" : isFest ? "row-fest" : "";
        const dLabel = `${DIAS[dow]} ${f.getDate()} ${MESES[f.getMonth()+1].slice(0,3)}`;

        html += `<tr class="${cls}" data-fecha="${item.fecha}">
          <td style="text-align:center">
            <input type="checkbox" ${isFest?"checked":""} onchange="PLAN.saveField('${item.fecha}','es_festivo',this.checked)">
          </td>
          <td style="text-align:center;color:var(--text3);font-size:10px;font-family:'DM Mono',monospace">${rowNum}</td>
          <td class="fecha-cell">${dLabel}</td>
          <td><input type="text" value="${reg.entrada||""}" placeholder="HH:MM" maxlength="5" onchange="PLAN.saveField('${item.fecha}','entrada',this.value)" onpaste="setTimeout(()=>PLAN.saveField('${item.fecha}','entrada',this.value),50)" style="text-transform:uppercase;letter-spacing:1px"></td>
          <td><input type="text" value="${reg.salida||""}" placeholder="HH:MM" maxlength="5" onchange="PLAN.saveField('${item.fecha}','salida',this.value)" onpaste="setTimeout(()=>PLAN.saveField('${item.fecha}','salida',this.value),50)" style="text-transform:uppercase;letter-spacing:1px"></td>
          <td><input type="number" value="${reg.descanso ? (reg.descanso/60).toFixed(1) : ''}" min="0" max="3" step="0.5" placeholder="0"
               onchange="PLAN.saveField('${item.fecha}','descanso',+this.value * 60)"></td>
          <td><select onchange="PLAN.saveField('${item.fecha}','observacion',this.value)">${obsOpts
            .replace(`value="${reg.observacion||""}"`,`value="${reg.observacion||""}" selected`)}</select></td>
          <td class="he-val">${fmt(res.horas_trab)||""}</td>
          <td class="ot-cell" id="ot-${si}"></td>
          ${['hed','hen','rno','hefd','hefn','rfd','rfn'].map(col => `
            <td class="he-val">
              <input type="number" value="${fmt(res[col])||''}" min="0" max="24" step="0.1"
                style="width:52px;padding:2px 4px;font-size:11px;text-align:center;
                color:${res[col]>0?'#008855':'inherit'}"
                onchange="PLAN.saveHE('${item.fecha}','${col}',+this.value)"
                onpaste="setTimeout(()=>PLAN.saveHE('${item.fecha}','${col}',+this.value),50)">
            </td>`).join('')}
        </tr>`;
      });

      // Fila OT semana - mostrar rango de fechas
      const ot = sem.ot_semana;
      const otCls = ot > 0 ? "he-pos" : ot < 0 ? "he-neg" : "";
      const semDias = sem.rows.filter(r => r.registro);
      const primerDia = sem.rows[0]?.fecha;
      const ultimoDia = sem.rows[sem.rows.length-1]?.fecha;
      const fmtRango = (f) => { if(!f) return ""; const d=new Date(f+"T00:00:00"); return `${DIAS[d.getDay()]} ${d.getDate()} ${MESES[d.getMonth()+1].slice(0,3)}`; };
      const rangoLabel = primerDia && ultimoDia ? `${fmtRango(primerDia)} → ${fmtRango(ultimoDia)}` : "";
      html += `<tr class="row-wk">
        <td colspan="7" style="text-align:right;padding-right:12px;color:var(--text3)">
          ${rangoLabel} · ${sem.horas_semana.toFixed(1)}h trabajadas
        </td>
        <td></td>
        <td class="ot-cell ${otCls}">${fmtOT(ot)}</td>
        <td colspan="7"></td>
      </tr>`;
    });

    body.innerHTML = html;

    // Subtotales
    const sub = this.data.subtotales;
    foot.innerHTML = `<tr class="row-sub">
      <td colspan="7" style="text-align:right;padding-right:12px">SUBTOTAL PERIODO</td>
      <td class="he-val">${fmt(sub.horas_total)}</td>
      <td class="ot-cell ${sub.ot_total>0?'he-pos':sub.ot_total<0?'he-neg':''}">${fmtOT(sub.ot_total)}</td>
      <td class="he-val">${fmt(sub.hed)}</td>
      <td class="he-val">${fmt(sub.hen)}</td>
      <td class="he-val">${fmt(sub.rno)}</td>
      <td class="he-val">${fmt(sub.hefd)}</td>
      <td class="he-val">${fmt(sub.hefn)}</td>
      <td class="he-val">${fmt(sub.rfd)}</td>
      <td class="he-val">${fmt(sub.rfn)}</td>
    </tr>`;
  },

  async saveField(fecha, field, value) {
    const tecId = STATE.planTecId;
    if (!tecId) return;

    // Construir el registro actual de esta fila
    const row = this.data?.semanas.flatMap(s => s.rows).find(r => r.fecha === fecha);
    const reg = row ? { ...row.registro } : {};
    reg[field] = value;
    reg.fecha  = fecha;

    // Defaults
    if (!reg.es_festivo) reg.es_festivo = false;
    if (!reg.descanso)   reg.descanso   = 0;

    try {
      await API.post(`/registros/${tecId}`, reg);
      // Recargar para reflejar cálculos
      await this.cargar();
    } catch(e) { UI.toast("Error al guardar", "err"); }
  },

  async saveHE(fecha, campo, valor) {
    const tecId = STATE.planTecId;
    if (!tecId) return;
    const row = this.data?.semanas.flatMap(s => s.rows).find(r => r.fecha === fecha);
    const reg = row ? { ...row.registro } : {};
    reg.fecha = fecha;
    reg[campo] = valor;
    if (!reg.es_festivo) reg.es_festivo = false;
    if (!reg.descanso)   reg.descanso   = 0;
    try {
      await API.post(`/registros/${tecId}/manual`, { fecha, campo, valor });
      await this.cargar();
    } catch(e) { UI.toast("Error al guardar HE", "err"); }
  },

  exportarPDF() {
    const { y, m } = STATE.planPeriod;
    const tecId = STATE.planTecId;
    if (!tecId) return;
    window.open(API.pdfUrl(`/exportar/tecnico/${tecId}/${y}/${m}`), "_blank");
  },
};
