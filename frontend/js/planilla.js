const PLAN = {
  data: null,

  initSelects() {
    const sel = document.getElementById("plan-tec-select");
    const cur = sel.value;
    sel.innerHTML = `<option value="">— Seleccionar técnico —</option>` +
      STATE.tecnicos.map(t=>`<option value="${t.id}">${t.nombre}</option>`).join("");
    if(cur) sel.value = cur;
    this._updatePeriodLabel();
  },

  init() {
    this.initSelects();
    this._updatePeriodLabel();
    if(STATE.planTecId) {
      document.getElementById("plan-tec-select").value = STATE.planTecId;
      this.cargar();
    }
  },

  _updatePeriodLabel() {
    const {y,m} = STATE.planPeriod;
    document.getElementById("plan-period-lbl").textContent = periodLabel(y,m);
    document.getElementById("plan-periodo").textContent = "Periodo: " + periodLabel(y,m);
  },

  cambiarPeriodo(delta) {
    let {y,m} = STATE.planPeriod;
    m+=delta;
    if(m>12){m=1;y++;} if(m<1){m=12;y--;}
    STATE.planPeriod={y,m};
    this._updatePeriodLabel();
    if(document.getElementById("plan-tec-select").value) this.cargar();
  },

  async cargar() {
    const tecId = document.getElementById("plan-tec-select").value;
    if(!tecId) {
      document.getElementById("plan-empty").style.display="block";
      document.getElementById("plan-table-wrap").style.display="none";
      document.getElementById("btn-pdf-tec").style.display="none";
      return;
    }
    STATE.planTecId = +tecId;
    const tec = STATE.tecnicos.find(t=>t.id===+tecId);
    document.getElementById("plan-titulo").textContent = tec?tec.nombre:"Planilla";
    const {y,m} = STATE.planPeriod;
    const eid = STATE.empresa.empresa_id;
    try {
      this.data = await API.get(`/calculos/periodo/${tecId}?year=${y}&month=${m}&empresa_id=${eid}`);
      this.render();
      document.getElementById("plan-empty").style.display="none";
      document.getElementById("plan-table-wrap").style.display="block";
      document.getElementById("btn-pdf-tec").style.display="inline-block";
    } catch(e) { UI.toast("Error al cargar planilla","err"); }
  },

  _horaOpts(sel) {
    const horas = [];
    for(let h=1;h<=24;h++){
      horas.push(`${String(h).padStart(2,'0')}:00`);
      if(h<24) horas.push(`${String(h).padStart(2,'0')}:30`);
    }
    return '<option value=""></option>' + horas.map(h=>`<option value="${h}"${sel===h?' selected':''}>${h}</option>`).join('');
  },

  render() {
    const body = document.getElementById("plan-body");
    const foot = document.getElementById("plan-foot");
    const obs  = STATE.observaciones;
    const obsOpts = `<option value=""></option>` +
      obs.map(o=>`<option value="${o.nombre}">${o.nombre}</option>`).join("");

    let html="", rowNum=0;

    this.data.semanas.forEach((sem,si)=>{
      const porFecha = {};
      sem.rows.forEach(item=>{
        if(!porFecha[item.fecha]) porFecha[item.fecha]=[];
        porFecha[item.fecha].push(item);
      });

      Object.entries(porFecha).forEach(([fecha, items])=>{
        rowNum++;
        const f=new Date(fecha+"T00:00:00"), dow=f.getDay();
        const isDom=dow===0;
        const dLabel=`${DIAS[dow]} ${f.getDate()} ${MESES[f.getMonth()+1].slice(0,3)}`;

        items.forEach((item, idx)=>{
          const reg=item.registro, res=item.resultado;
          const isFest=reg.es_festivo;
          const cls=isDom?"row-dom":isFest?"row-fest":"";
          const turno=reg.turno||1;

          html+=`<tr class="${cls}" data-fecha="${fecha}" data-turno="${turno}">`;

          if(idx===0) {
            html+=`<td style="text-align:center" rowspan="${items.length}">
              <input type="checkbox" ${isFest?"checked":""} onchange="PLAN.saveFestivo('${fecha}',this.checked)">
            </td>`;
            html+=`<td style="text-align:center;color:var(--text3);font-size:10px;font-family:'DM Mono',monospace" rowspan="${items.length}">${rowNum}</td>`;
            html+=`<td class="fecha-cell" rowspan="${items.length}">
              ${dLabel}
              <button onclick="PLAN.addTurno('${fecha}')" title="Agregar turno"
                style="margin-left:4px;background:none;border:1px solid var(--verde);color:var(--verde);
                border-radius:3px;cursor:pointer;font-size:9px;padding:1px 5px;">+</button>
            </td>`;
          }

          html+=`
          <td><select onchange="PLAN.saveField('${fecha}',${turno},'entrada',this.value)" style="width:82px;padding:2px 3px;font-size:11px;">${PLAN._horaOpts(reg.entrada||'')}</select></td>
          <td><select onchange="PLAN.saveField('${fecha}',${turno},'salida',this.value)" style="width:82px;padding:2px 3px;font-size:11px;">${PLAN._horaOpts(reg.salida||'')}</select></td>
          <td><input type="number" value="${reg.descanso?(reg.descanso/60).toFixed(1):''}" min="0" max="3" step="0.5" placeholder="0"
            onchange="PLAN.saveField('${fecha}',${turno},'descanso',+this.value*60)"></td>
          <td><select onchange="PLAN.saveField('${fecha}',${turno},'observacion',this.value)">${obsOpts
            .replace(`value="${reg.observacion||""}"`,`value="${reg.observacion||""}" selected`)}</select></td>
          <td class="he-val">${fmt(res.horas_trab)||""}</td>
          <td class="ot-cell"></td>
          ${['hed','hen','rno','hefd','hefn','rfd','rfn'].map(col=>`
            <td class="he-val">
              <input type="number" value="${reg[col]?fmt(reg[col]):res[col]>0?fmt(res[col]):''}" min="-24" max="24" step="0.1" readonly
                style="width:52px;padding:2px 4px;font-size:11px;text-align:center;
                color:${(reg[col]||res[col])>0?'#008855':(reg[col]||res[col])<0?'#cc0000':'inherit'};
                background:var(--bg2);cursor:default;">
            </td>`).join('')}`;

          if(turno>1) {
            html+=`<td style="text-align:center">
              <button onclick="PLAN.delTurno(${item.registro.id},'${fecha}')"
                style="background:none;border:none;color:#cc0000;cursor:pointer;font-size:12px;">✕</button>
            </td>`;
          } else {
            html+=`<td></td>`;
          }

          html+=`</tr>`;
        });
      });

      const ot=sem.ot_semana, otCls=ot>0?"he-pos":ot<0?"he-neg":"";
      const p1=sem.rows[0]?.fecha, p2=sem.rows[sem.rows.length-1]?.fecha;
      const fr=(f)=>{if(!f)return"";const d=new Date(f+"T00:00:00");return`${DIAS[d.getDay()]} ${d.getDate()} ${MESES[d.getMonth()+1].slice(0,3)}`;};
      html+=`<tr class="row-wk">
        <td colspan="7" style="text-align:right;padding-right:12px;color:var(--text3)">${fr(p1)} → ${fr(p2)} · ${sem.horas_semana.toFixed(1)}h</td>
        <td></td><td class="ot-cell ${otCls}">${fmtOT(ot)}</td>
        <td colspan="8"></td>
      </tr>`;
    });

    body.innerHTML=html;
    const sub=this.data.subtotales;
    foot.innerHTML=`<tr class="row-sub">
      <td colspan="7" style="text-align:right;padding-right:12px">SUBTOTAL PERIODO</td>
      <td class="he-val">${fmt(sub.horas_total)}</td>
      <td class="ot-cell ${sub.ot_total>0?'he-pos':sub.ot_total<0?'he-neg':''}">${fmtOT(sub.ot_total)}</td>
      <td class="he-val">${fmt(sub.hed)}</td><td class="he-val">${fmt(sub.hen)}</td>
      <td class="he-val">${fmt(sub.rno)}</td><td class="he-val">${fmt(sub.hefd)}</td>
      <td class="he-val">${fmt(sub.hefn)}</td><td class="he-val">${fmt(sub.rfd)}</td>
      <td class="he-val">${fmt(sub.rfn)}</td><td></td>
    </tr>`;
  },

  async saveFestivo(fecha, value) {
    const tecId=STATE.planTecId; if(!tecId) return;
    const rows = this.data?.semanas.flatMap(s=>s.rows).filter(r=>r.fecha===fecha) || [];
    for(const item of rows) {
      const turno = item.registro.turno||1;
      const reg = {...item.registro, es_festivo: value, fecha};
      if(!reg.descanso) reg.descanso=0;
      try { await API.post(`/registros/${tecId}`, reg); } catch(e){}
    }
    await this.cargar();
  },

  async saveField(fecha, turno, field, value) {
    const tecId=STATE.planTecId; if(!tecId) return;
    const row=this.data?.semanas.flatMap(s=>s.rows).find(r=>r.fecha===fecha&&(r.registro.turno||1)===turno);
    const reg=row?{...row.registro}:{};
    reg[field]=value; reg.fecha=fecha; reg.turno=turno;
    if(reg.es_festivo===undefined||reg.es_festivo===null) reg.es_festivo=false;
    if(!reg.descanso) reg.descanso=0;
    try {
      await API.post(`/registros/${tecId}`,reg);
      await this.cargar();
    } catch(e){UI.toast("Error al guardar","err");}
  },

  async saveHE(fecha, turno, campo, valor) {
    const tecId=STATE.planTecId; if(!tecId) return;
    try {
      await API.post(`/registros/${tecId}/manual`,{fecha,turno,campo,valor});
    } catch(e){UI.toast("Error al guardar HE","err");}
  },

  async addTurno(fecha) {
    const tecId=STATE.planTecId; if(!tecId) return;
    try {
      await API.post(`/registros/${tecId}/add_turno`,{fecha});
      await this.cargar();
    } catch(e){UI.toast("Error al agregar turno","err");}
  },

  async delTurno(registroId, fecha) {
    const tecId=STATE.planTecId; if(!tecId) return;
    UI.confirm(`¿Eliminar este turno del ${fecha}?`, async()=>{
      try {
        await API.del(`/registros/${tecId}/turno/${registroId}`);
        await this.cargar();
        UI.toast("✅ Turno eliminado");
      } catch(e){UI.toast(e.message||"Error","err");}
    });
  },

  exportarPDF() {
    const {y,m}=STATE.planPeriod, tecId=STATE.planTecId;
    if(!tecId) return;
    window.open(API.pdfUrl(`/exportar/tecnico/${tecId}/${y}/${m}`),"_blank");
  },
};