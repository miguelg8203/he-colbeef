from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, Empresa

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login")
def login(data: dict, db: Session = Depends(get_db)):
    slug = data.get("empresa","").lower()
    pwd  = data.get("password","")
    emp  = db.query(Empresa).filter(Empresa.slug == slug).first()
    if not emp or emp.password != pwd:
        raise HTTPException(401, "Empresa o contraseña incorrecta")
    return {"ok": True, "empresa_id": emp.id, "empresa_nombre": emp.nombre, "empresa_slug": emp.slug}
