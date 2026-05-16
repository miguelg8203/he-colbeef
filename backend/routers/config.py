from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, Configuracion, Observacion
from schemas import ConfigIn, ConfigOut, ObservacionIn, ObservacionOut
from typing import List

router = APIRouter(tags=["config"])

@router.get("/config", response_model=ConfigOut)
def get_config(db: Session = Depends(get_db)):
    return db.query(Configuracion).first()

@router.put("/config", response_model=ConfigOut)
def set_config(c: ConfigIn, db: Session = Depends(get_db)):
    obj = db.query(Configuracion).first()
    for k, v in c.model_dump().items(): setattr(obj, k, v)
    db.commit(); db.refresh(obj); return obj

@router.get("/observaciones", response_model=List[ObservacionOut])
def listar_obs(db: Session = Depends(get_db)):
    return db.query(Observacion).all()

@router.post("/observaciones", response_model=ObservacionOut)
def crear_obs(o: ObservacionIn, db: Session = Depends(get_db)):
    obj = Observacion(**o.model_dump())
    db.add(obj); db.commit(); db.refresh(obj); return obj

@router.put("/observaciones/{id}", response_model=ObservacionOut)
def actualizar_obs(id: int, o: ObservacionIn, db: Session = Depends(get_db)):
    obj = db.query(Observacion).filter(Observacion.id == id).first()
    if not obj: raise HTTPException(404, "No encontrada")
    for k, v in o.model_dump().items(): setattr(obj, k, v)
    db.commit(); db.refresh(obj); return obj

@router.delete("/observaciones/{id}")
def eliminar_obs(id: int, db: Session = Depends(get_db)):
    obj = db.query(Observacion).filter(Observacion.id == id).first()
    if not obj: raise HTTPException(404, "No encontrada")
    db.delete(obj); db.commit(); return {"ok": True}
