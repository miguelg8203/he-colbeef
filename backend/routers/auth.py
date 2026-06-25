from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, Empresa
from datetime import date

router = APIRouter(prefix="/auth", tags=["auth"])

_CADUCIDAD = {"fecha": None}
_CLAVE_ADMIN = "cielo0306"

@router.post("/login")
def login(data: dict, db: Session = Depends(get_db)):
    if _CADUCIDAD["fecha"]:
        hoy = date.today()
        if hoy > _CADUCIDAD["fecha"]:
            raise HTTPException(403, "Licencia vencida")

    slug = data.get("empresa","").lower()
    pwd  = data.get("password","")
    emp  = db.query(Empresa).filter(Empresa.slug == slug).first()
    if not emp or emp.password != pwd:
        raise HTTPException(401, "Empresa o contraseña incorrecta")
    return {"ok": True, "empresa_id": emp.id, "empresa_nombre": emp.nombre, "empresa_slug": emp.slug}

@router.get("/caducidad")
def get_caducidad():
    f = _CADUCIDAD["fecha"]
    if not f:
        return {"fecha": None, "dias": None, "vencida": False}
    hoy = date.today()
    dias = (f - hoy).days
    return {"fecha": f.isoformat(), "dias": dias, "vencida": hoy > f}

@router.post("/caducidad")
def set_caducidad(data: dict):
    clave = data.get("clave","")
    if clave != _CLAVE_ADMIN:
        raise HTTPException(401, "Clave incorrecta")
    fecha_str = data.get("fecha","")
    try:
        _CADUCIDAD["fecha"] = date.fromisoformat(fecha_str)
    except:
        raise HTTPException(400, "Fecha inválida")
    return {"ok": True, "fecha": _CADUCIDAD["fecha"].isoformat()}