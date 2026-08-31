"""NX05 — Protección knowledge auth V1: descarga exige Authorization."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from conftest import auth_header

pytestmark = [pytest.mark.auth, pytest.mark.tenant]

KNOWLEDGE_ROUTER = Path(__file__).resolve().parents[1] / "backend" / "app" / "routers" / "knowledge.py"


def test_nx05_knowledge_download_requires_authorization(client: TestClient, token: str):
    created = client.post(
        "/api/knowledge/text",
        headers=auth_header(token),
        json={"name": "NX05 doc", "content": "contenido protegido nx05"},
    )
    assert created.status_code == 201
    doc_id = created.json()["id"]

    without_auth = client.get(f"/api/knowledge/{doc_id}/download")
    assert without_auth.status_code == 401

    with_auth = client.get(f"/api/knowledge/{doc_id}/download", headers=auth_header(token))
    assert with_auth.status_code == 200
    assert b"nx05" in with_auth.content.lower()


def test_nx05_knowledge_router_contract_requires_current_user():
    """Contrato API: endpoint download depende de autenticación (grep estático)."""
    src = KNOWLEDGE_ROUTER.read_text(encoding="utf-8")
    assert "/download" in src
    assert "get_current_user" in src or "Depends(get_current_user)" in src
