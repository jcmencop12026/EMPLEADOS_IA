"""CURSOR-820 v3 — pruebas adversariales post-reauditoría Codex."""
from __future__ import annotations

import threading
import uuid
from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient

from app.events import bus
from app.events.bus import EventMessage, publish
from app.models import AlertRule, Notification, Organization, User
from app.notifications import emit_event, resolve_event_id
from app.security import hash_password
from conftest import TestingSessionLocal


def _org_user(db, prefix: str) -> tuple[Organization, User]:
    org = Organization(name=f"{prefix}-{uuid.uuid4().hex[:6]}")
    db.add(org)
    db.flush()
    user = User(
        organization_id=org.id,
        username=f"{prefix}-{uuid.uuid4().hex[:6]}",
        password_hash=hash_password("Test820*Pass"),
        role="admin",
    )
    db.add(user)
    db.commit()
    return org, user


def test_event_bus_cross_tenant_recipient_denied():
    db = TestingSessionLocal()
    try:
        org_a, user_a = _org_user(db, "TenantA")
        org_b, user_b = _org_user(db, "TenantB")
        rule = AlertRule(
            organization_id=org_a.id,
            name="Cross tenant rule",
            event_type="SYSTEM_ERROR",
            severity="HIGH",
            channel="IN_APP",
            enabled=True,
            created_by=user_a.id,
            recipient_user_id=user_b.id,
        )
        db.add(rule)
        db.commit()
        created = emit_event(
            "SYSTEM_ERROR",
            org_a.id,
            "test",
            str(uuid.uuid4()),
            {"message": "cross"},
            db,
            commit=True,
        )
        assert created == []
        assert (
            db.query(Notification)
            .filter(
                Notification.organization_id == org_a.id,
                Notification.recipient_user_id == user_b.id,
            )
            .count()
            == 0
        )
    finally:
        db.close()


def test_emit_event_manipulated_recipient_cross_tenant_denied():
    db = TestingSessionLocal()
    try:
        org_a, _ = _org_user(db, "EmitA")
        org_b, user_b = _org_user(db, "EmitB")
        created = emit_event(
            "APPROVAL_REQUIRED",
            org_a.id,
            "work_plan",
            str(uuid.uuid4()),
            {"recipient_user_id": user_b.id, "message": "manipulated"},
            db,
            commit=True,
        )
        assert created == []
    finally:
        db.close()


def test_emit_event_nonexistent_recipient_denied():
    db = TestingSessionLocal()
    try:
        org_a, _ = _org_user(db, "GhostRecipient")
        created = emit_event(
            "SYSTEM_ERROR",
            org_a.id,
            "test",
            str(uuid.uuid4()),
            {"recipient_user_id": str(uuid.uuid4()), "message": "ghost"},
            db,
            commit=True,
        )
        assert created == []
    finally:
        db.close()


def test_emit_event_same_tenant_recipient_allowed():
    db = TestingSessionLocal()
    try:
        org_a, user_a = _org_user(db, "SameTenant")
        created = emit_event(
            "APPROVAL_REQUIRED",
            org_a.id,
            "work_plan",
            str(uuid.uuid4()),
            {"recipient_user_id": user_a.id, "message": "ok"},
            db,
            commit=True,
        )
        assert len(created) == 1
        assert created[0].recipient_user_id == user_a.id
    finally:
        db.close()


def test_listener_commit_forbidden_and_savepoint_holds():
    db = TestingSessionLocal()
    malicious_listener = None
    try:
        admin = db.query(User).filter(User.username == "admin").one()
        original_role = admin.role

        def malicious_listener(event, session):
            session.add(
                Notification(
                    organization_id=event.organization_id,
                    type="INFO",
                    severity="LOW",
                    title="Malicious",
                    message="Should not commit",
                    source_type="test",
                )
            )
            session.commit()

        bus._subscribers.append(malicious_listener)
        admin.role = "operator"
        publish(
            EventMessage(
                event_type="SYSTEM_ERROR",
                organization_id=admin.organization_id,
                user_id=admin.id,
                payload={"test": True},
            ),
            db,
        )
        db.rollback()
        db.refresh(admin)
        assert admin.role == original_role
        assert (
            db.query(Notification)
            .filter(Notification.title == "Malicious")
            .count()
            == 0
        )
    finally:
        if malicious_listener and malicious_listener in bus._subscribers:
            bus._subscribers.remove(malicious_listener)
        admin = db.query(User).filter(User.username == "admin").one()
        admin.role = original_role
        db.commit()
        db.close()


def test_two_listeners_second_commit_fails_no_partial_persist():
    db = TestingSessionLocal()
    handlers = []
    try:
        admin = db.query(User).filter(User.username == "admin").one()
        original_role = admin.role
        marker = {"a": False}

        def listener_a(event, session):
            marker["a"] = True

        def listener_b(event, session):
            session.commit()

        handlers = [listener_a, listener_b]
        bus._subscribers.extend(handlers)
        admin.role = "operator"
        publish(
            EventMessage(
                event_type="SYSTEM_ERROR",
                organization_id=admin.organization_id,
                user_id=admin.id,
                payload={"two_listeners": True},
            ),
            db,
        )
        db.rollback()
        db.refresh(admin)
        assert marker["a"] is True
        assert admin.role != "operator"
    finally:
        for handler in handlers:
            if handler in bus._subscribers:
                bus._subscribers.remove(handler)
        admin = db.query(User).filter(User.username == "admin").one()
        admin.role = original_role
        db.commit()
        db.close()


def test_viewer_cannot_approve_or_reject(client: TestClient):
    db = TestingSessionLocal()
    try:
        from app.orchestration_models import ApprovalRequest, WorkPlan

        org = Organization(name=f"ViewerApprove-{uuid.uuid4().hex[:6]}")
        db.add(org)
        db.flush()
        viewer = User(
            organization_id=org.id,
            username=f"viewer-appr-{uuid.uuid4().hex[:6]}",
            password_hash=hash_password("ViewerAppr820*"),
            role="viewer",
        )
        db.add(viewer)
        db.flush()
        plan = WorkPlan(
            organization_id=org.id,
            user_id=viewer.id,
            correlation_id=str(uuid.uuid4()),
            request="Needs approval",
            objective="Test",
            status="WAITING_APPROVAL",
            approval_status="PENDING",
        )
        db.add(plan)
        db.flush()
        approval = ApprovalRequest(
            organization_id=org.id,
            work_plan_id=plan.id,
            action="Approve test",
            reason="Viewer approval test",
            requested_by=viewer.id,
        )
        db.add(approval)
        db.commit()
        username = viewer.username
        approval_id = approval.id
        plan_id = plan.id
    finally:
        db.close()

    token = client.post("/api/auth/login", json={"username": username, "password": "ViewerAppr820*"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    assert client.get(f"/api/operations/executions/{plan_id}", headers=headers).status_code == 200
    assert client.post(
        f"/api/operations/approvals/{approval_id}/decide",
        headers=headers,
        json={"decision": "approve"},
    ).status_code == 403
    assert client.post(
        f"/api/operations/approvals/{approval_id}/decide",
        headers=headers,
        json={"decision": "reject", "comment": "no"},
    ).status_code == 403


def test_operator_can_decide_approval(client: TestClient):
    db = TestingSessionLocal()
    try:
        from app.orchestration_models import ApprovalRequest, WorkPlan

        org = Organization(name=f"OperatorApprove-{uuid.uuid4().hex[:6]}")
        db.add(org)
        db.flush()
        operator = User(
            organization_id=org.id,
            username=f"operator-appr-{uuid.uuid4().hex[:6]}",
            password_hash=hash_password("OperatorAppr820*"),
            role="operator",
        )
        db.add(operator)
        db.flush()
        plan = WorkPlan(
            organization_id=org.id,
            user_id=operator.id,
            correlation_id=str(uuid.uuid4()),
            request="Needs approval",
            objective="Test",
            status="WAITING_APPROVAL",
            approval_status="PENDING",
        )
        db.add(plan)
        db.flush()
        approval = ApprovalRequest(
            organization_id=org.id,
            work_plan_id=plan.id,
            action="Approve test",
            reason="Operator approval test",
            requested_by=operator.id,
        )
        db.add(approval)
        db.commit()
        username = operator.username
        approval_id = approval.id
    finally:
        db.close()

    token = client.post("/api/auth/login", json={"username": username, "password": "OperatorAppr820*"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    res = client.post(
        f"/api/operations/approvals/{approval_id}/decide",
        headers=headers,
        json={"decision": "approve", "comment": "ok"},
    )
    assert res.status_code == 200


def test_event_idempotency_sequential_duplicate():
    db = TestingSessionLocal()
    try:
        org, user = _org_user(db, "IdemSeq")
        event_id = str(uuid.uuid4())
        payload = {"message": "once", "event_id": event_id, "recipient_user_id": user.id}
        first = emit_event("APPROVAL_REQUIRED", org.id, "wp", "wp-1", payload, db, commit=True)
        second = emit_event("APPROVAL_REQUIRED", org.id, "wp", "wp-1", payload, db, commit=True)
        assert len(first) == 1
        assert len(second) == 1
        assert first[0].id == second[0].id
        count = (
            db.query(Notification)
            .filter(Notification.organization_id == org.id, Notification.event_id == event_id)
            .count()
        )
        assert count == 1
    finally:
        db.close()


def test_event_idempotency_concurrent_duplicate():
    db_a = TestingSessionLocal()
    db_b = TestingSessionLocal()
    try:
        org, user = _org_user(db_a, "IdemConc")
        event_id = str(uuid.uuid4())
        payload = {"message": "race", "event_id": event_id, "recipient_user_id": user.id}
        barrier = threading.Barrier(2)

        def worker(session):
            barrier.wait()
            return emit_event(
                "APPROVAL_REQUIRED",
                org.id,
                "wp",
                "wp-race",
                payload,
                session,
                commit=True,
            )

        with ThreadPoolExecutor(max_workers=2) as pool:
            f1 = pool.submit(worker, db_a)
            f2 = pool.submit(worker, db_b)
            results = [f1.result(), f2.result()]
        ids = {row.id for batch in results for row in batch}
        assert len(ids) == 1
        count = (
            db_a.query(Notification)
            .filter(Notification.organization_id == org.id, Notification.event_id == event_id)
            .count()
        )
        assert count == 1
    finally:
        db_a.close()
        db_b.close()


def test_event_idempotency_two_recipients_same_event():
    db = TestingSessionLocal()
    try:
        org = Organization(name=f"IdemMulti-{uuid.uuid4().hex[:6]}")
        db.add(org)
        db.flush()
        user_a = User(
            organization_id=org.id,
            username=f"a-{uuid.uuid4().hex[:6]}",
            password_hash=hash_password("UserA820*"),
            role="admin",
        )
        user_b = User(
            organization_id=org.id,
            username=f"b-{uuid.uuid4().hex[:6]}",
            password_hash=hash_password("UserB820*"),
            role="operator",
        )
        db.add_all([user_a, user_b])
        db.commit()
        event_id = str(uuid.uuid4())
        first = emit_event(
            "APPROVAL_REQUIRED",
            org.id,
            "wp",
            "wp-1",
            {"event_id": event_id, "recipient_user_id": user_a.id},
            db,
            commit=True,
        )
        second = emit_event(
            "APPROVAL_REQUIRED",
            org.id,
            "wp",
            "wp-1",
            {"event_id": event_id, "recipient_user_id": user_b.id},
            db,
            commit=True,
        )
        assert len(first) == 1
        assert len(second) == 1
        assert first[0].id != second[0].id
    finally:
        db.close()


def test_resolve_event_id_is_stable():
    payload = {"correlation_id": "corr-1", "approval_id": "appr-1"}
    a = resolve_event_id("APPROVAL_REQUIRED", "org-1", "wp-1", payload)
    b = resolve_event_id("APPROVAL_REQUIRED", "org-1", "wp-1", payload)
    assert a == b
