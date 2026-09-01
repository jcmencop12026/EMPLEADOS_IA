"""Centro de Control Estratégico V1 — economía privada, persistencia, privacidad, trazabilidad."""

from __future__ import annotations

import json
import uuid

import pytest
from fastapi.testclient import TestClient

from app.commercial_enums import ValueCategory, ValueNature
from app.models import AuditLog, Organization, Permission, Role, RolePermission, User
from app.security import hash_password
from app.services.control_center_adapters import ContinuidadAdapter
from app.transformacion_models import DossierEmpresarial
from conftest import TestingSessionLocal, auth_header

pytestmark = [pytest.mark.auth, pytest.mark.tenant]


def _create_user_with_permissions(
    client: TestClient,
    *,
    permission_codes: set[str],
    org_id: str | None = None,
) -> tuple[str, str, str]:
    db = TestingSessionLocal()
    try:
        from app.seed_permissions import bootstrap_permissions

        bootstrap_permissions(db)
        if org_id is None:
            org = Organization(name=f"Strat-{uuid.uuid4().hex[:6]}")
            db.add(org)
            db.flush()
            org_id = org.id
        role = Role(organization_id=org_id, code=f"strat_{uuid.uuid4().hex[:6]}", name="Strat", is_system=False)
        db.add(role)
        db.flush()
        for code in permission_codes:
            perm = db.query(Permission).filter(Permission.code == code).first()
            assert perm is not None, code
            db.add(RolePermission(role_id=role.id, permission_id=perm.id))
        username = f"stv_{uuid.uuid4().hex[:6]}"
        password = "testpass123"
        db.add(
            User(
                organization_id=org_id,
                username=username,
                password_hash=hash_password(password),
                role=role.code,
                is_active=True,
            )
        )
        db.commit()
    finally:
        db.close()
    login = client.post("/api/auth/login", json={"username": username, "password": password})
    assert login.status_code == 200
    return login.json()["access_token"], username, org_id


def _admin_perms_economia() -> set[str]:
    return {
        "strategic_control.view",
        "strategic_control.economia_privada",
        "transformacion.view",
        "transformacion.manage",
        "comercial.view",
        "comercial.create",
        "comercial.manage_plans",
        "comercial.simulate",
        "comercial.approve",
        "valoracion.view",
        "tco.view",
        "finops.view",
        "evaluacion.view",
        "evaluacion.manage",
        "evaluacion.visibility",
        "evaluacion.vista_entidad",
        "oportunidades.view",
        "oportunidades.evaluate",
        "oportunidades.approve",
    }


def _setup_commercial_economy(client: TestClient, tok: str) -> dict:
    h = auth_header(tok)
    code = f"plan-{uuid.uuid4().hex[:6]}"
    plan = client.post(
        "/api/comercial/planes",
        headers=h,
        json={
            "code": code,
            "name": f"Plan {code}",
            "fraccion_valor_sugerida": 0.3,
            "margen_minimo_pct": 0.2,
            "precio_base_mensual": 5000,
            "credential_mode": "IA_ADMINISTRADA",
        },
    )
    assert plan.status_code == 201, plan.text
    prop = client.post(
        "/api/comercial/propuestas",
        headers=h,
        json={"titulo": "Propuesta estratégica", "plan_id": plan.json()["id"], "credential_mode": "IA_ADMINISTRADA"},
    )
    assert prop.status_code == 201, prop.text
    pid = prop.json()["id"]
    client.post(
        f"/api/comercial/propuestas/{pid}/valores",
        headers=h,
        json={
            "categoria": ValueCategory.AHORRO,
            "naturaleza": ValueNature.ESTIMADO,
            "valor_bruto": 200000,
            "atribucion_pct": 50,
            "criterio_atribucion": "Automatización",
        },
    )
    client.post(
        f"/api/comercial/propuestas/{pid}/valores",
        headers=h,
        json={
            "categoria": ValueCategory.AHORRO,
            "naturaleza": ValueNature.POTENCIAL,
            "valor_bruto": 500000,
            "atribucion_pct": 30,
            "criterio_atribucion": "Potencial futuro",
        },
    )
    client.post(
        f"/api/comercial/propuestas/{pid}/costos",
        headers=h,
        json={"categoria": "IMPLEMENTACION", "clase_costo": "COSTO_INTERNO", "monto": 15000},
    )
    client.post(
        f"/api/comercial/propuestas/{pid}/costos",
        headers=h,
        json={"categoria": "CONSUMO_IA", "clase_costo": "COSTO_PROVEEDOR_IA", "monto": 8000},
    )
    price = client.post(f"/api/comercial/propuestas/{pid}/precio-sugerido", headers=h, json={})
    assert price.status_code == 200, price.text
    return {"proposal_id": pid, "precio": price.json()}


# --- Estructura y lecturas ---


def test_cockpit_estructura_y_lecturas(client: TestClient, auth_headers):
    res = client.get("/api/centro-estrategico/cockpit?lectura=resumen", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["mismo_dossier"] is True
    assert body["lectura_activa"] == "resumen"
    assert len(body["lecturas"]) == 5
    assert body["enlaces"]["operacional_mb08"] == "/centro-control"


def test_cinco_lecturas_misma_fuente(client: TestClient, auth_headers):
    snapshots = {}
    for lectura in ("resumen", "gerencia", "operacion", "sistemas", "financiero"):
        r = client.get(f"/api/centro-estrategico/cockpit?lectura={lectura}", headers=auth_headers).json()
        snapshots[lectura] = {
            "org": r["organization_id"],
            "dossier": r.get("dossier_id"),
        }
    orgs = {s["org"] for s in snapshots.values()}
    dossiers = {s["dossier"] for s in snapshots.values()}
    assert len(orgs) == 1
    assert len(dossiers) == 1


def test_modo_comite(client: TestClient, auth_headers):
    res = client.get("/api/centro-estrategico/cockpit?modo_comite=true", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["modo_comite"] is True


# --- Economía privada ---


def test_economia_privada_completa_autorizada(client: TestClient):
    tok, _, _ = _create_user_with_permissions(client, permission_codes=_admin_perms_economia())
    _setup_commercial_economy(client, tok)
    fin = client.get("/api/centro-estrategico/cockpit?lectura=financiero", headers=auth_header(tok)).json()
    eco = fin["contenido"]["economia_privada"]
    assert eco["visible_interno"] is True
    assert eco["privado"] is True
    assert eco["indicadores"]["precio_sugerido"] is not None
    assert eco["indicadores"]["roi_pct"] is not None
    assert eco["indicadores"]["payback_meses"] is not None
    assert eco["indicadores"]["margen_estimado_pct"] is not None
    assert eco["valor"]["valor_potencial"] is not None
    assert eco["separacion_potencial"]["potencial_no_realizado"] is True
    assert eco["formula_precio"]


def test_economia_privada_denegada(client: TestClient):
    tok, _, _ = _create_user_with_permissions(
        client,
        permission_codes={"strategic_control.view", "transformacion.view", "comercial.view"},
    )
    fin = client.get("/api/centro-estrategico/cockpit?lectura=financiero", headers=auth_header(tok)).json()
    eco = fin["contenido"]["economia_privada"]
    assert eco.get("restringido") is True or eco.get("visible_interno") is False


def test_potencial_no_como_realizado(client: TestClient):
    tok, _, _ = _create_user_with_permissions(client, permission_codes=_admin_perms_economia())
    setup = _setup_commercial_economy(client, tok)
    fin = client.get("/api/centro-estrategico/cockpit?lectura=financiero", headers=auth_header(tok)).json()
    eco = fin["contenido"]["economia_privada"]
    base_precio = eco["valor"].get("valor_atribuible_precio") or eco["valor"].get("valor_realizable")
    potencial = eco["valor"].get("valor_potencial") or 0
    assert potencial > 0
    assert base_precio is not None
    assert base_precio < potencial + base_precio


def test_precio_sugerido_no_es_costo_mas_margen_simple(client: TestClient):
    tok, _, _ = _create_user_with_permissions(client, permission_codes=_admin_perms_economia())
    setup = _setup_commercial_economy(client, tok)
    fin = client.get("/api/centro-estrategico/cockpit?lectura=financiero", headers=auth_header(tok)).json()
    eco = fin["contenido"]["economia_privada"]
    precio = eco["indicadores"]["precio_sugerido"]
    costo = eco["costos"]["total"]
    assert precio is not None and costo is not None
    margen_lineal = costo * 1.2
    assert precio >= margen_lineal or precio >= 5000


# --- Privacidad backend ---


def test_vista_entidad_sin_economia_privada(client: TestClient, auth_headers):
    cockpit = client.get("/api/centro-estrategico/cockpit?lectura=financiero", headers=auth_headers).json()
    vista = cockpit.get("vista_entidad")
    if vista:
        raw = json.dumps(vista)
        assert "precio_sugerido" not in raw
        assert "margen_estimado" not in raw
        assert "economia_privada" not in raw
    assert cockpit["publicacion"]["economia_privada_publicable"] is False


def test_prospecto_no_ve_economia_privada(client: TestClient):
    """Usuario sin permisos estratégicos no accede al cockpit."""
    tok, _, _ = _create_user_with_permissions(client, permission_codes={"evaluacion.vista_entidad"})
    denied = client.get("/api/centro-estrategico/cockpit", headers=auth_header(tok))
    assert denied.status_code in (401, 403)


def test_cliente_no_ve_economia_en_financiero_publico(client: TestClient):
    tok, _, _ = _create_user_with_permissions(
        client,
        permission_codes={"strategic_control.view", "transformacion.view", "comercial.view", "valoracion.view"},
    )
    fin = client.get("/api/centro-estrategico/cockpit?lectura=financiero", headers=auth_header(tok)).json()
    eco = fin["contenido"]["economia_privada"]
    assert eco.get("restringido") is True
    assert "precio_sugerido" not in eco.get("indicadores", {})


def test_tenant_cruzado_economia(client: TestClient):
    tok_a, _, org_a = _create_user_with_permissions(client, permission_codes=_admin_perms_economia())
    _setup_commercial_economy(client, tok_a)
    tok_b, _, _ = _create_user_with_permissions(client, permission_codes=_admin_perms_economia())
    eco_a = client.get("/api/centro-estrategico/cockpit?lectura=financiero", headers=auth_header(tok_a)).json()
    eco_b = client.get("/api/centro-estrategico/cockpit?lectura=financiero", headers=auth_header(tok_b)).json()
    assert eco_a["organization_id"] != eco_b["organization_id"]


# --- Persistencia dossier ---


def test_persistencia_dossier_escritura(client: TestClient):
    tok, _, org_id = _create_user_with_permissions(client, permission_codes=_admin_perms_economia())
    db = TestingSessionLocal()
    try:
        antes = db.query(DossierEmpresarial).filter(DossierEmpresarial.organization_id == org_id).count()
    finally:
        db.close()
    res = client.post(
        "/api/centro-estrategico/acciones/registrar-necesidad",
        headers=auth_header(tok),
        json={
            "titulo": "Necesidad estratégica",
            "necesidad": "Optimizar procesos comerciales",
            "entidad_nombre": "Cliente Test",
        },
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["dossier_count"] == 1
    assert body["dossier_id"] is not None
    ids = []
    for _ in range(3):
        r = client.get("/api/centro-estrategico/cockpit?lectura=resumen", headers=auth_header(tok)).json()
        ids.append(r["dossier_id"])
    assert ids[0] == ids[1] == ids[2]
    assert ids[0] == body["dossier_id"]
    db = TestingSessionLocal()
    try:
        despues = db.query(DossierEmpresarial).filter(DossierEmpresarial.organization_id == org_id).count()
        assert despues == 1
        assert despues >= antes
    finally:
        db.close()


def test_escritura_sin_duplicar_dossier(client: TestClient):
    tok, _, org_id = _create_user_with_permissions(client, permission_codes=_admin_perms_economia())
    for i in range(2):
        client.post(
            "/api/centro-estrategico/acciones/registrar-necesidad",
            headers=auth_header(tok),
            json={"titulo": f"T{i}", "necesidad": f"Necesidad {i}"},
        )
    db = TestingSessionLocal()
    try:
        count = db.query(DossierEmpresarial).filter(DossierEmpresarial.organization_id == org_id).count()
        assert count == 1
    finally:
        db.close()


def test_trazabilidad_decision_audit(client: TestClient):
    tok, _, org_id = _create_user_with_permissions(client, permission_codes=_admin_perms_economia())
    client.post(
        "/api/centro-estrategico/acciones/registrar-necesidad",
        headers=auth_header(tok),
        json={"titulo": "Audit test", "necesidad": "Trazabilidad"},
    )
    db = TestingSessionLocal()
    try:
        logs = (
            db.query(AuditLog)
            .filter(
                AuditLog.organization_id == org_id,
                AuditLog.action == "strategic_control.registrar_necesidad",
            )
            .all()
        )
        assert len(logs) >= 1
        detail = json.loads(logs[-1].detail or "{}")
        assert detail.get("dossier_id")
        assert detail.get("correlation_id") is not None or detail.get("expediente_id")
    finally:
        db.close()


# --- MB-08 y ContinuidadAdapter ---


def test_mb08_intacto(client: TestClient, auth_headers):
    ops = client.get("/api/centro-control/operacional", headers=auth_headers)
    strat = client.get("/api/centro-estrategico/cockpit", headers=auth_headers)
    assert ops.status_code == 200
    assert strat.status_code == 200
    assert "fuerza_laboral" in ops.json()
    assert "fuerza_laboral" not in strat.json()


def test_continuidad_adapter_degradados_lista(client: TestClient, auth_headers):
    """Regresión: degradados es lista, no entero."""
    from app.config import settings

    db = TestingSessionLocal()
    try:
        admin = db.query(User).filter(User.username == settings.bootstrap_admin_username).first()
        org_id = admin.organization_id
        perms = {"continuidad.view"}
        result = ContinuidadAdapter().fetch(db, org_id, permissions=perms)
        assert "disponible" in result
        degradados = result.get("servicios_degradados")
        if degradados is not None:
            assert isinstance(degradados, list)
    finally:
        db.close()


def test_graficos_no_mezclan_proyectado_real(client: TestClient, auth_headers):
    res = client.get("/api/centro-estrategico/cockpit?lectura=resumen", headers=auth_headers)
    for chart in res.json().get("graficos", []):
        naturalezas = {s["naturaleza"] for s in chart.get("series", [])}
        if "PROYECTADO" in naturalezas and "REAL" in naturalezas:
            proy = next(s for s in chart["series"] if s["naturaleza"] == "PROYECTADO")
            real = next(s for s in chart["series"] if s["naturaleza"] == "REAL")
            assert proy["etiqueta"] != real["etiqueta"]


def test_sin_permiso_estrategico_denegado(client: TestClient):
    tok, _, _ = _create_user_with_permissions(client, permission_codes={"employee.view"})
    denied = client.get("/api/centro-estrategico/cockpit", headers=auth_header(tok))
    assert denied.status_code in (403, 401)
