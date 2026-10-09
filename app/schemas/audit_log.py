from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    actor_id: int | None
    action: str
    entity_type: str
    entity_id: int | None
    description: str | None
    extra_data: dict[str, Any] | None
    created_at: datetime


class AuditLogListResponse(BaseModel):
    items: list[AuditLogResponse]
    total: int
    page: int
    page_size: int