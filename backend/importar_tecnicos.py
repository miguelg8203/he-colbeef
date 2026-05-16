"""
importar_tecnicos.py
Ejecutar UNA SOLA VEZ para cargar los técnicos reales desde el Excel.
Uso: python importar_tecnicos.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))

from database import SessionLocal, Tecnico, init_db

# Datos reales del Excel HE Colbeef
TECNICOS = [
    ("Alberto Giraldo Muñoz",               "91299928",    "Técnico Locativo",                            1750905),
    ("Angel Manuel Vega Serrano",            "1095947101",  "Soldador",                                    2000000),
    ("Brayan Alberto Pimiento Caballero",    "1005372215",  "Técnico de Mantenimiento Industrial",         1750905),
    ("Edgar Andres Florez Villamizar",       "1098760784",  "Planeador Táctico de Mantenimiento Industrial",2100000),
    ("Edison Geovanny Leon Ortiz",           "1007770027",  "Técnico de Mantenimiento Industrial",         1750905),
    ("Erik Yasin Florez Parada",             "1098806507",  "Técnico Eléctrico",                           1750905),
    ("Jairo Andres Lopez Murillo",           "1099365824",  "Subcoordinador de Gestión de Activos",        2700000),
    ("Jhon Michael Velasco Castro",          "1095828837",  "Supervisor de Mantenimiento",                 2528000),
    ("Jhonnys de Jesús Mena Bonett",         "1118865973",  "Técnico de Mantenimiento Industrial",         1750905),
    ("Johan Andres Perez de la Rosa",        "1065872598",  "Técnico de Mantenimiento Industrial",         1750905),
    ("John Jairo Solano Jaimes",             "1099364262",  "Supervisor de Mantenimiento",                 2528557),
    ("Juan Camilo Nieves Vergara",           "1102389527",  "Técnico de Mantenimiento Industrial",         1750905),
    ("Ludwin Leonel Duran Leon",             "1097611606",  "Técnico Frigorista",                          2000000),
    ("Miguel Alexander Gutierrez Hernandez", "91514544",    "Auxiliar Administrativo",                     1750905),
    ("Nicolas Ardila Rosas",                 "1095925464",  "Técnico de Gestión de Activos",               1750905),
    ("Oscar Johel Cordero Grazt",            "1005289022",  "Técnico de Mantenimiento Industrial",         1750905),
    ("Sergio Enrique Torra Bustos",          "1098697161",  "Supervisor de Mantenimiento",                 2200000),
    ("Yan Sebastian Mora Rondon",            "1098764768",  "Técnico Frigorista",                          1750905),
    ("Yeison Jose Pereira Brochero",         "1007589766",  "Técnico de Mantenimiento Industrial",         1750905),
    ("Jahir Sanchez",                        "1000000000",  "Coordinador",                                 3000000),
]

def importar():
    init_db()
    db = SessionLocal()

    # Limpiar técnicos existentes
    db.query(Tecnico).delete()
    db.commit()

    for nombre, cedula, cargo, sueldo in TECNICOS:
        db.add(Tecnico(nombre=nombre, cedula=cedula, cargo=cargo, sueldo=sueldo))

    db.commit()
    total = db.query(Tecnico).count()
    db.close()
    print(f"✅ {total} técnicos importados correctamente")

if __name__ == "__main__":
    importar()
