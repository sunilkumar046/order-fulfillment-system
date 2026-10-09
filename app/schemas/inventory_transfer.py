from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class InventoryTransferCreate(BaseModel):
    product_id: int = Field(gt=0)
    source_warehouse_id: int = Field(gt=0)
    destination_warehouse_id: int = Field(gt=0)
    quantity: int = Field(gt=0)
    reference_id: str | None = None
    reason: str | None = Field(
        default=None,
        max_length=500,
    )


class InventoryTransferResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    source_warehouse_id: int
    destination_warehouse_id: int
    quantity: int
    status: str
    reference_id: str | None
    reason: str | None
    transferred_by: int
    created_at: datetime