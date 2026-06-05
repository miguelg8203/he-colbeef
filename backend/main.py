from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from database import init_db
from routers import tecnicos, registros, calculos, config, exportar, auth
import os

app = FastAPI(title="Time Xtra", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

init_db()

app.include_router(auth.router)
app.include_router(tecnicos.router)
app.include_router(registros.router)
app.include_router(calculos.router)
app.include_router(config.router)
app.include_router(exportar.router)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
for path in [os.path.join(BASE_DIR,"..","frontend"), os.path.join(BASE_DIR,"frontend"), "/app/frontend"]:
    if os.path.exists(path):
        fp = os.path.abspath(path)
        for folder, name in [("css","static"),("js","js"),("img","img")]:
            d = os.path.join(fp, folder)
            if os.path.exists(d):
                app.mount(f"/{name}", StaticFiles(directory=d), name=name)
        @app.get("/")
        def index(): return FileResponse(os.path.join(fp, "index.html"), headers={"Cache-Control": "no-cache, no-store, must-revalidate"})
        break

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.environ.get("PORT",8000)), reload=False)