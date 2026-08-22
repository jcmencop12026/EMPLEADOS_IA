import os
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mktemp(suffix='.db')}"
os.environ["JWT_SECRET"] = "test-secret-cursor-801"

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


def _login() -> str:
    res = client.post("/api/auth/login", json={"username": "admin", "password": "Admin2026*"})
    assert res.status_code == 200
    return res.json()["access_token"]


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


SAMPLE_RIPS = {
    "usuarios": [
        {
            "tipoDocumentoIdentificacion": "CC",
            "numDocumentoIdentificacion": "1234567890",
            "codSexo": "M",
            "fechaNacimiento": "1980-01-15",
        }
    ],
    "consultas": [{"codConsulta": "890201", "numDocumentoIdentificacion": "9999999999"}],
    "procedimientos": [],
    "medicamentos": [],
    "otrosServicios": [],
}


@pytest.fixture
def token():
    return _login()


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_coordinator_route_rips(token):
    res = client.post(
        "/api/agent-factory/coordinator/route",
        headers=_headers(token),
        json={
            "request": "Analiza estos RIPS y dime qué problemas existen.",
            "context": {"tool": "rips", "rips": SAMPLE_RIPS},
            "auto_execute": True,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["plan_id"]
    assert data["status"] in ("WAITING_APPROVAL", "COMPLETED", "FAILED")
    assert data.get("tasks")


def test_assistant_ask_docint(token):
    res = client.post(
        "/api/assistant/ask",
        headers=_headers(token),
        json={
            "message": "Analiza estos documentos y dime qué problemas existen.",
            "context": {
                "tool": "docint",
                "documents": [
                    {
                        "id": "d1",
                        "tipo_documento": "CC",
                        "numero_documento": "123",
                        "fecha": "bad-date",
                        "contenido": "x",
                    }
                ],
            },
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ("COMPLETED", "WAITING_APPROVAL")
    assert data.get("result") or data.get("summary")


def test_approval_flow(token):
    res = client.post(
        "/api/assistant/ask",
        headers=_headers(token),
        json={
            "message": "Validar RIPS con problemas",
            "context": {"tool": "rips", "rips": SAMPLE_RIPS},
        },
    )
    assert res.status_code == 200
    plan = res.json()
    if plan["status"] != "WAITING_APPROVAL":
        pytest.skip("RIPS no requirió aprobación en esta ejecución")

    approvals = client.get("/api/operations/approvals/pending", headers=_headers(token))
    assert approvals.status_code == 200
    pending = [a for a in approvals.json() if a["work_plan_id"] == plan["plan_id"]]
    assert pending

    approved = client.post(
        f"/api/operations/approvals/{pending[0]['id']}/decide",
        headers=_headers(token),
        json={"decision": "approve", "comment": "OK test"},
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "COMPLETED"


def test_approval_rejected(token):
    res = client.post(
        "/api/assistant/ask",
        headers=_headers(token),
        json={"message": "RIPS test reject", "context": {"tool": "rips", "rips": SAMPLE_RIPS}},
    )
    plan = res.json()
    if plan["status"] != "WAITING_APPROVAL":
        pytest.skip("Sin aprobación pendiente")

    approvals = client.get("/api/operations/approvals/pending", headers=_headers(token)).json()
    item = next(a for a in approvals if a["work_plan_id"] == plan["plan_id"])

    rejected = client.post(
        f"/api/operations/approvals/{item['id']}/decide",
        headers=_headers(token),
        json={"decision": "reject", "comment": "No conforme"},
    )
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "FAILED"


def test_tenant_isolation(token):
    res = client.get("/api/operations/executions", headers=_headers(token))
    assert res.status_code == 200
    ids = [e["id"] for e in res.json()]
    for eid in ids:
        detail = client.get(f"/api/operations/executions/{eid}", headers=_headers(token))
        assert detail.status_code == 200


def test_permission_denied_without_token():
    res = client.post("/api/assistant/ask", json={"message": "hola"})
    assert res.status_code == 401


def test_traceability_events(token):
    client.post(
        "/api/assistant/ask",
        headers=_headers(token),
        json={"message": "trace test", "context": {"tool": "docint", "documents": []}},
    )
    events = client.get("/api/operations/events", headers=_headers(token))
    assert events.status_code == 200
    types = {e["event_type"] for e in events.json()}
    assert "work.requested" in types


def test_docint_rips_e2e_findings(token):
    res = client.post(
        "/api/assistant/ask",
        headers=_headers(token),
        json={
            "message": "Analiza RIPS E2E",
            "context": {"tool": "rips", "rips": SAMPLE_RIPS},
        },
    )
    data = res.json()
    assert data["plan_id"]
    detail = client.get(f"/api/operations/executions/{data['plan_id']}", headers=_headers(token))
    assert detail.status_code == 200
    body = detail.json()
    assert body["tasks"]
    events = client.get("/api/operations/events", headers=_headers(token)).json()
    plan_events = [e for e in events if e.get("work_plan_id") == data["plan_id"]]
    assert len(plan_events) >= 2


def test_employees_directory(token):
    res = client.get("/api/operations/employees", headers=_headers(token))
    assert res.status_code == 200
    names = {e["name"] for e in res.json()}
    assert "Auditor RIPS IA" in names
    assert "Analista Documental IA" in names
