from fastapi import (
    APIRouter,
    Depends,
    Query,
)
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.notification import (
    NotificationListResponse,
    NotificationResponse,
)
from app.services.notification_service import (
    NotificationService,
)


router = APIRouter(
    prefix="/api/notifications",
    tags=["Notifications"],
)


@router.get(
    "",
    response_model=NotificationListResponse,
)
def list_my_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(
        20,
        ge=1,
        le=100,
    ),
    unread_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):

    items, total = (
        NotificationService.list_my_notifications(
            db=db,
            user_id=current_user.id,
            page=page,
            page_size=page_size,
            unread_only=unread_only,
        )
    )

    return NotificationListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationResponse,
)
def mark_notification_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):

    return NotificationService.mark_as_read(
        db=db,
        notification_id=notification_id,
        user_id=current_user.id,
    )


@router.patch(
    "/read-all",
)
def mark_all_notifications_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):

    return NotificationService.mark_all_as_read(
        db=db,
        user_id=current_user.id,
    )