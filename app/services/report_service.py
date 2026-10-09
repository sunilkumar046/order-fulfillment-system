from sqlalchemy.orm import Session

from app.repositories.report_repository import ReportRepository
from app.schemas.report import (
    LowStockReportItem,
    LowStockReportResponse,
    OrderStatusReportItem,
    OrderStatusReportResponse,
    OverdueOrderItem,
    OverdueOrderResponse,
    RevenueReportResponse,
)


class ReportService:

    @staticmethod
    def get_order_status_report(
        db: Session,
        status: str | None = None,
    ) -> OrderStatusReportResponse:

        rows = ReportRepository.order_status_report(
            db,
            status,
        )

        total = ReportRepository.total_orders(
            db,
            status,
        )

        items = [
            OrderStatusReportItem(
                status=str(row.status),
                count=int(row.count),
            )
            for row in rows
        ]

        return OrderStatusReportResponse(
            items=items,
            total_orders=total,
        )

    @staticmethod
    def get_revenue_report(
        db: Session,
    ) -> RevenueReportResponse:

        result = ReportRepository.revenue_report(db)

        return RevenueReportResponse(
            total_orders=int(
                result.total_orders or 0
            ),
            total_revenue=result.total_revenue or 0,
            average_order_value=(
                result.average_order_value or 0
            ),
        )

    @staticmethod
    def get_low_stock_report(
        db: Session,
        page: int,
        page_size: int,
    ) -> LowStockReportResponse:

        records, total = (
            ReportRepository.low_stock_items(
                db,
                page,
                page_size,
            )
        )

        items = [
            LowStockReportItem(
                inventory_id=item.id,
                product_id=item.product_id,
                warehouse_id=item.warehouse_id,
                available_quantity=item.available_quantity,
                reserved_quantity=item.reserved_quantity,
                reorder_level=item.reorder_level,
            )
            for item in records
        ]

        return LowStockReportResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )

    @staticmethod
    def get_overdue_orders(
        db: Session,
        page: int,
        page_size: int,
    ) -> OverdueOrderResponse:

        records, total = (
            ReportRepository.overdue_orders(
                db,
                page,
                page_size,
            )
        )

        items = [
            OverdueOrderItem(
                id=order.id,
                order_number=order.order_number,
                customer_id=order.customer_id,
                warehouse_id=order.warehouse_id,
                status=order.status,
                created_at=order.created_at,
            )
            for order in records
        ]

        return OverdueOrderResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )