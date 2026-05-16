// ── Técnicos ──────────────────────────────────────────────────────────────────
const TEC = {
  render() {
    const q   = (document.getElementById("tec-search").value || "").toLowerCase();
    const grid= document.getElementById("tec-grid");
    const list= STATE.tecnicos.filter(t =>
      t.nombre.toLowerCase().includes(q) || t.cargo.toLowerCase().includes(q));

    grid.innerHTML = list.length === 0
      ? `<p style="color:var(--text3);font-size:12px">Sin resultados</p>`
      : list.map(t => `
        <div class="tec-card">
          <div class="tec-card-name">${t.nombre}</div>
          <div class="tec-card-info">
            🪪 ${t.cedula}<br>
            🔧 ${t.cargo}<br>
            💰 ${fmtCop(t.sueldo)}
          </div>
          <div class="tec-card-foot">
            <button class="btn" style="font-size:10px" onclick="TEC.verPlanilla(${t.id})">Ver planilla</button>
            <button class="btn-g" style="font-size:10px;padding:6px 10px" onclick="TEC.editar(${t.id})">✏️</button>
            <button class="btn-x" onclick="TEC.eliminar(${t.id})">✕</button>
          </div>
        </div>`).join("");
  },

  filtrar() { this.render(); },

  verPlanilla(id) {
    STATE.planTecId = id;
    document.querySelector('.nv[data-view="planilla"]').click();
    document.getElementById("plan-tec-select").value = id;
    PLAN.cargar();
  },

  openForm(t = null) {
    document.getElementById("tec-id").value      = t ? t.id    : "";
    document.getElementById("tec-nombre").value  = t ? t.nombre: "";
    document.getElementById("tec-cedula").value  = t ? t.cedula: "";
    document.getElementById("tec-cargo").value   = t ? t.cargo : "";
    document.getElementById("tec-sueldo").value  = t ? t.sueldo: "";
    document.getElementById("modal-tec-titulo").textContent = t ? "Editar técnico" : "Nuevo técnico";
    UI.openModal("modal-tecnico");
  },

  editar(id) {
    const t = STATE.tecnicos.find(x => x.id === id);
    if (t) this.openForm(t);
  },

  async guardar() {
    const id     = document.getElementById("tec-id").value;
    const nombre = document.getElementById("tec-nombre").value.trim();
    const cedula = document.getElementById("tec-cedula").value.trim();
    const cargo  = document.getElementById("tec-cargo").value.trim();
    const sueldo = +document.getElementById("tec-sueldo").value;

    if (!nombre || !cedula || !cargo || !sueldo) {
      UI.toast("Completa todos los campos", "err"); return;
    }

    try {
      if (id) {
        const upd = await API.put(`/tecnicos/${id}`, { nombre, cedula, cargo, sueldo });
        STATE.tecnicos = STATE.tecnicos.map(t => t.id === +id ? upd : t);
      } else {
        const nuevo = await API.post("/tecnicos/", { nombre, cedula, cargo, sueldo });
        STATE.tecnicos.push(nuevo);
      }
      UI.closeModal("modal-tecnico");
      this.render();
      PLAN.initSelects();
      UI.toast("✅ Técnico guardado");
    } catch(e) { UI.toast("Error al guardar", "err"); }
  },

  eliminar(id) {
    const t = STATE.tecnicos.find(x => x.id === id);
    UI.confirm(`¿Eliminar a ${t.nombre}?`, async () => {
      try {
        await API.del(`/tecnicos/${id}`);
        STATE.tecnicos = STATE.tecnicos.filter(x => x.id !== id);
        this.render();
        PLAN.initSelects();
        UI.toast("✅ Técnico eliminado");
      } catch(e) { UI.toast("Error al eliminar", "err"); }
    });
  },
};

// Abrir modal nuevo
function openModalTecnico() { TEC.openForm(); }
document.querySelector('button[onclick="UI.openModal(\'modal-tecnico\')"]')
  .onclick = () => TEC.openForm();
