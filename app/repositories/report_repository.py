from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.inventory import Inventory
from app.models.order import Order


class ReportRepository:

    @staticmethod
    def order_status_report(
        db: Session,
        status: str | None = None,
    ):
        query = (
            db.query(
                Order.status,
                func.count(Order.id).label("count"),
            )
            .group_by(Order.status)
            .order_by(Order.status)
        )

        if status:
            query = query.filter(
                Order.status == status.upper()
            )

        return query.all()

    @staticmethod
    def total_orders(
        db: Session,
        status: str | None = None,
    ) -> int:
        query = db.query(
            func.count(Order.id)
        )

        if status:
            query = query.filter(
                Order.status == status.upper()
            )

        return query.scalar() or 0

    @staticmethod
    def revenue_report(
        db: Session,
    ):
        result = (
            db.query(
                func.count(Order.id).label(
                    "total_orders"
                ),
                func.coalesce(
                    func.sum(Order.total),
                    0,
                ).label(
                    "total_revenue"
                ),
                func.coalesce(
                    func.avg(Order.total),
                    0,
                ).label(
                    "average_order_value"
                ),
            )
            .filter(
                Order.status != "CANCELLED"
            )
            .first()
        )

        return result

    @staticmethod
    def low_stock_items(
        db: Session,
        page: int,
        page_size: int,
    ):
        query = (
            db.query(Inventory)
            .filter(
                Inventory.available_quantity
                <= Inventory.reorder_level
            )
            .order_by(
                Inventory.available_quantity.asc()
            )
        )

        total = query.count()

        items = (
            query
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return items, total

    @staticmethod
    def overdue_orders(
        db: Session,
        page: int,
        page_size: int,
    ):
        # Orders older than 7 days that are
        # still not completed/cancelled.
        active_statuses = [
            "PENDING",
            "CONFIRMED",
            "PROCESSING",
            "PACKED",
            "SHIPPED",
        ]

        query = (
            db.query(Order)
            .filter(
                Order.status.in_(active_statuses)
            )
            .filter(
                Order.created_at
                <= func.now()
                - func.make_interval(days=7)
            )
            .order_by(
                Order.created_at.asc()
            )
        )

        total = query.count()

        items = (
            query
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return items, total