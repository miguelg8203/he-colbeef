"""routers/calculos.py"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db, Registro, Configuracion, Observacion, Tecnico
from calculos import calcular_periodo, calcular_valores
from datetime import date

router = APIRouter(prefix="/calculos", tags=["calculos"])


def _get_cfg(db):
    c = db.query(Configuracion).first()
    return {"horas_sem": c.horas_sem, "inicio_diurno": c.inicio_diurno, "fin_diurno": c.fin_diurno}


def _get_obs_map(db):
    obs = db.query(Observacion).all()
    return {o.nombre.upper(): {"horas_fijas": o.horas_fijas, "cuenta_ot": o.cuenta_ot} for o in obs}


@router.get("/periodo/{tecnico_id}")
def periodo(tecnico_id: int, year: int, month: int, db: Session = Depends(get_db)):
    cfg     = _get_cfg(db)
    obs_map = _get_obs_map(db)

    mes_fin = month + 1 if month < 12 else 1
    año_fin = year if month < 12 else year + 1
    inicio  = date(year, month, 21)
    fin     = date(año_fin, mes_fin, 20)

    regs_db = db.query(Registro).filter(
        Registro.tecnico_id == tecnico_id,
        Registro.fecha >= inicio,
        Registro.fecha <= fin,
    ).all()

    regs = {}
    for r in regs_db:
        regs[r.fecha] = {
            "entrada": r.entrada, "salida": r.salida,
            "descanso": r.descanso, "es_festivo": r.es_festivo,
            "observacion": r.observacion,
        }

    return calcular_periodo(year, month, regs, cfg, obs_map)


@router.get("/resumen/{year}/{month}")
def resumen_periodo(year: int, month: int, db: Session = Depends(get_db)):
    """Resumen de todos los técnicos para la hoja HE"""
    cfg     = _get_cfg(db)
    obs_map = _get_obs_map(db)
    tecs    = db.query(Tecnico).filter(Tecnico.activo == True).all()
    result  = []

    for tec in tecs:
        mes_fin = month + 1 if month < 12 else 1
        año_fin = year if month < 12 else year + 1
        inicio  = date(year, month, 21)
        fin     = date(año_fin, mes_fin, 20)

        regs_db = db.query(Registro).filter(
            Registro.tecnico_id == tec.id,
            Registro.fecha >= inicio,
            Registro.fecha <= fin,
        ).all()

        regs = {r.fecha: {
            "entrada": r.entrada, "salida": r.salida,
            "descanso": r.descanso, "es_festivo": r.es_festivo,
            "observacion": r.observacion,
        } for r in regs_db}

        calc  = calcular_periodo(year, month, regs, cfg, obs_map)
        sub   = calc["subtotales"]
        vals  = calcular_valores(tec.sueldo, cfg["horas_sem"], sub)

        result.append({
            "id": tec.id, "nombre": tec.nombre,
            "cedula": tec.cedula, "cargo": tec.cargo, "sueldo": tec.sueldo,
            **sub, **vals,
        })

    return result
