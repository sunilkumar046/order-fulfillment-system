from datetime import datetime
from enum import Enum

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class InventoryTransferStatus(str, Enum):
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class InventoryTransfer(Base):
    __tablename__ = "inventory_transfers"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"),
        nullable=False,
        index=True,
    )

    source_warehouse_id: Mapped[int] = mapped_column(
        ForeignKey("warehouses.id"),
        nullable=False,
        index=True,
    )

    destination_warehouse_id: Mapped[int] = mapped_column(
        ForeignKey("warehouses.id"),
        nullable=False,
        index=True,
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    status: Mapped[InventoryTransferStatus] = mapped_column(
        String(20),
        nullable=False,
        default=InventoryTransferStatus.COMPLETED.value,
    )

    reference_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    reason: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    transferred_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    product = relationship("Product")

    source_warehouse = relationship(
        "Warehouse",
        foreign_keys=[source_warehouse_id],
    )

    destination_warehouse = relationship(
        "Warehouse",
        foreign_keys=[destination_warehouse_id],
    )

    user = relationship("User")