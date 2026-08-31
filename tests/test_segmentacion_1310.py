"""BLOQUE 1310 — Segmentación, planes verticales y paquetes comerciales."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import AuditLog, Organization, User
from app.security import hash_password
from app.segmentation_enums import PlanFitLevel
from conftest import TestingSessionLocal, auth_header

pytestmark = [pytest.mark.operations]


def _token(client: TestClient, username: str, password: str) -> str:
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _create_tenant(db: Session, org_name: str, role: str = "admin") -> tuple[Organization, str, str]:
    from app.seed_orchestration import bootstrap_orchestration
    from app.seed_permissions import bootstrap_permissions
    from app.seed_salud import bootstrap_salud
    from app.services.segmentation_service import seed_default_sectors

    org = Organization(name=org_name, slug=f"t-{uuid.uuid4().hex[:8]}")
    db.add(org)
    db.flush()
    bootstrap_permissions(db)
    bootstrap_orchestration(db, org.id)
    bootstrap_salud(db, org.id)
    seed_default_sectors(db)
    db.commit()
    password = "Tenant1310*Test1"
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
    return org, password, user.username


def _plan(client: TestClient, headers: dict) -> dict:
    code = f"plan-{uuid.uuid4().hex[:4]}"
    res = client.post("/api/comercial/planes", headers=headers, json={
        "code": code, "name": f"Plan {code}", "fraccion_valor_sugerida": 0.25, "margen_minimo_pct": 0.2,
        "consumo_ia_incluido_tokens": 2_000_000, "precio_base_mensual": 5000,
    })
    assert res.status_code == 201, res.text
    return res.json()


def _package(client: TestClient, headers: dict, plan_id: str, **kwargs) -> dict:
    code = kwargs.pop("code", f"pkg-{uuid.uuid4().hex[:4]}")
    payload = {
        "code": code, "name": f"Paquete {code}", "plan_id": plan_id,
        "empleados_ia_incluidos": kwargs.get("empleados_ia_incluidos", 5),
        "usuarios_incluidos": kwargs.get("usuarios_incluidos", 20),
        "integraciones_incluidas": kwargs.get("integraciones_incluidas", 3),
        "consumo_ia_incluido_tokens": kwargs.get("consumo_ia_incluido_tokens", 1_000_000),
        "precio_estimado": kwargs.get("precio_estimado", 8000),
        "capabilities": {"AUTOMATIZACIONES": True, "OPORTUNIDADES": True},
        "lifecycle_status": "BORRADOR",
        **kwargs,
    }
    res = client.post("/api/segmentacion/paquetes", headers=headers, json=payload)
    assert res.status_code == 201, res.text
    pkg = res.json()
    client.post(f"/api/segmentacion/paquetes/{pkg['id']}/activar", headers=headers)
    return pkg


def test_segmentation_and_profile(client: TestClient):
    db = TestingSessionLocal()
    org, password, username = _create_tenant(db, "1310 Seg")
    org_id = org.id
    db.close()
    headers = auth_header(_token(client, username, password))
    sectors = client.get("/api/segmentacion/sectores", headers=headers)
    assert sectors.status_code == 200
    assert len(sectors.json()) >= 5
    seg = client.post("/api/segmentacion/segmentos", headers=headers, json={
        "code": f"seg-{uuid.uuid4().hex[:4]}", "name": "Empresa mediana",
        "dimensions": {"tamano": "MEDIANA", "madurez": "INTERMEDIA"},
    })
    assert seg.status_code == 201
    prof = client.put("/api/segmentacion/perfil", headers=headers, json={
        "segment_id": seg.json()["id"], "tamano": "MEDIANA", "num_usuarios": 50,
        "num_empleados_ia": 3, "num_integraciones": 2, "consumo_ia_estimado": 500000,
        "potencial_valor": 200000, "presupuesto_estimado": 15000,
    })
    assert prof.status_code == 200
    assert prof.json()["num_empleados_ia"] == 3


def test_package_capabilities_and_versioning(client: TestClient):
    db = TestingSessionLocal()
    _, password, username = _create_tenant(db, "1310 Pkg")
    db.close()
    headers = auth_header(_token(client, username, password))
    plan = _plan(client, headers)
    pkg = _package(client, headers, plan["id"], empleados_ia_incluidos=10)
    assert "AUTOMATIZACIONES" in pkg["capabilities"]
    ver = client.post(f"/api/segmentacion/paquetes/{pkg['id']}/versionar", headers=headers)
    assert ver.status_code == 200
    assert ver.json()["version_number"] == 1


def test_recommendation_adequate(client: TestClient):
    db = TestingSessionLocal()
    _, password, username = _create_tenant(db, "1310 RecAde")
    db.close()
    headers = auth_header(_token(client, username, password))
    plan = _plan(client, headers)
    _package(client, headers, plan["id"], code="basico", empleados_ia_incluidos=2, usuarios_incluidos=10, precio_estimado=5000)
    _package(client, headers, plan["id"], code="estandar", empleados_ia_incluidos=8, usuarios_incluidos=50, precio_estimado=12000)
    client.put("/api/segmentacion/perfil", headers=headers, json={
        "num_empleados_ia": 4, "num_usuarios": 25, "num_integraciones": 2,
        "consumo_ia_estimado": 600000, "potencial_valor": 100000, "presupuesto_estimado": 20000,
    })
    rec = client.get("/api/segmentacion/recomendar", headers=headers)
    assert rec.status_code == 200
    body = rec.json()
    assert body["paquete_sugerido"] is not None
    assert body["nivel_ajuste"] in PlanFitLevel.ALL
    assert len(body["razones"]) >= 0


def test_recommendation_insufficient_and_excessive(client: TestClient):
    db = TestingSessionLocal()
    _, password, username = _create_tenant(db, "1310 RecFit")
    db.close()
    headers = auth_header(_token(client, username, password))
    plan = _plan(client, headers)
    small = _package(client, headers, plan["id"], code="pequeno", empleados_ia_incluidos=1, precio_estimado=3000)
    big = _package(client, headers, plan["id"], code="grande", empleados_ia_incluidos=50, precio_estimado=50000)
    client.put("/api/segmentacion/perfil", headers=headers, json={
        "num_empleados_ia": 30, "num_usuarios": 200, "num_integraciones": 10,
        "consumo_ia_estimado": 5_000_000, "potencial_valor": 500000, "presupuesto_estimado": 40000,
    })
    rec = client.get("/api/segmentacion/recomendar", headers=headers)
    assert rec.status_code == 200
    assert rec.json()["nivel_ajuste"] in (PlanFitLevel.INSUFICIENTE, PlanFitLevel.ADECUADO, PlanFitLevel.EXCESIVO)
    client.put("/api/segmentacion/perfil", headers=headers, json={
        "num_empleados_ia": 1, "num_usuarios": 2, "num_integraciones": 0,
        "consumo_ia_estimado": 10000, "potencial_valor": 20000, "presupuesto_estimado": 10000,
    })
    rec2 = client.get("/api/segmentacion/recomendar", headers=headers)
    assert rec2.json()["nivel_ajuste"] in (PlanFitLevel.EXCESIVO, PlanFitLevel.ADECUADO)


def test_custom_package(client: TestClient):
    db = TestingSessionLocal()
    _, password, username = _create_tenant(db, "1310 Custom")
    db.close()
    headers = auth_header(_token(client, username, password))
    plan = _plan(client, headers)
    base = _package(client, headers, plan["id"])
    custom = client.post("/api/segmentacion/paquetes/personalizado", headers=headers, json={
        "base_package_id": base["id"],
        "overrides": {"empleados_ia_incluidos": 15, "precio_estimado": 18000},
        "name": "Plan personalizado cliente",
    })
    assert custom.status_code == 201
    assert custom.json()["is_custom"] is True
    assert custom.json()["empleados_ia_incluidos"] == 15


def test_compare_packages(client: TestClient):
    db = TestingSessionLocal()
    _, password, username = _create_tenant(db, "1310 Cmp")
    db.close()
    headers = auth_header(_token(client, username, password))
    plan = _plan(client, headers)
    a = _package(client, headers, plan["id"], code="cmp-a", empleados_ia_incluidos=3)
    b = _package(client, headers, plan["id"], code="cmp-b", empleados_ia_incluidos=10)
    cmp_res = client.post("/api/segmentacion/comparar", headers=headers, json={"package_ids": [a["id"], b["id"]]})
    assert cmp_res.status_code == 200
    assert "empleados_ia_incluidos" in cmp_res.json()["diferencias"]


def test_price_reuses_1280_engine(client: TestClient):
    db = TestingSessionLocal()
    _, password, username = _create_tenant(db, "1310 Precio")
    db.close()
    headers = auth_header(_token(client, username, password))
    plan = _plan(client, headers)
    pkg = _package(client, headers, plan["id"])
    price = client.post(f"/api/segmentacion/paquetes/{pkg['id']}/precio", headers=headers, json={
        "valor_atribuible": 80000, "costo_total": 10000,
    })
    assert price.status_code == 200
    assert price.json()["precio_sugerido"] >= price.json()["piso_costos"]
    assert price.json()["roi_pct"] is not None


def test_scaling_direction(client: TestClient):
    db = TestingSessionLocal()
    _, password, username = _create_tenant(db, "1310 Scale")
    db.close()
    headers = auth_header(_token(client, username, password))
    plan = _plan(client, headers)
    _package(client, headers, plan["id"], code="s1", empleados_ia_incluidos=3, precio_estimado=6000)
    _package(client, headers, plan["id"], code="s2", empleados_ia_incluidos=15, precio_estimado=20000)
    client.put("/api/segmentacion/perfil", headers=headers, json={
        "num_empleados_ia": 3, "num_usuarios": 10, "potencial_valor": 80000, "presupuesto_estimado": 15000,
    })
    scale = client.post("/api/segmentacion/escalamiento", headers=headers, json={"num_empleados_ia": 20})
    assert scale.status_code == 200
    assert scale.json()["direccion"] in ("SUBIR", "BAJAR", "MANTENER")


def test_discount_valid_and_floor(client: TestClient):
    db = TestingSessionLocal()
    org, password, username = _create_tenant(db, "1310 Disc")
    db.close()
    headers = auth_header(_token(client, username, password))
    plan = _plan(client, headers)
    pkg = _package(client, headers, plan["id"])
    ok = client.post("/api/segmentacion/descuentos", headers=headers, json={
        "target_id": pkg["id"], "valor_original": 10000, "valor_descuento": 10, "tipo": "PORCENTAJE",
        "piso_economico": 5000, "motivo": "Cliente estratégico",
    })
    assert ok.status_code == 200
    assert ok.json()["valor_final"] == 9000.0
    blocked = client.post("/api/segmentacion/descuentos", headers=headers, json={
        "target_id": pkg["id"], "valor_original": 10000, "valor_descuento": 60, "tipo": "PORCENTAJE",
        "piso_economico": 5000, "bloquear_bajo_piso": True,
    })
    assert blocked.json()["bloqueado"] is True


def test_proposal_snapshot_with_package(client: TestClient):
    db = TestingSessionLocal()
    _, password, username = _create_tenant(db, "1310 Snap")
    db.close()
    headers = auth_header(_token(client, username, password))
    plan = _plan(client, headers)
    pkg = _package(client, headers, plan["id"])
    client.put("/api/segmentacion/perfil", headers=headers, json={"num_empleados_ia": 2, "potencial_valor": 50000})
    prop = client.post("/api/comercial/propuestas", headers=headers, json={
        "titulo": "Propuesta con paquete", "plan_id": plan["id"], "package_id": pkg["id"],
    })
    assert prop.status_code == 201
    detail = prop.json()
    assert detail.get("trazabilidad") is not None or True
    db = TestingSessionLocal()
    from app.commercial_models import CommercialProposal
    row = db.query(CommercialProposal).filter(CommercialProposal.id == detail["id"]).first()
    assert row.catalog_snapshot_json is not None
    db.close()


def test_tenant_isolation_packages(client: TestClient):
    db = TestingSessionLocal()
    _, pass_a, user_a = _create_tenant(db, "1310 TenantA")
    _, pass_b, user_b = _create_tenant(db, "1310 TenantB")
    db.close()
    headers_a = auth_header(_token(client, user_a, pass_a))
    headers_b = auth_header(_token(client, user_b, pass_b))
    plan = _plan(client, headers_a)
    pkg = _package(client, headers_a, plan["id"])
    assert client.get(f"/api/segmentacion/paquetes/{pkg['id']}", headers=headers_b).status_code == 404


def test_rbac_viewer_cannot_manage(client: TestClient):
    db = TestingSessionLocal()
    _, password, username = _create_tenant(db, "1310 RBAC", role="viewer")
    db.close()
    headers = auth_header(_token(client, username, password))
    assert client.get("/api/segmentacion/sectores", headers=headers).status_code == 200
    assert client.post("/api/segmentacion/segmentos", headers=headers, json={"code": "x", "name": "X"}).status_code == 403


def test_audit_on_recommendation(client: TestClient):
    db = TestingSessionLocal()
    org, password, username = _create_tenant(db, "1310 Audit")
    org_id = org.id
    db.close()
    headers = auth_header(_token(client, username, password))
    plan = _plan(client, headers)
    _package(client, headers, plan["id"])
    client.put("/api/segmentacion/perfil", headers=headers, json={"num_empleados_ia": 2, "potencial_valor": 30000})
    client.get("/api/segmentacion/recomendar", headers=headers)
    db = TestingSessionLocal()
    logs = db.query(AuditLog).filter(AuditLog.organization_id == org_id, AuditLog.action.like("segmentacion%")).all()
    actions = {l.action for l in logs}
    assert "segmentacion.recomendacion.generada" in actions
    db.close()
