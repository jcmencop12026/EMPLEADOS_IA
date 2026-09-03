"""Evidencias/adjuntos — espacio externo V1c."""

from __future__ import annotations

import io
import uuid

import pytest
from fastapi.testclient import TestClient

from conftest import auth_header
from tests.test_espacio_externo_v1 import _create_expediente, _setup_entidad_y_externo

pytestmark = [pytest.mark.tenant, pytest.mark.evaluacion]

SAMPLE_TXT = b"Evidencia de prueba para evaluacion empresarial."


def _sync_informacion(client: TestClient, auth_headers: dict[str, str], exp_id: str) -> str:
    client.post(f"/api/evaluaciones/{exp_id}/informacion/sync", headers=auth_headers)
    detail = client.get(f"/api/evaluaciones/{exp_id}", headers=auth_headers).json()
    return detail["informacion"][0]["id"]


def test_carga_adjunto_valida(client: TestClient, auth_headers):
    exp, _ent, ext_headers, _eid = _setup_entidad_y_externo(client, auth_headers)
    item_id = _sync_informacion(client, auth_headers, exp["id"])
    res = client.post(
        "/api/espacio-externo/mi-espacio/adjuntos",
        headers=ext_headers,
        data={"item_id": item_id, "observacion": "Adjunto inicial"},
        files=[("files", ("evidencia.txt", io.BytesIO(SAMPLE_TXT), "text/plain"))],
    )
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["adjuntos"][0]["nombre"] == "evidencia.txt"
    assert body["adjuntos"][0]["version"] == 1
    assert "storage_key" not in body["adjuntos"][0]


def test_multiples_archivos(client: TestClient, auth_headers):
    exp, _ent, ext_headers, _eid = _setup_entidad_y_externo(client, auth_headers)
    item_id = _sync_informacion(client, auth_headers, exp["id"])
    res = client.post(
        "/api/espacio-externo/mi-espacio/adjuntos",
        headers=ext_headers,
        data={"item_id": item_id},
        files=[
            ("files", ("a.txt", io.BytesIO(b"archivo a"), "text/plain")),
            ("files", ("b.txt", io.BytesIO(b"archivo b"), "text/plain")),
        ],
    )
    assert res.status_code == 201
    assert len(res.json()["adjuntos"]) == 2


def test_reemplazo_versionado(client: TestClient, auth_headers):
    exp, _ent, ext_headers, _eid = _setup_entidad_y_externo(client, auth_headers)
    item_id = _sync_informacion(client, auth_headers, exp["id"])
    up = client.post(
        "/api/espacio-externo/mi-espacio/adjuntos",
        headers=ext_headers,
        data={"item_id": item_id},
        files=[("files", ("doc.txt", io.BytesIO(b"v1"), "text/plain"))],
    ).json()
    adjunto_id = up["adjuntos"][0]["id"]
    entrega_id = up["entrega_id"]
    rep = client.post(
        f"/api/espacio-externo/mi-espacio/adjuntos/{adjunto_id}/reemplazar",
        headers=ext_headers,
        data={"observacion": "Version 2"},
        files=[("file", ("doc.txt", io.BytesIO(b"v2"), "text/plain"))],
    )
    assert rep.status_code == 201
    assert rep.json()["version"] == 2
    hist = client.get(
        f"/api/espacio-externo/adjuntos/historial/{up['adjuntos'][0]['grupo_archivo']}",
        headers=auth_headers,
    )
    assert hist.status_code == 200
    assert len(hist.json()) == 2
    lista = client.get(f"/api/espacio-externo/entregas/{entrega_id}/adjuntos", headers=auth_headers)
    assert lista.json()[0]["version"] == 2


def test_descarga_autorizada(client: TestClient, auth_headers):
    exp, _ent, ext_headers, _eid = _setup_entidad_y_externo(client, auth_headers)
    item_id = _sync_informacion(client, auth_headers, exp["id"])
    up = client.post(
        "/api/espacio-externo/mi-espacio/adjuntos",
        headers=ext_headers,
        data={"item_id": item_id},
        files=[("files", ("seguro.txt", io.BytesIO(SAMPLE_TXT), "text/plain"))],
    ).json()
    adjunto_id = up["adjuntos"][0]["id"]
    dl = client.get(f"/api/espacio-externo/mi-espacio/adjuntos/{adjunto_id}/descarga", headers=ext_headers)
    assert dl.status_code == 200
    assert dl.content == SAMPLE_TXT
    assert "evidence/" not in dl.headers.get("content-disposition", "")


def test_descarga_denegada_otro_tenant(client: TestClient, auth_headers):
    from app.models import Organization, User
    from app.security import hash_password
    from conftest import TestingSessionLocal

    exp, _ent, ext_headers, _eid = _setup_entidad_y_externo(client, auth_headers)
    item_id = _sync_informacion(client, auth_headers, exp["id"])
    up = client.post(
        "/api/espacio-externo/mi-espacio/adjuntos",
        headers=ext_headers,
        data={"item_id": item_id},
        files=[("files", ("privado.txt", io.BytesIO(SAMPLE_TXT), "text/plain"))],
    ).json()
    adjunto_id = up["adjuntos"][0]["id"]

    db = TestingSessionLocal()
    try:
        other_org = Organization(name="Org B", slug=f"b-{uuid.uuid4().hex[:6]}", status="ACTIVE")
        db.add(other_org)
        db.flush()
        other = User(
            organization_id=other_org.id,
            username=f"other-{uuid.uuid4().hex[:6]}",
            password_hash=hash_password("x"),
            role="admin",
            is_active=True,
        )
        db.add(other)
        db.commit()
        other_token = client.post("/api/auth/login", json={"username": other.username, "password": "x"}).json()["access_token"]
        other_headers = auth_header(other_token)
    finally:
        db.close()

    blocked = client.get(f"/api/espacio-externo/adjuntos/{adjunto_id}/descarga", headers=other_headers)
    assert blocked.status_code in (403, 404)


def test_usuario_revocado_no_descarga(client: TestClient, auth_headers):
    exp, ent, ext_headers, entidad_id = _setup_entidad_y_externo(client, auth_headers)
    item_id = _sync_informacion(client, auth_headers, exp["id"])
    up = client.post(
        "/api/espacio-externo/mi-espacio/adjuntos",
        headers=ext_headers,
        data={"item_id": item_id},
        files=[("files", ("x.txt", io.BytesIO(SAMPLE_TXT), "text/plain"))],
    ).json()
    adjunto_id = up["adjuntos"][0]["id"]
    acceso_id = client.get(f"/api/espacio-externo/entidades/{entidad_id}", headers=auth_headers).json()["accesos"][0]["id"]
    client.delete(f"/api/espacio-externo/accesos/{acceso_id}", headers=auth_headers)
    blocked = client.get(f"/api/espacio-externo/mi-espacio/adjuntos/{adjunto_id}/descarga", headers=ext_headers)
    assert blocked.status_code == 403


def test_complemento_y_validacion_interna(client: TestClient, auth_headers):
    exp, _ent, ext_headers, _eid = _setup_entidad_y_externo(client, auth_headers)
    item_id = _sync_informacion(client, auth_headers, exp["id"])
    up = client.post(
        "/api/espacio-externo/mi-espacio/adjuntos",
        headers=ext_headers,
        data={"item_id": item_id},
        files=[("files", ("req.txt", io.BytesIO(SAMPLE_TXT), "text/plain"))],
    ).json()
    entrega_id = up["entrega_id"]
    val = client.post(
        f"/api/espacio-externo/entregas/{entrega_id}/validar",
        headers=auth_headers,
        json={
            "estado": "REQUIERE_COMPLEMENTO",
            "observacion_publica": "Falta detalle financiero",
            "observacion_interna": "Nota interna no visible",
        },
    )
    assert val.status_code == 200
    assert val.json()["observacion_publica"] == "Falta detalle financiero"
    assert val.json()["observacion_interna"] == "Nota interna no visible"
    info = client.get("/api/espacio-externo/mi-espacio/informacion", headers=ext_headers).json()
    entrega = next(e for e in info["entregas"] if e["id"] == entrega_id)
    assert entrega["observacion_publica"] == "Falta detalle financiero"
    assert "observacion_interna" not in entrega


def test_formato_invalido(client: TestClient, auth_headers):
    exp, _ent, ext_headers, _eid = _setup_entidad_y_externo(client, auth_headers)
    item_id = _sync_informacion(client, auth_headers, exp["id"])
    res = client.post(
        "/api/espacio-externo/mi-espacio/adjuntos",
        headers=ext_headers,
        data={"item_id": item_id},
        files=[("files", ("malware.exe", io.BytesIO(b"MZ"), "application/octet-stream"))],
    )
    assert res.status_code == 422


def test_path_traversal_filename(client: TestClient, auth_headers):
    exp, _ent, ext_headers, _eid = _setup_entidad_y_externo(client, auth_headers)
    item_id = _sync_informacion(client, auth_headers, exp["id"])
    res = client.post(
        "/api/espacio-externo/mi-espacio/adjuntos",
        headers=ext_headers,
        data={"item_id": item_id},
        files=[("files", ("../../etc/passwd.txt", io.BytesIO(SAMPLE_TXT), "text/plain"))],
    )
    assert res.status_code == 201
    assert res.json()["adjuntos"][0]["nombre"] == "passwd.txt"


def test_vinculo_dossier_canonico(client: TestClient, auth_headers):
    from app.empresa_seguridad_models import EmpresaEvidenciaVinculo
    from conftest import TestingSessionLocal

    exp, _ent, ext_headers, _eid = _setup_entidad_y_externo(client, auth_headers)
    item_id = _sync_informacion(client, auth_headers, exp["id"])
    up = client.post(
        "/api/espacio-externo/mi-espacio/adjuntos",
        headers=ext_headers,
        data={"item_id": item_id},
        files=[("files", ("dossier.txt", io.BytesIO(SAMPLE_TXT), "text/plain"))],
    ).json()
    adjunto_id = up["adjuntos"][0]["id"]
    db = TestingSessionLocal()
    try:
        links = db.query(EmpresaEvidenciaVinculo).filter(EmpresaEvidenciaVinculo.referencia == adjunto_id).all()
        assert len(links) >= 1
        assert any(l.objeto_tipo == "expediente" for l in links)
    finally:
        db.close()
