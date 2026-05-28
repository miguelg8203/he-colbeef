const CFG = {
  init() {
    const c=STATE.config;
    document.getElementById("cfg-horas").value  = c.horas_sem||44;
    document.getElementById("cfg-inicio").value = c.inicio_diurno||"06:00";
    document.getElementById("cfg-fin").value    = c.fin_diurno||"19:00";
    this._updateHint();
    this.renderObs();
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
    };
    this._updateHint();
    try {
      STATE.config=await API.put(`/config?empresa_id=${eid}`,cfg);
      UI.toast("✅ Configuración guardada");
    } catch(e){UI.toast("Error al guardar config","err");}
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
