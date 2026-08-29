"""P1-ID-02 — Contrato semántico HECHO / INFERENCIA / RECOMENDACIÓN."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.orm import Session

from app.diagnostic_models import (
    Diagnostic,
    DiagnosticFinding,
    DiagnosticItem,
    DiagnosticProbableCause,
)
from app.models import Organization, User
from app.security import hash_password
from app.services import control_center_service as svc
from app.services.control_center_adapters import DiagnosticoExplicacionAdapter
from app.services.semantic_contract import (
    SEMANTIC_HECHO,
    SEMANTIC_INFERENCIA,
    SEMANTIC_RECOMENDACION,
    SEMANTIC_SIN_CLASIFICAR,
    enrich_control_center_payload,
    from_atencion_item,
    from_diagnostic_cause,
    from_external_signal,
    from_llm_output,
    from_tipo_entrada_explicacion,
    valor_field_semantics,
)

pytestmark = [pytest.mark.operations]


@pytest.fixture
def cc_db():
    from app.database import SessionLocal

    db = SessionLocal()
    yield db
    db.close()


def _cc_user(db: Session) -> tuple[Organization, User]:
    from app.seed_orchestration import bootstrap_orchestration
    from app.seed_permissions import bootstrap_permissions

    org = Organization(name=f"Org-sem-{uuid.uuid4().hex[:6]}")
    db.add(org)
    db.flush()
    bootstrap_permissions(db)
    bootstrap_orchestration(db, org.id)
    user = User(
        organization_id=org.id,
        username=f"u-sem-{uuid.uuid4().hex[:6]}",
        email=f"sem-{uuid.uuid4().hex[:6]}@test.com",
        password_hash=hash_password("Admin2026*"),
        role="admin",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return org, user


def _seed_explicacion(db: Session, org_id: str, *, correlation: bool = False) -> None:
    diag = Diagnostic(
        organization_id=org_id,
        codigo=f"DIAG-SEM-{uuid.uuid4().hex[:6]}",
        version=1,
        estado="GENERADO",
        resumen="Diagnóstico semántico",
        prioridad_score=90.0,
        correlation_id=str(uuid.uuid4()),
    )
    db.add(diag)
    db.flush()
    finding = DiagnosticFinding(
        organization_id=org_id,
        codigo="HAL-SEM",
        tipo_contenido="HECHO",
        que_ocurre="Facturación cayó 12 %",
        dominio="FINANCIERO",
        proceso="facturacion",
        evidencia_json='{"resumen":"dato observado","fuente":"erp"}',
    )
    db.add(finding)
    db.flush()
    cause = DiagnosticProbableCause(
        organization_id=org_id,
        finding_id=finding.id,
        diagnostic_id=diag.id,
        tipo="CORRELACION" if correlation else "PROBABLE",
        descripcion="Posible causa: menor disponibilidad",
        justificacion="Correlación observada" if correlation else "Evidencia parcial",
        confianza=0.55,
    )
    db.add(cause)
    db.flush()
    db.add(
        DiagnosticItem(
            organization_id=org_id,
            diagnostic_id=diag.id,
            item_type="HALLAZGO",
            hallazgo_id=finding.id,
            causa_id=cause.id,
            orden=1,
        )
    )
    db.commit()


def test_semantic_dato_observado_es_hecho():
    meta = from_tipo_entrada_explicacion("SITUACION", tipo_contenido="HECHO")
    assert meta["tipo_semantico"] == SEMANTIC_HECHO


def test_semantic_correlacion_es_inferencia():
    meta = from_diagnostic_cause("CORRELACION")
    assert meta["tipo_semantico"] == SEMANTIC_INFERENCIA
    assert meta["subtipo_semantico"] == "CORRELACION"


def test_semantic_causa_probable_es_inferencia():
    meta = from_diagnostic_cause("PROBABLE")
    assert meta["tipo_semantico"] == SEMANTIC_INFERENCIA


def test_semantic_hipotesis_es_inferencia():
    meta = from_diagnostic_cause("HIPOTESIS")
    assert meta["tipo_semantico"] == SEMANTIC_INFERENCIA


def test_semantic_recomendacion():
    meta = from_tipo_entrada_explicacion("RECOMENDACION")
    assert meta["tipo_semantico"] == SEMANTIC_RECOMENDACION


def test_semantic_prediccion_es_inferencia():
    meta = from_external_signal(classification="TENDENCIA")
    assert meta["tipo_semantico"] == SEMANTIC_INFERENCIA
    assert meta["subtipo_semantico"] == "PREDICCION"
    atencion = from_atencion_item("diagnostico_prioritario")
    assert atencion["tipo_semantico"] == SEMANTIC_INFERENCIA


def test_semantic_causa_demostrada_es_hecho():
    meta = from_diagnostic_cause("CONFIRMADA")
    assert meta["tipo_semantico"] == SEMANTIC_HECHO


def test_semantic_estimacion_no_es_hecho_realizado():
    meta = valor_field_semantics("valor_esperado", 1000)
    assert meta["tipo_semantico"] == SEMANTIC_INFERENCIA
    mat = valor_field_semantics("valor_materializado", 500)
    assert mat["tipo_semantico"] == SEMANTIC_HECHO


def test_semantic_ia_no_es_hecho():
    meta = from_llm_output()
    assert meta["tipo_semantico"] == SEMANTIC_INFERENCIA


def test_semantic_sin_clasificar_seguro():
    meta = from_tipo_entrada_explicacion(None)
    assert meta["tipo_semantico"] == SEMANTIC_SIN_CLASIFICAR


def test_cc_contrato_semantico_en_resumen(cc_db):
    _, user = _cc_user(cc_db)
    body = svc.get_executive_summary(cc_db, user)
    assert "contrato_semantico" in body
    assert body["contrato_semantico"]["version"] == "1.0"
    assert "HECHO" in body["contrato_semantico"]["tipos"]


def test_cc_explicacion_con_tipo_semantico(cc_db):
    org, user = _cc_user(cc_db)
    _seed_explicacion(cc_db, org.id, correlation=True)
    elementos = svc.get_executive_summary(cc_db, user)["explicacion"]["elementos"]
    assert elementos
    for el in elementos:
        assert el.get("tipo_semantico") in (
            "HECHO",
            "INFERENCIA",
            "RECOMENDACION",
            "SIN_CLASIFICAR",
        )


def test_cc_atencion_con_semantica(cc_db):
    _, user = _cc_user(cc_db)
    for item in svc.get_executive_summary(cc_db, user)["atencion_requerida"]:
        assert "tipo_semantico" in item


def test_cc_valor_retorno_campos_semanticos(cc_db):
    _, user = _cc_user(cc_db)
    vr = svc.get_executive_summary(cc_db, user).get("valor_retorno")
    if not vr or not vr.get("disponible"):
        return
    campos = vr.get("campos_semanticos") or {}
    if campos.get("valor_esperado"):
        assert campos["valor_esperado"]["tipo_semantico"] == SEMANTIC_INFERENCIA


def test_cc_llm_inferencia(cc_db):
    _, user = _cc_user(cc_db)
    llm = svc.get_executive_summary(cc_db, user).get("llm")
    if not llm or not llm.get("proveedores"):
        return
    prov = llm["proveedores"][0]
    assert isinstance(prov, dict)
    assert prov.get("tipo_semantico") == SEMANTIC_INFERENCIA


def test_cc_cross_tenant_semantica(cc_db):
    org_a, user_a = _cc_user(cc_db)
    org_b, user_b = _cc_user(cc_db)
    _seed_explicacion(cc_db, org_a.id)
    summary_a = svc.get_executive_summary(cc_db, user_a)
    summary_b = svc.get_executive_summary(cc_db, user_b)
    assert summary_a["organization_id"] != summary_b["organization_id"]
    ids_a = {e["id"] for e in (summary_a.get("explicacion") or {}).get("elementos") or []}
    ids_b = {e["id"] for e in (summary_b.get("explicacion") or {}).get("elementos") or []}
    assert not ids_a.intersection(ids_b) or (not ids_a and not ids_b)


def test_cc_responde_sin_explicacion(cc_db):
    _, user = _cc_user(cc_db)
    body = svc.get_executive_summary(cc_db, user)
    assert "contrato_semantico" in body
    assert body.get("explicacion") is not None


def test_semantic_rbac_sin_diagnosticos_view(cc_db):
    _, user = _cc_user(cc_db)
    adapter = DiagnosticoExplicacionAdapter()
    result = adapter.fetch(cc_db, user.organization_id, permissions={"control_center.view"})
    assert result.get("restringido") is True
    body = svc.get_executive_summary(cc_db, user, estado=None)
    assert "contrato_semantico" in body


def test_semantic_evidencia_no_expandida_por_clasificacion():
    payload = enrich_control_center_payload({
        "explicacion": {
            "elementos": [{
                "id": "1",
                "tipo_entrada": "CAUSA",
                "certeza_codigo": "PROBABLE",
                "evidencia": {"resumen": "dato restringido"},
            }],
        },
        "atencion_requerida": [],
    })
    el = payload["explicacion"]["elementos"][0]
    assert el["evidencia"] == {"resumen": "dato restringido"}
    assert el["tipo_semantico"] == SEMANTIC_INFERENCIA


def test_enrich_preserva_correlation_id():
    payload = enrich_control_center_payload({
        "explicacion": {
            "elementos": [{
                "id": "1",
                "tipo_entrada": "CAUSA",
                "certeza_codigo": "PROBABLE",
                "tipo_contenido": "HECHO",
                "correlation_id": "corr-abc-123",
                "evidencia": {"resumen": "test"},
            }],
        },
        "atencion_requerida": [],
    })
    el = payload["explicacion"]["elementos"][0]
    assert el["correlation_id"] == "corr-abc-123"
    assert el["tipo_semantico"] == SEMANTIC_INFERENCIA
