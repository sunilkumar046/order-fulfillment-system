from sqlalchemy.orm import Session

from app.repositories.dashboard_repository import DashboardRepository
from app.schemas.dashboard import (
    AdminDashboardResponse,
    LowStockItem,
    OperationsDashboardResponse,
    WarehouseInventorySummary,
)


class DashboardService:

    @staticmethod
    def get_admin_dashboard(
        db: Session,
    ) -> AdminDashboardResponse:

        return AdminDashboardResponse(
            total_users=DashboardRepository.count_users(db),
            total_customers=DashboardRepository.count_customers(db),
            total_products=DashboardRepository.count_products(db),
            total_warehouses=DashboardRepository.count_warehouses(db),
            total_orders=DashboardRepository.count_orders(db),
            total_revenue=DashboardRepository.total_revenue(db),
            orders_by_status=DashboardRepository.orders_by_status(db),
        )

    @staticmethod
    def get_operations_dashboard(
        db: Session,
    ) -> OperationsDashboardResponse:

        low_stock_records = (
            DashboardRepository.low_stock_items(db)
        )

        low_stock_items = [
            LowStockItem(
                inventory_id=item.id,
                product_id=item.product_id,
                warehouse_id=item.warehouse_id,
                available_quantity=item.available_quantity,
                reserved_quantity=item.reserved_quantity,
                reorder_level=item.reorder_level,
            )
            for item in low_stock_records
        ]

        warehouse_rows = (
            DashboardRepository.warehouse_inventory(db)
        )

        warehouse_inventory = [
            WarehouseInventorySummary(
                warehouse_id=row.warehouse_id,
                total_available=int(row.total_available),
                total_reserved=int(row.total_reserved),
                inventory_items=int(row.inventory_items),
            )
            for row in warehouse_rows
        ]

        return OperationsDashboardResponse(
            total_products=DashboardRepository.count_products(db),
            total_available_inventory=(
                DashboardRepository.total_available_inventory(db)
            ),
            total_reserved_inventory=(
                DashboardRepository.total_reserved_inventory(db)
            ),
            low_stock_count=len(low_stock_items),
            low_stock_items=low_stock_items,
            pending_orders=DashboardRepository.pending_orders(db),
            warehouse_inventory=warehouse_inventory,
        )