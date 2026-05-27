from pydantic import BaseModel
from typing import Optional
from datetime import date


class ConfigIn(BaseModel):
    horas_sem:     float = 44.0
    inicio_diurno: str   = "06:00"
    fin_diurno:    str   = "19:00"

class ConfigOut(ConfigIn):
    id: int
    model_config = {"from_attributes": True}


class ObservacionIn(BaseModel):
    nombre:      str
    horas_fijas: float = 0.0
    cuenta_ot:   bool  = False

class ObservacionOut(ObservacionIn):
    id: int
    model_config = {"from_attributes": True}


class TecnicoIn(BaseModel):
    nombre: str
    cedula: str
    cargo:  str
    sueldo: float

class TecnicoOut(TecnicoIn):
    id:     int
    activo: bool
    model_config = {"from_attributes": True}


class RegistroIn(BaseModel):
    fecha:       date
    turno:       int            = 1
    es_festivo:  bool           = False
    entrada:     Optional[str]  = None
    salida:      Optional[str]  = None
    descanso:    float          = 0.0
    observacion: Optional[str]  = None

class RegistroOut(RegistroIn):
    id:         int
    tecnico_id: int
    horas_trab: float
    hed:        float
    hen:        float
    rno:        float
    hefd:       float
    hefn:       float
    rfd:        float
    rfn:        float
    model_config = {"from_attributes": True}
