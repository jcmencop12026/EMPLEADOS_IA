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
from app import baseline_models  # noqa: F401 — línea base e impacto 1200
from app import valuation_models  # noqa: F401 — valoración económica 1210
from app import diagnostic_models  # noqa: F401 — diagnóstico transversal 1220
from app import external_models  # noqa: F401 — inteligencia externa 1240
from app import continuidad_models  # noqa: F401 — continuidad operativa 1360
from app import llm_models  # noqa: F401 — LLM Gateway V1
from app.health import build_health_report, health_http_status
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
    llm_providers,
    notifications as notification_routes,
    operations,
    organization,
    platform,
    salud,
    experience,
    linea_base,
    control_center,
    oportunidades,
    senales,
    valoracion,
    diagnosticos,
    inteligencia_externa,
    continuidad,
    test_lab,
    tools,
)
from app.seed import bootstrap
from app.security_config import validate_security_settings
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

    validate_security_settings(
        database_url=settings.database_url,
        jwt_secret=settings.jwt_secret,
        bootstrap_admin_password=settings.bootstrap_admin_password,
    )

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


_docs_kwargs: dict[str, str | None] = {}
if not settings.api_docs_enabled:
    _docs_kwargs = {"docs_url": None, "redoc_url": None, "openapi_url": None}

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    **_docs_kwargs,
)


@app.exception_handler(AuthorizationError)
async def authorization_error_handler(_request, exc: AuthorizationError):
    return JSONResponse(
        status_code=403,
        content={"detail": str(exc) or "No tiene permisos para realizar esta acción."},
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
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
app.include_router(senales.router)
app.include_router(linea_base.router)
app.include_router(valoracion.router)
app.include_router(diagnosticos.router)
app.include_router(inteligencia_externa.router)
app.include_router(continuidad.router)
app.include_router(control_center.router)
app.include_router(llm_providers.router)


@app.get("/health")
def health():
    report = build_health_report(include_schedulers=True)
    return JSONResponse(status_code=health_http_status(report), content=report)


@app.get("/health/live")
def health_live():
    return {
        "status": "up",
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_env,
        "message": "Proceso API en ejecución",
    }


@app.get("/health/ready")
def health_ready():
    report = build_health_report(include_schedulers=True)
    ready = report["components"]["database"]["status"] == "up"
    content = {
        "status": "up" if ready else "down",
        "environment": settings.app_env,
        "components": {
            "database": report["components"]["database"],
            "schedulers": report["components"].get("schedulers"),
        },
    }
    return JSONResponse(status_code=200 if ready else 503, content=content)


@app.get("/")
def root():
    payload = {
        "message": "EMPLEADOS_IA API",
        "health": "/health",
        "frontend": "http://127.0.0.1:5180",
    }
    if settings.api_docs_enabled:
        payload["docs"] = "/docs"
    return payload
