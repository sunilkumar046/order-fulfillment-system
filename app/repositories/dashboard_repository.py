from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.product import Product
from app.models.warehouse import Warehouse
from app.models.order import Order
from app.models.inventory import Inventory
from app.models.role import Role


class DashboardRepository:

    @staticmethod
    def count_users(db: Session) -> int:
        return db.query(func.count(User.id)).scalar() or 0

    @staticmethod
    def count_customers(db: Session) -> int:
        return (
            db.query(func.count(User.id))
            .join(Role, User.role_id == Role.id)
            .filter(Role.name == "Customer")
            .scalar()
            or 0
        )

    @staticmethod
    def count_products(db: Session) -> int:
        return db.query(func.count(Product.id)).scalar() or 0

    @staticmethod
    def count_warehouses(db: Session) -> int:
        return db.query(func.count(Warehouse.id)).scalar() or 0

    @staticmethod
    def count_orders(db: Session) -> int:
        return db.query(func.count(Order.id)).scalar() or 0

    @staticmethod
    def total_revenue(db: Session) -> float:
        result = (
            db.query(
                func.coalesce(
                    func.sum(Order.total),
                    0,
                )
            )
            .filter(
                Order.status != "CANCELLED"
            )
            .scalar()
        )

        return float(result or 0)

    @staticmethod
    def orders_by_status(db: Session) -> dict[str, int]:
        rows = (
            db.query(
                Order.status,
                func.count(Order.id),
            )
            .group_by(Order.status)
            .all()
        )

        return {
            str(status): count
            for status, count in rows
        }

    @staticmethod
    def total_available_inventory(db: Session) -> int:
        return (
            db.query(
                func.coalesce(
                    func.sum(
                        Inventory.available_quantity
                    ),
                    0,
                )
            )
            .scalar()
            or 0
        )

    @staticmethod
    def total_reserved_inventory(db: Session) -> int:
        return (
            db.query(
                func.coalesce(
                    func.sum(
                        Inventory.reserved_quantity
                    ),
                    0,
                )
            )
            .scalar()
            or 0
        )

    @staticmethod
    def low_stock_items(db: Session):
        return (
            db.query(Inventory)
            .filter(
                Inventory.available_quantity
                <= Inventory.reorder_level
            )
            .order_by(
                Inventory.available_quantity.asc()
            )
            .all()
        )

    @staticmethod
    def pending_orders(db: Session) -> int:
        pending_statuses = [
            "PENDING",
            "CONFIRMED",
            "PROCESSING",
            "PACKED",
        ]

        return (
            db.query(func.count(Order.id))
            .filter(
                Order.status.in_(pending_statuses)
            )
            .scalar()
            or 0
        )

    @staticmethod
    def warehouse_inventory(db: Session):
        rows = (
            db.query(
                Inventory.warehouse_id,
                func.coalesce(
                    func.sum(
                        Inventory.available_quantity
                    ),
                    0,
                ).label("total_available"),
                func.coalesce(
                    func.sum(
                        Inventory.reserved_quantity
                    ),
                    0,
                ).label("total_reserved"),
                func.count(
                    Inventory.id
                ).label("inventory_items"),
            )
            .group_by(
                Inventory.warehouse_id
            )
            .order_by(
                Inventory.warehouse_id
            )
            .all()
        )

        return rows