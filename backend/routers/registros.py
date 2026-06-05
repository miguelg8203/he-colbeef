from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, Registro
from schemas import RegistroIn, RegistroOut
from typing import List
from datetime import date

router = APIRouter(prefix="/registros", tags=["registros"])

@router.get("/{tecnico_id}", response_model=List[RegistroOut])
def listar(tecnico_id: int, year: int, month: int, db: Session = Depends(get_db)):
    mes_fin = month+1 if month<12 else 1
    año_fin = year if month<12 else year+1
    return db.query(Registro).filter(
        Registro.tecnico_id==tecnico_id,
        Registro.fecha>=date(year,month,21),
        Registro.fecha<=date(año_fin,mes_fin,20),
    ).order_by(Registro.fecha, Registro.turno).all()

@router.post("/{tecnico_id}", response_model=RegistroOut)
def guardar(tecnico_id: int, r: RegistroIn, db: Session = Depends(get_db)):
    obj = db.query(Registro).filter(
        Registro.tecnico_id==tecnico_id,
        Registro.fecha==r.fecha,
        Registro.turno==r.turno
    ).first()
    data = r.model_dump()
    data["tecnico_id"] = tecnico_id

    # Si no hay entrada O no hay salida → limpiar todo
    if not r.entrada or not r.salida:
        data["hed"]=data["hen"]=data["rno"]=0.0
        data["hefd"]=data["hefn"]=data["rfd"]=data["rfn"]=0.0
        data["horas_trab"]=0.0
    elif obj:
        # Si cambió entrada o salida → limpiar HE para que recalcule
        entrada_cambio = (obj.entrada or "") != (r.entrada or "")
        salida_cambio = (obj.salida or "") != (r.salida or "")
        if entrada_cambio or salida_cambio:
            data["hed"]=data["hen"]=data["rno"]=0.0
            data["hefd"]=data["hefn"]=data["rfd"]=data["rfn"]=0.0
            data["horas_trab"]=0.0
        else:
            # No cambió horario → conservar HE manuales
            data["hed"]=obj.hed; data["hen"]=obj.hen; data["rno"]=obj.rno
            data["hefd"]=obj.hefd; data["hefn"]=obj.hefn
            data["rfd"]=obj.rfd; data["rfn"]=obj.rfn
            data["horas_trab"]=obj.horas_trab
    else:
        data["hed"]=data["hen"]=data["rno"]=0.0
        data["hefd"]=data["hefn"]=data["rfd"]=data["rfn"]=0.0
        data["horas_trab"]=0.0

    if obj:
        for k,v in data.items(): setattr(obj,k,v)
    else:
        obj = Registro(**data); db.add(obj)
    db.commit(); db.refresh(obj); return obj

@router.post("/{tecnico_id}/add_turno")
def agregar_turno(tecnico_id: int, data: dict, db: Session = Depends(get_db)):
    fecha = date.fromisoformat(str(data["fecha"]))
    ultimo = db.query(Registro).filter(
        Registro.tecnico_id==tecnico_id,
        Registro.fecha==fecha
    ).order_by(Registro.turno.desc()).first()
    nuevo_turno = (ultimo.turno + 1) if ultimo else 1
    obj = Registro(
        tecnico_id=tecnico_id, fecha=fecha, turno=nuevo_turno,
        es_festivo=ultimo.es_festivo if ultimo else False,
        descanso=0, horas_trab=0,
        hed=0, hen=0, rno=0, hefd=0, hefn=0, rfd=0, rfn=0
    )
    db.add(obj); db.commit(); db.refresh(obj)
    return {"ok": True, "turno": nuevo_turno, "id": obj.id}

@router.delete("/{tecnico_id}/turno/{registro_id}")
def eliminar_turno(tecnico_id: int, registro_id: int, db: Session = Depends(get_db)):
    obj = db.query(Registro).filter(
        Registro.id==registro_id,
        Registro.tecnico_id==tecnico_id
    ).first()
    if not obj: raise HTTPException(404)
    count = db.query(Registro).filter(
        Registro.tecnico_id==tecnico_id,
        Registro.fecha==obj.fecha
    ).count()
    if count <= 1:
        raise HTTPException(400, "No se puede eliminar el único turno del día")
    db.delete(obj); db.commit()
    return {"ok": True}

@router.post("/{tecnico_id}/manual")
def guardar_manual(tecnico_id: int, data: dict, db: Session = Depends(get_db)):
    fecha = date.fromisoformat(str(data["fecha"]))
    campo = data["campo"]; valor = float(data["valor"])
    turno = int(data.get("turno", 1))
    if campo not in ["hed","hen","rno","hefd","hefn","rfd","rfn"]:
        raise HTTPException(400)
    obj = db.query(Registro).filter(
        Registro.tecnico_id==tecnico_id,
        Registro.fecha==fecha,
        Registro.turno==turno
    ).first()
    if not obj:
        obj = Registro(tecnico_id=tecnico_id, fecha=fecha, turno=turno,
                       es_festivo=False, descanso=0, horas_trab=0,
                       hed=0, hen=0, rno=0, hefd=0, hefn=0, rfd=0, rfn=0)
        db.add(obj)
    setattr(obj, campo, valor); db.commit()
    return {"ok": True}

@router.delete("/{tecnico_id}/{fecha}")
def eliminar(tecnico_id: int, fecha: date, db: Session = Depends(get_db)):
    db.query(Registro).filter(
        Registro.tecnico_id==tecnico_id, Registro.fecha==fecha
    ).delete(); db.commit()
    return {"ok": True}