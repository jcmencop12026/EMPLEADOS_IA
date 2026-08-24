from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, SessionLocal, engine
from app import orchestration_models, notifications  # noqa: F401 — registra tablas/suscriptores
from app.routers import agent_factory, assistant, audit, auth, notifications as notification_routes, operations, organization
from app.seed import bootstrap


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        bootstrap(db)
    finally:
        db.close()
    yield


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
app.include_router(notification_routes.notifications_router)
app.include_router(notification_routes.rules_router)


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
