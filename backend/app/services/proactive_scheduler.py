"""Scheduler proactivo — detección sin prompt humano (1030)."""

from __future__ import annotations

import json
import logging
import threading
import time
from datetime import datetime, timezone

from app.database import SessionLocal
from app.services.proactive_service import run_proactive_pipeline

logger = logging.getLogger(__name__)

_POLL_SECONDS = 60
_thread: threading.Thread | None = None
_stop = threading.Event()
_last_tick: dict[str, datetime] = {}


def _synthetic_indicators(org_key: str) -> list[dict]:
    """Indicadores sintéticos genéricos para detección proactiva."""
    hour = datetime.now(timezone.utc).hour
    indicators = []
    # NS-1: proceso administrativo repetitivo
    if hour % 4 == 0:
        indicators.append({
            "tipo": "proceso_repetitivo",
            "dominio": "administrativo",
            "evento": "automatizacion_proceso_administrativo",
            "payload": {
                "titulo": "Automatizar proceso administrativo repetitivo",
                "descripcion": "Detección de tareas manuales recurrentes con alto volumen",
                "tipo_oportunidad": "AUTOMATIZACION",
                "indicadores": {"volumen_mensual": 450, "tiempo_promedio_min": 12, "repeticiones": 30},
                "impacto_estimado": 2_500_000,
                "valor_potencial": 1_800_000,
                "urgencia": "MEDIA",
                "esfuerzo": "MEDIO",
                "source_reference": f"admin-repeat-{org_key}",
            },
        })
    # NS-2: caída conversión + capacidad ociosa
    if hour % 3 == 1:
        indicators.append({
            "tipo": "conversion_caida",
            "dominio": "comercial",
            "evento": "caida_conversion_capacidad_ociosa",
            "payload": {
                "titulo": "Recuperar conversión comercial con capacidad disponible",
                "descripcion": "Caída de tasa de conversión con capacidad comercial ociosa",
                "tipo_oportunidad": "COMERCIAL",
                "indicadores": {"tasa_conversion": 0.12, "tasa_anterior": 0.22, "capacidad_ociosa_pct": 35},
                "impacto_estimado": 8_000_000,
                "valor_potencial": 5_500_000,
                "urgencia": "ALTA",
                "tendencia": "EMPEORANDO",
                "source_reference": f"comercial-conv-{org_key}",
            },
        })
    return indicators


def _tick() -> None:
    db = SessionLocal()
    try:
        from app.models import Organization

        orgs = db.query(Organization).filter(Organization.status == "ACTIVE").all()
        for org in orgs:
            org_key = org.id[:8]
            for item in _synthetic_indicators(org_key):
                try:
                    result = run_proactive_pipeline(
                        db,
                        organization_id=org.id,
                        tipo=item["tipo"],
                        dominio=item["dominio"],
                        evento=item["evento"],
                        payload=item["payload"],
                        origen="proactive_scheduler",
                    )
                    db.commit()
                    if not result.get("deduplicated"):
                        logger.info(
                            "Proactive pipeline org=%s opp=%s estado=%s",
                            org.id, result.get("opportunity_id"), result.get("estado"),
                        )
                except Exception:
                    db.rollback()
                    logger.exception("Proactive pipeline error org=%s evento=%s", org.id, item["evento"])
    finally:
        db.close()


def _loop() -> None:
    while not _stop.is_set():
        try:
            _tick()
        except Exception:
            logger.exception("Proactive scheduler tick failed")
        _stop.wait(_POLL_SECONDS)


def start_proactive_scheduler() -> None:
    global _thread
    if _thread and _thread.is_alive():
        return
    _stop.clear()
    _thread = threading.Thread(target=_loop, name="proactive-scheduler", daemon=True)
    _thread.start()
    logger.info("Proactive scheduler started (poll=%ss)", _POLL_SECONDS)


def stop_proactive_scheduler() -> None:
    _stop.set()
    logger.info("Proactive scheduler stopped")


def is_scheduler_running() -> bool:
    return _thread is not None and _thread.is_alive()


def run_proactive_tick_once(db=None) -> list[dict]:
    """Ejecuta un tick manual — útil para tests."""
    from app.models import Organization

    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True
    results = []
    try:
        orgs = db.query(Organization).filter(Organization.status == "ACTIVE").all()
        for org in orgs:
            for item in _synthetic_indicators(org.id[:8]):
                result = run_proactive_pipeline(
                    db,
                    organization_id=org.id,
                    tipo=item["tipo"],
                    dominio=item["dominio"],
                    evento=item["evento"],
                    payload=item["payload"],
                    origen="proactive_scheduler_test",
                )
                results.append(result)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        if close_db:
            db.close()
    return results
