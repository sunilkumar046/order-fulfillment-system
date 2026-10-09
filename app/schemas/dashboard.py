from typing import Any

from pydantic import BaseModel


class AdminDashboardResponse(BaseModel):
    total_users: int
    total_customers: int
    total_products: int
    total_warehouses: int
    total_orders: int
    total_revenue: float
    orders_by_status: dict[str, int]


class LowStockItem(BaseModel):
    inventory_id: int
    product_id: int
    warehouse_id: int
    available_quantity: int
    reserved_quantity: int
    reorder_level: int


class WarehouseInventorySummary(BaseModel):
    warehouse_id: int
    total_available: int
    total_reserved: int
    inventory_items: int


class OperationsDashboardResponse(BaseModel):
    total_products: int
    total_available_inventory: int
    total_reserved_inventory: int
    low_stock_count: int
    low_stock_items: list[LowStockItem]
    pending_orders: int
    warehouse_inventory: list[WarehouseInventorySummary]