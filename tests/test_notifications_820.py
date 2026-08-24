import uuid

from app.models import AuditLog, Notification, Organization, User
from app.notifications import emit_event
from app.security import hash_password
from conftest import TestingSessionLocal


def _event(name="TENANT_SECURITY_EVENT", organization_id=None, **payload):
    db = TestingSessionLocal()
    try:
        if not organization_id:
            organization_id = db.query(User).filter(User.username == "admin").one().organization_id
        return emit_event(name, organization_id, "test", str(uuid.uuid4()), payload, db)[0].id
    finally:
        db.close()


def test_create_list_unread_read_acknowledge_dismiss_and_audit(client, auth_headers):
    first = _event(message="Acceso inusual")
    second = _event("EXECUTION_FAILED", message="Falló el proceso")
    rows = client.get("/api/notifications?severity=CRITICAL", headers=auth_headers)
    assert rows.status_code == 200 and any(row["id"] == first for row in rows.json())
    count = client.get("/api/notifications/unread-count", headers=auth_headers)
    assert count.status_code == 200 and count.json()["count"] >= 2
    assert client.post(f"/api/notifications/{first}/read", headers=auth_headers).json()["status"] == "READ"
    acknowledged = client.post(f"/api/notifications/{second}/acknowledge", headers=auth_headers)
    assert acknowledged.status_code == 200 and acknowledged.json()["acknowledged_at"]
    assert client.post(f"/api/notifications/{first}/dismiss", headers=auth_headers).json()["status"] == "DISMISSED"
    db = TestingSessionLocal()
    try:
        actions = {x.action for x in db.query(AuditLog).filter(AuditLog.detail.in_([first, second])).all()}
        assert {"notification.read", "notification.acknowledged", "notification.dismissed"} <= actions
    finally:
        db.close()


def test_rule_enable_disable_condition_severity_and_in_app(client, auth_headers):
    body = {"name": "Fallos críticos", "event_type": "EXECUTION_FAILED",
            "condition": {"match": {"critical": True}}, "severity": "CRITICAL", "channel": "IN_APP"}
    response = client.post("/api/alert-rules", headers=auth_headers, json=body)
    assert response.status_code == 201
    rule = response.json(); assert rule["enabled"] is True
    assert client.post(f"/api/alert-rules/{rule['id']}/disable", headers=auth_headers).json()["enabled"] is False
    assert client.post(f"/api/alert-rules/{rule['id']}/enable", headers=auth_headers).json()["enabled"] is True
    notification_id = _event("EXECUTION_FAILED", critical=True, message="Crítico")
    notification = client.get(f"/api/notifications/{notification_id}", headers=auth_headers).json()
    assert notification["severity"] == "CRITICAL" and notification["channel"] == "IN_APP"
    body["name"] = "Fallos críticos editada"
    assert client.put(f"/api/alert-rules/{rule['id']}", headers=auth_headers, json=body).status_code == 200
    assert client.get("/api/alert-rules", headers=auth_headers).status_code == 200


def test_approval_execution_and_security_event_defaults(client, auth_headers):
    expectations = [("APPROVAL_REQUIRED", "APPROVAL_REQUIRED", "HIGH"),
                    ("EXECUTION_FAILED", "TASK_FAILED", "HIGH"),
                    ("TENANT_SECURITY_EVENT", "SECURITY", "CRITICAL")]
    for event, expected_type, severity in expectations:
        row = client.get(f"/api/notifications/{_event(event)}", headers=auth_headers).json()
        assert (row["type"], row["severity"]) == (expected_type, severity)


def test_tenant_isolation_and_permissions(client, auth_headers):
    db = TestingSessionLocal()
    try:
        org = Organization(name=f"Tenant-{uuid.uuid4().hex[:6]}")
        db.add(org); db.flush()
        other = User(organization_id=org.id, username=f"other-{uuid.uuid4().hex[:6]}",
                     password_hash=hash_password("Other2026*"), role="admin")
        viewer = User(organization_id=org.id, username=f"viewer-{uuid.uuid4().hex[:6]}",
                      password_hash=hash_password("Viewer2026*"), role="viewer")
        db.add_all([other, viewer]); db.commit(); other_name = other.username; viewer_name = viewer.username; org_id = org.id
    finally:
        db.close()
    foreign_id = _event(organization_id=org_id)
    assert client.get(f"/api/notifications/{foreign_id}", headers=auth_headers).status_code == 404
    other_token = client.post("/api/auth/login", json={"username": other_name, "password": "Other2026*"}).json()["access_token"]
    other_headers = {"Authorization": f"Bearer {other_token}"}
    assert client.get(f"/api/notifications/{foreign_id}", headers=other_headers).status_code == 200
    viewer_token = client.post("/api/auth/login", json={"username": viewer_name, "password": "Viewer2026*"}).json()["access_token"]
    viewer_headers = {"Authorization": f"Bearer {viewer_token}"}
    assert client.get("/api/notifications", headers=viewer_headers).status_code == 200
    assert client.post("/api/alert-rules", headers=viewer_headers,
                       json={"name": "x", "event_type": "SYSTEM_ERROR"}).status_code == 403


def test_recipient_scope(client, auth_headers):
    db = TestingSessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").one()
        row = Notification(organization_id=admin.organization_id, type="INFO", severity="LOW", title="Directa",
                           message="Solo operador", source_type="test", recipient_role="operator")
        db.add(row); db.commit(); row_id = row.id
    finally:
        db.close()
    # Administrators have notification.manage and can inspect the tenant for operational management.
    assert client.get(f"/api/notifications/{row_id}", headers=auth_headers).status_code == 200
