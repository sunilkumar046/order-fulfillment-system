from sqlalchemy.orm import Session

from app.repositories.audit_log_repository import (
    AuditLogRepository,
)


class AuditLogService:

    @staticmethod
    def create(
        db: Session,
        actor_id: int | None,
        action: str,
        entity_type: str,
        entity_id: int | None = None,
        description: str | None = None,
        extra_data: dict | None = None,
    ):

        return AuditLogRepository.create(
            db=db,
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
            extra_data=extra_data,
        )

    @staticmethod
    def list_logs(
        db: Session,
        page: int,
        page_size: int,
        action: str | None = None,
        entity_type: str | None = None,
        entity_id: int | None = None,
    ):

        return AuditLogRepository.list_logs(
            db=db,
            page=page,
            page_size=page_size,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
        )