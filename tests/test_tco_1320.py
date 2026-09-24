"""BLOQUE 1320 — TCO y ecosistema de aliados."""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Organization, User
from app.security import hash_password
from app.services import finops_service
from app.services.tco_service import calcular_tarifa_volumen
from app.tco_enums import NaturalezaCosto, TipoCosto, TipoProveedorAliado
from app.tco_models import TcoAuditoria, TcoCostoHistorico
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
    password = "Tenant1320*Test1"
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
    org, _, password, username = _create_tenant(db, f"1320 {role}", role=role)
    return auth_header(_token(client, username, password)), org


def test_tarifa_volumen_tramos():
    tramos = [
        {"desde_unidades": 0, "hasta_unidades": 1_000_000, "precio_unidad": 10, "orden": 0},
        {"desde_unidades": 1_000_000, "hasta_unidades": 5_000_000, "precio_unidad": 8, "orden": 1},
        {"desde_unidades": 5_000_000, "hasta_unidades": None, "precio_unidad": 5, "orden": 2},
    ]
    r1 = calcular_tarifa_volumen(tramos, Decimal("500000"))
    assert float(r1["costo"]) == 5_000_000.0
    r2 = calcular_tarifa_volumen(tramos, Decimal("3000000"))
    assert float(r2["costo"]) == 10_000_000.0 + 16_000_000.0
    r3 = calcular_tarifa_volumen(tramos, Decimal("6000000"))
    assert float(r3["costo"]) == 10_000_000.0 + 32_000_000.0 + 5_000_000.0


def test_tco_basico_y_categorias(client: TestClient):
    db = TestingSessionLocal()
    headers, _ = _headers(client, db)
    db.close()
    res = client.get("/api/tco/categorias", headers=headers)
    assert res.status_code == 200
    cats = res.json()
    assert len(cats) >= 10
    assert any(c["code"] == "IA" for c in cats)


def test_costos_fijos_variables_estimado_real(client: TestClient):
    db = TestingSessionLocal()
    headers, _ = _headers(client, db)
    db.close()
    for tipo, nat, monto in [
        (TipoCosto.FIJO, NaturalezaCosto.ESTIMADO, 5_000_000),
        (TipoCosto.VARIABLE, NaturalezaCosto.ESTIMADO, 2_000_000),
        (TipoCosto.FIJO, NaturalezaCosto.REAL, 5_500_000),
    ]:
        res = client.post(
            "/api/tco/costos",
            headers=headers,
            json={"nombre": f"Costo {tipo} {nat}", "monto": monto, "categoria_code": "INFRAESTRUCTURA", "tipo_costo": tipo, "naturaleza": nat},
        )
        assert res.status_code == 201, res.text
    desv = client.get("/api/tco/desviacion", headers=headers)
    assert desv.status_code == 200
    d = desv.json()
    assert d["estimado"] == 7_000_000
    assert d["real"] == 5_500_000
    assert d["desviacion"] == -1_500_000


def test_proveedor_tarifa_contrato(client: TestClient):
    db = TestingSessionLocal()
    headers, _ = _headers(client, db)
    db.close()
    prov = client.post(
        "/api/tco/proveedores",
        headers=headers,
        json={"nombre": "OpenAI Partner", "tipo": TipoProveedorAliado.PROVEEDOR_IA},
    )
    assert prov.status_code == 201
    pid = prov.json()["id"]
    tarifa = client.post(
        "/api/tco/tarifas",
        headers=headers,
        json={
            "proveedor_id": pid,
            "nombre": "Tokens GPT",
            "unidad": "token",
            "tipo": "VOLUMEN",
            "tramos": [
                {"desde_unidades": 0, "hasta_unidades": 1_000_000, "precio_unidad": 0.002},
                {"desde_unidades": 1_000_000, "hasta_unidades": None, "precio_unidad": 0.0015},
            ],
        },
    )
    assert tarifa.status_code == 201
    contrato = client.post(
        "/api/tco/contratos",
        headers=headers,
        json={"proveedor_id": pid, "moneda": "USD", "sla": "99.9%", "minimo": 1000},
    )
    assert contrato.status_code == 201
    assert contrato.json()["moneda"] == "USD"


def test_moneda_conversion(client: TestClient):
    db = TestingSessionLocal()
    headers, _ = _headers(client, db)
    db.close()
    res = client.post(
        "/api/tco/costos",
        headers=headers,
        json={
            "nombre": "Licencia USD",
            "monto": 1000,
            "moneda": "USD",
            "tasa_conversion": 4000,
            "moneda_destino": "COP",
            "categoria_code": "SOFTWARE",
        },
    )
    assert res.status_code == 201
    assert res.json()["monto_convertido"] == 4_000_000


def test_distribucion_porcentaje(client: TestClient):
    db = TestingSessionLocal()
    headers, _ = _headers(client, db)
    db.close()
    costo = client.post(
        "/api/tco/costos",
        headers=headers,
        json={"nombre": "Servidor compartido", "monto": 10_000_000, "categoria_code": "INFRAESTRUCTURA"},
    )
    cid = costo.json()["id"]
    dist = client.post(
        "/api/tco/distribuciones",
        headers=headers,
        json={
            "costo_id": cid,
            "metodo": "PORCENTAJE_FIJO",
            "asignaciones": [
                {"organizacion_ref": "cliente-a", "porcentaje": 40},
                {"organizacion_ref": "cliente-b", "porcentaje": 60},
            ],
        },
    )
    assert dist.status_code == 201
    assert dist.json()["metodo"] == "PORCENTAJE_FIJO"


def test_tco_calculo_margen_punto_equilibrio(client: TestClient):
    db = TestingSessionLocal()
    headers, _ = _headers(client, db)
    db.close()
    client.post("/api/tco/costos", headers=headers, json={"nombre": "Infra", "monto": 3_000_000, "categoria_code": "INFRAESTRUCTURA"})
    client.post("/api/tco/costos", headers=headers, json={"nombre": "Soporte", "monto": 2_000_000, "categoria_code": "SOPORTE"})
    tco = client.post("/api/tco/calcular", headers=headers, json={"ingreso": 10_000_000, "margen_minimo_pct": 20})
    assert tco.status_code == 200
    body = tco.json()
    assert body["total"] == 5_000_000
    assert body["margen_bruto"] == 5_000_000
    assert body["margen_pct"] == 50.0
    assert body["punto_equilibrio"] == 5_000_000


def test_finops_integrado(client: TestClient):
    db = TestingSessionLocal()
    headers, org = _headers(client, db)
    finops_service.registrar_consumo(
        db,
        organization_id=org.id,
        provider="openai",
        model_name="gpt-4",
        tokens_in=1000,
        tokens_out=500,
        cost=25.50,
        currency="USD",
    )
    db.commit()
    db.close()
    tco = client.post("/api/tco/calcular", headers=headers, json={"incluir_finops": True})
    assert tco.status_code == 200
    assert tco.json()["finops_ia"] == 25.50


def test_rentabilidad(client: TestClient):
    db = TestingSessionLocal()
    headers, _ = _headers(client, db)
    db.close()
    client.post("/api/tco/costos", headers=headers, json={"nombre": "Costo", "monto": 4_000_000, "categoria_code": "IA"})
    res = client.post("/api/tco/rentabilidad", headers=headers, json={"ingreso_estimado": 12_000_000})
    assert res.status_code == 200
    body = res.json()
    assert body["tco_estimado"] == 4_000_000
    assert body["margen_estimado"] == 8_000_000


def test_make_or_buy_simulacion(client: TestClient):
    db = TestingSessionLocal()
    headers, _ = _headers(client, db)
    db.close()
    res = client.post(
        "/api/tco/simular/make-or-buy",
        headers=headers,
        json={"costo_interno": 50_000_000, "costo_tercero": 35_000_000, "riesgo_interno": "ALTO", "riesgo_tercero": "BAJO"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["costo_tercero_total"] < body["costo_interno_total"]
    assert "no ejecuta" in body["recomendacion_explicativa"].lower() or "TERCERO" in body["recomendacion_explicativa"]
    assert body["es_simulacion"] is True


def test_sustitucion_proveedor(client: TestClient):
    db = TestingSessionLocal()
    headers, _ = _headers(client, db)
    db.close()
    p1 = client.post("/api/tco/proveedores", headers=headers, json={"nombre": "Proveedor A", "tipo": "PROVEEDOR_IA"}).json()
    p2 = client.post("/api/tco/proveedores", headers=headers, json={"nombre": "Proveedor B", "tipo": "PROVEEDOR_IA"}).json()
    client.post(
        "/api/tco/tarifas",
        headers=headers,
        json={"proveedor_id": p1["id"], "nombre": "Tarifa A", "monto_base": 5000, "tramos": []},
    )
    client.post(
        "/api/tco/tarifas",
        headers=headers,
        json={"proveedor_id": p2["id"], "nombre": "Tarifa B", "monto_base": 3000, "tramos": []},
    )
    res = client.post(
        "/api/tco/simular/sustitucion-proveedor",
        headers=headers,
        json={"proveedor_actual_id": p1["id"], "proveedor_alternativo_id": p2["id"]},
    )
    assert res.status_code == 200
    assert res.json()["ahorro_esperado"] == 2000


def test_comparar_proveedores(client: TestClient):
    db = TestingSessionLocal()
    headers, _ = _headers(client, db)
    db.close()
    p1 = client.post("/api/tco/proveedores", headers=headers, json={"nombre": "Barato", "tipo": "PROVEEDOR_IA"}).json()
    p2 = client.post("/api/tco/proveedores", headers=headers, json={"nombre": "Caro", "tipo": "PROVEEDOR_IA"}).json()
    client.post("/api/tco/tarifas", headers=headers, json={"proveedor_id": p1["id"], "nombre": "T1", "monto_base": 100})
    client.post("/api/tco/tarifas", headers=headers, json={"proveedor_id": p2["id"], "nombre": "T2", "monto_base": 200})
    res = client.post("/api/tco/comparar-proveedores", headers=headers, json={"proveedor_ids": [p1["id"], p2["id"]]})
    assert res.status_code == 200
    assert res.json()[0]["costo"] <= res.json()[1]["costo"]


def test_concentracion_y_riesgo(client: TestClient):
    db = TestingSessionLocal()
    headers, _ = _headers(client, db)
    db.close()
    prov = client.post("/api/tco/proveedores", headers=headers, json={"nombre": "Dominante", "tipo": "PROVEEDOR_IA"}).json()
    client.patch(
        f"/api/tco/proveedores/{prov['id']}/riesgo",
        headers=headers,
        json={"riesgo_nivel": "ALTO", "riesgo_justificacion": "Dependencia crítica"},
    )
    client.post(
        "/api/tco/costos",
        headers=headers,
        json={"nombre": "Costo dominante", "monto": 9_000_000, "proveedor_id": prov["id"], "categoria_code": "IA"},
    )
    client.post("/api/tco/costos", headers=headers, json={"nombre": "Otro", "monto": 1_000_000, "categoria_code": "OTROS"})
    tco = client.post("/api/tco/calcular", headers=headers, json={"incluir_finops": False, "ingreso": 20_000_000, "margen_minimo_pct": 50})
    body = tco.json()
    assert body["concentracion"]["max_proveedor_pct"] >= 80
    assert any(a["tipo"] == "CONCENTRACION_ALTA" for a in body["alertas"])


def test_alianza_y_estado(client: TestClient):
    db = TestingSessionLocal()
    headers, _ = _headers(client, db)
    db.close()
    res = client.post(
        "/api/tco/alianzas",
        headers=headers,
        json={"nombre": "Alianza tech", "tipo": "TECNOLOGICA", "objetivo": "Integración"},
    )
    assert res.status_code == 201
    aid = res.json()["id"]
    upd = client.patch(f"/api/tco/alianzas/{aid}/estado", headers=headers, json={"estado": "ACTIVA", "justificacion": "Aprobada"})
    assert upd.status_code == 200
    assert upd.json()["estado"] == "ACTIVA"


def test_simulacion_no_destructiva(client: TestClient):
    db = TestingSessionLocal()
    headers, _ = _headers(client, db)
    db.close()
    client.post("/api/tco/costos", headers=headers, json={"nombre": "Base", "monto": 5_000_000, "categoria_code": "IA"})
    antes = client.post("/api/tco/calcular", headers=headers, json={}).json()["total"]
    sim = client.post("/api/tco/simular", headers=headers, json={"tipo": "AUMENTO_CONSUMO", "parametros": {"factor": 2}})
    assert sim.status_code == 200
    assert sim.json()["tco_simulado"] == antes * 2
    despues = client.post("/api/tco/calcular", headers=headers, json={}).json()["total"]
    assert despues == antes


def test_historico_costo_y_auditoria(client: TestClient):
    db = TestingSessionLocal()
    headers, org = _headers(client, db)
    costo = client.post("/api/tco/costos", headers=headers, json={"nombre": "Hist", "monto": 1_000_000, "categoria_code": "IA"})
    cid = costo.json()["id"]
    client.patch(f"/api/tco/costos/{cid}", headers=headers, json={"monto": 1_500_000, "motivo": "Ajuste"})
    hist = db.query(TcoCostoHistorico).filter(TcoCostoHistorico.costo_id == cid).count()
    audit = db.query(TcoAuditoria).filter(TcoAuditoria.organization_id == org.id).count()
    db.close()
    assert hist >= 1
    assert audit >= 2
    res = client.get("/api/tco/historial", headers=headers)
    assert res.status_code == 200
    assert "auditoria" in res.json()


def test_rbac_viewer_no_manage(client: TestClient):
    db = TestingSessionLocal()
    headers, _ = _headers(client, db, role="viewer")
    db.close()
    res = client.post("/api/tco/costos", headers=headers, json={"nombre": "X", "monto": 1, "categoria_code": "IA"})
    assert res.status_code == 403


def test_multiempresa_aislamiento(client: TestClient):
    db = TestingSessionLocal()
    h1, org1 = _headers(client, db, "admin")
    h2, _ = _headers(client, db, "admin")
    prov = client.post("/api/tco/proveedores", headers=h1, json={"nombre": "Privado", "tipo": "PROVEEDOR_IA"})
    pid = prov.json()["id"]
    db.close()
    res = client.get("/api/tco/proveedores", headers=h2)
    ids = [p["id"] for p in res.json()]
    assert pid not in ids


def test_tablero_centro_control(client: TestClient):
    db = TestingSessionLocal()
    headers, _ = _headers(client, db)
    db.close()
    client.post("/api/tco/costos", headers=headers, json={"nombre": "Tablero", "monto": 2_000_000, "categoria_code": "SOPORTE"})
    res = client.get("/api/tco/tablero", headers=headers)
    assert res.status_code == 200
    assert res.json()["tco_total"] >= 2_000_000
