from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, Tecnico
from schemas import TecnicoIn, TecnicoOut
from typing import List

router = APIRouter(prefix="/tecnicos", tags=["tecnicos"])

@router.get("/", response_model=List[TecnicoOut])
def listar(db: Session = Depends(get_db)):
    return db.query(Tecnico).filter(Tecnico.activo == True).all()

@router.post("/", response_model=TecnicoOut)
def crear(t: TecnicoIn, db: Session = Depends(get_db)):
    obj = Tecnico(**t.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

@router.put("/{id}", response_model=TecnicoOut)
def actualizar(id: int, t: TecnicoIn, db: Session = Depends(get_db)):
    obj = db.query(Tecnico).filter(Tecnico.id == id).first()
    if not obj: raise HTTPException(404, "No encontrado")
    for k, v in t.model_dump().items(): setattr(obj, k, v)
    db.commit(); db.refresh(obj); return obj

@router.delete("/{id}")
def eliminar(id: int, db: Session = Depends(get_db)):
    obj = db.query(Tecnico).filter(Tecnico.id == id).first()
    if not obj: raise HTTPException(404, "No encontrado")
    obj.activo = False
    db.commit(); return {"ok": True}
