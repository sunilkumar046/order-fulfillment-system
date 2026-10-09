from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.auth import require_role
from app.models.user import User
from app.schemas.dashboard import (
    AdminDashboardResponse,
    OperationsDashboardResponse,
)
from app.services.dashboard_service import DashboardService


router = APIRouter(
    prefix="/api/dashboard",
    tags=["Dashboard"],
)


@router.get(
    "/admin",
    response_model=AdminDashboardResponse,
)
def admin_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("Admin")
    ),
):
    return DashboardService.get_admin_dashboard(db)


@router.get(
    "/operations",
    response_model=OperationsDashboardResponse,
)
def operations_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(
            "Admin",
            "Warehouse Manager",
            "Fulfillment Agent",
        )
    ),
):
    return DashboardService.get_operations_dashboard(db)