from datetime import datetime, timezone
from app.routers import reunion_demo


def test_public_room_never_exposes_internal_ids():
    room={"codigo":"ABC123","token":"secret","organization_id":"org","operator_id":"user","expediente_id":"exp","tema":"glosas","estado":"ABIERTA","revision":1,"expires_at":datetime.now(timezone.utc)}
    public=reunion_demo._public(room)
    assert "organization_id" not in public and "operator_id" not in public
    assert public["tema"] == "glosas"


def test_guest_token_is_never_exposed_publicly():
    room={"token":"abc","organization_id":"o","operator_id":"u"}
    assert "token" not in reunion_demo._public(room)


def test_public_url_fallback_is_external():
    fallback = "https://controversial-flowers-bible-erik.trycloudflare.com"
    assert fallback.startswith("https://") and "localhost" not in fallback
