from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import Base, SessionLocal, engine
from app import automation_models  # noqa: F401
from app import finops_models  # noqa: F401
from app import knowledge_models  # noqa: F401 — registra tablas
from app import orchestration_models, notifications  # noqa: F401 — registra tablas/suscriptores
from app import salud_models  # noqa: F401 — registra tablas IPS
from app import experience_models  # noqa: F401 — experiencia transversal core
from app import opportunity_models  # noqa: F401 — oportunidades proactivas 1030
from app.routers import (
    admin,
    agent_factory,
    assistant,
    audit,
    auth,
    automations,
    capabilities,
    finops,
    knowledge,
    notifications as notification_routes,
    operations,
    organization,
    platform,
    salud,
    experience,
    oportunidades,
    test_lab,
    tools,
)
from app.seed import bootstrap
from app.services.automation_events import register_automation_event_handlers
from app.services.automation_scheduler import start_scheduler, stop_scheduler
from app.services.proactive_scheduler import start_proactive_scheduler, stop_proactive_scheduler
from app.services.authorization import AuthorizationError


@asynccontextmanager
async def lifespan(_app: FastAPI):
    from scripts.migration_control import MigrationControlError, run_database_preflight

    try:
        run_database_preflight(settings.database_url)
    except MigrationControlError as exc:
        raise RuntimeError(str(exc)) from exc

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        bootstrap(db)
    finally:
        db.close()
    register_automation_event_handlers()
    start_scheduler()
    start_proactive_scheduler()
    yield
    stop_proactive_scheduler()
    stop_scheduler()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)


@app.exception_handler(AuthorizationError)
async def authorization_error_handler(_request, exc: AuthorizationError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


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
app.include_router(platform.router)
app.include_router(admin.router)
app.include_router(audit.router)
app.include_router(assistant.router)
app.include_router(agent_factory.router)
app.include_router(capabilities.router)
app.include_router(tools.router)
app.include_router(knowledge.router)
app.include_router(test_lab.router)
app.include_router(operations.router)
app.include_router(automations.router)
app.include_router(automations.runs_router)
app.include_router(notification_routes.notifications_router)
app.include_router(notification_routes.rules_router)
app.include_router(finops.router)
app.include_router(salud.router)
app.include_router(experience.router)
app.include_router(oportunidades.router)


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
