from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


class AuditLogRepository:

    @staticmethod
    def create(
        db: Session,
        actor_id: int | None,
        action: str,
        entity_type: str,
        entity_id: int | None = None,
        description: str | None = None,
        extra_data: dict | None = None,
    ) -> AuditLog:

        audit_log = AuditLog(
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
            extra_data=extra_data,
        )

        db.add(audit_log)
        db.flush()

        return audit_log

    @staticmethod
    def list_logs(
        db: Session,
        page: int,
        page_size: int,
        action: str | None = None,
        entity_type: str | None = None,
        entity_id: int | None = None,
    ):
        query = db.query(AuditLog)

        if action:
            query = query.filter(
                AuditLog.action == action
            )

        if entity_type:
            query = query.filter(
                AuditLog.entity_type == entity_type
            )

        if entity_id:
            query = query.filter(
                AuditLog.entity_id == entity_id
            )

        total = query.with_entities(
            func.count(AuditLog.id)
        ).scalar()

        items = (
            query
            .order_by(AuditLog.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return items, total