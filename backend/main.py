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

# Servir frontend
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=os.path.join(frontend_path, "css")), name="css")
    app.mount("/js",     StaticFiles(directory=os.path.join(frontend_path, "js")),  name="js")
    img_path = os.path.join(frontend_path, "img")
    if os.path.exists(img_path):
        app.mount("/img", StaticFiles(directory=img_path), name="img")

    @app.get("/")
    def index():
        return FileResponse(os.path.join(frontend_path, "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
