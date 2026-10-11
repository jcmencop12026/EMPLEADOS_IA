from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Organization, User
from app.permissions import user_permissions
from app.schemas import LoginRequest, TokenResponse, UserMe
from app.services.auth_service import authenticate_user, logout_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    _user, token = authenticate_user(db, body.username, body.password)
    return TokenResponse(access_token=token)


@router.post("/logout", status_code=204)
def logout(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    logout_user(db, user)


@router.get("/me", response_model=UserMe)
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    org = db.query(Organization).filter(Organization.id == user.organization_id).first()
    return UserMe(
        id=user.id,
        username=user.username,
        role=user.role,
        organization_id=user.organization_id,
        organization_name=org.name if org else "",
        email=user.email,
        full_name=user.full_name,
        status=user.status,
        permissions=sorted(user_permissions(user, db)),
    )
