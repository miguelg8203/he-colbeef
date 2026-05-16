from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from database import init_db
from routers import tecnicos, registros, calculos, config, exportar
import os

app = FastAPI(title="HE Colbeef", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar base de datos
init_db()

# Routers
app.include_router(tecnicos.router)
app.include_router(registros.router)
app.include_router(calculos.router)
app.include_router(config.router)
app.include_router(exportar.router)

# Servir frontend - buscar en varias rutas posibles
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_PATHS = [
    os.path.join(BASE_DIR, "..", "frontend"),
    os.path.join(BASE_DIR, "frontend"),
    "/app/frontend",
]

frontend_path = None
for p in FRONTEND_PATHS:
    if os.path.exists(p):
        frontend_path = os.path.abspath(p)
        break

if frontend_path:
    css_path = os.path.join(frontend_path, "css")
    js_path  = os.path.join(frontend_path, "js")
    img_path = os.path.join(frontend_path, "img")

    if os.path.exists(css_path):
        app.mount("/static", StaticFiles(directory=css_path), name="css")
    if os.path.exists(js_path):
        app.mount("/js", StaticFiles(directory=js_path), name="js")
    if os.path.exists(img_path):
        app.mount("/img", StaticFiles(directory=img_path), name="img")

    @app.get("/")
    def index():
        return FileResponse(os.path.join(frontend_path, "index.html"))
else:
    @app.get("/")
    def index_fallback():
        return {"status": "ok", "msg": "Frontend no encontrado"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
