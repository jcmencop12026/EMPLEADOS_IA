from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.routers import reunion_demo
from app.services import demo_reunion_copilot_service as copilot
from app.services import communications_service as communications


def test_copilot_catalog_has_six_domains():
    expected = {"facturacion", "glosas", "rrhh", "operaciones", "compras", "sistemas"}
    assert set(copilot.TOPIC_GUIDE) == expected
    assert set(copilot.TOPIC_ALIASES) == expected


@pytest.mark.parametrize("question,active,expected", [
    ("¿Qué glosas se repiten más?", "glosas", "glosas"),
    ("¿Dónde hay reprocesos y cuellos de botella?", "operaciones", "operaciones"),
    ("¿Qué riesgos de ciberseguridad tenemos?", "sistemas", "sistemas"),
    ("¿Cómo está la productividad del personal?", "rrhh", "rrhh"),
    ("¿Hay vencimientos de inventario?", "compras", "compras"),
    ("¿Qué cartera podemos recuperar?", "facturacion", "facturacion"),
])
def test_topic_detection_preserves_domain(question, active, expected):
    assert expected in copilot._topics(question, active)


def test_external_invite_requires_configured_public_url(monkeypatch):
    monkeypatch.delenv("EIIAX_PUBLIC_URL", raising=False)
    original = dict(reunion_demo._ROOMS)
    reunion_demo._ROOMS.clear()
    now = datetime.now(timezone.utc)
    reunion_demo._ROOMS["INV001"] = {"codigo":"INV001","token":"t","expires_at":now+timedelta(hours=1),"organization_id":"org1"}
    user = SimpleNamespace(id="u1", organization_id="org1")
    with pytest.raises(HTTPException) as exc:
        reunion_demo.invitar_sala("INV001", reunion_demo.SalaInvite(email="gerencia@example.com"), None, user)
    assert exc.value.status_code == 503
    reunion_demo._ROOMS.clear(); reunion_demo._ROOMS.update(original)


def test_room_create_update_public_and_token(tmp_path):
    original_store = reunion_demo._ROOM_STORE
    reunion_demo._ROOM_STORE = tmp_path / "rooms.json"
    reunion_demo._ROOMS.clear()
    user = SimpleNamespace(id="u1", organization_id="org1")
    created = reunion_demo.crear_sala(reunion_demo.SalaCreate(expediente_id="EVA-1", tema="glosas"), user)
    assert created["tema"] == "glosas"
    assert created["guest_token"]
    if created.get("guest_url"):
        assert "/sala-demo/" in created["guest_url"]
    assert "token" not in created and "organization_id" not in created and "operator_id" not in created
    code, token = created["codigo"], created["guest_token"]

    updated = reunion_demo.actualizar_sala(code, reunion_demo.SalaUpdate(
        tema="compras", visible={"titulo":"Compras", "private_strategy":"NO PUBLICAR"}
    ), user)
    assert updated["tema"] == "compras"
    assert updated["visible"] == {"titulo": "Compras"}
    assert "private_strategy" not in reunion_demo._ROOMS[code]["visible"]
    assert reunion_demo._ROOM_STORE.exists()
    public = reunion_demo.ver_sala_publica(code, token)
    assert public["tema"] == "compras"
    assert "token" not in public and "organization_id" not in public and "operator_id" not in public

    # Defensa en profundidad: aunque datos privados entren al estado interno,
    # la respuesta del invitado usa lista blanca y nunca los publica.
    reunion_demo._ROOMS[code]["private_strategy"] = "cobro táctico reservado"
    reunion_demo._ROOMS[code]["formula"] = "dato privado"
    reunion_demo._ROOMS[code]["visible"] = {
        "titulo": "Compras", "contenido": ["Dato publicable"],
        "private_strategy": "NO PUBLICAR", "formula": "NO PUBLICAR",
        "source_records": [1, 2, 3], "elia_private": "NO PUBLICAR",
    }
    public = reunion_demo.ver_sala_publica(code, token)
    assert public["visible"] == {"titulo": "Compras", "contenido": ["Dato publicable"]}
    serialized = repr(public)
    for secret in ("private_strategy", "formula", "source_records", "elia_private", "NO PUBLICAR"):
        assert secret not in serialized

    with pytest.raises(HTTPException) as exc:
        reunion_demo.ver_sala_publica(code, "token-invalido")
    assert exc.value.status_code == 403
    reunion_demo._ROOMS.clear()
    reunion_demo._ROOM_STORE = original_store
    reunion_demo._load_rooms()


def test_public_commitments_are_allowed_without_private_methodology():
    room = {
        "codigo": "SAFE01", "expediente_id": "EVA-1", "tema": "glosas",
        "proposito": "DEMO_INTEGRAL", "estado": "ABIERTA", "revision": 2,
        "created_at": datetime.now(timezone.utc),
        "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
        "token": "secret", "organization_id": "org1", "operator_id": "u1",
        "visible": {
            "titulo": "Compromisos de la IPS / Gerencia",
            "compromisos": [{"responsable": "IPS", "descripcion": "Entregar datos completos", "fecha":"Antes de línea base", "beneficio":"Habilita medición", "estado":"PROPUESTO", "estrategia_privada":"NO PUBLICAR"}],
            "nota": "Beneficio condicionado a validación real.",
            "metodologia_privada": "NO PUBLICAR",
        },
    }
    public = reunion_demo._public(room)
    assert public["visible"]["compromisos"][0]["responsable"] == "IPS"
    assert public["visible"]["compromisos"][0]["fecha"] == "Antes de línea base"
    assert public["visible"]["compromisos"][0]["beneficio"] == "Habilita medición"
    assert "estrategia_privada" not in public["visible"]["compromisos"][0]
    assert "metodologia_privada" not in public["visible"]
    assert "token" not in public
    answer = reunion_demo._sanitize_visible({"titulo":"ELIA", "respuesta":"Respuesta publicable", "elia_private":"NO"})
    assert answer == {"titulo":"ELIA", "respuesta":"Respuesta publicable"}


def test_room_store_survives_memory_reset(tmp_path):
    original_store = reunion_demo._ROOM_STORE
    try:
        reunion_demo._ROOM_STORE = tmp_path / "rooms.json"
        reunion_demo._ROOMS.clear()
        user = SimpleNamespace(id="u1", organization_id="org1")
        created = reunion_demo.crear_sala(reunion_demo.SalaCreate(expediente_id="EVA-PERSIST"), user)
        code, token = created["codigo"], created["guest_token"]
        assert reunion_demo._ROOM_STORE.exists()
        reunion_demo._ROOMS.clear()
        reunion_demo._load_rooms()
        restored = reunion_demo.ver_sala_publica(code, token)
        assert restored["expediente_id"] == "EVA-PERSIST"
        assert restored["revision"] == 1
    finally:
        reunion_demo._ROOMS.clear()
        reunion_demo._ROOM_STORE = original_store
        reunion_demo._load_rooms()


def test_expired_room_is_rejected():
    original = dict(reunion_demo._ROOMS)
    reunion_demo._ROOMS.clear()
    reunion_demo._ROOMS["ABC123"] = {"expires_at": datetime.now(timezone.utc)-timedelta(seconds=1)}
    with pytest.raises(HTTPException) as exc:
        reunion_demo._get("ABC123")
    assert exc.value.status_code == 404
    reunion_demo._ROOMS.clear()
    reunion_demo._ROOMS.update(original)


def test_email_transport_prefers_stable_smtp_when_app_password_exists(monkeypatch):
    monkeypatch.setenv("EIIAX_SMTP_APP_PASSWORD", "abcdefghijklmnop")
    cfg = communications._effective_email_config({
        "auth_mode": "gmail_api",
        "from_email": "proauditorx@gmail.com",
    })
    assert cfg["auth_mode"] == "password"
    assert cfg["smtp_host"] == "smtp.gmail.com"
    assert cfg["smtp_port"] == 587
    assert cfg["use_tls"] is True
    assert cfg["use_ssl"] is False
    assert cfg["smtp_secret_ref"] == "env:EIIAX_SMTP_APP_PASSWORD"
    assert "abcdefghijklmnop" not in repr(cfg)


def test_email_transport_preserves_legacy_channel_without_app_password(monkeypatch):
    monkeypatch.delenv("EIIAX_SMTP_APP_PASSWORD", raising=False)
    monkeypatch.setattr(communications, "secret_configured", lambda ref: False)
    original = {"auth_mode": "gmail_api", "from_email": "proauditorx@gmail.com"}
    assert communications._effective_email_config(original) == original


def test_elia_demo_answers_without_rebuilding_presentation():
    answer = copilot.answer_demo_question(
        None, "org-demo", "exp-demo",
        "¿Cuánto podríamos recuperar de la cartera y cuáles son las principales oportunidades?",
        "facturacion",
    )
    assert answer["respuesta"]
    assert "Ingresos, facturación y cartera" in answer["respuesta"]
    assert "SIMULADOS/ESTIMADOS" in answer["respuesta"]
    assert answer["modo"] == "DEMO"
    assert answer["requiere_datos_reales"] is True
