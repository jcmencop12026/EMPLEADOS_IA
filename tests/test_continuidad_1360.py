"""BLOQUE 1360 — Continuidad operativa, resiliencia, backup y recuperación."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.continuidad_enums import EstadoBackup, EstadoIncidente, EstadoOperacional
from app.continuidad_models import ContinuidadAuditoria
from app.models import Organization, User
from conftest import TestingSessionLocal, auth_header

pytestmark = [pytest.mark.operations]


def _token(client: TestClient, username: str, password: str) -> str:
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _create_tenant_user(
    db: Session,
    *,
    org_name: str,
    role: str = "admin",
    password: str = "Tenant1360*Test1",
) -> tuple[Organization, User, str, str]:
    from app.seed_orchestration import bootstrap_orchestration
    from app.seed_permissions import bootstrap_permissions
    from app.seed_salud import bootstrap_salud

    org = Organization(name=org_name, slug=f"tenant-{uuid.uuid4().hex[:8]}")
    db.add(org)
    db.flush()
    bootstrap_permissions(db)
    bootstrap_orchestration(db, org.id)
    bootstrap_salud(db, org.id)
    username = f"user-{uuid.uuid4().hex[:6]}"
    user = User(
        organization_id=org.id,
        username=username,
        password_hash=__import__("app.security", fromlist=["hash_password"]).hash_password(password),
        role=role,
        status="ACTIVE",
        is_active=True,
    )
    db.add(user)
    db.commit()
    return org, user, password, username


def _headers(client: TestClient, username: str, password: str) -> dict[str, str]:
    return auth_header(_token(client, username, password))


def _create_servicio(client: TestClient, headers: dict[str, str], **extra) -> dict:
    payload = {
        "nombre": "Base de datos principal",
        "tipo": "BASE_DE_DATOS",
        "criticidad": "CRITICA",
        "justificacion_criticidad": "Almacena datos transaccionales",
        "rto_valor": 60,
        "rto_unidad": "minutos",
        "rpo_valor": 15,
        "rpo_unidad": "minutos",
        **extra,
    }
    res = client.post("/api/continuidad/servicios", headers=headers, json=payload)
    assert res.status_code == 201, res.text
    return res.json()


@pytest.fixture
def tenant(client: TestClient):
    db = TestingSessionLocal()
    org, user, password, username = _create_tenant_user(db, org_name="Continuidad Org")
    org_id = org.id
    db.close()
    return {
        "org_id": org_id,
        "headers": _headers(client, username, password),
        "username": username,
        "password": password,
    }


def test_servicio_critico_y_rto_rpo(tenant, client: TestClient):
    svc = _create_servicio(client, tenant["headers"])
    assert svc["criticidad"] == "CRITICA"
    assert svc["rto_valor"] == 60
    assert svc["rpo_valor"] == 15
    eval_res = client.post(
        f"/api/continuidad/servicios/{svc['id']}/evaluar-rto-rpo",
        headers=tenant["headers"],
        params={"tiempo_recuperacion_min": 45, "perdida_datos_min": 10},
    )
    assert eval_res.status_code == 200
    assert eval_res.json()["rto_cumplido"] is True
    assert eval_res.json()["rpo_cumplido"] is True


def test_rto_incumplido_y_rpo_incumplido(tenant, client: TestClient):
    svc = _create_servicio(client, tenant["headers"])
    rto_fail = client.post(
        f"/api/continuidad/servicios/{svc['id']}/evaluar-rto-rpo",
        headers=tenant["headers"],
        params={"tiempo_recuperacion_min": 120, "perdida_datos_min": 30},
    )
    assert rto_fail.status_code == 200
    body = rto_fail.json()
    assert body["rto_cumplido"] is False
    assert body["rpo_cumplido"] is False
    alertas = client.get("/api/continuidad/alertas", headers=tenant["headers"])
    tipos = {a["tipo"] for a in alertas.json()}
    assert "RTO_INCUMPLIDO" in tipos
    assert "RPO_EN_RIESGO" in tipos


def test_dependencias_y_puntos_falla(tenant, client: TestClient):
    api = _create_servicio(client, tenant["headers"], nombre="API Backend", tipo="BACKEND")
    db = _create_servicio(client, tenant["headers"], nombre="PostgreSQL", tipo="BASE_DE_DATOS")
    dep = client.post(
        "/api/continuidad/dependencias",
        headers=tenant["headers"],
        json={
            "servicio_origen_id": api["id"],
            "servicio_destino_id": db["id"],
            "critica": True,
            "tipo": "REQUIERE",
        },
    )
    assert dep.status_code == 201
    analisis = client.get("/api/continuidad/dependencias/analisis", headers=tenant["headers"])
    assert analisis.status_code == 200
    data = analisis.json()
    assert data["total"] == 1
    assert data["criticas"] == 1
    assert len(data["puntos_falla"]) == 1


def test_plan_continuidad(tenant, client: TestClient):
    plan = client.post(
        "/api/continuidad/planes",
        headers=tenant["headers"],
        json={"nombre": "Plan caída BD", "alcance": "Recuperación de datos", "rto_valor": 2, "rto_unidad": "horas"},
    )
    assert plan.status_code == 201
    assert plan.json()["estado"] == "BORRADOR"
    lista = client.get("/api/continuidad/planes", headers=tenant["headers"])
    assert len(lista.json()) >= 1


def test_backup_programado_ejecutado_verificado(tenant, client: TestClient):
    pol = client.post(
        "/api/continuidad/backups/politicas",
        headers=tenant["headers"],
        json={"recurso": "bd-prod-dump", "frecuencia": "DIARIA", "ubicacion_logica": "almacen-seguro"},
    )
    assert pol.status_code == 201
    assert pol.json()["estado"] == EstadoBackup.PROGRAMADO
    now = datetime.now(timezone.utc).isoformat()
    ej = client.post(
        "/api/continuidad/backups/ejecuciones",
        headers=tenant["headers"],
        json={"politica_id": pol.json()["id"], "inicio": now, "resultado": "EXITOSO", "tamano_bytes": 1024},
    )
    assert ej.status_code == 201
    assert ej.json()["estado_registro"] == EstadoBackup.EJECUTADO
    ver = client.post(
        "/api/continuidad/backups/verificaciones",
        headers=tenant["headers"],
        json={"ejecucion_id": ej.json()["id"], "existe": True, "tamano_ok": True, "integridad_ok": True, "vigente": True},
    )
    assert ver.status_code == 201


def test_backup_fallido_genera_alerta(tenant, client: TestClient):
    pol = client.post(
        "/api/continuidad/backups/politicas",
        headers=tenant["headers"],
        json={"recurso": "archivos-compartidos"},
    )
    now = datetime.now(timezone.utc).isoformat()
    ej = client.post(
        "/api/continuidad/backups/ejecuciones",
        headers=tenant["headers"],
        json={"politica_id": pol.json()["id"], "inicio": now, "resultado": "FALLIDO", "error_seguro": "Timeout de red"},
    )
    assert ej.status_code == 201
    alertas = client.get("/api/continuidad/alertas", headers=tenant["headers"])
    assert any(a["tipo"] == "BACKUP_FALLIDO" for a in alertas.json())


def test_restore_simulado_y_real_registrado(tenant, client: TestClient):
    pol = client.post(
        "/api/continuidad/backups/politicas",
        headers=tenant["headers"],
        json={"recurso": "restore-test"},
    )
    now = datetime.now(timezone.utc).isoformat()
    ej = client.post(
        "/api/continuidad/backups/ejecuciones",
        headers=tenant["headers"],
        json={"politica_id": pol.json()["id"], "inicio": now, "resultado": "EXITOSO"},
    )
    sim = client.post(
        "/api/continuidad/backups/restores",
        headers=tenant["headers"],
        json={
            "ejecucion_id": ej.json()["id"],
            "tipo": "SIMULADA",
            "entorno_destino": "laboratorio",
            "fecha": now,
            "duracion_minutos": 30,
            "datos_validados": "Esquema y muestra OK",
        },
    )
    assert sim.status_code == 201
    real = client.post(
        "/api/continuidad/backups/restores",
        headers=tenant["headers"],
        json={
            "ejecucion_id": ej.json()["id"],
            "tipo": "REAL",
            "entorno_destino": "staging",
            "fecha": now,
            "duracion_minutos": 45,
        },
    )
    assert real.status_code == 201


def test_restore_real_produccion_bloqueado(tenant, client: TestClient):
    pol = client.post(
        "/api/continuidad/backups/politicas",
        headers=tenant["headers"],
        json={"recurso": "prod-block"},
    )
    now = datetime.now(timezone.utc).isoformat()
    ej = client.post(
        "/api/continuidad/backups/ejecuciones",
        headers=tenant["headers"],
        json={"politica_id": pol.json()["id"], "inicio": now},
    )
    blocked = client.post(
        "/api/continuidad/backups/restores",
        headers=tenant["headers"],
        json={
            "ejecucion_id": ej.json()["id"],
            "tipo": "REAL",
            "entorno_destino": "PRODUCCION",
            "fecha": now,
        },
    )
    assert blocked.status_code == 400


def test_incidente_severidad_y_ciclo(tenant, client: TestClient):
    svc = _create_servicio(client, tenant["headers"])
    inc = client.post(
        "/api/continuidad/incidentes",
        headers=tenant["headers"],
        json={
            "titulo": "Caída parcial API",
            "servicio_id": svc["id"],
            "severidad": "SEV2",
            "impacto": {"usuarios_afectados": 120, "duracion_min": 45},
        },
    )
    assert inc.status_code == 201
    iid = inc.json()["id"]
    upd = client.patch(
        f"/api/continuidad/incidentes/{iid}/estado",
        headers=tenant["headers"],
        json={"estado": EstadoIncidente.EN_CONTENCION, "causa_raiz_tipo": "PROBABLE"},
    )
    assert upd.status_code == 200
    close = client.post(f"/api/continuidad/incidentes/{iid}/cerrar", headers=tenant["headers"])
    assert close.status_code == 200
    assert close.json()["estado"] == EstadoIncidente.CERRADO


def test_contingencia_activacion(tenant, client: TestClient):
    plan = client.post(
        "/api/continuidad/planes",
        headers=tenant["headers"],
        json={"nombre": "Contingencia IA", "activadores": "Proveedor IA no disponible"},
    )
    act = client.post(
        f"/api/continuidad/planes/{plan.json()['id']}/activar",
        headers=tenant["headers"],
        json={"plan_id": plan.json()["id"], "motivo": "Proveedor principal caído", "acciones": ["Activar fallback"]},
    )
    assert act.status_code == 201
    assert act.json()["estado"] == "ACTIVADO"


def test_modo_degradado(tenant, client: TestClient):
    svc = _create_servicio(client, tenant["headers"], nombre="Frontend web", tipo="FRONTEND")
    deg = client.post(
        "/api/continuidad/modo-degradado",
        headers=tenant["headers"],
        json={
            "servicio_id": svc["id"],
            "funciones_continuan": ["consulta"],
            "funciones_bloqueadas": ["exportación masiva"],
            "funciones_limitadas": ["informes"],
        },
    )
    assert deg.status_code == 201
    servicios = client.get("/api/continuidad/servicios", headers=tenant["headers"])
    front = next(s for s in servicios.json() if s["id"] == svc["id"])
    assert front["estado_operacional"] == EstadoOperacional.DEGRADADO


def test_disponibilidad_y_sla(tenant, client: TestClient):
    svc = _create_servicio(client, tenant["headers"], nombre="Servicio SLA", tipo="BACKEND")
    disp = client.post(
        "/api/continuidad/disponibilidad",
        headers=tenant["headers"],
        json={"servicio_id": svc["id"], "periodo": "2026-08", "tiempo_disponible_min": 43200, "tiempo_caido_min": 60},
    )
    assert disp.status_code == 201
    assert disp.json()["disponibilidad_pct"] > 99
    slo = client.post(
        "/api/continuidad/slos",
        headers=tenant["headers"],
        json={"servicio_id": svc["id"], "nombre": "Disponibilidad mensual", "objetivo_pct": 99.9},
    )
    assert slo.status_code == 201
    med = client.post(
        f"/api/continuidad/slos/{slo.json()['id']}/medir",
        headers=tenant["headers"],
        json={"medido_pct": 98.5},
    )
    assert med.status_code == 200
    assert med.json()["incumplido"] is True


def test_escalamiento_y_runbook(tenant, client: TestClient):
    esc = client.post(
        "/api/continuidad/escalamientos",
        headers=tenant["headers"],
        json={"severidad": "SEV1", "nivel": 1, "tiempo_max_min": 15, "siguiente_nivel": 2},
    )
    assert esc.status_code == 201
    rb = client.post(
        "/api/continuidad/runbooks",
        headers=tenant["headers"],
        json={
            "nombre": "Recuperación BD",
            "pasos": [
                {"orden": 1, "descripcion": "Verificar estado del clúster", "responsable": "DBA"},
                {"orden": 2, "descripcion": "Restaurar desde último backup verificado", "validacion": "Consultas OK"},
            ],
        },
    )
    assert rb.status_code == 201
    assert len(rb.json()["pasos"]) == 2
    blocked = client.post(
        "/api/continuidad/runbooks",
        headers=tenant["headers"],
        json={"nombre": "Malicioso", "pasos": [{"orden": 1, "comando": "rm -rf /"}]},
    )
    assert blocked.status_code == 400


def test_prueba_continuidad_post_incidente_y_accion(tenant, client: TestClient):
    plan = client.post(
        "/api/continuidad/planes",
        headers=tenant["headers"],
        json={"nombre": "Ejercicio anual"},
    )
    prueba = client.post(
        "/api/continuidad/pruebas",
        headers=tenant["headers"],
        json={
            "tipo": "SIMULACION",
            "escenario": "CAIDA_BASE_DE_DATOS",
            "plan_id": plan.json()["id"],
            "objetivo": "Validar RTO",
            "rto_obtenido": 55,
            "rpo_obtenido": 10,
            "resultado": "EXITOSO",
        },
    )
    assert prueba.status_code == 201
    inc = client.post(
        "/api/continuidad/incidentes",
        headers=tenant["headers"],
        json={"titulo": "Incidente post-mortem", "severidad": "SEV3"},
    )
    post = client.post(
        "/api/continuidad/post-incidentes",
        headers=tenant["headers"],
        json={
            "incidente_id": inc.json()["id"],
            "que_ocurrio": "Fallo de disco",
            "causa_raiz_tipo": "CONFIRMADA",
            "que_funciono": "Failover automático",
            "que_fallo": "Monitoreo tardío",
        },
    )
    assert post.status_code == 201
    assert post.json()["integracion_1260_prep"] is True
    acc = client.post(
        "/api/continuidad/acciones-correctivas",
        headers=tenant["headers"],
        json={
            "incidente_id": inc.json()["id"],
            "post_incidente_id": post.json()["id"],
            "accion": "Ampliar alertas de disco",
            "prioridad": "ALTA",
        },
    )
    assert acc.status_code == 201


def test_tablero_y_centro_control(tenant, client: TestClient):
    _create_servicio(client, tenant["headers"])
    tab = client.get("/api/continuidad/tablero", headers=tenant["headers"])
    assert tab.status_code == 200
    body = tab.json()
    assert "servicios_criticos" in body
    assert "centro_control_adapter" in body
    assert "integracion_1330_prep" in body
    cc = client.get("/api/continuidad/centro-control-resumen", headers=tenant["headers"])
    assert cc.status_code == 200


def test_rbac_viewer_no_puede_gestionar(client: TestClient):
    db = TestingSessionLocal()
    org, user, password, username = _create_tenant_user(db, org_name="Viewer Org", role="viewer")
    db.close()
    headers = _headers(client, username, password)
    denied = client.post(
        "/api/continuidad/servicios",
        headers=headers,
        json={"nombre": "No permitido"},
    )
    assert denied.status_code == 403
    ok = client.get("/api/continuidad/tablero", headers=headers)
    assert ok.status_code == 200


def test_multiempresa_aislamiento(client: TestClient):
    db = TestingSessionLocal()
    org_a, _, pass_a, user_a = _create_tenant_user(db, org_name="Org A")
    org_b, _, pass_b, user_b = _create_tenant_user(db, org_name="Org B")
    db.close()
    headers_a = _headers(client, user_a, pass_a)
    headers_b = _headers(client, user_b, pass_b)
    svc_a = _create_servicio(client, headers_a, nombre="Servicio A exclusivo")
    tab_b = client.get("/api/continuidad/tablero", headers=headers_b)
    nombres_b = {s["nombre"] for s in tab_b.json()["servicios_criticos"]}
    assert "Servicio A exclusivo" not in nombres_b
    estado = client.patch(
        f"/api/continuidad/servicios/{svc_a['id']}/estado",
        headers=headers_b,
        params={"estado": "NO_DISPONIBLE"},
    )
    assert estado.status_code == 404


def test_auditoria_registra_cambios(tenant, client: TestClient):
    svc = _create_servicio(client, tenant["headers"])
    db = TestingSessionLocal()
    try:
        rows = (
            db.query(ContinuidadAuditoria)
            .filter(ContinuidadAuditoria.organization_id == tenant["org_id"])
            .all()
        )
        assert any(r.entidad == "servicio" and r.accion == "CREAR" for r in rows)
    finally:
        db.close()
    client.post(
        "/api/continuidad/incidentes",
        headers=tenant["headers"],
        json={"titulo": "Para auditoría", "severidad": "SEV4"},
    )
    db = TestingSessionLocal()
    try:
        rows = (
            db.query(ContinuidadAuditoria)
            .filter(ContinuidadAuditoria.organization_id == tenant["org_id"], ContinuidadAuditoria.entidad == "incidente")
            .all()
        )
        assert len(rows) >= 1
    finally:
        db.close()
