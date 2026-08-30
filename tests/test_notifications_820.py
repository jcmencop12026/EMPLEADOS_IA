import uuid

from app.events import bus
from app.events.bus import EventMessage, publish
from app.models import AuditLog, Notification, Organization, User
from app.notifications import emit_event, normalize_event_type
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


def test_subscriber_failure_isolated_logged_and_later_subscriber_runs():
    calls = []

    def subscriber_a(event, db):
        calls.append("A")

    def failing_notifications(event, db):
        calls.append("Notifications")
        raise RuntimeError("notifications unavailable")

    def subscriber_c(event, db):
        calls.append("C")

    db = TestingSessionLocal()
    admin = db.query(User).filter(User.username == "admin").one()
    original_role = admin.role
    handlers = [subscriber_a, failing_notifications, subscriber_c]
    bus._subscribers.extend(handlers)
    try:
        admin.role = "operator"  # representative business mutation in the owning transaction
        publish(EventMessage(event_type="SYSTEM_ERROR", organization_id=admin.organization_id,
                             user_id=admin.id, payload={"test": True}), db)
        db.commit()
        db.refresh(admin)
        assert admin.role == "operator"
        assert calls == ["A", "Notifications", "C"]
        failure = db.query(AuditLog).filter(AuditLog.action == "event.subscriber_failed").order_by(AuditLog.created_at.desc()).first()
        assert failure and "notifications unavailable" in (failure.detail or "")
    finally:
        admin.role = original_role
        db.commit()
        for handler in handlers:
            bus._subscribers.remove(handler)
        db.close()


def test_state_contract_valid_and_invalid_transitions(client, auth_headers):
    direct_ack = _event("TENANT_SECURITY_EVENT", message="Direct ack")
    assert client.post(f"/api/notifications/{direct_ack}/acknowledge", headers=auth_headers).status_code == 200
    assert client.post(f"/api/notifications/{direct_ack}/read", headers=auth_headers).status_code == 409

    dismissed = _event("SYSTEM_ERROR", message="Dismiss")
    assert client.post(f"/api/notifications/{dismissed}/dismiss", headers=auth_headers).status_code == 200
    assert client.post(f"/api/notifications/{dismissed}/acknowledge", headers=auth_headers).status_code == 409


def test_approval_decision_alias_never_approves_rejection():
    assert normalize_event_type("approval.completed", {"decision": "approve"}) == "APPROVAL_APPROVED"
    assert normalize_event_type("approval.completed", {"decision": "reject"}) == "APPROVAL_REJECTED"


def test_recipient_can_dismiss_own_notification_but_not_another_tenant(client):
    db = TestingSessionLocal()
    try:
        org = Organization(name=f"Recipient-{uuid.uuid4().hex[:6]}")
        db.add(org); db.flush()
        viewer = User(organization_id=org.id, username=f"recipient-{uuid.uuid4().hex[:6]}",
                      password_hash=hash_password("Recipient2026*"), role="viewer")
        db.add(viewer); db.flush()
        own = Notification(organization_id=org.id, type="INFO", severity="LOW", title="Propia",
                           message="Descartable", source_type="test", recipient_user_id=viewer.id)
        foreign_org = db.query(Organization).filter(Organization.id != org.id).first()
        foreign = Notification(organization_id=foreign_org.id, type="INFO", severity="LOW", title="Ajena",
                               message="No visible", source_type="test")
        db.add_all([own, foreign]); db.commit()
        username, own_id, foreign_id = viewer.username, own.id, foreign.id
    finally:
        db.close()
    token = client.post("/api/auth/login", json={"username": username, "password": "Recipient2026*"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    assert client.post(f"/api/notifications/{own_id}/dismiss", headers=headers).status_code == 200
    assert client.post(f"/api/notifications/{foreign_id}/dismiss", headers=headers).status_code == 404


def test_invalid_login_publishes_tenant_security_event(client):
    assert client.post("/api/auth/login", json={"username": "admin", "password": "wrong"}).status_code == 401
    db = TestingSessionLocal()
    try:
        from app.orchestration_models import WorkEvent
        assert db.query(WorkEvent).filter(WorkEvent.event_type == "TENANT_SECURITY_EVENT").first()
    finally:
        db.close()


def test_update_rule_rejects_cross_tenant_recipient(client, auth_headers):
    db = TestingSessionLocal()
    try:
        org = Organization(name=f"Foreign-{uuid.uuid4().hex[:6]}")
        db.add(org)
        db.flush()
        foreign_user = User(
            organization_id=org.id,
            username=f"foreign-{uuid.uuid4().hex[:6]}",
            password_hash=hash_password("Foreign2026*"),
            role="admin",
        )
        db.add(foreign_user)
        db.commit()
        foreign_id = foreign_user.id
    finally:
        db.close()

    created = client.post(
        "/api/alert-rules",
        headers=auth_headers,
        json={"name": "Regla base", "event_type": "SYSTEM_ERROR"},
    )
    assert created.status_code == 201
    rule_id = created.json()["id"]

    updated = client.put(
        f"/api/alert-rules/{rule_id}",
        headers=auth_headers,
        json={
            "name": "Regla base",
            "event_type": "SYSTEM_ERROR",
            "recipient_user_id": foreign_id,
        },
    )
    assert updated.status_code == 400


def test_viewer_cannot_acknowledge_notification(client):
    db = TestingSessionLocal()
    try:
        org = Organization(name=f"ViewerAck-{uuid.uuid4().hex[:6]}")
        db.add(org)
        db.flush()
        viewer = User(
            organization_id=org.id,
            username=f"viewer-ack-{uuid.uuid4().hex[:6]}",
            password_hash=hash_password("ViewerAck2026*"),
            role="viewer",
        )
        db.add(viewer)
        db.commit()
        username = viewer.username
        viewer_id = viewer.id
        org_id = org.id
    finally:
        db.close()

    db = TestingSessionLocal()
    try:
        own = Notification(
            organization_id=org_id,
            type="SECURITY",
            severity="HIGH",
            title="Propia",
            message="Ack test",
            source_type="test",
            recipient_user_id=viewer_id,
        )
        db.add(own)
        db.commit()
        own_id = own.id
    finally:
        db.close()

    token = client.post("/api/auth/login", json={"username": username, "password": "ViewerAck2026*"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    assert client.post(f"/api/notifications/{own_id}/read", headers=headers).status_code == 200
    assert client.post(f"/api/notifications/{own_id}/acknowledge", headers=headers).status_code == 403


def test_cross_tenant_alert_rule_returns_404(client, auth_headers):
    db = TestingSessionLocal()
    try:
        org = Organization(name=f"RuleTenant-{uuid.uuid4().hex[:6]}")
        db.add(org)
        db.flush()
        other = User(
            organization_id=org.id,
            username=f"rule-other-{uuid.uuid4().hex[:6]}",
            password_hash=hash_password("RuleOther2026*"),
            role="admin",
        )
        db.add(other)
        db.commit()
        other_token = client.post(
            "/api/auth/login",
            json={"username": other.username, "password": "RuleOther2026*"},
        ).json()["access_token"]
        other_headers = {"Authorization": f"Bearer {other_token}"}
        foreign_rule = client.post(
            "/api/alert-rules",
            headers=other_headers,
            json={"name": "Ajena", "event_type": "SYSTEM_ERROR"},
        ).json()["id"]
    finally:
        db.close()

    assert client.put(
        f"/api/alert-rules/{foreign_rule}",
        headers=auth_headers,
        json={"name": "Hack", "event_type": "SYSTEM_ERROR"},
    ).status_code == 404
