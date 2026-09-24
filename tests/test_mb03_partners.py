"""MB-03 Partners / Aliados — pruebas de aislamiento y RBAC."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Organization, User
from app.partner_models import PartnerOrganizationGrant, PartnerUserMembership
from app.security import hash_password

pytestmark = [pytest.mark.partners]


@pytest.fixture
def partners_db(client):
    from tests.conftest import TestingSessionLocal

    db = TestingSessionLocal()
    yield db
    db.close()


def _create_partner(client: TestClient, headers: dict[str, str], nombre: str) -> dict:
    res = client.post(
        "/api/partners",
        headers=headers,
        json={"nombre": nombre, "tipo_relacion": "CONSULTOR", "contacto_email": f"{nombre}@test.local"},
    )
    assert res.status_code == 201, res.text
    return res.json()


def _create_org(db: Session, name: str) -> Organization:
    org = Organization(id=str(uuid.uuid4()), name=name, slug=f"org-{uuid.uuid4().hex[:8]}")
    db.add(org)
    db.flush()
    return org


def _create_user(db: Session, org: Organization, username: str, *, role: str = "viewer") -> User:
    user = User(
        id=str(uuid.uuid4()),
        organization_id=org.id,
        username=username,
        email=f"{username}@test.local",
        password_hash=hash_password("testpass123"),
        is_active=True,
        role=role,
    )
    db.add(user)
    db.flush()
    return user


def _login(client: TestClient, username: str) -> dict[str, str]:
    res = client.post("/api/auth/login", json={"username": username, "password": "testpass123"})
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def test_mb03_crear_y_activar_partner(client: TestClient, auth_headers, partners_db):
    p = _create_partner(client, auth_headers, "Partner Alpha")
    assert p["codigo"].startswith("PTR-")
    assert p["estado"] == "BORRADOR"

    act = client.post(f"/api/partners/{p['id']}/estado", headers=auth_headers, json={"estado": "ACTIVO"})
    assert act.status_code == 200
    assert act.json()["estado"] == "ACTIVO"

    detail = client.get(f"/api/partners/{p['id']}", headers=auth_headers)
    assert detail.status_code == 200
    assert detail.json()["nombre"] == "Partner Alpha"


def test_mb03_asociar_organizacion_y_auditar(client: TestClient, auth_headers, partners_db):
    p = _create_partner(client, auth_headers, "Partner Beta")
    client.post(f"/api/partners/{p['id']}/estado", headers=auth_headers, json={"estado": "ACTIVO"})

    org = _create_org(partners_db, "Org Concedida Beta")
    partners_db.commit()

    grant = client.post(
        f"/api/partners/{p['id']}/organizaciones",
        headers=auth_headers,
        json={"organization_id": org.id, "alcance": ["organizacion.read", "cc.view"]},
    )
    assert grant.status_code == 201
    body = grant.json()
    assert body["organization_id"] == org.id
    assert "organizacion.read" in body["alcance"]

    audit = client.get(f"/api/partners/{p['id']}/auditoria", headers=auth_headers)
    assert audit.status_code == 200
    actions = [e["action"] for e in audit.json()["items"]]
    assert "partner.org.grant" in actions


def test_mb03_aislamiento_partner_a_no_accede_org_de_partner_b(
    client: TestClient, auth_headers, partners_db,
):
    pa = _create_partner(client, auth_headers, "Partner A Aislamiento")
    pb = _create_partner(client, auth_headers, "Partner B Aislamiento")
    client.post(f"/api/partners/{pa['id']}/estado", headers=auth_headers, json={"estado": "ACTIVO"})
    client.post(f"/api/partners/{pb['id']}/estado", headers=auth_headers, json={"estado": "ACTIVO"})

    org_a = _create_org(partners_db, "Org Solo A")
    org_b = _create_org(partners_db, "Org Solo B")
    partners_db.commit()

    client.post(
        f"/api/partners/{pa['id']}/organizaciones",
        headers=auth_headers,
        json={"organization_id": org_a.id, "alcance": ["organizacion.read"]},
    )
    client.post(
        f"/api/partners/{pb['id']}/organizaciones",
        headers=auth_headers,
        json={"organization_id": org_b.id, "alcance": ["organizacion.read"]},
    )

    user_a = _create_user(partners_db, org_a, f"pa_user_{uuid.uuid4().hex[:6]}")
    partners_db.add(
        PartnerUserMembership(partner_id=pa["id"], user_id=user_a.id, rol="OPERADOR", is_active=True)
    )
    partners_db.commit()

    headers_a = _login(client, user_a.username)

    ok = client.get(
        f"/api/partners/{pa['id']}/organizaciones/{org_a.id}/contexto",
        headers=headers_a,
    )
    assert ok.status_code == 200

    denied = client.get(
        f"/api/partners/{pa['id']}/organizaciones/{org_b.id}/contexto",
        headers=headers_a,
    )
    assert denied.status_code == 403

    cross_partner = client.get(
        f"/api/partners/{pb['id']}/organizaciones/{org_b.id}/contexto",
        headers=headers_a,
    )
    assert cross_partner.status_code == 403


def test_mb03_sin_grant_no_accede(client: TestClient, auth_headers, partners_db):
    p = _create_partner(client, auth_headers, "Partner Sin Grant")
    client.post(f"/api/partners/{p['id']}/estado", headers=auth_headers, json={"estado": "ACTIVO"})

    org = _create_org(partners_db, "Org No Asignada")
    user = _create_user(partners_db, org, f"nopartner_{uuid.uuid4().hex[:6]}")
    partners_db.add(
        PartnerUserMembership(partner_id=p["id"], user_id=user.id, rol="OPERADOR", is_active=True)
    )
    partners_db.commit()

    headers_u = _login(client, user.username)
    res = client.get(
        f"/api/partners/{p['id']}/organizaciones/{org.id}/contexto",
        headers=headers_u,
    )
    assert res.status_code == 403


def test_mb03_revocacion_efectiva(client: TestClient, auth_headers, partners_db):
    p = _create_partner(client, auth_headers, "Partner Revocacion")
    client.post(f"/api/partners/{p['id']}/estado", headers=auth_headers, json={"estado": "ACTIVO"})

    org = _create_org(partners_db, "Org Revocable")
    user = _create_user(partners_db, org, f"rev_{uuid.uuid4().hex[:6]}")
    partners_db.commit()

    grant_res = client.post(
        f"/api/partners/{p['id']}/organizaciones",
        headers=auth_headers,
        json={"organization_id": org.id, "alcance": ["organizacion.read"]},
    )
    grant_id = grant_res.json()["id"]

    partners_db.add(
        PartnerUserMembership(partner_id=p["id"], user_id=user.id, rol="OPERADOR", is_active=True)
    )
    partners_db.commit()
    headers_u = _login(client, user.username)

    assert client.get(
        f"/api/partners/{p['id']}/organizaciones/{org.id}/contexto",
        headers=headers_u,
    ).status_code == 200

    revoke = client.post(
        f"/api/partners/{p['id']}/organizaciones/{grant_id}/revocar",
        headers=auth_headers,
    )
    assert revoke.status_code == 200
    assert revoke.json()["estado"] == "REVOCADO"

    denied = client.get(
        f"/api/partners/{p['id']}/organizaciones/{org.id}/contexto",
        headers=headers_u,
    )
    assert denied.status_code == 403


def test_mb03_manipulacion_api_partner_id_incorrecto(client: TestClient, auth_headers, partners_db):
    pa = _create_partner(client, auth_headers, "Manip A")
    pb = _create_partner(client, auth_headers, "Manip B")
    client.post(f"/api/partners/{pa['id']}/estado", headers=auth_headers, json={"estado": "ACTIVO"})
    client.post(f"/api/partners/{pb['id']}/estado", headers=auth_headers, json={"estado": "ACTIVO"})

    org = _create_org(partners_db, "Org Manip")
    partners_db.commit()

    grant_b = client.post(
        f"/api/partners/{pb['id']}/organizaciones",
        headers=auth_headers,
        json={"organization_id": org.id, "alcance": ["organizacion.read"]},
    ).json()

    # Intentar revocar grant de B usando partner A
    res = client.post(
        f"/api/partners/{pa['id']}/organizaciones/{grant_b['id']}/revocar",
        headers=auth_headers,
    )
    assert res.status_code == 404


def test_mb03_rbac_sin_permiso_manage(client: TestClient, auth_headers, partners_db):
    org = _create_org(partners_db, "Org RBAC")
    viewer = _create_user(partners_db, org, f"viewer_{uuid.uuid4().hex[:6]}")
    partners_db.commit()

    headers_v = _login(client, viewer.username)
    res = client.post(
        "/api/partners",
        headers=headers_v,
        json={"nombre": "No Autorizado"},
    )
    assert res.status_code == 403


def test_mb03_asignar_usuario_y_listar(client: TestClient, auth_headers, partners_db):
    p = _create_partner(client, auth_headers, "Partner Usuarios")
    org = _create_org(partners_db, "Org Usuarios Partner")
    user = _create_user(partners_db, org, f"member_{uuid.uuid4().hex[:6]}")
    partners_db.commit()

    assign = client.post(
        f"/api/partners/{p['id']}/usuarios",
        headers=auth_headers,
        json={"user_id": user.id, "rol": "LECTOR"},
    )
    assert assign.status_code == 201
    assert assign.json()["rol"] == "LECTOR"

    detail = client.get(f"/api/partners/{p['id']}", headers=auth_headers)
    assert detail.status_code == 200
    user_ids = [u["user_id"] for u in detail.json()["usuarios"]]
    assert user.id in user_ids


def test_mb03_recorrido_e2e_operativo(client: TestClient, auth_headers, partners_db):
    """Recorrido: crear → activar → asociar org → asignar usuario → conceder alcance → revocar."""
    p = _create_partner(client, auth_headers, "Partner E2E")
    pid = p["id"]

    client.post(f"/api/partners/{pid}/estado", headers=auth_headers, json={"estado": "ACTIVO"})

    org1 = _create_org(partners_db, "E2E Org 1")
    org2 = _create_org(partners_db, "E2E Org 2")
    op = _create_user(partners_db, org1, f"e2e_op_{uuid.uuid4().hex[:6]}")
    partners_db.commit()

    g1 = client.post(
        f"/api/partners/{pid}/organizaciones",
        headers=auth_headers,
        json={"organization_id": org1.id, "alcance": ["organizacion.read"]},
    ).json()
    g2 = client.post(
        f"/api/partners/{pid}/organizaciones",
        headers=auth_headers,
        json={"organization_id": org2.id, "alcance": ["organizacion.read", "trabajo.view"]},
    ).json()

    client.post(
        f"/api/partners/{pid}/usuarios",
        headers=auth_headers,
        json={"user_id": op.id, "rol": "OPERADOR"},
    )

    upd = client.patch(
        f"/api/partners/{pid}/organizaciones/{g2['id']}/alcance",
        headers=auth_headers,
        json={"alcance": ["organizacion.read", "cc.view", "trabajo.view"]},
    )
    assert upd.status_code == 200
    assert "cc.view" in upd.json()["alcance"]

    headers_op = _login(client, op.username)
    mis = client.get(f"/api/partners/{pid}/mis-organizaciones", headers=headers_op)
    assert mis.status_code == 200
    assert mis.json()["total"] == 2

    client.post(f"/api/partners/{pid}/organizaciones/{g1['id']}/revocar", headers=auth_headers)
    grant_db = partners_db.query(PartnerOrganizationGrant).filter(PartnerOrganizationGrant.id == g1["id"]).one()
    assert grant_db.estado == "REVOCADO"

    list_res = client.get("/api/partners", headers=auth_headers)
    assert list_res.status_code == 200
    assert list_res.json()["total"] >= 1
