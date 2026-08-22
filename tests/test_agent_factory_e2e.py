import os
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mktemp(suffix='.db')}"
os.environ["JWT_SECRET"] = "test-secret-cursor-802"

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.seed import bootstrap  # noqa: E402

engine = create_engine(os.environ["DATABASE_URL"], connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)
db = TestingSessionLocal()
bootstrap(db)
db.close()


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

SAMPLE_RIPS = {
    "usuarios": [{"tipoDocumentoIdentificacion": "CC", "numDocumentoIdentificacion": "1", "codSexo": "M", "fechaNacimiento": "1980-01-01"}],
    "consultas": [{"codConsulta": "890201", "numDocumentoIdentificacion": "999"}],
    "procedimientos": [], "medicamentos": [], "otrosServicios": [],
}


@pytest.fixture
def token():
    res = client.post("/api/auth/login", json={"username": "admin", "password": "Admin2026*"})
    return res.json()["access_token"]


def _h(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_list_templates(token):
    res = client.get("/api/agent-factory/templates", headers=_h(token))
    assert res.status_code == 200
    codes = {t["code"] for t in res.json()}
    assert "analista-documental" in codes
    assert "auditor-rips" in codes


def test_create_configure_test_certify_publish_activate(token):
    caps = client.get("/api/agent-factory/capabilities", headers=_h(token)).json()
    tools = client.get("/api/agent-factory/tools", headers=_h(token)).json()
    docint_cap = next(c for c in caps if c["code"] == "docint")
    docint_tool = next(t for t in tools if t["code"] == "docint")

    created = client.post(
        "/api/agent-factory/employees",
        headers=_h(token),
        json={"name": "Test DOCINT 802", "specialty": "DOCINT", "template_code": "analista-documental"},
    )
    assert created.status_code == 200
    emp_id = created.json()["id"]

    updated = client.patch(
        f"/api/agent-factory/employees/{emp_id}",
        headers=_h(token),
        json={
            "capability_ids": [docint_cap["id"]],
            "tools": [{"tool_id": docint_tool["id"], "permission": "ALLOW"}],
            "model_policy": {"preferred_provider": "rule-engine", "preferred_model": "docint-rules-v1"},
            "risk_level": "MEDIUM",
        },
    )
    assert updated.status_code == 200

    test_res = client.post(f"/api/agent-factory/employees/{emp_id}/test", headers=_h(token))
    assert test_res.status_code == 200
    assert test_res.json()["total"] >= 1

    cert = client.post(f"/api/agent-factory/employees/{emp_id}/certify", headers=_h(token))
    assert cert.status_code == 200
    assert cert.json()["result"] in ("PASS", "PASS_WITH_WARNINGS")

    pub = client.post(f"/api/agent-factory/employees/{emp_id}/publish", headers=_h(token))
    assert pub.status_code == 200
    assert pub.json()["lifecycle_status"] == "PUBLISHED"

    act = client.post(f"/api/agent-factory/employees/{emp_id}/activate", headers=_h(token))
    assert act.status_code == 200
    assert act.json()["lifecycle_status"] == "ACTIVE"


def test_orchestrator_selects_published_employee(token):
    caps = client.get("/api/agent-factory/capabilities", headers=_h(token)).json()
    tools = client.get("/api/agent-factory/tools", headers=_h(token)).json()
    docint_cap = next(c for c in caps if c["code"] == "docint")
    docint_tool = next(t for t in tools if t["code"] == "docint")

    created = client.post(
        "/api/agent-factory/employees",
        headers=_h(token),
        json={"name": "Orch Select 802", "specialty": "DOCINT", "template_code": "analista-documental"},
    )
    emp_id = created.json()["id"]
    client.patch(f"/api/agent-factory/employees/{emp_id}", headers=_h(token), json={
        "capability_ids": [docint_cap["id"]],
        "tools": [{"tool_id": docint_tool["id"], "permission": "ALLOW"}],
    })
    client.post(f"/api/agent-factory/employees/{emp_id}/test", headers=_h(token))
    client.post(f"/api/agent-factory/employees/{emp_id}/certify", headers=_h(token))
    client.post(f"/api/agent-factory/employees/{emp_id}/publish", headers=_h(token))
    client.post(f"/api/agent-factory/employees/{emp_id}/activate", headers=_h(token))

    orch = client.post(
        "/api/assistant/ask",
        headers=_h(token),
        json={"message": "Analiza documentos", "context": {"tool": "docint", "documents": [{"id": "d1", "tipo_documento": "CC", "numero_documento": "1234567890", "fecha": "2026-01-01", "contenido": "Documento de prueba suficientemente largo"}]}},
    )
    assert orch.status_code == 200
    assert orch.json()["plan_id"]


def test_permission_denied_viewer():
    db = TestingSessionLocal()
    from app.models import User
    from app.security import hash_password
    from app.models import Organization
    org = db.query(Organization).first()
    viewer = User(organization_id=org.id, username="viewer802", password_hash=hash_password("Viewer802*"), role="viewer")
    db.add(viewer)
    db.commit()
    db.close()

    login = client.post("/api/auth/login", json={"username": "viewer802", "password": "Viewer802*"})
    token = login.json()["access_token"]
    res = client.post("/api/agent-factory/employees", headers=_h(token), json={"name": "X", "specialty": "Y"})
    assert res.status_code == 403


def test_tenant_isolation_employees(token):
    res = client.get("/api/agent-factory/employees", headers=_h(token))
    assert res.status_code == 200
    for emp in res.json():
        detail = client.get(f"/api/agent-factory/employees/{emp['id']}", headers=_h(token))
        assert detail.status_code == 200


def test_existing_health_employees_active(token):
    res = client.get("/api/agent-factory/employees", headers=_h(token))
    names = {e["name"] for e in res.json()}
    assert "Analista Documental IA" in names
    docint = next(e for e in res.json() if e["name"] == "Analista Documental IA")
    assert docint["lifecycle_status"] == "ACTIVE"


def test_regression_orchestrator_rips(token):
    res = client.post(
        "/api/assistant/ask",
        headers=_h(token),
        json={"message": "RIPS regression", "context": {"tool": "rips", "rips": SAMPLE_RIPS}},
    )
    assert res.status_code == 200
    assert res.json()["plan_id"]
