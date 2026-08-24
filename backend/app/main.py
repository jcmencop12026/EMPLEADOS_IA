from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, SessionLocal, engine
from app import orchestration_models  # noqa: F401 — registra tablas
from app import automation_models  # noqa: F401
from app.routers import agent_factory, assistant, audit, auth, automations, operations, organization
from app.seed import bootstrap
from app.services.automation_scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        bootstrap(db)
    finally:
        db.close()
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(organization.router)
app.include_router(audit.router)
app.include_router(assistant.router)
app.include_router(agent_factory.router)
app.include_router(operations.router)
app.include_router(automations.router)
app.include_router(automations.runs_router)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "phase": "B2-agent-factory",
    }


@app.get("/")
def root():
    return {
        "message": "EMPLEADOS_IA API",
        "docs": "/docs",
        "health": "/health",
        "frontend": "http://127.0.0.1:5180",
    }
