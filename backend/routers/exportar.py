"""routers/exportar.py"""
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from database import get_db, Tecnico, Configuracion, Observacion, Registro
from calculos import calcular_periodo, calcular_valores, FACTORES
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from datetime import date
import io

router = APIRouter(prefix="/exportar", tags=["exportar"])

MESES = ["","Enero","Febrero","Marzo","Abril","Mayo","Junio",
         "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
DIAS  = ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"]

C_AZUL   = colors.HexColor("#1a3a5c")
C_VERDE  = colors.HexColor("#00c885")
C_DOM    = colors.HexColor("#dbeafe")
C_FEST   = colors.HexColor("#fde8e8")
C_GRIS   = colors.HexColor("#f5f5f5")
C_BLANCO = colors.white


def _get_cfg(db):
    c = db.query(Configuracion).first()
    return {"horas_sem": c.horas_sem, "inicio_diurno": c.inicio_diurno, "fin_diurno": c.fin_diurno}


def _get_obs_map(db):
    obs = db.query(Observacion).all()
    return {o.nombre.upper(): {"horas_fijas": o.horas_fijas, "cuenta_ot": o.cuenta_ot} for o in obs}


def fmt(v):
    if v is None or v == 0.0: return ""
    return f"{v:.1f}"


@router.get("/tecnico/{tecnico_id}/{year}/{month}")
def pdf_tecnico(tecnico_id: int, year: int, month: int, db: Session = Depends(get_db)):
    tec     = db.query(Tecnico).filter(Tecnico.id == tecnico_id).first()
    cfg     = _get_cfg(db)
    obs_map = _get_obs_map(db)

    mes_fin = month + 1 if month < 12 else 1
    año_fin = year if month < 12 else year + 1
    inicio  = date(year, month, 21)
    fin     = date(año_fin, mes_fin, 20)

    regs_db = db.query(Registro).filter(
        Registro.tecnico_id == tecnico_id,
        Registro.fecha >= inicio, Registro.fecha <= fin,
    ).all()
    regs = {r.fecha: r for r in regs_db}

    calc = calcular_periodo(year, month, regs_db and
        {r.fecha: {"entrada":r.entrada,"salida":r.salida,"descanso":r.descanso,
                   "es_festivo":r.es_festivo,"observacion":r.observacion}
         for r in regs_db} or {}, cfg, obs_map)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4),
                            leftMargin=1*cm, rightMargin=1*cm,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)

    styles = getSampleStyleSheet()
    title_s = ParagraphStyle("t", fontSize=13, textColor=C_AZUL, fontName="Helvetica-Bold")
    sub_s   = ParagraphStyle("s", fontSize=9,  textColor=colors.grey)

    periodo_lbl = f"21 {MESES[month]} → 20 {MESES[mes_fin]} {año_fin}"
    story = [
        Paragraph("HORAS EXTRAS · COLBEEF", title_s),
        Paragraph(f"{tec.nombre}  |  {tec.cargo}  |  Periodo: {periodo_lbl}", sub_s),
        Spacer(1, 0.4*cm),
    ]

    # Encabezado tabla
    headers = ["#","Fecha","Entrada","Salida","Desc.","Observación",
               "H.Trab","OT","HED","HEN","RNO","HEFD","HEFN","RFD","RFN"]
    col_w   = [0.6,2.6,1.3,1.3,0.9,3.2,1.1,1.1,1.0,1.0,1.0,1.0,1.0,1.0,1.0]
    col_w_cm= [x*cm for x in col_w]

    tabla_data = [headers]
    row_styles = []
    fila = 1  # 0 = header

    sub_acum = {"hed":0,"hen":0,"rno":0,"hefd":0,"hefn":0,"rfd":0,"rfn":0}
    ot_prev  = None
    num = 0

    for sem in calc["semanas"]:
        ot_sem = sem["ot_semana"]
        for item in sem["rows"]:
            f   = item["fecha"]
            r   = item["registro"]
            res = item["resultado"]
            num += 1

            is_dom  = f.weekday() == 6
            is_fest = r.get("es_festivo", False)

            obs_str = r.get("observacion") or ""
            row = [
                str(num),
                f"{DIAS[f.weekday()]} {f.day} {MESES[f.month][:3]}",
                r.get("entrada") or "",
                r.get("salida")  or "",
                fmt(r.get("descanso")),
                obs_str[:28],
                fmt(res["horas_trab"]),
                "",  # OT se llena al final de semana
                fmt(res["hed"]), fmt(res["hen"]), fmt(res["rno"]),
                fmt(res["hefd"]),fmt(res["hefn"]),fmt(res["rfd"]),fmt(res["rfn"]),
            ]
            tabla_data.append(row)

            if is_dom:
                row_styles.append(("BACKGROUND", (0,fila),(-1,fila), C_DOM))
            elif is_fest:
                row_styles.append(("BACKGROUND", (0,fila),(-1,fila), C_FEST))
            elif fila % 2 == 0:
                row_styles.append(("BACKGROUND", (0,fila),(-1,fila), C_GRIS))

            fila += 1

        # Fila subtotal semana
        for k in sub_acum: sub_acum[k] += sum(item["resultado"][k] for item in sem["rows"])
        ot_str = f"{ot_sem:+.1f}h" if ot_sem != 0 else "0.0h"
        tabla_data.append(["","","","","",f"SEMANA  H:{sem['horas_semana']:.1f}",
                           "","" + ot_str,"","","","","","",""])
        row_styles.append(("BACKGROUND", (0,fila),(-1,fila), colors.HexColor("#e8f5e9")))
        row_styles.append(("FONTNAME",   (0,fila),(-1,fila), "Helvetica-Bold"))
        row_styles.append(("FONTSIZE",   (0,fila),(-1,fila), 7))
        fila += 1

    # Fila SUBTOTAL PERIODO
    sub = calc["subtotales"]
    tabla_data.append([
        "","","","","","SUBTOTAL PERIODO","","",
        fmt(sub["hed"]), fmt(sub["hen"]), fmt(sub["rno"]),
        fmt(sub["hefd"]),fmt(sub["hefn"]),fmt(sub["rfd"]),fmt(sub["rfn"]),
    ])
    row_styles.append(("BACKGROUND", (0,fila),(-1,fila), C_VERDE))
    row_styles.append(("FONTNAME",   (0,fila),(-1,fila), "Helvetica-Bold"))
    row_styles.append(("TEXTCOLOR",  (0,fila),(-1,fila), colors.white))

    base_style = [
        ("BACKGROUND", (0,0),  (-1,0),  C_AZUL),
        ("TEXTCOLOR",  (0,0),  (-1,0),  colors.white),
        ("FONTNAME",   (0,0),  (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",   (0,0),  (-1,-1), 7),
        ("ALIGN",      (0,0),  (-1,-1), "CENTER"),
        ("ALIGN",      (5,1),  (5,-1),  "LEFT"),
        ("GRID",       (0,0),  (-1,-1), 0.3, colors.lightgrey),
        ("ROWBACKGROUNDS", (0,1),(-1,-2), [C_BLANCO, C_GRIS]),
    ]

    t = Table(tabla_data, colWidths=col_w_cm, repeatRows=1)
    t.setStyle(TableStyle(base_style + row_styles))
    story.append(t)
    doc.build(story)
    buf.seek(0)

    nombre_archivo = f"HE_{tec.nombre.replace(' ','_')}_{year}_{month:02d}.pdf"
    return StreamingResponse(buf, media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={nombre_archivo}"})


@router.get("/resumen/{year}/{month}")
def pdf_resumen(year: int, month: int, db: Session = Depends(get_db)):
    """PDF hoja HE resumen con todos los técnicos"""
    from routers.calculos import resumen_periodo
    data = resumen_periodo(year, month, db)

    mes_fin = month + 1 if month < 12 else 1
    año_fin = year if month < 12 else year + 1

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4),
                            leftMargin=1*cm, rightMargin=1*cm,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)

    styles = getSampleStyleSheet()
    title_s = ParagraphStyle("t", fontSize=13, textColor=C_AZUL, fontName="Helvetica-Bold")
    sub_s   = ParagraphStyle("s", fontSize=9,  textColor=colors.grey)

    periodo_lbl = f"21 {MESES[month]} → 20 {MESES[mes_fin]} {año_fin}"
    story = [
        Paragraph("RESUMEN HORAS EXTRAS · COLBEEF", title_s),
        Paragraph(f"Periodo: {periodo_lbl}  |  44 Horas Semanales  |  Recargos desde las 19:00", sub_s),
        Spacer(1, 0.5*cm),
    ]

    headers = ["#","Nombre","Cargo","Sueldo",
               "HED","HEN","RNO","HEFD","HEFN","RFD","RFN","Neto a Pagar"]
    col_w   = [0.6,4.5,3.5,1.8,1.0,1.0,1.0,1.0,1.0,1.0,1.0,2.2]
    col_w_cm= [x*cm for x in col_w]

    tabla = [headers]
    total_neto = 0.0

    for i, t in enumerate(data, 1):
        tabla.append([
            str(i), t["nombre"], t["cargo"],
            f"${t['sueldo']:,.0f}",
            fmt(t["hed"]), fmt(t["hen"]), fmt(t["rno"]),
            fmt(t["hefd"]),fmt(t["hefn"]),fmt(t["rfd"]),fmt(t["rfn"]),
            f"${t['neto']:,.0f}",
        ])
        total_neto += t["neto"]

    tabla.append(["","","","TOTAL","","","","","","","",f"${total_neto:,.0f}"])

    ts = TableStyle([
        ("BACKGROUND", (0,0),  (-1,0),  C_AZUL),
        ("TEXTCOLOR",  (0,0),  (-1,0),  colors.white),
        ("FONTNAME",   (0,0),  (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",   (0,0),  (-1,-1), 8),
        ("ALIGN",      (0,0),  (-1,-1), "CENTER"),
        ("ALIGN",      (1,1),  (2,-1),  "LEFT"),
        ("ROWBACKGROUNDS",(0,1),(-1,-2),[C_BLANCO, C_GRIS]),
        ("BACKGROUND", (0,-1),(-1,-1),  C_VERDE),
        ("FONTNAME",   (0,-1),(-1,-1),  "Helvetica-Bold"),
        ("TEXTCOLOR",  (0,-1),(-1,-1),  colors.white),
        ("GRID",       (0,0), (-1,-1),  0.3, colors.lightgrey),
    ])

    tbl = Table(tabla, colWidths=col_w_cm, repeatRows=1)
    tbl.setStyle(ts)
    story.append(tbl)
    doc.build(story)
    buf.seek(0)

    nombre_archivo = f"HE_Resumen_{year}_{month:02d}.pdf"
    return StreamingResponse(buf, media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={nombre_archivo}"})
