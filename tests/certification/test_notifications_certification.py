"""Certificación permanente PR #7 — notificaciones y alertas.

Ejecución rápida: pytest -m "certification and notifications"
PostgreSQL:      pytest -m "certification and notifications and postgresql"
"""
from __future__ import annotations

import threading
import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from app.events import bus
from app.events.bus import EventMessage, publish
from app.events.subscriber_session import SubscriberCommitForbiddenError, SubscriberSession
from app.models import AlertRule, Notification, Organization, User
from app.notifications import emit_event
from app.security import hash_password
from conftest import TestingSessionLocal

pytestmark = [pytest.mark.certification, pytest.mark.notifications]


def _org_user(db, prefix: str) -> tuple[Organization, User]:
    org = Organization(name=f"{prefix}-{uuid.uuid4().hex[:6]}")
    db.add(org)
    db.flush()
    user = User(
        organization_id=org.id,
        username=f"{prefix}-{uuid.uuid4().hex[:6]}",
        password_hash=hash_password("Cert820*Pass"),
        role="admin",
    )
    db.add(user)
    db.commit()
    return org, user


# 1. Recipient cross-tenant
@pytest.mark.tenant
def test_cert_01_recipient_cross_tenant_denied():
    db = TestingSessionLocal()
    try:
        org_a, user_a = _org_user(db, "CertA")
        org_b, user_b = _org_user(db, "CertB")
        db.add(AlertRule(
            organization_id=org_a.id, name="Cross", event_type="SYSTEM_ERROR",
            severity="HIGH", channel="IN_APP", enabled=True,
            created_by=user_a.id, recipient_user_id=user_b.id,
        ))
        db.commit()
        created = emit_event("SYSTEM_ERROR", org_a.id, "test", str(uuid.uuid4()), {"message": "x"}, db, commit=True)
        assert created == []
        assert db.query(Notification).filter(Notification.recipient_user_id == user_b.id).count() == 0
    finally:
        db.close()


# 2. Recipient inexistente
def test_cert_02_recipient_inexistente_denied():
    db = TestingSessionLocal()
    try:
        org_a, _ = _org_user(db, "Ghost")
        created = emit_event(
            "SYSTEM_ERROR", org_a.id, "test", str(uuid.uuid4()),
            {"recipient_user_id": str(uuid.uuid4()), "message": "ghost"}, db, commit=True,
        )
        assert created == []
    finally:
        db.close()


# 3. SubscriberSession commit/rollback/close
def test_cert_03_subscriber_session_sin_control_transaccion():
    db = TestingSessionLocal()
    sub = SubscriberSession(db)
    with pytest.raises(SubscriberCommitForbiddenError):
        sub.commit()
    with pytest.raises(SubscriberCommitForbiddenError):
        sub.rollback()
    with pytest.raises(SubscriberCommitForbiddenError):
        sub.close()


# 4. SAVEPOINT — dos listeners
def test_cert_04_savepoint_dos_listeners_sin_persistencia_parcial():
    db = TestingSessionLocal()
    handlers = []
    try:
        admin = db.query(User).filter(User.username == "admin").one()
        marker = {"a": False}

        def listener_a(_event, _session):
            marker["a"] = True

        def listener_b(_event, session):
            session.commit()

        handlers = [listener_a, listener_b]
        bus._subscribers.extend(handlers)
        admin.role = "operator"
        publish(EventMessage(
            event_type="SYSTEM_ERROR", organization_id=admin.organization_id,
            user_id=admin.id, payload={"cert": True},
        ), db)
        db.rollback()
        db.refresh(admin)
        assert marker["a"] is True
        assert admin.role != "operator"
    finally:
        for h in handlers:
            if h in bus._subscribers:
                bus._subscribers.remove(h)
        admin = db.query(User).filter(User.username == "admin").one()
        admin.role = "admin"
        db.commit()
        db.close()


# 5. Viewer approval → 403
@pytest.mark.auth
@pytest.mark.operations
def test_cert_05_viewer_approve_403(client: TestClient):
    db = TestingSessionLocal()
    try:
        from app.orchestration_models import ApprovalRequest, WorkPlan
        org = Organization(name=f"CertView-{uuid.uuid4().hex[:6]}")
        db.add(org)
        db.flush()
        viewer = User(
            organization_id=org.id, username=f"viewer-{uuid.uuid4().hex[:6]}",
            password_hash=hash_password("ViewerCert820*"), role="viewer",
        )
        db.add(viewer)
        db.flush()
        plan = WorkPlan(
            organization_id=org.id, user_id=viewer.id, correlation_id=str(uuid.uuid4()),
            request="x", objective="x", status="WAITING_APPROVAL", approval_status="PENDING",
        )
        db.add(plan)
        db.flush()
        approval = ApprovalRequest(
            organization_id=org.id, work_plan_id=plan.id, action="x",
            reason="x", requested_by=viewer.id,
        )
        db.add(approval)
        db.commit()
        username, approval_id = viewer.username, approval.id
    finally:
        db.close()
    token = client.post("/api/auth/login", json={"username": username, "password": "ViewerCert820*"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    assert client.post(f"/api/operations/approvals/{approval_id}/decide", headers=headers, json={"decision": "approve"}).status_code == 403


# 6. Viewer rejection → 403
@pytest.mark.auth
@pytest.mark.operations
def test_cert_06_viewer_reject_403(client: TestClient):
    db = TestingSessionLocal()
    try:
        from app.orchestration_models import ApprovalRequest, WorkPlan
        org = Organization(name=f"CertRej-{uuid.uuid4().hex[:6]}")
        db.add(org)
        db.flush()
        viewer = User(
            organization_id=org.id, username=f"viewer-r-{uuid.uuid4().hex[:6]}",
            password_hash=hash_password("ViewerRej820*"), role="viewer",
        )
        db.add(viewer)
        db.flush()
        plan = WorkPlan(
            organization_id=org.id, user_id=viewer.id, correlation_id=str(uuid.uuid4()),
            request="x", objective="x", status="WAITING_APPROVAL", approval_status="PENDING",
        )
        db.add(plan)
        db.flush()
        approval = ApprovalRequest(
            organization_id=org.id, work_plan_id=plan.id, action="x",
            reason="x", requested_by=viewer.id,
        )
        db.add(approval)
        db.commit()
        username, approval_id = viewer.username, approval.id
    finally:
        db.close()
    token = client.post("/api/auth/login", json={"username": username, "password": "ViewerRej820*"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    assert client.post(
        f"/api/operations/approvals/{approval_id}/decide",
        headers=headers, json={"decision": "reject", "comment": "no"},
    ).status_code == 403


# 7. Deep link no concede permisos
@pytest.mark.auth
def test_cert_07_deep_link_no_concede_permisos(client: TestClient, auth_headers):
    db = TestingSessionLocal()
    try:
        org = Organization(name=f"Deep-{uuid.uuid4().hex[:6]}")
        db.add(org)
        db.flush()
        viewer = User(
            organization_id=org.id, username=f"deep-v-{uuid.uuid4().hex[:6]}",
            password_hash=hash_password("DeepView820*"), role="viewer",
        )
        db.add(viewer)
        db.commit()
        org_id = org.id
        viewer_name = viewer.username
        viewer_id = viewer.id
        from app.orchestration_models import WorkPlan
        plan = WorkPlan(
            organization_id=org_id, user_id=viewer.id, correlation_id=str(uuid.uuid4()),
            request="deep", objective="deep", status="WAITING_APPROVAL",
        )
        db.add(plan)
        db.commit()
        plan_id = plan.id
        viewer_id = viewer.id
        viewer_name = viewer.username
    finally:
        db.close()
    db_emit = TestingSessionLocal()
    try:
        created = emit_event(
            "APPROVAL_REQUIRED", org_id, "work_plan", plan_id,
            {"recipient_user_id": viewer_id, "message": "deep link test"},
            db_emit, commit=True,
        )
        assert len(created) >= 1
    finally:
        db_emit.close()
    vtoken = client.post("/api/auth/login", json={"username": viewer_name, "password": "DeepView820*"}).json()["access_token"]
    vheaders = {"Authorization": f"Bearer {vtoken}"}
    assert client.get(f"/api/operations/executions/{plan_id}?approval=malicious", headers=vheaders).status_code == 200
    me = client.get("/api/auth/me", headers=vheaders).json()
    assert "operations.approve" not in me.get("permissions", [])


# 8. Idempotencia secuencial
def test_cert_08_idempotencia_secuencial():
    db = TestingSessionLocal()
    try:
        org, user = _org_user(db, "IdemSeq")
        event_id = str(uuid.uuid4())
        payload = {"message": "once", "event_id": event_id, "recipient_user_id": user.id}
        first = emit_event("APPROVAL_REQUIRED", org.id, "wp", "wp-1", payload, db, commit=True)
        second = emit_event("APPROVAL_REQUIRED", org.id, "wp", "wp-1", payload, db, commit=True)
        assert len(first) == 1 and len(second) == 1 and first[0].id == second[0].id
        assert db.query(Notification).filter(Notification.event_id == event_id).count() == 1
    finally:
        db.close()


# 9. Idempotencia concurrente
@pytest.mark.concurrency
def test_cert_09_idempotencia_concurrente():
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


# 10. Retry IntegrityError — sin duplicación
def test_cert_10_retry_integrity_sin_duplicacion():
    db = TestingSessionLocal()
    try:
        org, user = _org_user(db, "Retry")
        event_id = str(uuid.uuid4())
        payload = {"message": "retry", "event_id": event_id, "recipient_user_id": user.id}
        batches = [
            emit_event("APPROVAL_REQUIRED", org.id, "wp", "wp-r", payload, db, commit=True)
            for _ in range(3)
        ]
        ids = {row.id for batch in batches for row in batch}
        assert len(ids) == 1
        assert db.query(Notification).filter(Notification.event_id == event_id).count() == 1
    finally:
        db.close()


# 11. API notificaciones accesible (frontend: build como control)
def test_cert_11_api_notificaciones_list(client: TestClient, auth_headers):
    res = client.get("/api/notifications", headers=auth_headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)
