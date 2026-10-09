from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ProductCreate(BaseModel):
    sku: str = Field(..., min_length=2, max_length=100)
    name: str = Field(..., min_length=2, max_length=200)
    description: str | None = Field(
        default=None,
        max_length=1000,
    )
    category_id: int = Field(..., gt=0)
    price: Decimal = Field(..., gt=0)
    is_active: bool = True


class ProductUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=200,
    )
    description: str | None = Field(
        default=None,
        max_length=1000,
    )
    category_id: int | None = Field(
        default=None,
        gt=0,
    )
    price: Decimal | None = Field(
        default=None,
        gt=0,
    )
    is_active: bool | None = None


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sku: str
    name: str
    description: str | None
    category_id: int
    price: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime