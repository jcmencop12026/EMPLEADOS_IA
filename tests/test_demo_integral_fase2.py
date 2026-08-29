"""Demo integral Fase 2 — seed idempotente, aislamiento y borrado seguro."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.orm import Session

from app.demo_integral.constants import (
    DEMO_ADMIN_PASSWORD,
    DEMO_ADMIN_USERNAME,
    DEMO_CORRELATION_ID,
    DEMO_OPP_CODE,
    DEMO_ORG_NAME,
    DEMO_ORG_SLUG,
)
from app.demo_integral.manifest import get_compatibility_manifest
from app.demo_integral.purge import DemoPurgeAbortError, purge_demo_integral
from app.demo_integral.seed import seed_demo_integral
from app.models import Organization, User
from app.opportunity_models import Opportunity
from app.security import hash_password
from conftest import TestingSessionLocal

pytestmark = [pytest.mark.operations]


def _other_org(db: Session) -> Organization:
    from app.seed_orchestration import bootstrap_orchestration
    from app.seed_permissions import bootstrap_permissions
    from app.seed_salud import bootstrap_salud

    org = Organization(name=f"Org Real {uuid.uuid4().hex[:6]}", slug=f"real-{uuid.uuid4().hex[:8]}")
    db.add(org)
    db.flush()
    bootstrap_permissions(db)
    bootstrap_orchestration(db, org.id)
    bootstrap_salud(db, org.id)
    user = User(
        organization_id=org.id,
        username=f"real-{uuid.uuid4().hex[:6]}",
        password_hash=hash_password("RealOrg*Test1"),
        role="admin",
        status="ACTIVE",
        is_active=True,
    )
    db.add(user)
    db.commit()
    return org


@pytest.fixture(autouse=True)
def _clean_demo_org():
    db = TestingSessionLocal()
    try:
        from app.demo_integral.purge import DemoPurgeAbortError, purge_demo_integral

        try:
            purge_demo_integral(db)
        except DemoPurgeAbortError:
            db.rollback()
    finally:
        db.close()
    yield


def test_demo_seed_initial():
    db = TestingSessionLocal()
    try:
        result = seed_demo_integral(db)
        assert result["status"] == "ok"
        assert result["organization_slug"] == DEMO_ORG_SLUG
        assert result["organization_name"] == DEMO_ORG_NAME
        assert result["correlation_id"] == DEMO_CORRELATION_ID
        assert result["login"]["username"] == DEMO_ADMIN_USERNAME
        assert result["entities"]["primary_opportunity_code"] == DEMO_OPP_CODE
        manifest = get_compatibility_manifest()
        assert manifest["comercial_1280"]["propuesta"]["potencial_en_precio"] is False
    finally:
        db.close()


def test_demo_seed_idempotent():
    db = TestingSessionLocal()
    try:
        first = seed_demo_integral(db)
        second = seed_demo_integral(db)
        assert first["organization_id"] == second["organization_id"]
        assert first["entities"]["primary_opportunity_id"] == second["entities"]["primary_opportunity_id"]
        opp_count = (
            db.query(Opportunity)
            .filter(Opportunity.organization_id == first["organization_id"], Opportunity.codigo == DEMO_OPP_CODE)
            .count()
        )
        assert opp_count == 1
    finally:
        db.close()


def test_demo_isolation_other_org_unaffected():
    db = TestingSessionLocal()
    try:
        other = _other_org(db)
        before = db.query(Opportunity).filter(Opportunity.organization_id == other.id).count()
        seed_demo_integral(db)
        after = db.query(Opportunity).filter(Opportunity.organization_id == other.id).count()
        assert before == after
        demo = db.query(Organization).filter(Organization.slug == DEMO_ORG_SLUG).first()
        assert demo is not None
        assert demo.id != other.id
    finally:
        db.close()


def test_demo_correlation_id_on_opportunity():
    db = TestingSessionLocal()
    try:
        result = seed_demo_integral(db)
        opp = db.query(Opportunity).filter(Opportunity.id == result["entities"]["primary_opportunity_id"]).first()
        assert opp is not None
        assert opp.correlation_id == DEMO_CORRELATION_ID
    finally:
        db.close()


def test_demo_purge_safe_only_demo():
    db = TestingSessionLocal()
    try:
        other = _other_org(db)
        seed_demo_integral(db)
        result = purge_demo_integral(db)
        assert result["status"] == "purged"
        assert db.query(Organization).filter(Organization.slug == DEMO_ORG_SLUG).first() is None
        assert db.query(Organization).filter(Organization.id == other.id).first() is not None
    finally:
        db.close()


def test_demo_purge_abort_when_not_found():
    db = TestingSessionLocal()
    try:
        purge_demo_integral(db)
    except DemoPurgeAbortError:
        pass
    else:
        pytest.fail("Debe abortar si no existe organización demo")
    finally:
        db.close()


def test_demo_login_credentials_exist():
    db = TestingSessionLocal()
    try:
        seed_demo_integral(db)
        user = db.query(User).filter(User.username == DEMO_ADMIN_USERNAME).first()
        assert user is not None
        assert user.organization_id
        from app.security import verify_password

        assert verify_password(DEMO_ADMIN_PASSWORD, user.password_hash)
    finally:
        db.close()
