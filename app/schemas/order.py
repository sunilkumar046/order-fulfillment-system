from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field



# ORDER CREATION 

class OrderItemCreate(BaseModel):
    product_id: int = Field(
        ...,
        gt=0,
    )

    quantity: int = Field(
        ...,
        gt=0,
    )


class OrderCreate(BaseModel):
    warehouse_id: int = Field(
        ...,
        gt=0,
    )

    items: list[OrderItemCreate] = Field(
        ...,
        min_length=1,
    )

    shipping_address: str = Field(
        ...,
        min_length=5,
        max_length=1000,
    )

    notes: str | None = Field(
        default=None,
        max_length=2000,
    )


# ORDER ITEM RESPONSE

class OrderItemResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    product_id: int
    quantity: int
    unit_price: Decimal
    subtotal: Decimal
    created_at: datetime



# ORDER RESPONSE

class OrderResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    order_number: str

    customer_id: int

    warehouse_id: int

    assigned_agent_id: int | None

    status: str

    subtotal: Decimal
    total: Decimal

    shipping_address: str
    notes: str | None

    created_at: datetime
    updated_at: datetime

    items: list[OrderItemResponse]



# ORDER STATUS UPDATE

class OrderStatusUpdate(BaseModel):
    status: str = Field(
        ...,
        min_length=3,
        max_length=30,
    )

    reason: str | None = Field(
        default=None,
        max_length=500,
    )



# ORDER STATUS HISTORY

class OrderStatusHistoryResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    order_id: int
    old_status: str | None
    new_status: str
    changed_by: int
    reason: str | None
    created_at: datetime


# ORDER LIST

class OrderListResponse(BaseModel):
    items: list[OrderResponse]
    total: int
    page: int
    page_size: int



# FULFILLMENT AGENT ASSIGNMENT

class OrderAssignmentRequest(BaseModel):
    agent_id: int = Field(
        ...,
        gt=0,
    )