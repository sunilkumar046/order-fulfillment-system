from datetime import datetime
from enum import Enum

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class ReturnStatus(str, Enum):
    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ReturnCondition(str, Enum):
    GOOD = "GOOD"
    DAMAGED = "DAMAGED"


class ReturnRequest(Base):
    __tablename__ = "return_requests"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id"),
        nullable=False,
        unique=True,
        index=True,
    )

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=ReturnStatus.REQUESTED.value,
        index=True,
    )

    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    rejection_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    approved_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
    )

    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    order = relationship(
        "Order",
        back_populates="return_request",
    )

    customer = relationship(
        "User",
        foreign_keys=[customer_id],
    )

    approver = relationship(
        "User",
        foreign_keys=[approved_by],
    )

    items = relationship(
        "ReturnItem",
        back_populates="return_request",
        cascade="all, delete-orphan",
    )


class ReturnItem(Base):
    __tablename__ = "return_items"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    return_request_id: Mapped[int] = mapped_column(
        ForeignKey("return_requests.id"),
        nullable=False,
        index=True,
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"),
        nullable=False,
        index=True,
    )

    quantity: Mapped[int] = mapped_column(
        nullable=False,
    )

    condition: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=ReturnCondition.GOOD.value,
    )

    return_request = relationship(
        "ReturnRequest",
        back_populates="items",
    )

    product = relationship(
        "Product",
    )