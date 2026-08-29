"""Cadena focal RESULTADO → APRENDIZAJE → REPRIORIZACIÓN → OPTIMIZACIÓN → RECOMENDACIÓN."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Organization, User
from app.security import hash_password
from conftest import TestingSessionLocal, auth_header

pytestmark = [pytest.mark.operations]


def _token(client: TestClient, username: str, password: str) -> str:
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _create_tenant(
    db: Session,
    *,
    org_name: str,
    password: str = "Cadena1260*Test1",
) -> tuple[Organization, User, str]:
    from app.seed_orchestration import bootstrap_orchestration
    from app.seed_permissions import bootstrap_permissions
    from app.seed_salud import bootstrap_salud

    org = Organization(name=org_name, slug=f"cad-{uuid.uuid4().hex[:8]}")
    db.add(org)
    db.flush()
    bootstrap_permissions(db)
    bootstrap_orchestration(db, org.id)
    bootstrap_salud(db, org.id)
    username = f"user-{uuid.uuid4().hex[:6]}"
    user = User(
        organization_id=org.id,
        username=username,
        password_hash=hash_password(password),
        role="admin",
        status="ACTIVE",
        is_active=True,
    )
    db.add(user)
    db.commit()
    return org, user, password


def _create_opportunity(client: TestClient, headers: dict[str, str]) -> str:
    res = client.post(
        "/api/oportunidades/pipeline-proactivo",
        headers=headers,
        json={
            "tipo": "financiera",
            "dominio": "financiero",
            "evento": "cadena_integracion",
            "payload": {
                "titulo": "Oportunidad cadena 1260-1290-1270",
                "tipo_oportunidad": "FINANCIERA",
                "indicadores": {"kpi": 1},
                "impacto_estimado": 5_000_000,
                "valor_potencial": 4_000_000,
                "costo_estimado": 1_000_000,
                "urgencia": "ALTA",
                "source_reference": f"ref-{uuid.uuid4().hex[:8]}",
            },
            "origen": "test_cadena_integracion",
        },
    )
    assert res.status_code == 200, res.text
    return res.json()["opportunity_id"]


def test_cadena_resultado_aprendizaje_optimizacion_recomendacion(client: TestClient):
    """Flujo integral: resultado materializado → aprendizaje → repriorización → optimización → recomendación."""
    db = TestingSessionLocal()
    try:
        _, user, password = _create_tenant(db, org_name="Org Cadena Integracion")
        headers = auth_header(_token(client, user.username, password))
        opp_id = _create_opportunity(client, headers)

        client.post(f"/api/oportunidades/{opp_id}/aprobar", headers=headers, json={"aprobado": True})
        client.post(f"/api/oportunidades/{opp_id}/activar", headers=headers, json={"auto_execute": False})

        resultado = client.post(
            f"/api/oportunidades/{opp_id}/resultado",
            headers=headers,
            json={
                "valor_real": 2_500_000,
                "valor_esperado": 4_000_000,
                "estado_resultado": "PARCIAL",
            },
        )
        assert resultado.status_code == 200, resultado.text

        ciclo = client.post(
            "/api/aprendizaje/ciclos",
            headers=headers,
            json={
                "opportunity_id": opp_id,
                "valor_real": 2_500_000,
                "impacto_real": 3_000_000,
            },
        )
        assert ciclo.status_code == 201, ciclo.text
        ciclo_id = ciclo.json()["id"]

        evaluado = client.post(
            f"/api/aprendizaje/ciclos/{ciclo_id}/evaluar",
            headers=headers,
            json={
                "valor_real": 2_500_000,
                "impacto_real": 3_000_000,
                "tipo_explicacion": "PROBABLE",
            },
        )
        assert evaluado.status_code == 200, evaluado.text
        eval_body = evaluado.json()
        assert eval_body["ciclo"]["estado"] == "EVALUADO"
        assert eval_body["explicacion_prioridad"]["score"] is not None
        rec_id = eval_body["recalibraciones"][0]["id"]

        client.post(f"/api/aprendizaje/recalibraciones/{rec_id}/aprobar", headers=headers)
        aplicada = client.post(f"/api/aprendizaje/recalibraciones/{rec_id}/aplicar", headers=headers)
        assert aplicada.status_code == 200
        assert aplicada.json()["estado"] == "APLICADA"

        sim = client.post(
            "/api/optimizacion/simular",
            headers=headers,
            json={"objetivo": "RESULTADO_EQUILIBRADO", "opportunity_ids": [opp_id]},
        )
        assert sim.status_code == 200, sim.text
        sim_body = sim.json()
        assert len(sim_body["oportunidades"][0]["aprendizaje"]["ciclos"]) >= 1

        recomendacion = client.post(
            "/api/optimizacion/recomendaciones",
            headers=headers,
            json={"objetivo": "MAXIMIZAR_VALOR", "restricciones": {"max_iniciativas": 1}},
        )
        assert recomendacion.status_code == 201, recomendacion.text
        rec_opt_id = recomendacion.json()["id"]
        assert recomendacion.json()["estado"] in ("BORRADOR", "PROPUESTA")

        observabilidad = client.get("/api/llm/observability?periodo=mtd", headers=headers)
        assert observabilidad.status_code == 200, observabilidad.text
        assert "total_inferencias" in observabilidad.json()

        detalle = client.get(f"/api/optimizacion/recomendaciones/{rec_opt_id}", headers=headers)
        assert detalle.status_code == 200
        assert detalle.json()["objetivo"] == "MAXIMIZAR_VALOR"
    finally:
        db.close()
