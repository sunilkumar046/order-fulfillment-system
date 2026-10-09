from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReturnItemCreate(BaseModel):
    product_id: int = Field(..., gt=0)

    quantity: int = Field(
        ...,
        gt=0,
    )

    condition: str = Field(
        default="GOOD",
        pattern="^(GOOD|DAMAGED)$",
    )


class ReturnRequestCreate(BaseModel):
    reason: str = Field(
        ...,
        min_length=5,
        max_length=1000,
    )

    items: list[ReturnItemCreate] = Field(
        ...,
        min_length=1,
    )


class ReturnItemResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    product_id: int
    quantity: int
    condition: str


class ReturnRequestResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    order_id: int
    customer_id: int
    status: str
    reason: str
    rejection_reason: str | None
    approved_by: int | None
    approved_at: datetime | None
    created_at: datetime
    updated_at: datetime

    items: list[ReturnItemResponse]


class ReturnRejectRequest(BaseModel):
    reason: str = Field(
        ...,
        min_length=5,
        max_length=1000,
    )