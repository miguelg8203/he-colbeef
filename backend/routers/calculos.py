from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db, Registro, Configuracion, Observacion, Tecnico
from calculos import calcular_fila, calcular_valores, get_lunes
from datetime import date, timedelta

router = APIRouter(prefix="/calculos", tags=["calculos"])

def _cfg(empresa_id, db):
    c = db.query(Configuracion).filter(Configuracion.empresa_id==empresa_id).first()
    if not c: return {"horas_sem":44.0,"inicio_diurno":"06:00","fin_diurno":"19:00"}
    return {"horas_sem":c.horas_sem,"inicio_diurno":c.inicio_diurno,"fin_diurno":c.fin_diurno}

def _obs(empresa_id, db):
    obs = db.query(Observacion).filter(Observacion.empresa_id==empresa_id).all()
    return {o.nombre.upper():{"horas_fijas":o.horas_fijas,"cuenta_ot":o.cuenta_ot} for o in obs}

def _regs(tecnico_id, year, month, db):
    mes_fin = month+1 if month<12 else 1
    año_fin = year if month<12 else year+1
    inicio  = date(year, month, 21)
    fin     = date(año_fin, mes_fin, 20)
    inicio_ext = inicio - timedelta(days=7)

    rows = db.query(Registro).filter(
        Registro.tecnico_id==tecnico_id,
        Registro.fecha>=inicio_ext,
        Registro.fecha<=fin,
    ).order_by(Registro.fecha, Registro.turno).all()

    result = {}
    for r in rows:
        reg_dict = {
            "id": r.id, "turno": r.turno,
            "entrada":r.entrada,"salida":r.salida,"descanso":r.descanso,
            "es_festivo":r.es_festivo,"observacion":r.observacion,
            "hed":r.hed,"hen":r.hen,"rno":r.rno,
            "hefd":r.hefd,"hefn":r.hefn,"rfd":r.rfd,"rfn":r.rfn
        }
        if r.fecha not in result:
            result[r.fecha] = []
        result[r.fecha].append(reg_dict)
    return result


def calcular_periodo_multi(year, month, registros_multi, cfg, obs_map):
    from datetime import date as date_type
    inicio = date_type(year, month, 21)
    mes_fin = month+1 if month<12 else 1
    año_fin = year if month<12 else year+1
    fin = date_type(año_fin, mes_fin, 20)

    dias = []
    d = inicio
    while d <= fin:
        dias.append(d)
        d += timedelta(days=1)

    semanas = {}
    for d in dias:
        dow = d.weekday()
        dom = d if dow == 6 else d - timedelta(days=dow+1)
        if dom not in semanas:
            semanas[dom] = []
        semanas[dom].append(d)

    registros_simple = {}
    for fecha, regs in registros_multi.items():
        registros_simple[fecha] = regs[0] if regs else {}

    cols_he = ["hed","hen","rno","hefd","hefn","rfd","rfn"]

    semanas_result = []
    for dom in sorted(semanas.keys()):
        dias_sem = semanas[dom]
        min_acum = 0.0
        rows = []

        for fecha in dias_sem:
            turnos = registros_multi.get(fecha, [{}])
            if not turnos:
                turnos = [{}]

            filas_dia = []
            for reg in turnos:
                # Calcular resultado automático
                res = calcular_fila(fecha, reg, obs_map, registros_todos=registros_simple)

                # Si el registro tiene HE guardados manualmente, usarlos
                tiene_manual = any(reg.get(c, 0) for c in cols_he)
                if tiene_manual:
                    for c in cols_he:
                        res[c] = reg.get(c, 0) or 0.0

                filas_dia.append({
                    "fecha": fecha.isoformat(),
                    "resultado": res,
                    "registro": {**reg, "fecha": fecha.isoformat()}
                })
                min_acum += res["min_dia"]

            rows.extend(filas_dia)

        ot_sem = round(min_acum/60 - cfg["horas_sem"], 1)
        horas_sem = round(min_acum/60, 1)
        semanas_result.append({"lunes": dom, "rows": rows, "ot_semana": ot_sem, "horas_semana": horas_sem})

    sub = dict(hed=0.0, hen=0.0, rno=0.0, hefd=0.0, hefn=0.0,
               rfd=0.0, rfn=0.0, horas_total=0.0, ot_total=0.0)
    for sem in semanas_result:
        sub["ot_total"]    += sem["ot_semana"]
        sub["horas_total"] += sem["horas_semana"]
        for row in sem["rows"]:
            for col in cols_he:
                sub[col] += row["resultado"][col]
    for k in sub:
        sub[k] = round(sub[k], 1)

    return {"semanas": semanas_result, "subtotales": sub,
            "dias": [d.isoformat() for d in dias],
            "inicio": inicio.isoformat(), "fin": fin.isoformat()}


@router.get("/periodo/{tecnico_id}")
def periodo(tecnico_id: int, year: int, month: int, empresa_id: int, db: Session = Depends(get_db)):
    return calcular_periodo_multi(year, month, _regs(tecnico_id,year,month,db), _cfg(empresa_id,db), _obs(empresa_id,db))


@router.get("/resumen/{year}/{month}")
def resumen(year: int, month: int, empresa_id: int, db: Session = Depends(get_db)):
    cfg = _cfg(empresa_id,db); obs = _obs(empresa_id,db)
    tecs = db.query(Tecnico).filter(Tecnico.empresa_id==empresa_id, Tecnico.activo==True).all()
    result = []
    for tec in tecs:
        calc = calcular_periodo_multi(year, month, _regs(tec.id,year,month,db), cfg, obs)
        sub  = calc["subtotales"]
        vals = calcular_valores(tec.sueldo, cfg["horas_sem"], sub)
        result.append({"id":tec.id,"nombre":tec.nombre,"cedula":tec.cedula,
                       "cargo":tec.cargo,"sueldo":tec.sueldo,**sub,**vals})
    return result