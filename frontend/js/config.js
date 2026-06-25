const CFG = {
  desbloqueado: false,

  init() {
    this.desbloqueado = false;
    this._renderLock();
    const c=STATE.config;
    document.getElementById("cfg-horas").value  = c.horas_sem||44;
    document.getElementById("cfg-inicio").value = c.inicio_diurno||"06:00";
    document.getElementById("cfg-fin").value    = c.fin_diurno||"19:00";
    document.getElementById("cfg-f-hed").value  = c.factor_hed||1.25;
    document.getElementById("cfg-f-hen").value  = c.factor_hen||1.75;
    document.getElementById("cfg-f-rno").value  = c.factor_rno||0.35;
    document.getElementById("cfg-f-hefd").value = c.factor_hefd||2.05;
    document.getElementById("cfg-f-hefn").value = c.factor_hefn||2.55;
    document.getElementById("cfg-f-rfd").value  = c.factor_rfd||0.80;
    document.getElementById("cfg-f-rfn").value  = c.factor_rfn||1.15;
    this._updateHint();
    this.renderObs();
    this._cargarCaducidad();
  },

  _renderLock() {
    const btn = document.getElementById("cfg-lock-btn");
    const content = document.getElementById("cfg-content");
    if(btn) btn.textContent = this.desbloqueado ? "🔒 Bloquear Config" : "🔓 Desbloquear Config";
    if(content) content.style.display = this.desbloqueado ? "block" : "none";
  },

  toggleLock() {
    if(!this.desbloqueado) {
      const clave = prompt("Clave para acceder a configuración:");
      if(clave !== "1234") { UI.toast("Clave incorrecta","err"); return; }
      this.desbloqueado = true;
    } else {
      this.desbloqueado = false;
    }
    this._renderLock();
  },

  _updateHint() {
    const h=+document.getElementById("cfg-horas").value||44;
    const jd=+(h/6).toFixed(2), jm=Math.round(jd*30);
    const dEl=document.getElementById("cfg-jornada-dia");
    const mEl=document.getElementById("cfg-jornada-mes");
    if(dEl) dEl.textContent=jd;
    if(mEl) mEl.textContent=jm;
  },

  async guardar() {
    const eid=STATE.empresa.empresa_id;
    const cfg={
      horas_sem:     +document.getElementById("cfg-horas").value,
      inicio_diurno:  document.getElementById("cfg-inicio").value,
      fin_diurno:     document.getElementById("cfg-fin").value,
      factor_hed:    +document.getElementById("cfg-f-hed").value,
      factor_hen:    +document.getElementById("cfg-f-hen").value,
      factor_rno:    +document.getElementById("cfg-f-rno").value,
      factor_hefd:   +document.getElementById("cfg-f-hefd").value,
      factor_hefn:   +document.getElementById("cfg-f-hefn").value,
      factor_rfd:    +document.getElementById("cfg-f-rfd").value,
      factor_rfn:    +document.getElementById("cfg-f-rfn").value,
    };
    this._updateHint();
    try {
      STATE.config=await API.put(`/config?empresa_id=${eid}`,cfg);
      UI.toast("✅ Configuración guardada");
    } catch(e){UI.toast("Error al guardar config","err");}
  },

  async _cargarCaducidad() {
    try {
      const r = await API.get("/auth/caducidad");
      const el = document.getElementById("cfg-caducidad-fecha");
      if(el && r.fecha) el.value = r.fecha;
      const info = document.getElementById("cfg-caducidad-info");
      if(info) {
        if(r.dias === null) { info.textContent = "Sin fecha configurada"; info.style.color="var(--text3)"; }
        else if(r.dias < 0) { info.textContent = "⛔ Licencia vencida"; info.style.color="#ff4444"; }
        else if(r.dias <= 5) { info.textContent = `⚠️ Vence en ${r.dias} día${r.dias!==1?'s':''}`;info.style.color="#ffaa00"; }
        else { info.textContent = `✅ ${r.dias} días restantes`; info.style.color="#00c885"; }
      }
    } catch(e){}
  },

  async guardarCaducidad() {
    const clave = prompt("Clave de administrador:");
    if(!clave) return;
    const fecha = document.getElementById("cfg-caducidad-fecha").value;
    if(!fecha) { UI.toast("Selecciona una fecha","err"); return; }
    try {
      await API.post("/auth/caducidad", {clave, fecha});
      UI.toast("✅ Fecha de caducidad guardada");
      this._cargarCaducidad();
    } catch(e) { UI.toast("Clave incorrecta","err"); }
  },

  renderObs() {
    const list=document.getElementById("obs-list");
    list.innerHTML=STATE.observaciones.map(o=>`
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
    const o=STATE.observaciones.find(x=>x.id===id); if(!o) return;
    try {
      const res=await API.put(`/observaciones/${id}`,{...o,[field]:val});
      STATE.observaciones=STATE.observaciones.map(x=>x.id===id?res:x);
    } catch(e){UI.toast("Error al actualizar","err");}
  },

  async addObs() {
    const nombre=document.getElementById("obs-nombre").value.trim();
    const horas=+document.getElementById("obs-horas").value||0;
    const ot=document.getElementById("obs-ot").checked;
    if(!nombre){UI.toast("Escribe el nombre","err");return;}
    const eid=STATE.empresa.empresa_id;
    try {
      const nueva=await API.post(`/observaciones?empresa_id=${eid}`,{nombre,horas_fijas:horas,cuenta_ot:ot});
      STATE.observaciones.push(nueva); this.renderObs();
      document.getElementById("obs-nombre").value="";
      document.getElementById("obs-horas").value="";
      document.getElementById("obs-ot").checked=false;
      UI.toast("✅ Observación agregada");
    } catch(e){UI.toast("Error al agregar","err");}
  },

  async delObs(id) {
    const o=STATE.observaciones.find(x=>x.id===id);
    UI.confirm(`¿Eliminar "${o.nombre}"?`, async()=>{
      try {
        await API.del(`/observaciones/${id}`);
        STATE.observaciones=STATE.observaciones.filter(x=>x.id!==id);
        this.renderObs(); UI.toast("✅ Eliminada");
      } catch(e){UI.toast("Error","err");}
    });
  },
};

document.getElementById("cfg-horas").addEventListener("input", ()=>CFG._updateHint());
document.getElementById("cfg-horas").addEventListener("change",()=>CFG._updateHint());