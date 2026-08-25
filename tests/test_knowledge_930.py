"""Tests CONOCIMIENTO-930 — Centro de Conocimiento."""
import io
import json
import uuid
import zipfile

import pytest

from app.models import Organization, User
from app.security import hash_password
from conftest import TestingSessionLocal, auth_header


def _create_org_user(client, org_name: str, username: str, password: str, role: str = "admin") -> str:
    db = TestingSessionLocal()
    org = Organization(name=org_name)
    db.add(org)
    db.flush()
    db.add(User(organization_id=org.id, username=username, password_hash=hash_password(password), role=role))
    db.commit()
    db.close()
    login = client.post("/api/auth/login", json={"username": username, "password": password})
    assert login.status_code == 200
    return login.json()["access_token"]


def _create_text_doc(client, token: str, name: str, content: str):
    return client.post(
        "/api/knowledge/text",
        headers=auth_header(token),
        json={"name": name, "content": content, "metadata": {"area": "operaciones"}},
    )


def test_create_text_document(client, token):
    res = _create_text_doc(client, token, "Manual operativo", "Contenido de prueba para conocimiento empresarial.")
    assert res.status_code == 201
    body = res.json()
    assert body["name"] == "Manual operativo"
    assert body["status"] == "AVAILABLE"
    assert body["metadata"]["area"] == "operaciones"


def test_upload_txt_file(client, token, tmp_path):
    content = b"Linea uno\nLinea dos"
    files = {"file": ("notas.txt", io.BytesIO(content), "text/plain")}
    res = client.post("/api/knowledge/upload", headers=auth_header(token), files=files)
    assert res.status_code == 201
    assert res.json()["file_type"] == "txt"


def test_invalid_format_rejected(client, token):
    files = {"file": ("mal.exe", io.BytesIO(b"data"), "application/octet-stream")}
    res = client.post("/api/knowledge/upload", headers=auth_header(token), files=files)
    assert res.status_code == 400


def test_empty_file_rejected(client, token):
    res = client.post(
        "/api/knowledge/text",
        headers=auth_header(token),
        json={"name": "Vacio", "content": "   "},
    )
    assert res.status_code == 400


def test_list_and_detail(client, token):
    created = _create_text_doc(client, token, "Listado", "Texto listado").json()
    listed = client.get("/api/knowledge", headers=auth_header(token))
    assert listed.status_code == 200
    assert any(row["id"] == created["id"] for row in listed.json())
    detail = client.get(f"/api/knowledge/{created['id']}", headers=auth_header(token))
    assert detail.status_code == 200
    assert detail.json()["chunks_count"] >= 1


def test_partial_update_preserves_metadata(client, token):
    created = _create_text_doc(client, token, "Parcial", "Contenido parcial").json()
    patched = client.patch(
        f"/api/knowledge/{created['id']}",
        headers=auth_header(token),
        json={"name": "Parcial actualizado"},
    )
    assert patched.status_code == 200
    body = patched.json()
    assert body["name"] == "Parcial actualizado"
    assert body["metadata"]["area"] == "operaciones"


def test_process_and_reprocess(client, token):
    created = _create_text_doc(client, token, "Proceso", "Texto para reprocesar.").json()
    repro = client.post(f"/api/knowledge/{created['id']}/reprocess", headers=auth_header(token))
    assert repro.status_code == 200
    assert repro.json()["status"] == "AVAILABLE"


def test_search_and_retrieve(client, token):
    _create_text_doc(client, token, "Politica seguridad", "La contraseña debe rotarse cada 90 días.")
    search = client.get("/api/knowledge/search", headers=auth_header(token), params={"q": "contraseña"})
    assert search.status_code == 200
    assert len(search.json()) >= 1
    retrieve = client.post(
        "/api/knowledge/retrieve",
        headers=auth_header(token),
        json={"query": "contraseña", "limit": 5},
    )
    assert retrieve.status_code == 200
    assert len(retrieve.json()) >= 1


def test_download_and_delete(client, token):
    created = _create_text_doc(client, token, "Descargable", "Contenido descargable").json()
    download = client.get(f"/api/knowledge/{created['id']}/download", headers=auth_header(token))
    assert download.status_code == 200
    assert b"descargable" in download.content.lower()
    deleted = client.delete(f"/api/knowledge/{created['id']}", headers=auth_header(token))
    assert deleted.status_code == 204
    missing = client.get(f"/api/knowledge/{created['id']}", headers=auth_header(token))
    assert missing.status_code == 404


def test_tenant_isolation(client):
    token_a = _create_org_user(client, "Org A 930", f"a-{uuid.uuid4().hex[:6]}", "AdminA930*")
    token_b = _create_org_user(client, "Org B 930", f"b-{uuid.uuid4().hex[:6]}", "AdminB930*")
    doc = _create_text_doc(client, token_a, "Privado A", "Solo org A").json()
    cross = client.get(f"/api/knowledge/{doc['id']}", headers=auth_header(token_b))
    assert cross.status_code == 404


def test_viewer_cannot_upload(client, token):
    viewer_token = _create_org_user(client, "Org Viewer 930", f"v-{uuid.uuid4().hex[:6]}", "Viewer930*", role="viewer")
    res = client.post(
        "/api/knowledge/text",
        headers=auth_header(viewer_token),
        json={"name": "No permitido", "content": "x"},
    )
    assert res.status_code == 403


def test_admin_can_delete_viewer_cannot(client, token):
    created = _create_text_doc(client, token, "Borrar", "contenido").json()
    viewer_token = _create_org_user(client, "Org Viewer Del 930", f"vd-{uuid.uuid4().hex[:6]}", "ViewerDel930*", role="viewer")
    denied = client.delete(f"/api/knowledge/{created['id']}", headers=auth_header(viewer_token))
    assert denied.status_code == 403
    allowed = client.delete(f"/api/knowledge/{created['id']}", headers=auth_header(token))
    assert allowed.status_code == 204


def test_path_traversal_filename_normalized(client, token):
    files = {"file": ("../../etc/passwd.txt", io.BytesIO(b"seguro"), "text/plain")}
    res = client.post("/api/knowledge/upload", headers=auth_header(token), files=files)
    assert res.status_code == 201
    assert ".." not in (res.json().get("original_filename") or "")


def test_docx_extraction(client, token):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(
            "word/document.xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            "<w:body><w:p><w:r><w:t>Hola DOCX</w:t></w:r></w:p></w:body></w:document>",
        )
    files = {"file": ("prueba.docx", io.BytesIO(buffer.getvalue()), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    res = client.post("/api/knowledge/upload", headers=auth_header(token), files=files)
    assert res.status_code == 201
    detail = client.get(f"/api/knowledge/{res.json()['id']}", headers=auth_header(token)).json()
    assert "Hola DOCX" in (detail.get("processed_content") or "")


def test_employee_grant_contract(client, token):
    doc = _create_text_doc(client, token, "Grant", "contenido empleado").json()
    emp = client.post(
        "/api/agent-factory/employees",
        headers=auth_header(token),
        json={"name": "Empleado conocimiento", "specialty": "DOCINT"},
    ).json()
    grant = client.post(
        f"/api/knowledge/employees/{emp['id']}/grant/{doc['id']}",
        headers=auth_header(token),
    )
    assert grant.status_code == 200
    listed = client.get(f"/api/knowledge/employees/{emp['id']}/grants", headers=auth_header(token))
    assert listed.status_code == 200
    assert listed.json()[0]["document_id"] == doc["id"]
    retrieve = client.post(
        "/api/knowledge/retrieve",
        headers=auth_header(token),
        json={"query": "contenido", "employee_id": emp["id"], "limit": 5},
    )
    assert retrieve.status_code == 200
    assert len(retrieve.json()) >= 1


def test_activity_logged(client, token):
    created = _create_text_doc(client, token, "Actividad", "registro actividad").json()
    activity = client.get(f"/api/knowledge/{created['id']}/activity", headers=auth_header(token))
    assert activity.status_code == 200
    actions = {row["action"] for row in activity.json()}
    assert "CARGA" in actions
    assert "PROCESAMIENTO" in actions
