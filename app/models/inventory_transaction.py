from datetime import datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class InventoryTransactionType(str, Enum):
    PURCHASE = "PURCHASE"
    SALE = "SALE"
    RESERVATION = "RESERVATION"
    RELEASE = "RELEASE"
    ADJUSTMENT = "ADJUSTMENT"
    TRANSFER_IN = "TRANSFER_IN"
    TRANSFER_OUT = "TRANSFER_OUT"
    RETURN = "RETURN"
    DAMAGE = "DAMAGE"


class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    inventory_id: Mapped[int] = mapped_column(
        ForeignKey("inventory.id"),
        nullable=False,
        index=True,
    )

    transaction_type: Mapped[InventoryTransactionType] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    previous_quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    new_quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    amount: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    reference_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    inventory = relationship(
        "Inventory",
        back_populates="transactions",
    )

    user = relationship("User")