from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.notification import Notification


class NotificationRepository:

    @staticmethod
    def create(
        db: Session,
        user_id: int,
        title: str,
        message: str,
        notification_type: str,
        entity_type: str | None = None,
        entity_id: int | None = None,
    ) -> Notification:

        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            entity_type=entity_type,
            entity_id=entity_id,
        )

        db.add(notification)
        db.flush()

        return notification

    @staticmethod
    def get_user_notifications(
        db: Session,
        user_id: int,
        page: int,
        page_size: int,
        unread_only: bool = False,
    ):
        query = db.query(Notification).filter(
            Notification.user_id == user_id
        )

        if unread_only:
            query = query.filter(
                Notification.is_read.is_(False)
            )

        total = query.with_entities(
            func.count(Notification.id)
        ).scalar()

        items = (
            query
            .order_by(Notification.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return items, total

    @staticmethod
    def get_by_id(
        db: Session,
        notification_id: int,
    ) -> Notification | None:

        return db.query(Notification).filter(
            Notification.id == notification_id
        ).first()

    @staticmethod
    def mark_as_read(
        notification: Notification,
    ) -> Notification:

        notification.is_read = True
        notification.read_at = datetime.utcnow()

        return notification

    @staticmethod
    def mark_all_as_read(
        db: Session,
        user_id: int,
    ) -> int:

        notifications = (
            db.query(Notification)
            .filter(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
            .all()
        )

        now = datetime.utcnow()

        for notification in notifications:
            notification.is_read = True
            notification.read_at = now

        return len(notifications)