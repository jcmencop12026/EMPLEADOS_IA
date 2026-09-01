"""MB-06 Fábrica — puente Arquitecto, biblioteca, multitenant y runtime."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Organization, User
from app.orchestration_models import AIEmployee
from app.security import hash_password
from app.transformacion_models import EmpleadoIARequerimiento

pytestmark = [pytest.mark.auth, pytest.mark.tenant]


@pytest.fixture
def fab_db(client):
    from tests.conftest import TestingSessionLocal

    db = TestingSessionLocal()
    yield db
    db.close()


def _login(client: TestClient, username: str) -> dict[str, str]:
    res = client.post("/api/auth/login", json={"username": username, "password": "testpass123"})
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def _create_org_user(db: Session, name: str) -> tuple[Organization, User]:
    org = Organization(id=str(uuid.uuid4()), name=name, slug=f"fab-{uuid.uuid4().hex[:8]}")
    db.add(org)
    user = User(
        id=str(uuid.uuid4()),
        organization_id=org.id,
        username=f"fab_{uuid.uuid4().hex[:6]}",
        email=f"fab_{uuid.uuid4().hex[:6]}@test.local",
        password_hash=hash_password("testpass123"),
        is_active=True,
        role="operator",
    )
    db.add(user)
    db.flush()
    return org, user


def _requerimiento(db: Session, org_id: str) -> EmpleadoIARequerimiento:
    from app.transformacion_models import DossierEmpresarial

    dossier = db.query(DossierEmpresarial).filter(DossierEmpresarial.organization_id == org_id).first()
    if not dossier:
        dossier = DossierEmpresarial(organization_id=org_id, etapa_actual="OPORTUNIDADES")
        db.add(dossier)
        db.flush()
    req = EmpleadoIARequerimiento(
        organization_id=org_id,
        dossier_id=dossier.id,
        objetivo="Automatizar clasificación de solicitudes",
        responsabilidad="Clasificar y enrutar solicitudes entrantes",
        entradas_json='["solicitudes", "reglas"]',
        salidas_json='["categoría", "prioridad"]',
        herramientas_json='["conocimiento", "operaciones"]',
        frecuencia="Diaria",
        riesgo="MEDIO",
        supervision="Revisión humana en excepciones",
        estado="PENDIENTE",
    )
    db.add(req)
    db.flush()
    return req


def test_caso1_arquitecto_a_fabrica_borrador(client: TestClient, auth_headers, fab_db):
    """Diagnóstico → requerimiento → borrador en fábrica."""
    admin = fab_db.query(User).filter(User.username == "admin").first()
    req = _requerimiento(fab_db, admin.organization_id)
    fab_db.commit()

    res = client.post(f"/api/agent-factory/employees/from-requerimiento/{req.id}", headers=auth_headers)
    assert res.status_code == 200, res.text
    body = res.json()
    emp = body["employee"]
    assert emp["lifecycle_status"] == "DRAFT"
    assert body["trazabilidad"]["origen"] == "ARQUITECTO"

    emp_row = fab_db.query(AIEmployee).filter(AIEmployee.id == emp["id"]).one()
    assert emp_row.source_type == "ARQUITECTO"
    assert emp_row.requerimiento_id == req.id

    fab_db.expire_all()
    req_db = fab_db.query(EmpleadoIARequerimiento).filter(EmpleadoIARequerimiento.id == req.id).one()
    assert req_db.estado == "CONSUMIDO"
    assert req_db.employee_id == emp["id"]


def test_caso2_creacion_guiada_biblioteca_y_estimacion(client: TestClient, auth_headers, fab_db):
    created = client.post(
        "/api/agent-factory/employees",
        headers=auth_headers,
        json={"name": "Asistente guiado", "specialty": "DOCINT", "template_code": "asistente-operativo"},
    )
    assert created.status_code == 200
    emp_id = created.json()["id"]

    bib = client.get("/api/agent-factory/biblioteca", headers=auth_headers)
    assert bib.status_code == 200
    assert bib.json()["total"] >= 1

    est = client.get(f"/api/agent-factory/employees/{emp_id}/estimate-capacity", headers=auth_headers)
    assert est.status_code == 200
    assert "finops" in est.json() or "advertencia" in est.json()


def test_caso3_falla_controlada_proveedor(client: TestClient, auth_headers, fab_db):
    created = client.post(
        "/api/agent-factory/employees",
        headers=auth_headers,
        json={"name": "Sin proveedor", "specialty": "DOCINT"},
    ).json()
    emp_id = created["id"]
    client.patch(
        f"/api/agent-factory/employees/{emp_id}",
        headers=auth_headers,
        json={"model_policy": {"preferred_provider": "openai-inexistente", "preferred_model": "gpt-4"}},
    )
    val = client.get(f"/api/agent-factory/employees/{emp_id}/validate-provider", headers=auth_headers)
    assert val.status_code == 200
    assert val.json()["valid"] is False

    pub = client.post(f"/api/agent-factory/employees/{emp_id}/publish", headers=auth_headers)
    assert pub.status_code in (403, 400, 422)


def test_caso4_multitenant_empleado_aislamiento(client: TestClient, auth_headers, fab_db):
    admin = fab_db.query(User).filter(User.username == "admin").first()
    req = _requerimiento(fab_db, admin.organization_id)
    fab_db.commit()
    created = client.post(
        f"/api/agent-factory/employees/from-requerimiento/{req.id}",
        headers=auth_headers,
    ).json()
    emp_id = created["employee"]["id"]

    org_b, user_b = _create_org_user(fab_db, "Tenant B Fab")
    fab_db.commit()
    headers_b = _login(client, user_b.username)

    denied = client.get(f"/api/agent-factory/employees/{emp_id}", headers=headers_b)
    assert denied.status_code in (403, 404)

    bib_b = client.get("/api/agent-factory/biblioteca", headers=headers_b).json()
    ids_b = [i["id"] for i in bib_b["items"]]
    assert emp_id not in ids_b


def test_clone_como_borrador_no_activa(client: TestClient, auth_headers, fab_db):
    from tests.test_employee_lifecycle_factory_mb06 import _create_ready_employee

    token = auth_headers["Authorization"].split(" ", 1)[1]
    emp_id = _create_ready_employee(client, token)
    clone = client.post(f"/api/agent-factory/employees/{emp_id}/clone", headers=auth_headers)
    assert clone.status_code == 200
    assert clone.json()["lifecycle_status"] == "DRAFT"
    assert clone.json()["source_type"] == "PLANTILLA_CLON"


def test_gobierno_operacional_boundary(client: TestClient, auth_headers):
    res = client.get("/api/agent-factory/gobierno-operacional/boundary", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["estado"] == "FRONTERA_PREPARADA"
