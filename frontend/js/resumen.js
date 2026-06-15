const RES = {
  init() { this._updateLabel(); this.cargar(); },

  _updateLabel() {
    const {y,m}=STATE.resPeriod, lbl=periodLabel(y,m);
    document.getElementById("res-period-lbl").textContent=lbl;
    document.getElementById("res-periodo").textContent="Periodo: "+lbl;
  },

  cambiarPeriodo(delta) {
    let {y,m}=STATE.resPeriod; m+=delta;
    if(m>12){m=1;y++;} if(m<1){m=12;y--;}
    STATE.resPeriod={y,m}; this._updateLabel(); this.cargar();
  },

  async cargar() {
    const {y,m}=STATE.resPeriod, eid=STATE.empresa.empresa_id;
    try {
      const data=await API.get(`/calculos/resumen/${y}/${m}?empresa_id=${eid}`);
      this.render(data);
    } catch(e){UI.toast("Error al cargar resumen","err");}
  },

  render(data) {
    const body=document.getElementById("res-body"), foot=document.getElementById("res-foot");
    let totalNeto=0;
    const totSub={hed:0,hen:0,rno:0,hefd:0,hefn:0,rfd:0,rfn:0};
    const totVal={hed:0,hen:0,rno:0,hefd:0,hefn:0,rfd:0,rfn:0};
    const fc=v=>v?fmtCop(v):"";
    body.innerHTML=data.map((t,i)=>{
      totalNeto+=t.neto||0;
      ["hed","hen","rno","hefd","hefn","rfd","rfn"].forEach(k=>{
        totSub[k]+=t[k]||0; totVal[k]+=t["val_"+k]||0;
      });
      return `<tr>
        <td class="num">${i+1}</td><td>${t.nombre}</td>
        <td class="num">${fmt(t.hed)}</td><td class="num">${fc(t.val_hed)}</td>
        <td class="num">${fmt(t.hen)}</td><td class="num">${fc(t.val_hen)}</td>
        <td class="num">${fmt(t.rno)}</td><td class="num">${fc(t.val_rno)}</td>
        <td class="num">${fmt(t.hefd)}</td><td class="num">${fc(t.val_hefd)}</td>
        <td class="num">${fmt(t.hefn)}</td><td class="num">${fc(t.val_hefn)}</td>
        <td class="num">${fmt(t.rfd)}</td><td class="num">${fc(t.val_rfd)}</td>
        <td class="num">${fmt(t.rfn)}</td><td class="num">${fc(t.val_rfn)}</td>
        <td class="neto">${fmtCop(t.neto||0)}</td>
      </tr>`;
    }).join("");
    foot.innerHTML=`<tr>
      <td colspan="2" style="text-align:right;padding-right:12px">TOTAL</td>
      <td class="num">${fmt(totSub.hed)}</td><td class="num">${fc(totVal.hed)}</td>
      <td class="num">${fmt(totSub.hen)}</td><td class="num">${fc(totVal.hen)}</td>
      <td class="num">${fmt(totSub.rno)}</td><td class="num">${fc(totVal.rno)}</td>
      <td class="num">${fmt(totSub.hefd)}</td><td class="num">${fc(totVal.hefd)}</td>
      <td class="num">${fmt(totSub.hefn)}</td><td class="num">${fc(totVal.hefn)}</td>
      <td class="num">${fmt(totSub.rfd)}</td><td class="num">${fc(totVal.rfd)}</td>
      <td class="num">${fmt(totSub.rfn)}</td><td class="num">${fc(totVal.rfn)}</td>
      <td class="neto">${fmtCop(totalNeto)}</td>
    </tr>`;
  },

  exportarPDF() {
    const {y,m}=STATE.resPeriod;
    window.open(API.pdfUrl(`/exportar/resumen/${y}/${m}`),"_blank");
  },
};