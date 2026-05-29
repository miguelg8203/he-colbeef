const DASH = {
  charts: {},
  period: null,

  init() {
    if(!this.period) this.period = {...STATE.planPeriod};
    this._updateLabel();
    this.cargar();
  },

  _updateLabel() {
    const {y,m} = this.period;
    const lbl = periodLabel(y,m);
    document.getElementById("dash-period-lbl").textContent = lbl;
    document.getElementById("dash-periodo").textContent = "Periodo: " + lbl;
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
      const data = await API.get(`/calculos/resumen/${y}/${m}?empresa_id=${eid}`);
      this.render(data);
    } catch(e) { UI.toast("Error al cargar dashboard","err"); }
  },

  render(data) {
    if(!data || data.length===0) return;

    const cols = ["hed","hen","rno","hefd","hefn","rfd","rfn"];
    const colors = ["#378ADD","#1D9E75","#BA7517","#534AB7","#D4537E","#D85A30","#A32D2D"];
    const labels = ["HED","HEN","RNO","HEFD","HEFN","RFD","RFN"];

    // Métricas
    const totalH = data.reduce((s,t)=>s+(t.horas_total||0),0);
    const totalNeto = data.reduce((s,t)=>s+(t.neto||0),0);
    const topTec = [...data].sort((a,b)=>(b.neto||0)-(a.neto||0))[0];
    const catTotales = cols.map((c,i)=>({label:labels[i],val:data.reduce((s,t)=>s+(t[c]||0),0)}));
    const catLider = catTotales.reduce((a,b)=>b.val>a.val?b:a);

    document.getElementById("dash-total-h").textContent = totalH.toFixed(1)+"h";
    document.getElementById("dash-total-h-sub").textContent = data.length+" técnicos";
    document.getElementById("dash-neto").textContent = fmtCop(totalNeto);
    document.getElementById("dash-neto-sub").textContent = "periodo actual";
    document.getElementById("dash-top-tec").textContent = topTec?.nombre?.split(" ")[0]+" "+topTec?.nombre?.split(" ")[1]||"";
    document.getElementById("dash-top-tec-sub").textContent = fmtCop(topTec?.neto||0)+" · "+(topTec?.horas_total||0).toFixed(1)+"h";
    document.getElementById("dash-cat-lider").textContent = catLider.label;
    document.getElementById("dash-cat-lider-sub").textContent = catLider.val.toFixed(1)+"h este periodo";

    // Leyenda chart1
    document.getElementById("dash-leg1").innerHTML = labels.map((l,i)=>
      `<span><i style="width:10px;height:10px;border-radius:2px;display:inline-block;background:${colors[i]}"></i>${l}</span>`
    ).join("");

    // Chart 1: barras por categoría
    const ctx1 = document.getElementById("dash-chart1").getContext("2d");
    if(this.charts.c1) this.charts.c1.destroy();
    this.charts.c1 = new Chart(ctx1, {
      type: "bar",
      data: {
        labels,
        datasets: [{
          data: catTotales.map(c=>c.val),
          backgroundColor: colors,
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { ticks: { color:"#888" }, grid: { color:"rgba(0,0,0,0.05)" } },
          y: { ticks: { color:"#888" }, grid: { color:"rgba(0,0,0,0.05)" } }
        }
      }
    });

    // Chart 2: top técnicos horizontal
    const top10 = [...data].sort((a,b)=>(b.horas_total||0)-(a.horas_total||0)).slice(0,10);
    const ctx2 = document.getElementById("dash-chart2").getContext("2d");
    if(this.charts.c2) this.charts.c2.destroy();
    this.charts.c2 = new Chart(ctx2, {
      type: "bar",
      data: {
        labels: top10.map(t=>t.nombre.split(" ")[0]+" "+t.nombre.split(" ")[1]),
        datasets: [{
          data: top10.map(t=>t.horas_total||0),
          backgroundColor: "#378ADD",
        }]
      },
      options: {
        indexAxis: "y",
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { ticks: { color:"#888" }, grid: { color:"rgba(0,0,0,0.05)" } },
          y: { ticks: { color:"#888", font:{ size:10 } }, grid: { display:false } }
        }
      }
    });

    // Tabla
    const tbody = document.getElementById("dash-tbody");
    tbody.innerHTML = [...data].sort((a,b)=>(b.neto||0)-(a.neto||0)).map((t,i)=>`
      <tr>
        <td>${i+1}</td>
        <td>${t.nombre}</td>
        <td style="text-align:right">${t.hed||0}</td>
        <td style="text-align:right">${t.hen||0}</td>
        <td style="text-align:right">${t.rno||0}</td>
        <td style="text-align:right">${t.hefd||0}</td>
        <td style="text-align:right">${t.hefn||0}</td>
        <td style="text-align:right">${t.rfd||0}</td>
        <td style="text-align:right">${t.rfn||0}</td>
        <td style="text-align:right;font-weight:600">${(t.horas_total||0).toFixed(1)}</td>
        <td style="text-align:right;font-weight:600">${fmtCop(t.neto||0)}</td>
      </tr>`).join("");
  }
};
