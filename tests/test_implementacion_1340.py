"""BLOQUE 1340 — Implementación y éxito del cliente."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.implementacion_enums import ReadinessResultado, ResultadoPiloto, SaludCliente
from app.implementacion_models import ImplementacionAuditoria
from app.models import Organization, User
from app.security import hash_password
from conftest import TestingSessionLocal, auth_header

pytestmark = [pytest.mark.operations]

CHECKLIST = {k: True for k in (
    "configuracion", "usuarios", "permisos", "integraciones", "seguridad",
    "datos", "monitoreo", "soporte", "respaldo", "documentacion", "capacitacion",
)}


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
    password = "Tenant1340*Test1"
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


def _headers(client: TestClient, db: Session, role: str = "admin") -> tuple[dict, Organization]:
    org, _, password, username = _create_tenant(db, f"1340 {role}", role=role)
    return auth_header(_token(client, username, password)), org


def _create_proyecto(client: TestClient, headers: dict, titulo: str = "Impl test", proposal_id: str | None = None) -> dict:
    res = client.post("/api/implementacion/proyectos", headers=headers, json={"titulo": titulo, "proposal_id": proposal_id})
    assert res.status_code == 201, res.text
    return res.json()


def _create_proposal(client: TestClient, headers: dict) -> dict:
    res = client.post("/api/comercial/propuestas", headers=headers, json={"titulo": "Propuesta 1340"})
    assert res.status_code == 201
    return res.json()


def _piloto_exitoso(client: TestClient, headers: dict, pid: str) -> str:
    pil = client.post(f"/api/implementacion/proyectos/{pid}/pilotos", headers=headers, json={"alcance": "Piloto", "duracion_dias": 14})
    assert pil.status_code == 201
    piloto_id = pil.json()["id"]
    client.post(f"/api/implementacion/pilotos/{piloto_id}/resultado", headers=headers, json={"resultado": ResultadoPiloto.EXITOSO, "explicacion": "OK"})
    client.post(f"/api/implementacion/pilotos/{piloto_id}/aprobar-produccion", headers=headers, json={})
    return piloto_id


def test_crear_implementacion_con_valor_compromiso(client: TestClient):
    db = TestingSessionLocal()
    headers, _ = _headers(client, db)
    db.close()
    prop = _create_proposal(client, headers)
    proj = _create_proyecto(client, headers, proposal_id=prop["id"])
    detail = client.get(f"/api/implementacion/proyectos/{proj['id']}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["valor_compromiso"] is not None
    assert detail.json()["proposal_id"] == prop["id"]


def test_fases_hitos_dependencias(client: TestClient):
    db = TestingSessionLocal()
    headers, _ = _headers(client, db)
    db.close()
    proj = _create_proyecto(client, headers)
    pid = proj["id"]
    fase = client.post(f"/api/implementacion/proyectos/{pid}/fases", headers=headers, json={"nombre": "Preparación", "orden": 1})
    assert fase.status_code == 201
    h1 = client.post(f"/api/implementacion/proyectos/{pid}/hitos", headers=headers, json={"nombre": "Datos disponibles", "fase_id": fase.json()["id"]})
    h2 = client.post(f"/api/implementacion/proyectos/{pid}/hitos", headers=headers, json={"nombre": "Usuarios creados", "dependencias": [h1.json()["id"]]})
    assert h2.status_code == 201
    done = client.post(f"/api/implementacion/hitos/{h1.json()['id']}/completar", headers=headers, json={"evidencia": "Datos OK"})
    assert done.status_code == 200
    assert done.json()["estado"] == "COMPLETADO"


def test_requisito_bloqueante_y_readiness(client: TestClient):
    db = TestingSessionLocal()
    headers, _ = _headers(client, db)
    db.close()
    proj = _create_proyecto(client, headers)
    pid = proj["id"]
    client.post(f"/api/implementacion/proyectos/{pid}/requisitos", headers=headers, json={"tipo": "CREDENCIALES", "descripcion": "API keys", "bloqueante": True})
    ready = client.post(f"/api/implementacion/proyectos/{pid}/readiness", headers=headers, json={
        "dimensiones": {"DATOS": 0.3, "TECNOLOGIA": 0.9, "INTEGRACIONES": 0.8, "PERSONAL": 0.9, "GOBIERNO": 0.8, "SEGURIDAD": 0.9, "PROCESOS": 0.8, "APROBACIONES": 0.9}
    })
    assert ready.status_code == 201
    assert ready.json()["resultado"] == ReadinessResultado.NO_LISTO
    ready2 = client.post(f"/api/implementacion/proyectos/{pid}/readiness", headers=headers, json={
        "dimensiones": {"DATOS": 0.9, "TECNOLOGIA": 0.9, "INTEGRACIONES": 0.9, "PERSONAL": 0.9, "GOBIERNO": 0.9, "SEGURIDAD": 0.9, "PROCESOS": 0.9, "APROBACIONES": 0.9}
    })
    assert ready2.json()["resultado"] == ReadinessResultado.LISTO


def test_bloqueador_y_riesgo(client: TestClient):
    db = TestingSessionLocal()
    headers, _ = _headers(client, db)
    db.close()
    pid = _create_proyecto(client, headers)["id"]
    bloq = client.post(f"/api/implementacion/proyectos/{pid}/bloqueadores", headers=headers, json={"tipo": "CLIENTE", "descripcion": "Sin aprobación", "critico": True})
    assert bloq.status_code == 201
    riesgo = client.post(f"/api/implementacion/proyectos/{pid}/riesgos", headers=headers, json={"descripcion": "Retraso integración", "probabilidad": "ALTA", "impacto": "ALTO"})
    assert riesgo.status_code == 201
    assert riesgo.json()["nivel"] == "ALTO"


def test_piloto_exitoso_y_no_concluyente(client: TestClient):
    db = TestingSessionLocal()
    headers, _ = _headers(client, db)
    db.close()
    pid = _create_proyecto(client, headers)["id"]
    _piloto_exitoso(client, headers, pid)
    pid2 = _create_proyecto(client, headers, titulo="Piloto NC")["id"]
    pil = client.post(f"/api/implementacion/proyectos/{pid2}/pilotos", headers=headers, json={"alcance": "Test"})
    piloto_id = pil.json()["id"]
    res = client.post(f"/api/implementacion/pilotos/{piloto_id}/resultado", headers=headers, json={"resultado": ResultadoPiloto.NO_CONCLUYENTE, "explicacion": "Datos insuficientes"})
    assert res.status_code == 200


def test_go_live_requiere_aprobaciones(client: TestClient):
    db = TestingSessionLocal()
    headers, _ = _headers(client, db)
    db.close()
    pid = _create_proyecto(client, headers)["id"]
    fail = client.post(f"/api/implementacion/proyectos/{pid}/go-live", headers=headers, json={"checklist": CHECKLIST})
    assert fail.status_code == 422
    client.post(f"/api/implementacion/proyectos/{pid}/bloqueadores", headers=headers, json={"tipo": "TECNICO", "descripcion": "Crítico", "critico": True})
    _piloto_exitoso(client, headers, pid)
    fail2 = client.post(f"/api/implementacion/proyectos/{pid}/go-live", headers=headers, json={"checklist": CHECKLIST})
    assert fail2.status_code == 422


def test_go_live_aprobacion_completa(client: TestClient):
    db = TestingSessionLocal()
    headers, _ = _headers(client, db)
    db.close()
    pid = _create_proyecto(client, headers)["id"]
    _piloto_exitoso(client, headers, pid)
    ok = client.post(f"/api/implementacion/proyectos/{pid}/go-live", headers=headers, json={"checklist": CHECKLIST, "observaciones": "Aprobado"})
    assert ok.status_code == 200
    assert ok.json()["go_live_aprobado"] is True
    assert ok.json()["estado"] == "EN_PRODUCCION"


def test_adopcion_capacitacion(client: TestClient):
    db = TestingSessionLocal()
    headers, _ = _headers(client, db)
    db.close()
    pid = _create_proyecto(client, headers)["id"]
    adop = client.post(f"/api/implementacion/proyectos/{pid}/adopcion", headers=headers, json={"metricas": {"usuarios_habilitados": 100, "usuarios_activos": 75}})
    assert adop.status_code == 201
    cap = client.post(f"/api/implementacion/proyectos/{pid}/capacitaciones", headers=headers, json={"tema": "Uso empleados IA", "asistentes": 20})
    assert cap.status_code == 201


def test_plan_exito_valor_desviacion_accion(client: TestClient):
    db = TestingSessionLocal()
    headers, _ = _headers(client, db)
    db.close()
    pid = _create_proyecto(client, headers)["id"]
    plan = client.post("/api/implementacion/exito/planes", headers=headers, json={"proyecto_id": pid, "titulo": "Plan éxito", "valor_esperado": 10000000})
    plan_id = plan.json()["id"]
    obj = client.post(f"/api/implementacion/exito/planes/{plan_id}/objetivos", headers=headers, json={"nombre": "Ahorro mensual", "valor_esperado": 5000000})
    obj_id = obj.json()["id"]
    medir = client.post(f"/api/implementacion/exito/objetivos/{obj_id}/medir", headers=headers, json={"valor_medido": 3000000})
    assert medir.json()["estado_valor"] == "POR_DEBAJO_DE_LO_ESPERADO"
    acc = client.post(f"/api/implementacion/exito/planes/{plan_id}/acciones", headers=headers, json={"causa": "ADOPCION", "accion": "Capacitación adicional"})
    assert acc.status_code == 201


def test_revision_periodica(client: TestClient):
    db = TestingSessionLocal()
    headers, _ = _headers(client, db)
    db.close()
    pid = _create_proyecto(client, headers)["id"]
    plan = client.post("/api/implementacion/exito/planes", headers=headers, json={"proyecto_id": pid, "titulo": "Revisión"})
    rev = client.post(f"/api/implementacion/exito/planes/{plan.json()['id']}/revisiones", headers=headers, json={
        "fecha": datetime.now(timezone.utc).isoformat(),
        "periodicidad": "MENSUAL",
        "decisiones": "Continuar plan de adopción",
    })
    assert rev.status_code == 201


def test_salud_saludable_y_riesgo(client: TestClient):
    db = TestingSessionLocal()
    headers, _ = _headers(client, db)
    db.close()
    pid = _create_proyecto(client, headers)["id"]
    client.post(f"/api/implementacion/proyectos/{pid}/adopcion", headers=headers, json={"metricas": {"usuarios_habilitados": 10, "usuarios_activos": 9}})
    h = client.post(f"/api/implementacion/proyectos/{pid}/hitos", headers=headers, json={"nombre": "H1"})
    client.post(f"/api/implementacion/hitos/{h.json()['id']}/completar", headers=headers, json={})
    salud = client.post(f"/api/implementacion/proyectos/{pid}/salud", headers=headers, json={})
    assert salud.status_code == 200
    assert salud.json()["resultado"] in SaludCliente.ALL
    assert "factores" in salud.json()


def test_renovacion_expansion(client: TestClient):
    db = TestingSessionLocal()
    headers, _ = _headers(client, db)
    db.close()
    pid = _create_proyecto(client, headers)["id"]
    ren = client.post("/api/implementacion/exito/renovaciones", headers=headers, json={"proyecto_id": pid})
    assert ren.json()["estado"] == "PENDIENTE"
    exp = client.post("/api/implementacion/exito/expansiones", headers=headers, json={
        "proyecto_id": pid, "tipo": "EMPLEADOS_IA", "descripcion": "Más empleados", "recomendacion": "Revisar con cliente",
    })
    assert exp.status_code == 201


def test_tco_1320_integrado_tablero(client: TestClient):
    db = TestingSessionLocal()
    headers, _ = _headers(client, db)
    db.close()
    pid = _create_proyecto(client, headers)["id"]
    client.post("/api/tco/costos", headers=headers, json={"nombre": "Costo impl", "monto": 2000000, "categoria_code": "SOPORTE"})
    tab = client.get(f"/api/implementacion/proyectos/{pid}/tablero", headers=headers)
    assert tab.status_code == 200
    assert tab.json()["tco"] is not None
    assert tab.json()["tco"]["total"] >= 2000000


def test_aliado_1320_en_hito(client: TestClient):
    db = TestingSessionLocal()
    headers, _ = _headers(client, db)
    db.close()
    prov = client.post("/api/tco/proveedores", headers=headers, json={"nombre": "Integrador X", "tipo": "INTEGRADOR"})
    pid = _create_proyecto(client, headers)["id"]
    hito = client.post(f"/api/implementacion/proyectos/{pid}/hitos", headers=headers, json={"nombre": "Integración lista", "proveedor_id": prov.json()["id"]})
    assert hito.status_code == 201


def test_rbac_viewer(client: TestClient):
    db = TestingSessionLocal()
    headers, _ = _headers(client, db, role="viewer")
    db.close()
    res = client.post("/api/implementacion/proyectos", headers=headers, json={"titulo": "X"})
    assert res.status_code == 403


def test_multiempresa(client: TestClient):
    db = TestingSessionLocal()
    h1, _ = _headers(client, db, "admin")
    h2, _ = _headers(client, db, "admin")
    p1 = _create_proyecto(client, h1)
    db.close()
    res = client.get(f"/api/implementacion/proyectos/{p1['id']}", headers=h2)
    assert res.status_code == 404


def test_auditoria(client: TestClient):
    db = TestingSessionLocal()
    headers, org = _headers(client, db)
    _create_proyecto(client, headers)
    count = db.query(ImplementacionAuditoria).filter(ImplementacionAuditoria.organization_id == org.id).count()
    db.close()
    assert count >= 1


def test_tablero_trazabilidad(client: TestClient):
    db = TestingSessionLocal()
    headers, _ = _headers(client, db)
    db.close()
    prop = _create_proposal(client, headers)
    pid = _create_proyecto(client, headers, proposal_id=prop["id"])["id"]
    tab = client.get(f"/api/implementacion/proyectos/{pid}/tablero", headers=headers)
    t = tab.json()["trazabilidad"]
    assert "que_vendimos" in t
    assert "que_prometimos" in t
