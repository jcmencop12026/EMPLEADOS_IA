from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.audit import write_audit
from app.database import get_db
from app.deps import get_current_user
from app.events.bus import EventMessage, publish
from app.models import Organization, User
from app.schemas import LoginRequest, TokenResponse, UserMe
from app.permissions import user_permissions
from app.security import create_access_token, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == body.username).first()
    if not user or not verify_password(body.password, user.password_hash):
        if user:
            publish(
                EventMessage(
                    event_type="TENANT_SECURITY_EVENT",
                    organization_id=user.organization_id,
                    user_id=user.id,
                    payload={"kind": "invalid_login", "username": body.username},
                ),
                db,
            )
            db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales incorrectas")
    token = create_access_token(user.id, {"role": user.role, "org": user.organization_id})
    write_audit(
        db,
        action="auth.login",
        organization_id=user.organization_id,
        user_id=user.id,
        detail=user.username,
    )
    db.commit()
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserMe)
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    org = db.query(Organization).filter(Organization.id == user.organization_id).first()
    return UserMe(
        id=user.id,
        username=user.username,
        role=user.role,
        organization_id=user.organization_id,
        organization_name=org.name if org else "",
        permissions=sorted(user_permissions(user)),
    )
