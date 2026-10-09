from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Inventory(Base):
    __tablename__ = "inventory"

    __table_args__ = (
    UniqueConstraint(
        "product_id",
        "warehouse_id",
        name="uq_inventory_product_warehouse",
    ),
    CheckConstraint(
        "available_quantity >= 0",
        name="ck_inventory_available_non_negative",
    ),
    CheckConstraint(
        "reserved_quantity >= 0",
        name="ck_inventory_reserved_non_negative",
    ),
    CheckConstraint(
        "reserved_quantity <= available_quantity",
        name="ck_inventory_reserved_not_greater_than_available",
    ),
    CheckConstraint(
        "damaged_quantity >= 0",
        name="ck_inventory_damaged_non_negative",
    ),
    CheckConstraint(
        "reorder_level >= 0",
        name="ck_inventory_reorder_level_non_negative",
    ),
)

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"),
        nullable=False,
        index=True,
    )

    warehouse_id: Mapped[int] = mapped_column(
        ForeignKey("warehouses.id"),
        nullable=False,
        index=True,
    )

    available_quantity: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
    )

    reserved_quantity: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
    )

    damaged_quantity: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
    )

    reorder_level: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
    )

    unit_cost: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=0,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    product = relationship(
        "Product",
        back_populates="inventory_items",
    )

    warehouse = relationship(
        "Warehouse",
        back_populates="inventory_items",
    )

    transactions = relationship(
        "InventoryTransaction",
        back_populates="inventory",
    )