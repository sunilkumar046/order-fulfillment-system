from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    user_id: int
    title: str
    message: str
    notification_type: str
    is_read: bool
    entity_type: str | None = None
    entity_id: int | None = None
    created_at: datetime
    read_at: datetime | None = None


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    total: int
    page: int
    page_size: int