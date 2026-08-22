from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.deps import get_current_user
from app.database import get_db
from app.models import User
from app.schemas_orchestration import AssistantAskRequest, PlanResponse
from app.services.coordinator import route_task

router = APIRouter(prefix="/api/assistant", tags=["assistant"])


@router.post("/ask", response_model=PlanResponse)
def assistant_ask(
    body: AssistantAskRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = route_task(
        db,
        organization_id=user.organization_id,
        user_id=user.id,
        request=body.message,
        context=body.context,
        auto_execute=body.auto_execute,
    )
    return PlanResponse(**result)
