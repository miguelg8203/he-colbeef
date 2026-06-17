from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, Tecnico
from schemas import TecnicoIn, TecnicoOut
from typing import List
from datetime import date

router = APIRouter(prefix="/tecnicos", tags=["tecnicos"])

@router.get("/lista-inactivos", response_model=List[TecnicoOut])
def listar_inactivos(empresa_id: int, db: Session = Depends(get_db)):
    return db.query(Tecnico).filter(
        Tecnico.empresa_id==empresa_id, Tecnico.activo==False
    ).order_by(Tecnico.nombre).all()

@router.get("/", response_model=List[TecnicoOut])
def listar(empresa_id: int, db: Session = Depends(get_db)):
    return db.query(Tecnico).filter(
        Tecnico.empresa_id==empresa_id, Tecnico.activo==True
    ).order_by(Tecnico.nombre).all()

@router.post("/", response_model=TecnicoOut)
def crear(t: TecnicoIn, empresa_id: int, db: Session = Depends(get_db)):
    obj = Tecnico(**t.model_dump(), empresa_id=empresa_id)
    db.add(obj); db.commit(); db.refresh(obj); return obj

@router.put("/{id}", response_model=TecnicoOut)
def actualizar(id: int, t: TecnicoIn, db: Session = Depends(get_db)):
    obj = db.query(Tecnico).filter(Tecnico.id==id).first()
    if not obj: raise HTTPException(404)
    for k,v in t.model_dump().items(): setattr(obj,k,v)
    db.commit(); db.refresh(obj); return obj

@router.post("/{id}/reactivar", response_model=TecnicoOut)
def reactivar(id: int, db: Session = Depends(get_db)):
    obj = db.query(Tecnico).filter(Tecnico.id==id).first()
    if not obj: raise HTTPException(404)
    obj.activo = True
    obj.fecha_retiro = None
    db.commit(); db.refresh(obj); return obj

@router.delete("/{id}/definitivo")
def eliminar_definitivo(id: int, db: Session = Depends(get_db)):
    obj = db.query(Tecnico).filter(Tecnico.id==id).first()
    if not obj: raise HTTPException(404)
    db.delete(obj); db.commit()
    return {"ok": True}

@router.delete("/{id}")
def ocultar(id: int, fecha_retiro: str = None, db: Session = Depends(get_db)):
    obj = db.query(Tecnico).filter(Tecnico.id==id).first()
    if not obj: raise HTTPException(404)
    obj.activo = False
    try:
        obj.fecha_retiro = date.fromisoformat(fecha_retiro) if fecha_retiro else date.today()
    except:
        obj.fecha_retiro = date.today()
    db.commit()
    return {"ok": True}