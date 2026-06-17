const TEC = {
  mostrarInactivos: false,

  render() {
    const q = (document.getElementById("tec-search").value||"").toLowerCase();
    const grid = document.getElementById("tec-grid");
    const fuente = this.mostrarInactivos ? STATE.tecnicosInactivos : STATE.tecnicos;
    const list = fuente.filter(t => t.nombre.toLowerCase().includes(q)||t.cargo.toLowerCase().includes(q));

    const btnToggle = document.getElementById("btn-toggle-inactivos");
    if(btnToggle) {
      btnToggle.textContent = this.mostrarInactivos ? "👁 Ver activos" : "👁 Ver ocultados";
      btnToggle.style.opacity = this.mostrarInactivos ? "1" : "0.6";
    }

    grid.innerHTML = list.length===0
      ? `<p style="color:var(--text3);font-size:12px">${this.mostrarInactivos?'No hay técnicos ocultados':'Sin resultados'}</p>`
      : list.map(t=>`
        <div class="tec-card" style="${!t.activo?'opacity:0.6;border:1px dashed var(--border)':''}">
          <div class="tec-card-name">${t.nombre}${!t.activo?' <span style="font-size:10px;color:var(--text3)">(ocultado)</span>':''}</div>
          <div class="tec-card-info">🪪 ${t.cedula}<br>🔧 ${t.cargo}<br>💰 ${fmtCop(t.sueldo)}${t.fecha_retiro?`<br>📅 Retiro: ${t.fecha_retiro}`:''}</div>
          <div class="tec-card-foot">
            ${t.activo
              ? `<button class="btn" style="font-size:10px" onclick="TEC.verPlanilla(${t.id})">Ver planilla</button>
                 <button class="btn-g" style="font-size:10px;padding:6px 10px" onclick="TEC.editar(${t.id})">✏️</button>
                 <button class="btn-x" onclick="TEC.ocultar(${t.id})">Ocultar</button>`
              : `<button class="btn" style="font-size:10px;background:var(--verde)" onclick="TEC.reactivar(${t.id})">Reactivar</button>
                 <button class="btn-x" onclick="TEC.eliminar(${t.id})">Eliminar</button>`
            }
          </div>
        </div>`).join("");
  },

  filtrar() { this.render(); },

  async toggleInactivos() {
    this.mostrarInactivos = !this.mostrarInactivos;
    if(this.mostrarInactivos && !STATE.tecnicosInactivos) {
      await this.cargarInactivos();
    }
    this.render();
  },

  async cargarInactivos() {
    const eid = STATE.empresa.empresa_id;
    try {
      STATE.tecnicosInactivos = await API.get(`/tecnicos/lista-inactivos?empresa_id=${eid}`);
    } catch(e) { STATE.tecnicosInactivos = []; }
  },

  verPlanilla(id) {
    STATE.planTecId = id;
    document.querySelector('.nv[data-view="planilla"]').click();
    document.getElementById("plan-tec-select").value = id;
    PLAN.cargar();
  },

  openForm(t=null) {
    document.getElementById("tec-id").value     = t?t.id:"";
    document.getElementById("tec-nombre").value = t?t.nombre:"";
    document.getElementById("tec-cedula").value = t?t.cedula:"";
    document.getElementById("tec-cargo").value  = t?t.cargo:"";
    document.getElementById("tec-sueldo").value = t?t.sueldo:"";
    document.getElementById("modal-tec-titulo").textContent = t?"Editar técnico":"Nuevo técnico";
    UI.openModal("modal-tecnico");
  },

  editar(id) { const t=STATE.tecnicos.find(x=>x.id===id); if(t) this.openForm(t); },

  async guardar() {
    const id=document.getElementById("tec-id").value;
    const nombre=document.getElementById("tec-nombre").value.trim();
    const cedula=document.getElementById("tec-cedula").value.trim();
    const cargo=document.getElementById("tec-cargo").value.trim();
    const sueldo=+document.getElementById("tec-sueldo").value;
    if(!nombre||!cedula||!cargo||!sueldo){UI.toast("Completa todos los campos","err");return;}
    const eid=STATE.empresa.empresa_id;
    try {
      if(id) {
        const upd=await API.put(`/tecnicos/${id}`,{nombre,cedula,cargo,sueldo});
        STATE.tecnicos=STATE.tecnicos.map(t=>t.id===+id?upd:t);
      } else {
        const nuevo=await API.post(`/tecnicos/?empresa_id=${eid}`,{nombre,cedula,cargo,sueldo});
        STATE.tecnicos.push(nuevo);
      }
      UI.closeModal("modal-tecnico"); this.render(); PLAN.initSelects();
      UI.toast("✅ Técnico guardado");
    } catch(e){UI.toast("Error al guardar","err");}
  },

  ocultar(id) {
    const t = STATE.tecnicos.find(x=>x.id===id);
    const hoy = new Date().toISOString().split("T")[0];
    document.getElementById("confirm-msg").innerHTML = `
      <p style="margin-bottom:12px;font-size:13px">¿Ocultar a <b>${t.nombre}</b>?</p>
      <label style="font-size:11px;color:var(--text3);text-transform:uppercase;letter-spacing:.06em">Fecha de retiro</label>
      <input type="date" id="fecha-retiro-input" value="${hoy}"
        style="width:100%;margin-top:6px;padding:8px;border-radius:6px;border:1px solid var(--border);background:var(--bg2);color:var(--text);font-size:13px;">
    `;
    document.getElementById("confirm-ok").onclick = async () => {
      const fecha = document.getElementById("fecha-retiro-input").value;
      if(!fecha){UI.toast("Selecciona una fecha","err");return;}
      UI.closeModal("modal-confirm");
      try {
        await API.del(`/tecnicos/${id}?fecha_retiro=${fecha}`);
        STATE.tecnicos = STATE.tecnicos.filter(x=>x.id!==id);
        STATE.tecnicosInactivos = null;
        this.render(); PLAN.initSelects(); UI.toast("✅ Técnico ocultado");
      } catch(e){UI.toast("Error","err");}
    };
    UI.openModal("modal-confirm");
  },

  async eliminar(id) {
    const clave = prompt("Clave para eliminar definitivamente:");
    if(clave !== "1234") { UI.toast("Clave incorrecta","err"); return; }
    const t = STATE.tecnicosInactivos?.find(x=>x.id===id);
    UI.confirm(`¿Eliminar DEFINITIVAMENTE a ${t?.nombre}? No se puede deshacer.`, async()=>{
      try {
        await API.del(`/tecnicos/${id}/definitivo`);
        STATE.tecnicosInactivos = STATE.tecnicosInactivos.filter(x=>x.id!==id);
        this.render(); UI.toast("✅ Técnico eliminado");
      } catch(e){UI.toast("Error","err");}
    });
  },

  async reactivar(id) {
    try {
      await API.post(`/tecnicos/${id}/reactivar`, {});
      const t = STATE.tecnicosInactivos?.find(x=>x.id===id);
      if(t) {
        t.activo = true;
        t.fecha_retiro = null;
        STATE.tecnicos.push(t);
        STATE.tecnicosInactivos = STATE.tecnicosInactivos.filter(x=>x.id!==id);
      }
      this.render(); PLAN.initSelects();
      UI.toast("✅ Técnico reactivado");
    } catch(e){UI.toast("Error","err");}
  },
};