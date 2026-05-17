from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, Registro, Configuracion, Observacion
from schemas import RegistroIn, RegistroOut
from calculos import clasificar_dia, get_lunes
from typing import List
from datetime import date, timedelta

router = APIRouter(prefix="/registros", tags=["registros"])


def _get_cfg(db):
    c = db.query(Configuracion).first()
    return {"horas_sem": c.horas_sem, "inicio_diurno": c.inicio_diurno, "fin_diurno": c.fin_diurno}


def _get_obs_map(db):
    obs = db.query(Observacion).all()
    return {o.nombre.upper(): {"horas_fijas": o.horas_fijas, "cuenta_ot": o.cuenta_ot} for o in obs}


def _min_acum_semana(tecnico_id: int, fecha: date, db: Session) -> float:
    lunes = get_lunes(fecha)
    total = 0.0
    d = lunes
    while d < fecha:
        r = db.query(Registro).filter(Registro.tecnico_id == tecnico_id, Registro.fecha == d).first()
        if r:
            total += r.horas_trab * 60
        d += timedelta(days=1)
    return total


def _es_culto_semana(tecnico_id: int, fecha: date, db: Session) -> bool:
    lunes = get_lunes(fecha)
    sabado = lunes + timedelta(days=5)
    r = db.query(Registro).filter(
        Registro.tecnico_id == tecnico_id,
        Registro.fecha == sabado
    ).first()
    return r is not None and (r.observacion or "").upper() == "DESCANSO POR CULTO"


@router.get("/{tecnico_id}", response_model=List[RegistroOut])
def listar(tecnico_id: int, year: int, month: int, db: Session = Depends(get_db)):
    mes_fin = month + 1 if month < 12 else 1
    año_fin = year if month < 12 else year + 1
    inicio  = date(year, month, 21)
    fin     = date(año_fin, mes_fin, 20)
    return db.query(Registro).filter(
        Registro.tecnico_id == tecnico_id,
        Registro.fecha >= inicio,
        Registro.fecha <= fin,
    ).order_by(Registro.fecha).all()


@router.post("/{tecnico_id}", response_model=RegistroOut)
def guardar(tecnico_id: int, r: RegistroIn, db: Session = Depends(get_db)):
    cfg     = _get_cfg(db)
    obs_map = _get_obs_map(db)
    min_ac  = _min_acum_semana(tecnico_id, r.fecha, db)
    es_culto= _es_culto_semana(tecnico_id, r.fecha, db)

    calc = clasificar_dia(r.fecha, r.model_dump(), min_ac, cfg, es_culto, obs_map)

    obj = db.query(Registro).filter(
        Registro.tecnico_id == tecnico_id, Registro.fecha == r.fecha
    ).first()

    data = r.model_dump()
    data.update({
        "tecnico_id": tecnico_id,
        "horas_trab": calc["horas_trab"],
        "hed": calc["hed"], "hen": calc["hen"], "rno": calc["rno"],
        "hefd": calc["hefd"], "hefn": calc["hefn"], "rfd": calc["rfd"], "rfn": calc["rfn"],
    })

    if obj:
        for k, v in data.items(): setattr(obj, k, v)
    else:
        obj = Registro(**data)
        db.add(obj)

    db.commit(); db.refresh(obj)
    return obj


@router.delete("/{tecnico_id}/{fecha}")
def eliminar(tecnico_id: int, fecha: date, db: Session = Depends(get_db)):
    obj = db.query(Registro).filter(
        Registro.tecnico_id == tecnico_id, Registro.fecha == fecha
    ).first()
    if obj:
        db.delete(obj); db.commit()
    return {"ok": True}


@router.post("/{tecnico_id}/manual")
def guardar_manual(tecnico_id: int, data: dict, db: Session = Depends(get_db)):
    """Guardar un valor HE manualmente para un día específico."""
    from datetime import date as date_type
    fecha  = date_type.fromisoformat(data["fecha"])
    campo  = data["campo"]
    valor  = float(data["valor"])

    campos_validos = ["hed","hen","rno","hefd","hefn","rfd","rfn"]
    if campo not in campos_validos:
        raise HTTPException(400, "Campo no válido")

    obj = db.query(Registro).filter(
        Registro.tecnico_id == tecnico_id,
        Registro.fecha == fecha
    ).first()

    if not obj:
        obj = Registro(tecnico_id=tecnico_id, fecha=fecha)
        db.add(obj)

    setattr(obj, campo, valor)
    db.commit()
    return {"ok": True}
