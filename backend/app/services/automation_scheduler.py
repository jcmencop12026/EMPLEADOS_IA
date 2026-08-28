"""Scheduler backend V1 — polling sin depender del navegador (CURSOR-810)."""
from __future__ import annotations

import logging
import threading
import time
from datetime import datetime, timezone

from app.database import SessionLocal
from app.automation_models import Automation
from app.enums import AutomationStatus, AutomationTriggerType
from app.services import automation_service

logger = logging.getLogger(__name__)

_POLL_SECONDS = 30
_thread: threading.Thread | None = None
_stop = threading.Event()


def _tick() -> None:
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        due = (
            db.query(Automation)
            .filter(
                Automation.status == AutomationStatus.ACTIVE,
                Automation.trigger_type == AutomationTriggerType.SCHEDULE,
                Automation.next_run_at.isnot(None),
                Automation.next_run_at <= now,
            )
            .all()
        )
        for automation in due:
            try:
                from app.audit import write_audit

                automation_service.trigger_run(
                    db,
                    automation=automation,
                    user_id=automation.created_by_id,
                    trigger_source=AutomationTriggerType.SCHEDULE,
                    scheduled_for=automation.next_run_at,
                )
                write_audit(
                    db,
                    action="automation.scheduler_run",
                    organization_id=automation.organization_id,
                    user_id=automation.created_by_id,
                    detail=automation.name,
                )
            except Exception:
                logger.exception("Scheduler error automation=%s", automation.id)
                automation.status = AutomationStatus.ERROR
                db.commit()
    finally:
        db.close()


def _loop() -> None:
    while not _stop.is_set():
        try:
            _tick()
        except Exception:
            logger.exception("Scheduler tick failed")
        _stop.wait(_POLL_SECONDS)


def start_scheduler() -> None:
    global _thread
    db = SessionLocal()
    try:
        automation_service.recalculate_all_active(db)
    finally:
        db.close()
    if _thread and _thread.is_alive():
        return
    _stop.clear()
    _thread = threading.Thread(target=_loop, name="automation-scheduler", daemon=True)
    _thread.start()
    logger.info("Automation scheduler started")


def stop_scheduler() -> None:
    _stop.set()
    if _thread:
        _thread.join(timeout=2)


def is_scheduler_running() -> bool:
    return _thread is not None and _thread.is_alive()
