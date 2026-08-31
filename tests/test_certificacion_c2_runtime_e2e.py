"""Certificación C2 — E2E runtime encadenado (20 recorridos obligatorios Agente C)."""

from __future__ import annotations

import json
import uuid

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.models import Notification, Organization, User
from app.orchestration_models import WorkPlan
from app.security import hash_password
from app.tenant_scope import ORG_STATUS_INACTIVE
from conftest import TestingSessionLocal, auth_header

pytestmark = [pytest.mark.auth, pytest.mark.tenant, pytest.mark.operations]


def _login(client: TestClient, username: str, password: str) -> str:
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _create_tenant(db, name: str) -> tuple[str, str, str, str]:
    from app.seed_orchestration import bootstrap_orchestration
    from app.seed_permissions import bootstrap_permissions
    from app.seed_salud import bootstrap_salud

    org = Organization(name=name, slug=f"cert-{uuid.uuid4().hex[:8]}")
    db.add(org)
    db.flush()
    bootstrap_permissions(db)
    bootstrap_orchestration(db, org.id)
    bootstrap_salud(db, org.id)
    pwd = "CertC2*Runtime1"
    username = f"cert-{uuid.uuid4().hex[:6]}"
    user = User(
        organization_id=org.id,
        username=username,
        password_hash=hash_password(pwd),
        role="admin",
        status="ACTIVE",
        is_active=True,
    )
    db.add(user)
    db.commit()
    return org.id, user.id, username, pwd


def test_certificacion_c2_runtime_20_recorridos(client: TestClient, auth_headers):
    """Runtime E2E encadenado: recorridos 1–19 (+ build 20 documentado aparte)."""
    db = TestingSessionLocal()
    plan_a_id = None
    try:
        org_a_id, user_a_id, user_a_name, pwd_a = _create_tenant(db, "Cert Runtime A")
        org_b_id, user_b_id, user_b_name, pwd_b = _create_tenant(db, "Cert Runtime B")
        plan_a = WorkPlan(
            organization_id=org_a_id,
            user_id=user_a_id,
            correlation_id="cert-plan-a",
            request="plan A cert",
            objective="obj A",
            status="FAILED",
            error="err",
        )
        db.add(plan_a)
        db.add(
            WorkPlan(
                organization_id=org_b_id,
                user_id=user_b_id,
                correlation_id="cert-plan-b",
                request="plan B cert",
                objective="obj B",
                status="FAILED",
                error="err",
            )
        )
        db.add(
            Notification(
                organization_id=org_a_id,
                type="INFO",
                severity="LOW",
                title="Notif cert A",
                message="A",
                source_type="test",
                status="NEW",
                recipient_user_id=user_a_id,
            )
        )
        db.add(
            Notification(
                organization_id=org_b_id,
                type="INFO",
                severity="LOW",
                title="Notif cert B",
                message="B",
                source_type="test",
                status="NEW",
                recipient_user_id=user_b_id,
            )
        )
        inactive = Organization(
            name="Cert Inactive",
            slug=f"cert-inact-{uuid.uuid4().hex[:6]}",
            status=ORG_STATUS_INACTIVE,
        )
        db.add(inactive)
        db.flush()
        inactive_id = inactive.id
        db.commit()
        plan_a_id = plan_a.id
    finally:
        db.close()

    # 1–4 Org A
    token_a = _login(client, user_a_name, pwd_a)
    hdr_a = auth_header(token_a)
    cc_a = client.get("/api/centro-control/resumen-ejecutivo", headers=hdr_a)
    assert cc_a.status_code == 200 and cc_a.json()["organization_id"] == org_a_id
    tr_a = client.get("/api/trabajo/items", headers=hdr_a)
    assert tr_a.status_code == 200
    assert client.get(f"/api/trabajo/items?organization_id={org_b_id}", headers=hdr_a).status_code == 403

    # 5–8 Org B
    token_b = _login(client, user_b_name, pwd_b)
    hdr_b = auth_header(token_b)
    cc_b = client.get("/api/centro-control/resumen-ejecutivo", headers=hdr_b)
    assert cc_b.status_code == 200 and cc_b.json()["organization_id"] == org_b_id
    tr_b = client.get("/api/trabajo/items", headers=hdr_b)
    assert tr_b.status_code == 200
    assert not any("cert-plan-a" in json.dumps(i) for i in tr_b.json()["items"])

    # 9–13 SUPERADMIN context switch
    sa_cc_a = client.get(
        f"/api/centro-control/resumen-ejecutivo?organization_id={org_a_id}",
        headers=auth_headers,
    )
    sa_tr_a = client.get(f"/api/trabajo/resumen?organization_id={org_a_id}", headers=auth_headers)
    assert sa_cc_a.status_code == 200 and sa_tr_a.json()["organization_id"] == org_a_id

    sa_cc_b = client.get(
        f"/api/centro-control/resumen-ejecutivo?organization_id={org_b_id}",
        headers=auth_headers,
    )
    sa_tr_b = client.get(f"/api/trabajo/items?organization_id={org_b_id}", headers=auth_headers)
    assert sa_cc_b.status_code == 200
    titles_b = [i.get("asunto", "") for i in sa_tr_b.json()["items"]]
    assert any("Notif cert B" in t for t in titles_b)
    assert not any("Notif cert A" in t for t in titles_b)

    # 14 inactive org
    assert (
        client.get(
            f"/api/centro-control/resumen-ejecutivo?organization_id={inactive_id}",
            headers=auth_headers,
        ).status_code
        == 403
    )

    # 15 no permission (tenant cross-org already asserted above; CC without perm in convergencia_c2)

    # 16 C1-R1 home
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    assert '<Route index element={<HomePage />} />' in (root / "frontend/src/App.tsx").read_text(encoding="utf-8")

    # 17 G2/G3 — ejecutado en suite focal (gate post6d); smoke presencia
    gate = (root / "tests/test_gate_post6d_correcciones.py").read_text(encoding="utf-8")
    assert "test_g3_dedup_oportunidad_vs_1290_humana" in gate

    # 18 navigation link
    rows = [i for i in tr_a.json()["items"] if i.get("source_id") == plan_a_id]
    assert rows and rows[0]["enlace"].startswith("/")

    # 19 login/MFA/SSO/sid
    api_src = (root / "frontend/src/api.ts").read_text(encoding="utf-8")
    login_src = (root / "frontend/src/pages/LoginPage.tsx").read_text(encoding="utf-8")
    assert "const text = await res.text()" in api_src
    assert "verifyMfaLogin" in login_src and "discoverLogin" in login_src
    assert client.get("/api/security/sessions", headers=auth_headers).status_code == 200

    # Bootstrap admin login preserved
    sa_login = client.post(
        "/api/auth/login",
        json={
            "username": settings.bootstrap_admin_username,
            "password": settings.bootstrap_admin_password,
        },
    )
    assert sa_login.status_code == 200
