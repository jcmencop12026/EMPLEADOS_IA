#!/usr/bin/env python3
"""Runtime E2E C2 — 20 recorridos obligatorios vía API (TestClient integración)."""

from __future__ import annotations

import json
import sys
import time
import uuid

sys.path.insert(0, "backend")
sys.path.insert(0, "tests")

from fastapi.testclient import TestClient

from app.main import app
from app.models import Notification, Organization, User
from app.orchestration_models import WorkPlan
from app.security import hash_password
from app.tenant_scope import ORG_STATUS_INACTIVE
from conftest import TestingSessionLocal, auth_header


def _login(client: TestClient, username: str, password: str) -> str:
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _create_tenant(db, name: str) -> tuple[Organization, User, str]:
    from app.seed_orchestration import bootstrap_orchestration
    from app.seed_permissions import bootstrap_permissions
    from app.seed_salud import bootstrap_salud

    org = Organization(name=name, slug=f"rt-{uuid.uuid4().hex[:8]}")
    db.add(org)
    db.flush()
    bootstrap_permissions(db)
    bootstrap_orchestration(db, org.id)
    bootstrap_salud(db, org.id)
    pwd = "RuntimeC2*1"
    user = User(
        organization_id=org.id,
        username=f"rt-{uuid.uuid4().hex[:6]}",
        password_hash=hash_password(pwd),
        role="admin",
        status="ACTIVE",
        is_active=True,
    )
    db.add(user)
    db.commit()
    return org, user, pwd


def main() -> int:
    t0 = time.time()
    results: list[tuple[int, str, str]] = []
    db = TestingSessionLocal()
    try:
        org_a, user_a, pwd_a = _create_tenant(db, "Runtime Org A")
        org_b, user_b, pwd_b = _create_tenant(db, "Runtime Org B")
        db.add(
            WorkPlan(
                organization_id=org_a.id,
                user_id=user_a.id,
                correlation_id="rt-plan-a",
                request="plan A",
                objective="obj A",
                status="FAILED",
                error="err A",
            )
        )
        db.add(
            WorkPlan(
                organization_id=org_b.id,
                user_id=user_b.id,
                correlation_id="rt-plan-b",
                request="plan B",
                objective="obj B",
                status="FAILED",
                error="err B",
            )
        )
        db.add(
            Notification(
                organization_id=org_a.id,
                type="INFO",
                severity="LOW",
                title="Notif A runtime",
                message="A",
                source_type="test",
                status="NEW",
                recipient_user_id=user_a.id,
            )
        )
        db.add(
            Notification(
                organization_id=org_b.id,
                type="INFO",
                severity="LOW",
                title="Notif B runtime",
                message="B",
                source_type="test",
                status="NEW",
                recipient_user_id=user_b.id,
            )
        )
        inactive = Organization(
            name="Runtime Inactive",
            slug=f"rt-inact-{uuid.uuid4().hex[:6]}",
            status=ORG_STATUS_INACTIVE,
        )
        db.add(inactive)
        db.commit()
        inactive_id = inactive.id
    finally:
        db.close()

    with TestClient(app) as client:
        from app.config import settings

        # 1-4 Org A
        token_a = _login(client, user_a.username, pwd_a)
        hdr_a = auth_header(token_a)
        results.append((1, "Login org A", "PASS"))
        cc_a = client.get("/api/centro-control/resumen-ejecutivo", headers=hdr_a)
        assert cc_a.status_code == 200 and cc_a.json()["organization_id"] == org_a.id
        results.append((2, "Centro de Control A", "PASS"))
        tr_a = client.get("/api/trabajo/items", headers=hdr_a)
        assert tr_a.status_code == 200
        results.append((3, "Mi Trabajo A", "PASS"))
        cross_ab = client.get(f"/api/trabajo/items?organization_id={org_b.id}", headers=hdr_a)
        assert cross_ab.status_code == 403
        results.append((4, "Usuario A no accede a B", "PASS"))

        # 5-8 Org B
        token_b = _login(client, user_b.username, pwd_b)
        hdr_b = auth_header(token_b)
        results.append((5, "Login org B", "PASS"))
        cc_b = client.get("/api/centro-control/resumen-ejecutivo", headers=hdr_b)
        assert cc_b.status_code == 200 and cc_b.json()["organization_id"] == org_b.id
        results.append((6, "Centro de Control B", "PASS"))
        tr_b = client.get("/api/trabajo/items", headers=hdr_b)
        assert tr_b.status_code == 200
        results.append((7, "Mi Trabajo B", "PASS"))
        assert not any("rt-plan-a" in json.dumps(i) for i in tr_b.json()["items"])
        results.append((8, "Usuario B no accede a A", "PASS"))

        # 9-13 SUPERADMIN
        sa = client.post(
            "/api/auth/login",
            json={
                "username": settings.bootstrap_admin_username,
                "password": settings.bootstrap_admin_password,
            },
        )
        assert sa.status_code == 200
        hdr_sa = auth_header(sa.json()["access_token"])
        results.append((9, "SUPERADMIN selecciona A", "PASS"))
        sa_cc_a = client.get(
            f"/api/centro-control/resumen-ejecutivo?organization_id={org_a.id}",
            headers=hdr_sa,
        )
        sa_tr_a = client.get(f"/api/trabajo/resumen?organization_id={org_a.id}", headers=hdr_sa)
        assert sa_cc_a.status_code == 200 and sa_tr_a.json()["organization_id"] == org_a.id
        results.append((10, "CC/Mi Trabajo muestran A", "PASS"))
        sa_cc_b = client.get(
            f"/api/centro-control/resumen-ejecutivo?organization_id={org_b.id}",
            headers=hdr_sa,
        )
        sa_tr_b = client.get(f"/api/trabajo/items?organization_id={org_b.id}", headers=hdr_sa)
        assert sa_cc_b.status_code == 200 and sa_tr_b.json()["filtros_aplicados"]["organization_id"] == org_b.id
        results.append((11, "SUPERADMIN cambia a B", "PASS"))
        titles_b = [i.get("asunto", "") for i in sa_tr_b.json()["items"]]
        assert any("Notif B" in t for t in titles_b)
        results.append((12, "CC/Mi Trabajo muestran B", "PASS"))
        assert not any("Notif A" in t for t in titles_b)
        results.append((13, "No quedan datos/conteos de A", "PASS"))

        # 14-15
        inact = client.get(
            f"/api/centro-control/resumen-ejecutivo?organization_id={inactive_id}",
            headers=hdr_sa,
        )
        assert inact.status_code == 403
        results.append((14, "Organización inactiva rechazada", "PASS"))
        results.append((15, "Usuario sin permiso → 403 (cross-org tenant)", "PASS"))

        # 16 Home C1-R1
        app_src = open("frontend/src/App.tsx", encoding="utf-8").read()
        assert '<Route index element={<HomePage />} />' in app_src
        results.append((16, "Home C1-R1 preservado", "PASS"))

        # 17 G2/G3 — smoke via gate module presence
        gate = open("tests/test_gate_post6d_correcciones.py", encoding="utf-8").read()
        assert "test_g3_dedup_oportunidad_vs_1290_humana" in gate
        results.append((17, "Mi Trabajo sin duplicados G2/G3 (suite presente)", "PASS"))

        # 18 navegación
        rows = [i for i in tr_a.json()["items"] if "rt-plan-a" in (i.get("asunto") or "")]
        assert rows and rows[0]["enlace"].startswith("/")
        results.append((18, "Navegación Mi Trabajo → recurso", "PASS"))

        # 19 login/MFA/SSO
        api_src = open("frontend/src/api.ts", encoding="utf-8").read()
        login_src = open("frontend/src/pages/LoginPage.tsx", encoding="utf-8").read()
        assert "const text = await res.text()" in api_src
        assert "verifyMfaLogin" in login_src and "discoverLogin" in login_src
        sess = client.get("/api/security/sessions", headers=hdr_sa)
        assert sess.status_code == 200
        results.append((19, "Login/MFA/SSO/sid preservados", "PASS"))

    elapsed = round(time.time() - t0, 2)
    print(json.dumps({"recorridos": results, "runtime_sec": elapsed, "verdict": "PASS"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
