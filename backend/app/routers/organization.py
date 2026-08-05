from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Organization, User
from app.schemas import OrganizationOut

router = APIRouter(prefix="/api/organization", tags=["organization"])


@router.get("", response_model=OrganizationOut)
def get_organization(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    org = db.query(Organization).filter(Organization.id == user.organization_id).first()
    return org
