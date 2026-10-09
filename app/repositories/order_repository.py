from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.order_status_history import OrderStatusHistory


class OrderRepository:

    @staticmethod
    def get_by_id(
        db: Session,
        order_id: int,
    ) -> Order | None:

        return db.scalar(
            select(Order)
            .where(Order.id == order_id)
        )

    @staticmethod
    def get_by_order_number(
        db: Session,
        order_number: str,
    ) -> Order | None:

        return db.scalar(
            select(Order)
            .where(Order.order_number == order_number)
        )

    @staticmethod
    def create(
        db: Session,
        order: Order,
    ) -> Order:

        db.add(order)
        db.flush()
        db.refresh(order)

        return order

    @staticmethod
    def create_item(
        db: Session,
        item: OrderItem,
    ) -> OrderItem:

        db.add(item)
        db.flush()
        db.refresh(item)

        return item

    @staticmethod
    def create_status_history(
        db: Session,
        history: OrderStatusHistory,
    ) -> OrderStatusHistory:

        db.add(history)
        db.flush()
        db.refresh(history)

        return history

    @staticmethod
    def list_customer_orders(
        db: Session,
        customer_id: int,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Order]:

        statement = (
            select(Order)
            .where(Order.customer_id == customer_id)
            .order_by(Order.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        return list(
            db.scalars(statement).unique().all()
        )

    @staticmethod
    def count_customer_orders(
        db: Session,
        customer_id: int,
    ) -> int:

        return (
            db.scalar(
                select(func.count(Order.id))
                .where(Order.customer_id == customer_id)
            )
            or 0
        )

    @staticmethod
    def list_all(
        db: Session,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Order]:

        statement = (
            select(Order)
            .order_by(Order.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        return list(
            db.scalars(statement).unique().all()
        )

    @staticmethod
    def count_all(
        db: Session,
    ) -> int:

        return (
            db.scalar(
                select(func.count(Order.id))
            )
            or 0
        )

    @staticmethod
    def get_status_history(
        db: Session,
        order_id: int,
    ) -> list[OrderStatusHistory]:

        statement = (
            select(OrderStatusHistory)
            .where(
                OrderStatusHistory.order_id == order_id
            )
            .order_by(
                OrderStatusHistory.created_at.asc()
            )
        )

        return list(
            db.scalars(statement).all()
        )