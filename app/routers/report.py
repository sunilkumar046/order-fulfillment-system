from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.auth import require_role
from app.models.user import User
from app.schemas.report import (
    LowStockReportResponse,
    OrderStatusReportResponse,
    OverdueOrderResponse,
    RevenueReportResponse,
)
from app.services.report_service import ReportService


router = APIRouter(
    prefix="/api/reports",
    tags=["Reports"],
)


@router.get(
    "/order-status",
    response_model=OrderStatusReportResponse,
)
def order_status_report(
    status: str | None = Query(
        default=None
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(
            "Admin",
            "Warehouse Manager",
            "Fulfillment Agent",
        )
    ),
):
    return ReportService.get_order_status_report(
        db,
        status,
    )


@router.get(
    "/revenue",
    response_model=RevenueReportResponse,
)
def revenue_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("Admin")
    ),
):
    return ReportService.get_revenue_report(db)


@router.get(
    "/low-stock",
    response_model=LowStockReportResponse,
)
def low_stock_report(
    page: int = Query(
        default=1,
        ge=1,
    ),
    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(
            "Admin",
            "Warehouse Manager",
            "Fulfillment Agent",
        )
    ),
):
    return ReportService.get_low_stock_report(
        db,
        page,
        page_size,
    )


@router.get(
    "/overdue-orders",
    response_model=OverdueOrderResponse,
)
def overdue_orders_report(
    page: int = Query(
        default=1,
        ge=1,
    ),
    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(
            "Admin",
            "Warehouse Manager",
            "Fulfillment Agent",
        )
    ),
):
    return ReportService.get_overdue_orders(
        db,
        page,
        page_size,
    )