import os
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, Date, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./he_colbeef.db")
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Empresa(Base):
    __tablename__ = "empresas"
    id       = Column(Integer, primary_key=True, autoincrement=True)
    nombre   = Column(String, nullable=False)
    slug     = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    tecnicos = relationship("Tecnico", back_populates="empresa", cascade="all, delete")
    config   = relationship("Configuracion", back_populates="empresa", uselist=False, cascade="all, delete")
    obs      = relationship("Observacion", back_populates="empresa", cascade="all, delete")


class Configuracion(Base):
    __tablename__ = "configuracion"
    id            = Column(Integer, primary_key=True, autoincrement=True)
    empresa_id    = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    horas_sem     = Column(Float, default=44.0)
    inicio_diurno = Column(String, default="06:00")
    fin_diurno    = Column(String, default="19:00")
    empresa       = relationship("Empresa", back_populates="config")


class Observacion(Base):
    __tablename__ = "observaciones"
    id          = Column(Integer, primary_key=True, autoincrement=True)
    empresa_id  = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    nombre      = Column(String, nullable=False)
    horas_fijas = Column(Float, default=0.0)
    cuenta_ot   = Column(Boolean, default=False)
    empresa     = relationship("Empresa", back_populates="obs")


class Tecnico(Base):
    __tablename__ = "tecnicos"
    id            = Column(Integer, primary_key=True, autoincrement=True)
    empresa_id    = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    nombre        = Column(String, nullable=False)
    cedula        = Column(String, nullable=False)
    cargo         = Column(String, nullable=False)
    sueldo        = Column(Float, nullable=False)
    activo        = Column(Boolean, default=True)
    fecha_retiro  = Column(Date, nullable=True)
    registros     = relationship("Registro", back_populates="tecnico", cascade="all, delete")
    empresa       = relationship("Empresa", back_populates="tecnicos")


class Registro(Base):
    __tablename__ = "registros"
    id          = Column(Integer, primary_key=True, autoincrement=True)
    tecnico_id  = Column(Integer, ForeignKey("tecnicos.id"), nullable=False)
    fecha       = Column(Date, nullable=False)
    turno       = Column(Integer, default=1)
    es_festivo  = Column(Boolean, default=False)
    entrada     = Column(String, nullable=True)
    salida      = Column(String, nullable=True)
    descanso    = Column(Float, default=0.0)
    observacion = Column(String, nullable=True)
    horas_trab  = Column(Float, default=0.0)
    hed         = Column(Float, default=0.0)
    hen         = Column(Float, default=0.0)
    rno         = Column(Float, default=0.0)
    hefd        = Column(Float, default=0.0)
    hefn        = Column(Float, default=0.0)
    rfd         = Column(Float, default=0.0)
    rfn         = Column(Float, default=0.0)
    tecnico     = relationship("Tecnico", back_populates="registros")


OBS_DEFAULT = [
    ("DESCANSO",0.0,False),("DESCANSO FESTIVO",0.0,False),("INCAPACIDAD",0.0,False),
    ("PERMISO",0.0,False),("DIA DE LA FAMILIA",0.0,False),("CAPACITACION ALTURAS",8.0,True),
    ("DIA COMPENSATORIO",8.0,True),("RENUNCIA",0.0,False),("DESCANSO POR CULTO",0.0,False),
    ("LICENCIA POR LUTO",0.0,False),("AUSENCIA INJUSTIFICADA",0.0,False),
    ("PERMISO JURADO VOTACION",0.0,False),("CITA MEDICA",0.0,True),
    ("DISPONIBILIDAD",0.0,True),("VACACIONES",0.0,False),("VOTACION",0.0,False),
    ("REUNION",4.0,True),
]

TECNICOS_COLBEEF = [
    ("Alberto Giraldo Muñoz","91299928","Técnico Locativo",1750905),
    ("Angel Manuel Vega Serrano","1095947101","Soldador",2000000),
    ("Brayan Alberto Pimiento Caballero","1005372215","Técnico de Mantenimiento Industrial",1750905),
    ("Edgar Andres Florez Villamizar","1098760784","Planeador Táctico de Mantenimiento",2100000),
    ("Edison Geovanny Leon Ortiz","1007770027","Técnico de Mantenimiento Industrial",1750905),
    ("Erik Yasin Florez Parada","1098806507","Técnico Eléctrico",1750905),
    ("Jairo Andres Lopez Murillo","1099365824","Subcoordinador de Gestión de Activos",2700000),
    ("Jhon Michael Velasco Castro","1095828837","Supervisor de Mantenimiento",2528000),
    ("Jhonnys de Jesús Mena Bonett","1118865973","Técnico de Mantenimiento Industrial",1750905),
    ("Johan Andres Perez de la Rosa","1065872598","Técnico de Mantenimiento Industrial",1750905),
    ("John Jairo Solano Jaimes","1099364262","Supervisor de Mantenimiento",2528557),
    ("Juan Camilo Nieves Vergara","1102389527","Técnico de Mantenimiento Industrial",1750905),
    ("Ludwin Leonel Duran Leon","1097611606","Técnico Frigorista",2000000),
    ("Miguel Alexander Gutierrez Hernandez","91514544","Auxiliar Administrativo",1750905),
    ("Nicolas Ardila Rosas","1095925464","Técnico de Gestión de Activos",1750905),
    ("Oscar Johel Cordero Grazt","1005289022","Técnico de Mantenimiento Industrial",1750905),
    ("Sergio Enrique Torra Bustos","1098697161","Supervisor de Mantenimiento",2200000),
    ("Yan Sebastian Mora Rondon","1098764768","Técnico Frigorista",1750905),
    ("Yeison Jose Pereira Brochero","1007589766","Técnico de Mantenimiento Industrial",1750905),
    ("Jahir Sanchez","1000000000","Coordinador",3000000),
]


def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    if not db.query(Empresa).first():
        for nombre, slug, pwd in [
            ("Colbeef","colbeef","colbeef2024"),
            ("Manzanares","manzanares","manz2024"),
            ("Vitelsa","vitelsa","vite2024"),
        ]:
            emp = Empresa(nombre=nombre, slug=slug, password=pwd)
            db.add(emp); db.flush()
            db.add(Configuracion(empresa_id=emp.id))
            for n,h,ot in OBS_DEFAULT:
                db.add(Observacion(empresa_id=emp.id, nombre=n, horas_fijas=h, cuenta_ot=ot))
            if slug == "colbeef":
                for n,c,ca,s in TECNICOS_COLBEEF:
                    db.add(Tecnico(empresa_id=emp.id, nombre=n, cedula=c, cargo=ca, sueldo=s))
        db.commit()
    db.close()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()