from fastapi import (
    APIRouter,
    Depends,
    Query,
)
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.auth import require_role
from app.models.user import User
from app.schemas.audit_log import (
    AuditLogListResponse,
)
from app.services.audit_log_service import (
    AuditLogService,
)


router = APIRouter(
    prefix="/api/audit-logs",
    tags=["Audit Logs"],
)


@router.get(
    "",
    response_model=AuditLogListResponse,
)
def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(
        20,
        ge=1,
        le=100,
    ),
    action: str | None = Query(
        default=None,
    ),
    entity_type: str | None = Query(
        default=None,
    ),
    entity_id: int | None = Query(
        default=None,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("Admin")
    ),
):

    items, total = AuditLogService.list_logs(
        db=db,
        page=page,
        page_size=page_size,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
    )

    return AuditLogListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )