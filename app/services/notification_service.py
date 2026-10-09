from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.notification_repository import (
    NotificationRepository,
)


class NotificationService:

    @staticmethod
    def create_notification(
        db: Session,
        user_id: int,
        title: str,
        message: str,
        notification_type: str,
        entity_type: str | None = None,
        entity_id: int | None = None,
    ):

        notification = NotificationRepository.create(
            db=db,
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            entity_type=entity_type,
            entity_id=entity_id,
        )

        db.commit()
        db.refresh(notification)

        return notification

    @staticmethod
    def list_my_notifications(
        db: Session,
        user_id: int,
        page: int,
        page_size: int,
        unread_only: bool = False,
    ):

        return NotificationRepository.get_user_notifications(
            db=db,
            user_id=user_id,
            page=page,
            page_size=page_size,
            unread_only=unread_only,
        )

    @staticmethod
    def mark_as_read(
        db: Session,
        notification_id: int,
        user_id: int,
    ):

        notification = NotificationRepository.get_by_id(
            db=db,
            notification_id=notification_id,
        )

        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found",
            )

        if notification.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot modify this notification",
            )

        NotificationRepository.mark_as_read(
            notification
        )

        db.commit()
        db.refresh(notification)

        return notification

    @staticmethod
    def mark_all_as_read(
        db: Session,
        user_id: int,
    ):

        count = NotificationRepository.mark_all_as_read(
            db=db,
            user_id=user_id,
        )

        db.commit()

        return {
            "message": "All notifications marked as read",
            "updated_count": count,
        }