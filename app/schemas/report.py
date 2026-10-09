from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class OrderStatusReportItem(BaseModel):
    status: str
    count: int


class OrderStatusReportResponse(BaseModel):
    items: list[OrderStatusReportItem]
    total_orders: int


class RevenueReportResponse(BaseModel):
    total_orders: int
    total_revenue: Decimal
    average_order_value: Decimal


class LowStockReportItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    inventory_id: int
    product_id: int
    warehouse_id: int
    available_quantity: int
    reserved_quantity: int
    reorder_level: int


class LowStockReportResponse(BaseModel):
    items: list[LowStockReportItem]
    total: int
    page: int
    page_size: int


class OverdueOrderItem(BaseModel):
    id: int
    order_number: str
    customer_id: int
    warehouse_id: int
    status: str
    created_at: datetime


class OverdueOrderResponse(BaseModel):
    items: list[OverdueOrderItem]
    total: int
    page: int
    page_size: int