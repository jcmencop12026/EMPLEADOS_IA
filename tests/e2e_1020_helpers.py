"""Utilidades compartidas — E2E-INTEGRAL-1020."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from app.fixtures.motor_analitico_datasets import get_motor_dataset
from app.models import Organization, User
from app.orchestration_models import AIEmployee
from app.security import hash_password
from conftest import TestingSessionLocal, auth_header

E2E_SOLICITUD = (
    "Analiza por qué estamos demorando la recuperación de cartera, "
    "qué está afectando el flujo de caja y qué debemos hacer primero."
)

EVIDENCE_DIR = Path(__file__).resolve().parents[1] / "INTERCAMBIO" / "SALIDA" / "e2e_1020"


def e2e_datasets() -> dict[str, list[dict[str, Any]]]:
    """Caso empresarial sintético complejo (motor D + contratos)."""
    data = get_motor_dataset("D")
    if "contratos" not in data:
        data["contratos"] = [
            {"pagador": "EPS Norte", "plazo_pago_dias": 30, "clausula_radicacion": "10 días hábiles"},
        ]
    return data


def save_evidence(name: str, payload: dict[str, Any]) -> Path:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    path = EVIDENCE_DIR / f"{name}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return path


def create_org_token(client, org_name: str, username: str, password: str, role: str = "admin") -> str:
    db = TestingSessionLocal()
    org = Organization(name=org_name)
    db.add(org)
    db.flush()
    db.add(User(organization_id=org.id, username=username, password_hash=hash_password(password), role=role))
    db.commit()
    db.close()
    login = client.post("/api/auth/login", json={"username": username, "password": password})
    assert login.status_code == 200
    return login.json()["access_token"]


def radicacion_employee_id() -> str:
    db = TestingSessionLocal()
    try:
        emp = db.query(AIEmployee).filter(AIEmployee.code == "ips-radicacion-analyst").first()
        assert emp is not None
        return emp.id
    finally:
        db.close()


def upload_knowledge(client, token: str, name: str, content: str, metadata: dict | None = None) -> str:
    res = client.post(
        "/api/knowledge/text",
        headers=auth_header(token),
        json={"name": name, "content": content, "metadata": metadata or {"tipo": "contrato", "area": "radicacion"}},
    )
    assert res.status_code in (200, 201)
    return res.json()["id"]


def grant_knowledge(client, token: str, employee_id: str, document_id: str) -> None:
    res = client.post(
        f"/api/knowledge/employees/{employee_id}/grant/{document_id}",
        headers=auth_header(token),
    )
    assert res.status_code in (200, 201)


def run_salud_analysis(client, token: str, *, ips_name: str = "IPS E2E-1020", solicitud: str | None = None):
    return client.post(
        "/api/salud/analisis",
        headers=auth_header(token),
        json={
            "ips_name": ips_name,
            "request_text": solicitud or E2E_SOLICITUD,
            "inline_datasets": e2e_datasets(),
        },
    )


def build_trace_chain(diag: dict[str, Any], *, work_plan_id: str | None = None, experiencia_id: str | None = None) -> dict[str, Any]:
    esp = diag.get("especialistas") or {}
    lider = esp.get("lider") or {}
    return {
        "solicitud": diag.get("id"),
        "orquestacion": esp.get("selection_log_id"),
        "equipo": {
            "lider": lider.get("employee_name"),
            "razon": esp.get("razon_seleccion_global"),
            "validador": (esp.get("validador") or {}).get("employee_name"),
        },
        "conocimiento": diag.get("conocimiento"),
        "analisis": {
            "hipotesis_principal": diag.get("hipotesis_principal"),
            "hallazgos": len(diag.get("hallazgos") or []),
            "motor": bool(diag.get("recomendacion_consolidada")),
        },
        "recomendacion": diag.get("recomendacion_consolidada"),
        "work_plan_id": work_plan_id or diag.get("work_plan_id"),
        "finops": diag.get("finops"),
        "experiencia_core_id": experiencia_id,
    }
