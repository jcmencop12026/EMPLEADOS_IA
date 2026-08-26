from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

NotificationType = Literal["INFO", "SUCCESS", "WARNING", "ERROR", "APPROVAL_REQUIRED", "TASK_COMPLETED", "TASK_FAILED", "SECURITY", "SYSTEM"]
Severity = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]


class NotificationOut(BaseModel):
    id: str
    organization_id: str
    type: str
    severity: str
    title: str
    message: str
    source_type: str
    source_id: str | None
    recipient_user_id: str | None
    recipient_role: str | None
    status: str
    channel: str
    created_at: datetime
    read_at: datetime | None
    acknowledged_at: datetime | None
    expires_at: datetime | None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AlertRuleIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    event_type: str = Field(min_length=1, max_length=80)
    condition: dict[str, Any] | None = None
    severity: Severity = "MEDIUM"
    recipient_user_id: str | None = None
    recipient_role: str | None = Field(default=None, max_length=40)
    channel: Literal["IN_APP"] = "IN_APP"
    enabled: bool = True


class AlertRuleOut(BaseModel):
    id: str
    organization_id: str
    name: str
    event_type: str
    condition: dict[str, Any] | None
    severity: str
    recipient_user_id: str | None
    recipient_role: str | None
    channel: str
    enabled: bool
    created_by: str
    created_at: datetime
    updated_at: datetime
