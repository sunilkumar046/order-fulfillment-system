from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class InventoryBase(BaseModel):
    product_id: int
    warehouse_id: int
    available_quantity: int = Field(default=0, ge=0)
    reserved_quantity: int = Field(default=0, ge=0)
    damaged_quantity: int = Field(default=0, ge=0)
    reorder_level: int = Field(default=0, ge=0)
    unit_cost: Decimal = Field(default=Decimal("0.00"), ge=0)


class InventoryCreate(InventoryBase):
    pass


class InventoryUpdate(BaseModel):
    available_quantity: int | None = Field(default=None, ge=0)
    reserved_quantity: int | None = Field(default=None, ge=0)
    damaged_quantity: int | None = Field(default=None, ge=0)
    reorder_level: int | None = Field(default=None, ge=0)
    unit_cost: Decimal | None = Field(default=None, ge=0)


class InventoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    warehouse_id: int
    available_quantity: int
    reserved_quantity: int
    damaged_quantity: int
    reorder_level: int
    unit_cost: Decimal
    updated_at: datetime


class InventoryListResponse(BaseModel):
    items: list[InventoryResponse]
    total: int
    page: int
    page_size: int


class InventoryTransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    inventory_id: int
    transaction_type: str
    quantity: int
    previous_quantity: int
    new_quantity: int
    amount: Decimal | None
    reason: str | None
    reference_id: str | None
    user_id: int
    created_at: datetime