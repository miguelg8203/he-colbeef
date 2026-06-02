const DASH2 = {
  period: null,

  init() {
    if(!this.period) this.period = {...STATE.planPeriod};
    this._updateLabel();
    this.cargar();
  },

  _updateLabel() {
    const {y,m} = this.period;
    const lbl = periodLabel(y,m);
    document.getElementById("dash2-period-lbl").textContent = lbl;
    document.getElementById("dash2-periodo").textContent = "Periodo: " + lbl;
  },

  cambiarPeriodo(delta) {
    let {y,m} = this.period;
    m+=delta;
    if(m>12){m=1;y++;} if(m<1){m=12;y--;}
    this.period={y,m};
    this._updateLabel();
    this.cargar();
  },

  async cargar() {
    const {y,m} = this.period;
    const eid = STATE.empresa.empresa_id;
    try {
      const data = await API.get(`/calculos/observaciones/${y}/${m}?empresa_id=${eid}`);
      this.render(data);
    } catch(e) { UI.toast("Error al cargar observaciones","err"); }
  },

  render(data) {
    // Métricas
    const totalDias = data.reduce((s,t)=>s+t.obs.reduce((a,o)=>a+o.dias,0),0);
    const incap = data.reduce((s,t)=>s+t.obs.filter(o=>o.tipo==="INCAPACIDAD").reduce((a,o)=>a+o.dias,0),0);
    const ausencias = data.reduce((s,t)=>s+t.obs.filter(o=>o.tipo==="AUSENCIA INJUSTIFICADA").reduce((a,o)=>a+o.dias,0),0);
    const vacas = data.reduce((s,t)=>s+t.obs.filter(o=>o.tipo==="VACACIONES").reduce((a,o)=>a+o.dias,0),0);

    document.getElementById("dash2-total").textContent = totalDias;
    document.getElementById("dash2-incap").textContent = incap;
    document.getElementById("dash2-ausencia").textContent = ausencias;
    document.getElementById("dash2-vacas").textContent = vacas;

    // Filtros
    const selTec = document.getElementById("dash2-sel-tec");
    const selObs = document.getElementById("dash2-sel-obs");
    const curTec = selTec.value;
    const curObs = selObs.value;

    selTec.innerHTML = '<option value="">Todos los técnicos</option>' +
      data.map(t=>`<option value="${t.id}">${t.nombre.split(" ")[0]} ${t.nombre.split(" ")[1]||""}</option>`).join("");
    if(curTec) selTec.value = curTec;

    const tiposSet = new Set(data.flatMap(t=>t.obs.map(o=>o.tipo)));
    selObs.innerHTML = '<option value="">Todas las observaciones</option>' +
      [...tiposSet].sort().map(tp=>`<option value="${tp}">${tp}</option>`).join("");
    if(curObs) selObs.value = curObs;

    this._renderCards(data);
  },

  filtrar() {
    this.cargar();
  },

  _renderCards(data) {
    const tecFilter = document.getElementById("dash2-sel-tec").value;
    const obsFilter = document.getElementById("dash2-sel-obs").value;

    let filtered = data.filter(t => !tecFilter || t.id==tecFilter);
    if(obsFilter) {
      filtered = filtered
        .map(t=>({...t, obs: t.obs.filter(o=>o.tipo===obsFilter)}))
        .filter(t=>t.obs.length>0);
    }

    const OBS_COLORS = {
      "INCAPACIDAD": "#FAECE7;color:#993C1D",
      "PERMISO": "#E6F1FB;color:#185FA5",
      "DESCANSO": "#EAF3DE;color:#3B6D11",
      "DESCANSO FESTIVO": "#EAF3DE;color:#3B6D11",
      "DESCANSO POR CULTO": "#EAF3DE;color:#3B6D11",
      "AUSENCIA INJUSTIFICADA": "#FCEBEB;color:#A32D2D",
      "VACACIONES": "#EEEDFE;color:#3C3489",
      "RENUNCIA": "#FCEBEB;color:#A32D2D",
      "LICENCIA POR LUTO": "#E6F1FB;color:#185FA5",
      "PERMISO JURADO VOTACION": "#E6F1FB;color:#185FA5",
      "CITA MEDICA": "#E6F1FB;color:#185FA5",
      "DIA DE LA FAMILIA": "#EAF3DE;color:#3B6D11",
      "DIA COMPENSATORIO": "#EAF3DE;color:#3B6D11",
      "CAPACITACION ALTURAS": "#E6F1FB;color:#185FA5",
      "DISPONIBILIDAD": "#F1EFE8;color:#5F5E5A",
      "VOTACION": "#F1EFE8;color:#5F5E5A",
      "REUNION": "#F1EFE8;color:#5F5E5A",
    };

    const cont = document.getElementById("dash2-cards");
    if(!filtered.length) {
      cont.innerHTML = `<div style="text-align:center;padding:2rem;color:var(--text3);font-size:13px">Sin novedades para este filtro</div>`;
      return;
    }

    cont.innerHTML = filtered.map(t => {
      const totalDias = t.obs.reduce((s,o)=>s+o.dias,0);
      const ini = t.nombre.split(" ").map(w=>w[0]).slice(0,2).join("").toUpperCase();
      const pills = t.obs.map(o => {
        const clr = OBS_COLORS[o.tipo] || "#F1EFE8;color:#5F5E5A";
        return `<span style="display:inline-flex;align-items:center;gap:4px;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:500;background:${clr.split(';')[0]};${clr.split(';')[1]}">
          ${o.tipo} · ${o.dias}d
        </span>`;
      }).join("");

      return `<div style="background:var(--bg2);border:0.5px solid var(--border);border-radius:8px;padding:1rem 1.25rem;margin-bottom:10px;">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
          <div style="width:36px;height:36px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:500;background:#e3f2fd;color:#1565c0;flex-shrink:0;">${ini}</div>
          <div>
            <div style="font-size:14px;font-weight:500;color:var(--text)">${t.nombre}</div>
            <div style="font-size:12px;color:var(--text3)">${t.cargo}</div>
          </div>
          <div style="margin-left:auto;background:var(--bg3);border-radius:4px;padding:2px 10px;font-size:12px;color:var(--text3)">${totalDias} día${totalDias!==1?'s':''}</div>
        </div>
        <div style="display:flex;flex-wrap:wrap;gap:6px;">${pills}</div>
      </div>`;
    }).join("");
  }
};
