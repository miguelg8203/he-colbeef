# HE Colbeef · Gestor de Horas Extras

## Requisitos
- Python 3.10+
- VS Code con extensión Python

## Instalación

```bash
# 1. Instalar dependencias
cd backend
pip install -r requirements.txt

# 2. Iniciar servidor
python main.py
```

## Uso
Abrir en el navegador: **http://127.0.0.1:8000**

## Estructura
```
he-colbeef/
├── backend/
│   ├── main.py          → Servidor FastAPI
│   ├── database.py      → Modelos SQLite
│   ├── calculos.py      → Lógica HE (Ley 2101/2021)
│   ├── schemas.py       → Validación datos
│   ├── requirements.txt
│   └── routers/
│       ├── tecnicos.py  → CRUD técnicos
│       ├── registros.py → CRUD planilla diaria
│       ├── calculos.py  → Cálculo periodos
│       ├── config.py    → Config + observaciones
│       └── exportar.py  → PDF
└── frontend/
    ├── index.html
    ├── css/styles.css
    └── js/
        ├── app.js
        ├── tecnicos.js
        ├── planilla.js
        └── resumen.js
```

## API Docs
Con el servidor corriendo: **http://127.0.0.1:8000/docs**

## Configuración
- Horas semanales: 44h (ajustable a 42h en Jul 2026)
- Diurno: 06:00 → 19:00
- Periodo: 21 de cada mes → 20 del mes siguiente
