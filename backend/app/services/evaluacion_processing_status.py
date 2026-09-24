"""Estado efímero del procesamiento de evaluaciones para consola interna."""
from __future__ import annotations

from datetime import datetime, timezone
from threading import Lock
from time import perf_counter
from typing import Any

_lock = Lock()
_state: dict[str, dict[str, Any]] = {}


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def start(expediente_id: str) -> None:
    with _lock:
        _state[expediente_id] = {
            "status": "PROCESSING",
            "stage": "EVALUACION_PRELIMINAR",
            "progress": 45,
            "started_at": _iso_now(),
            "started_perf": perf_counter(),
            "finished_at": None,
            "duration_ms": None,
            "error": None,
        }


def finish(expediente_id: str) -> dict[str, Any]:
    with _lock:
        current = _state.get(expediente_id) or {}
        started_perf = current.get("started_perf")
        duration_ms = round((perf_counter() - started_perf) * 1000, 1) if started_perf else None
        current.update({
            "status": "DONE",
            "stage": "RESULTADO_DISPONIBLE",
            "progress": 100,
            "finished_at": _iso_now(),
            "duration_ms": duration_ms,
            "error": None,
        })
        current.pop("started_perf", None)
        _state[expediente_id] = current
        return dict(current)


def fail(expediente_id: str, message: str) -> dict[str, Any]:
    with _lock:
        current = _state.get(expediente_id) or {}
        started_perf = current.get("started_perf")
        duration_ms = round((perf_counter() - started_perf) * 1000, 1) if started_perf else None
        current.update({"status": "ERROR", "stage": "ERROR", "finished_at": _iso_now(), "duration_ms": duration_ms, "error": message})
        current.pop("started_perf", None)
        _state[expediente_id] = current
        return dict(current)


def get(expediente_id: str) -> dict[str, Any]:
    with _lock:
        current = dict(_state.get(expediente_id) or {})
    if not current:
        return {
            "status": "IDLE",
            "stage": "SIN_EJECUCION_ACTIVA",
            "progress": 0,
            "started_at": None,
            "finished_at": None,
            "duration_ms": None,
            "elapsed_ms": None,
            "error": None,
        }
    started_perf = current.pop("started_perf", None)
    current["elapsed_ms"] = round((perf_counter() - started_perf) * 1000, 1) if current.get("status") == "PROCESSING" and started_perf else current.get("duration_ms")
    return current
