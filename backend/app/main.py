from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
# Импортируем все модели для правильной инициализации relationships
from app.db.base import *  # noqa: F401, F403

app = FastAPI(
    title="EDU MAX",
    description="EDU MAX | Backend",
    version="3.0.0",
    contact={
        "name": "Dev",
        "email": "insentodesu@icloud.com",
    },
    license_info={
        "name": "MIT",
    },
    swagger_ui_parameters={
        "docExpansion": "none",
        "defaultModelsExpandDepth": -1,
    },
)

Base.metadata.create_all(bind=engine)

app.include_router(api_router, prefix=settings.api_v1_prefix)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = Path(settings.static_root)
static_dir.mkdir(parents=True, exist_ok=True)
app.mount(settings.static_url, StaticFiles(directory=static_dir, check_dir=False), name="static")

@app.get(
    "/health",
    tags=["Служебные"],
    summary="Проверка состояния",
    description="Проверка состояния сервиса",
)
def healthcheck():
    return {"status": "ok"}
