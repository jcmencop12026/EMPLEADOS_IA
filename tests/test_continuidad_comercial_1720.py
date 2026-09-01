"""Continuidad comercial y operacional EIAAX — Bloque 1720."""

from __future__ import annotations

import json
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.commercial_enums import ProposalStatus
from app.implementacion_models import ImplementacionProyecto
from app.models import Organization, User
from app.negocio_models import NegocioProposalExtension
from app.security import hash_password
from conftest import TestingSessionLocal, auth_header

pytestmark = [pytest.mark.operations]


def _token(client: TestClient, username: str, password: str) -> str:
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _create_tenant(db: Session, org_name: str, role: str = "admin") -> tuple[Organization, User, str, str]:
    from app.seed_orchestration import bootstrap_orchestration
    from app.seed_permissions import bootstrap_permissions
    from app.seed_salud import bootstrap_salud

    org = Organization(name=org_name, slug=f"t-{uuid.uuid4().hex[:8]}")
    db.add(org)
    db.flush()
    bootstrap_permissions(db)
    bootstrap_orchestration(db, org.id)
    bootstrap_salud(db, org.id)
    password = "Cont1720*Test1"
    user = User(
        organization_id=org.id,
        username=f"u-{uuid.uuid4().hex[:6]}",
        password_hash=hash_password(password),
        role=role,
        status="ACTIVE",
        is_active=True,
    )
    db.add(user)
    db.commit()
    return org, user, password, user.username


def _setup_propuesta_contratada(client: TestClient, headers: dict) -> dict:
    ev = client.post(
        "/api/evaluaciones",
        headers=headers,
        json={
            "titulo": "Eval continuidad",
            "entidad_nombre": "Cliente Continuidad",
            "necesidad": "Automatizar procesos",
            "objetivo": "Reducir tiempos",
            "area_proceso": "Operaciones",
            "nivel": "PRELIMINAR",
        },
    )
    assert ev.status_code == 201
    opp = client.post(
        "/api/oportunidades/pipeline-proactivo",
        headers=headers,
        json={
            "tipo": "operativa",
            "dominio": "operaciones",
            "evento": "continuidad_test",
            "payload": {"titulo": "Opp continuidad", "descripcion": "Test", "impacto_estimado": 50000},
        },
    )
    assert opp.status_code in (200, 201)
    opp_id = opp.json().get("oportunidad", opp.json()).get("id") or opp.json().get("id")
    prop = client.post(
        "/api/centro-negocios/propuestas/desde-expediente",
        headers=headers,
        json={"evaluacion_id": ev.json()["id"], "opportunity_id": opp_id, "titulo": "Propuesta continuidad"},
    )
    assert prop.status_code in (200, 201), prop.text
    pid = prop.json()["id"] if "id" in prop.json() else prop.json()["proposal"]["id"]
    client.put(
        f"/api/centro-negocios/propuestas/{pid}/ia-consumo",
        headers=headers,
        json={"consumo_incluido_usd": 2500, "consumo_incluido_tokens": 10000, "periodicidad": "MENSUAL"},
    )
    client.post(f"/api/centro-negocios/propuestas/{pid}/transicion", headers=headers, json={"nuevo_estado": "APROBADA"})
    client.post(
        f"/api/centro-negocios/propuestas/{pid}/precio",
        headers=headers,
        json={"action": "MODIFICAR", "precio_decidido": 45000, "justificacion": "Precio acordado"},
    )
    client.post(f"/api/centro-negocios/propuestas/{pid}/transicion", headers=headers, json={"nuevo_estado": "ENVIADA"})
    pdf = client.post(f"/api/centro-negocios/propuestas/{pid}/pdf", headers=headers, json={})
    assert pdf.status_code in (200, 201), pdf.text
    contr = client.post(
        f"/api/centro-negocios/propuestas/{pid}/contratar",
        headers=headers,
        json={"condiciones": "SLA 99.5%, soporte 8x5"},
    )
    assert contr.status_code == 200, contr.text
    return {"proposal_id": pid, "contract_id": contr.json()["contract_id"], "opportunity_id": opp_id, "evaluacion_id": ev.json()["id"]}


def test_conversion_persiste_compromiso_y_referencias(client: TestClient):
    db = TestingSessionLocal()
    org, _, password, username = _create_tenant(db, "Cont-Conv")
    db.close()
    headers = auth_header(_token(client, username, password))
    ctx = _setup_propuesta_contratada(client, headers)
    conv = client.post(
        f"/api/centro-negocios/propuestas/{ctx['proposal_id']}/convertir-implementacion",
        headers=headers,
        json={"condiciones": "Condiciones adicionales"},
    )
    assert conv.status_code == 200, conv.text
    data = conv.json()
    assert data["datos_reutilizados"] is True
    assert data["referencias"]["opportunity_id"] == ctx["opportunity_id"]
    assert data["compromiso"]["contrato"]["condiciones"]
    pid = data["proyecto_id"]
    det = client.get(f"/api/implementacion/proyectos/{pid}", headers=headers)
    assert det.status_code == 200
    proj = det.json()
    assert proj["opportunity_id"] == ctx["opportunity_id"]
    assert proj["evaluacion_id"] == ctx["evaluacion_id"]
    assert proj["contract_id"] == ctx["contract_id"]
    assert proj["compromiso_contractual"] is not None
    assert "SLA" in (proj["alcance"] or "")


def test_entregables_y_subentidades(client: TestClient):
    db = TestingSessionLocal()
    org, _, password, username = _create_tenant(db, "Cont-Ent")
    db.close()
    headers = auth_header(_token(client, username, password))
    ctx = _setup_propuesta_contratada(client, headers)
    conv = client.post(f"/api/centro-negocios/propuestas/{ctx['proposal_id']}/convertir-implementacion", headers=headers, json={})
    proyecto_id = conv.json()["proyecto_id"]
    ent = client.post(
        f"/api/implementacion/proyectos/{proyecto_id}/entregables",
        headers=headers,
        json={"nombre": "Manual operativo", "descripcion": "Entrega formal"},
    )
    assert ent.status_code == 201
    eid = ent.json()["id"]
    ok = client.patch(f"/api/implementacion/entregables/{eid}", headers=headers, json={"aceptacion": "ACEPTADO", "evidencia": "doc.pdf"})
    assert ok.status_code == 200
    assert ok.json()["estado"] == "ACEPTADO"
    tarea = client.post(f"/api/implementacion/proyectos/{proyecto_id}/tareas", headers=headers, json={"titulo": "Configurar"})
    tid = tarea.json()["id"]
    done = client.post(f"/api/implementacion/tareas/{tid}/completar", headers=headers, json={"evidencia": "ok"})
    assert done.status_code == 200
    assert done.json()["estado"] == "COMPLETADA"
    bloq = client.post(
        f"/api/implementacion/proyectos/{proyecto_id}/bloqueadores",
        headers=headers,
        json={"tipo": "TECNICO", "descripcion": "Falta VPN", "critico": True},
    )
    bid = bloq.json()["id"]
    res = client.post(f"/api/implementacion/bloqueadores/{bid}/resolver", headers=headers, json={"observaciones": "VPN lista"})
    assert res.status_code == 200
    assert res.json()["estado"] == "RESUELTO"


def test_vista_continuidad_compromiso_resultado(client: TestClient):
    db = TestingSessionLocal()
    org, _, password, username = _create_tenant(db, "Cont-Vista")
    db.close()
    headers = auth_header(_token(client, username, password))
    ctx = _setup_propuesta_contratada(client, headers)
    conv = client.post(f"/api/centro-negocios/propuestas/{ctx['proposal_id']}/convertir-implementacion", headers=headers, json={})
    proyecto_id = conv.json()["proyecto_id"]
    vista = client.get(f"/api/continuidad-comercial/proyectos/{proyecto_id}/vista", headers=headers)
    assert vista.status_code == 200
    body = vista.json()
    assert body["diagnosticado"]["id"] == ctx["evaluacion_id"]
    assert body["contratado"] is not None
    assert body["implementado"]["proyecto_id"] == proyecto_id
    assert body["resultado_real"]["fuente"] == "local_adapter"


def test_finops_budget_desde_contrato(client: TestClient):
    db = TestingSessionLocal()
    org, _, password, username = _create_tenant(db, "Cont-Fin")
    db.close()
    headers = auth_header(_token(client, username, password))
    ctx = _setup_propuesta_contratada(client, headers)
    conv = client.post(f"/api/centro-negocios/propuestas/{ctx['proposal_id']}/convertir-implementacion", headers=headers, json={})
    assert conv.json().get("finops_budget_id")
    vista = client.get(f"/api/continuidad-comercial/contratos/{ctx['contract_id']}/vista", headers=headers)
    assert vista.json()["operando"]["finops"]["ingreso_comercial"]["precio_contratado"] == 45000


def test_cambio_alcance_flujo(client: TestClient):
    db = TestingSessionLocal()
    org, _, password, username = _create_tenant(db, "Cont-Cambio")
    db.close()
    headers = auth_header(_token(client, username, password))
    ctx = _setup_propuesta_contratada(client, headers)
    conv = client.post(f"/api/centro-negocios/propuestas/{ctx['proposal_id']}/convertir-implementacion", headers=headers, json={})
    cambio = client.post(
        "/api/continuidad-comercial/cambios-alcance",
        headers=headers,
        json={"proposal_id": ctx["proposal_id"], "proyecto_id": conv.json()["proyecto_id"], "solicitud": "Ampliar usuarios"},
    )
    assert cambio.status_code == 200
    cid = cambio.json()["id"]
    client.post(f"/api/continuidad-comercial/cambios-alcance/{cid}/avanzar", headers=headers, json={"accion": "analizar", "analisis": "Impacto moderado"})
    client.post(
        f"/api/continuidad-comercial/cambios-alcance/{cid}/avanzar",
        headers=headers,
        json={"accion": "impacto", "impacto": {"alcance": "50 usuarios", "tiempo": "2 semanas", "costo": 5000}},
    )
    fin = client.post(
        f"/api/continuidad-comercial/cambios-alcance/{cid}/avanzar",
        headers=headers,
        json={"accion": "decidir", "decision": "Aprobado", "aprobado": True},
    )
    assert fin.json()["estado"] == "APROBADO"


def test_renovacion_crea_oportunidad(client: TestClient):
    db = TestingSessionLocal()
    org, _, password, username = _create_tenant(db, "Cont-Ren")
    db.close()
    headers = auth_header(_token(client, username, password))
    ctx = _setup_propuesta_contratada(client, headers)
    conv = client.post(f"/api/centro-negocios/propuestas/{ctx['proposal_id']}/convertir-implementacion", headers=headers, json={})
    ren = client.post(
        "/api/implementacion/exito/renovaciones",
        headers=headers,
        json={"proyecto_id": conv.json()["proyecto_id"], "crear_oportunidad": True, "notas": "Renovación anual"},
    )
    assert ren.status_code == 201
    assert ren.json()["opportunity_id"]


def test_offboarding_cierre_contrato(client: TestClient):
    db = TestingSessionLocal()
    org, _, password, username = _create_tenant(db, "Cont-Cierre")
    db.close()
    headers = auth_header(_token(client, username, password))
    ctx = _setup_propuesta_contratada(client, headers)
    cierre = client.post(
        f"/api/continuidad-comercial/contratos/{ctx['contract_id']}/cierre",
        headers=headers,
        json={"motivo": "Fin de proyecto", "pendientes": ["Retirar accesos"], "empleados_retirar": ["emp-1"]},
    )
    assert cierre.status_code == 200
    cid = cierre.json()["id"]
    ok = client.post(f"/api/continuidad-comercial/cierres/{cid}/confirmar", headers=headers, json={"confirmacion": True})
    assert ok.status_code == 200
    assert ok.json()["estado"] == "COMPLETADO"
    assert ok.json()["confirmacion"] is True


def test_multiempresa_aislamiento(client: TestClient):
    db = TestingSessionLocal()
    org_a, _, pass_a, user_a = _create_tenant(db, "Org-A-Cont")
    org_b, _, pass_b, user_b = _create_tenant(db, "Org-B-Cont")
    db.close()
    ha = auth_header(_token(client, user_a, pass_a))
    hb = auth_header(_token(client, user_b, pass_b))
    ctx = _setup_propuesta_contratada(client, ha)
    conv = client.post(f"/api/centro-negocios/propuestas/{ctx['proposal_id']}/convertir-implementacion", headers=ha, json={})
    proyecto_id = conv.json()["proyecto_id"]
    deny = client.get(f"/api/implementacion/proyectos/{proyecto_id}", headers=hb)
    assert deny.status_code == 404
    deny2 = client.get(f"/api/continuidad-comercial/proyectos/{proyecto_id}/vista", headers=hb)
    assert deny2.status_code == 404


def test_privacidad_economia_no_en_vista_cliente(client: TestClient):
    db = TestingSessionLocal()
    org, _, password, username = _create_tenant(db, "Cont-Priv", role="viewer")
    org_id = org.id
    db.close()
    headers = auth_header(_token(client, username, password))
    admin_db = TestingSessionLocal()
    admin = User(
        organization_id=org_id,
        username=f"adm-{uuid.uuid4().hex[:4]}",
        password_hash=hash_password("Admin1720*"),
        role="admin",
        status="ACTIVE",
        is_active=True,
    )
    admin_db.add(admin)
    admin_db.commit()
    admin_headers = auth_header(_token(client, admin.username, "Admin1720*"))
    admin_db.close()
    ctx = _setup_propuesta_contratada(client, admin_headers)
    conv = client.post(f"/api/centro-negocios/propuestas/{ctx['proposal_id']}/convertir-implementacion", headers=admin_headers, json={})
    vista = client.get(f"/api/continuidad-comercial/proyectos/{conv.json()['proyecto_id']}/vista", headers=headers)
    if vista.status_code == 200:
        assert "compromiso_snapshot" not in vista.json().get("resultado_real", {})
