"""Contrato API para vistas de aprendizaje, optimización y multiproveedor."""

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


def _create_tenant(db: Session, *, role: str = "admin") -> tuple[Organization, User, str]:
    from app.seed_orchestration import bootstrap_orchestration
    from app.seed_permissions import bootstrap_permissions
    from app.seed_salud import bootstrap_salud

    org = Organization(name=f"Org {uuid.uuid4().hex[:6]}", slug=f"v-{uuid.uuid4().hex[:8]}")
    db.add(org)
    db.flush()
    bootstrap_permissions(db)
    bootstrap_orchestration(db, org.id)
    bootstrap_salud(db, org.id)
    password = "VistasAO*Test1"
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
    return org, user, password


def test_vistas_aprendizaje_list_contract(client: TestClient):
    db = TestingSessionLocal()
    try:
        _, user, pwd = _create_tenant(db)
        token = _token(client, user.username, pwd)
        res = client.get("/api/aprendizaje/ciclos", headers=auth_header(token))
        assert res.status_code == 200
        assert isinstance(res.json(), list)
    finally:
        db.close()


def test_vistas_aprendizaje_recalibraciones_contract(client: TestClient):
    db = TestingSessionLocal()
    try:
        _, user, pwd = _create_tenant(db)
        token = _token(client, user.username, pwd)
        res = client.get("/api/aprendizaje/recalibraciones", headers=auth_header(token))
        assert res.status_code == 200
        assert isinstance(res.json(), list)
    finally:
        db.close()


def test_vistas_optimizacion_recomendaciones_contract(client: TestClient):
    db = TestingSessionLocal()
    try:
        _, user, pwd = _create_tenant(db)
        token = _token(client, user.username, pwd)
        res = client.get("/api/optimizacion/recomendaciones", headers=auth_header(token))
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        if data:
            assert "estado" in data[0]
            assert "codigo" in data[0]
    finally:
        db.close()


def test_vistas_llm_providers_contract(client: TestClient):
    db = TestingSessionLocal()
    try:
        _, user, pwd = _create_tenant(db)
        token = _token(client, user.username, pwd)
        res = client.get("/api/llm/providers", headers=auth_header(token))
        assert res.status_code == 200
        assert isinstance(res.json(), list)
    finally:
        db.close()


def test_vistas_llm_observability_contract(client: TestClient):
    db = TestingSessionLocal()
    try:
        _, user, pwd = _create_tenant(db)
        token = _token(client, user.username, pwd)
        res = client.get("/api/llm/observability?periodo=7d", headers=auth_header(token))
        assert res.status_code == 200
        body = res.json()
        assert "total_inferencias" in body
        assert "por_proveedor" in body
    finally:
        db.close()


def test_vistas_llm_secrets_masked(client: TestClient):
    db = TestingSessionLocal()
    try:
        _, user, pwd = _create_tenant(db)
        token = _token(client, user.username, pwd)
        res = client.get("/api/llm/providers", headers=auth_header(token))
        assert res.status_code == 200
        for p in res.json():
            assert "secret_ref" not in p or p.get("secret_ref") is None or "***" in str(p.get("secret_masked", ""))
            raw = str(p)
            assert "sk-" not in raw
            assert "api_key" not in raw.lower() or "secret_" in raw.lower()
    finally:
        db.close()


def test_vistas_multiempresa_aprendizaje_aislado(client: TestClient):
    db = TestingSessionLocal()
    try:
        org_a, user_a, pwd_a = _create_tenant(db)
        org_b, user_b, pwd_b = _create_tenant(db)
        token_a = _token(client, user_a.username, pwd_a)
        token_b = _token(client, user_b.username, pwd_b)
        res_a = client.get("/api/aprendizaje/ciclos", headers=auth_header(token_a))
        res_b = client.get("/api/aprendizaje/ciclos", headers=auth_header(token_b))
        assert res_a.status_code == 200
        assert res_b.status_code == 200
        for c in res_a.json():
            assert c.get("organization_id", org_a.id) == org_a.id
    finally:
        db.close()
