"""Sala temporal para demostración comercial en dos dispositivos."""
from __future__ import annotations

import json
import os
import secrets
import threading
from pathlib import Path
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.deps import get_current_user
from app.models import User
from app.database import get_db
from app.config import DATA_DIR
from sqlalchemy.orm import Session
from app.services import communications_service as comm_svc


_PUBLIC_URL_FILE = DATA_DIR.parent / "runtime" / "eiaax_public_url.txt"


def _manager_public_base() -> str:
    """Devuelve exclusivamente una base publica utilizable por un invitado remoto."""
    configured = os.getenv("EIIAX_PUBLIC_URL", "").strip().rstrip("/")
    if configured.startswith("https://") and "127.0.0.1" not in configured and "localhost" not in configured.lower():
        return configured

    try:
        persisted = _PUBLIC_URL_FILE.read_text(encoding="utf-8").strip().rstrip("/")
    except OSError:
        persisted = ""
    if persisted.startswith("https://") and "trycloudflare.com" in persisted.lower():
        return persisted

    raise HTTPException(
        503,
        "Acceso remoto no disponible. Inicie EIIAX con ARRANCAR.bat y espere a que muestre EIIAX REMOTO LISTO.",
    )


router = APIRouter(prefix="/api/reunion-demo", tags=["reunion-demo"])
_LOCK = threading.RLock()
_ROOMS: dict[str, dict] = {}
_ROOM_STORE = DATA_DIR / "demo_rooms.json"
if os.getenv("EIIAX_DEMO_ROOM_STORE"):
    _ROOM_STORE = Path(os.environ["EIIAX_DEMO_ROOM_STORE"])


def _serialize_room(room: dict) -> dict:
    data = dict(room)
    for key in ("created_at", "expires_at"):
        if isinstance(data.get(key), datetime):
            data[key] = data[key].isoformat()
    return data


def _persist_rooms() -> None:
    _ROOM_STORE.parent.mkdir(parents=True, exist_ok=True)
    tmp = _ROOM_STORE.with_suffix(".tmp")
    tmp.write_text(json.dumps({k: _serialize_room(v) for k, v in _ROOMS.items()}, ensure_ascii=False), encoding="utf-8")
    tmp.replace(_ROOM_STORE)


def _load_rooms() -> None:
    if not _ROOM_STORE.exists():
        return
    try:
        raw = json.loads(_ROOM_STORE.read_text(encoding="utf-8"))
        now = datetime.now(timezone.utc)
        changed = False
        for code, room in raw.items():
            for key in ("created_at", "expires_at"):
                if isinstance(room.get(key), str):
                    room[key] = datetime.fromisoformat(room[key])
            if not room.get("expires_at") or room["expires_at"] <= now:
                changed = True
                continue
            _ROOMS[code] = room
        if changed:
            _persist_rooms()
    except (OSError, ValueError, TypeError):
        return


_load_rooms()

class SalaCreate(BaseModel):
    expediente_id: str
    tema: str = "facturacion"
    proposito: str = "DEMO_INTEGRAL"

class SalaInvite(BaseModel):
    email: str = Field(..., min_length=5, max_length=254)
    nombre: str = Field("Gerencia", max_length=120)

class SalaUpdate(BaseModel):
    tema: str | None = None
    visible: dict | None = None
    estado: str | None = None

class GuestAction(BaseModel):
    accion: str = Field(..., min_length=2, max_length=80)
    tema: str = Field("", max_length=120)
    detalle: str = Field("", max_length=500)

PUBLIC_ROOM_FIELDS = {
    "codigo", "expediente_id", "tema", "proposito", "estado",
    "visible", "revision", "created_at", "expires_at", "intereses",
}
PUBLIC_VISIBLE_FIELDS = {"titulo", "subtitulo", "contenido", "respuesta", "nota", "tipo", "compromisos", "nivel", "metodologia"}


COMMITMENT_FIELDS = {"responsable", "descripcion", "evidencia", "estado", "fecha", "beneficio"}


def _sanitize_visible(value: dict | None) -> dict | None:
    if not isinstance(value, dict):
        return None
    result = {k: value[k] for k in PUBLIC_VISIBLE_FIELDS if k in value and k != "compromisos"}
    if isinstance(value.get("compromisos"), list):
        result["compromisos"] = [
            {k: item[k] for k in COMMITMENT_FIELDS if k in item}
            for item in value["compromisos"] if isinstance(item, dict)
        ]
    return result


def _public(room: dict) -> dict:
    result = {k: room[k] for k in PUBLIC_ROOM_FIELDS if k in room}
    result["visible"] = _sanitize_visible(room.get("visible"))
    return result

def _get(code: str) -> dict:
    with _LOCK:
        room = _ROOMS.get(code.upper())
        if not room or datetime.now(timezone.utc) > room["expires_at"]:
            if room:
                _ROOMS.pop(code.upper(), None)
                _persist_rooms()
            raise HTTPException(404, "Sala no disponible o vencida")
        return room

@router.post("/salas")
def crear_sala(body: SalaCreate, user: User = Depends(get_current_user)):
    public_url = _manager_public_base()
    code = secrets.token_hex(3).upper()
    token = secrets.token_urlsafe(24)
    now = datetime.now(timezone.utc)
    room = {"codigo": code, "token": token, "expediente_id": body.expediente_id,
            "tema": body.tema, "proposito": body.proposito, "estado": "ABIERTA",
            "visible": None, "intereses": [], "revision": 1, "created_at": now, "expires_at": now + timedelta(hours=4),
            "organization_id": user.organization_id, "operator_id": user.id}
    with _LOCK:
        _ROOMS[code] = room
        _persist_rooms()
    result = {**_public(room), "guest_token": token}
    result["guest_url"] = f"{public_url}/sala-demo/{code}?token={token}"
    return result

@router.patch("/salas/{code}")
def actualizar_sala(code: str, body: SalaUpdate, user: User = Depends(get_current_user)):
    room = _get(code)
    if room["organization_id"] != user.organization_id: raise HTTPException(403, "Sala de otra organización")
    with _LOCK:
        for key in ("tema", "visible", "estado"):
            value = getattr(body, key)
            if value is not None:
                room[key] = _sanitize_visible(value) if key == "visible" else value
        room["revision"] += 1
        _persist_rooms()
    result = _public(room)
    result["guest_token"] = room["token"]
    try:
        result["guest_url"] = f"{_manager_public_base()}/sala-demo/{room['codigo']}?token={room['token']}"
    except HTTPException:
        result["guest_url"] = None
    return result

@router.get("/sala/{code}")
def ver_sala_publica(code: str, token: str):
    room = _get(code)
    if not secrets.compare_digest(token, room["token"]): raise HTTPException(403, "Enlace de sala inválido")
    return _public(room)


@router.post("/salas/{code}/invitar")
def invitar_sala(code: str, body: SalaInvite, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    room = _get(code)
    if room["organization_id"] != user.organization_id: raise HTTPException(403, "Sala de otra organización")
    base = _manager_public_base()
    link = f"{base}/sala-demo/{room['codigo']}?token={room['token']}"
    subject = "EIIAX | Invitación a demostración ejecutiva"
    text = f"Hola {body.nombre},\n\nHa sido invitado a una demostración ejecutiva de EIIAX.\n\nDurante la reunión podrá ver, en tiempo real, los temas que el presentador comparta y las respuestas de ELIA que se decida publicar. Los datos utilizados son ficticios y demostrativos.\n\nIngresar a la sala: {link}\n\nEl enlace es temporal y no da acceso al Centro de Control ni al espacio de evaluación.\n\nEIIAX"
    result = comm_svc.send_direct_email(db, user.organization_id, destinatario=body.email.strip(), asunto=subject, contenido=text)
    if result.get("estado") != "ENVIADA": raise HTTPException(503, result.get("detalle") or "No se pudo enviar")
    return {"estado":"ENVIADA","email":body.email.strip(),"codigo":room["codigo"]}


@router.post("/sala/{code}/interes")
def registrar_interes_publico(code: str, body: GuestAction, token: str):
    room = _get(code)
    if not secrets.compare_digest(token, room["token"]):
        raise HTTPException(403, "Enlace de sala inválido")
    item = {
        "accion": body.accion,
        "tema": body.tema,
        "detalle": body.detalle,
        "fecha": datetime.now(timezone.utc).isoformat(),
    }
    with _LOCK:
        room.setdefault("intereses", []).append(item)
        room["intereses"] = room["intereses"][-20:]
        room["revision"] += 1
        _persist_rooms()
    return {"estado": "REGISTRADO", "interes": item, "revision": room["revision"]}


@router.get("/salas/{code}")
def ver_sala_presentador(code: str, user: User = Depends(get_current_user)):
    room = _get(code)
    if room["organization_id"] != user.organization_id:
        raise HTTPException(403, "Sala de otra organización")
    result = _public(room)
    result["guest_token"] = room["token"]
    try:
        result["guest_url"] = f"{_manager_public_base()}/sala-demo/{room['codigo']}?token={room['token']}"
    except HTTPException:
        result["guest_url"] = None
    return result
