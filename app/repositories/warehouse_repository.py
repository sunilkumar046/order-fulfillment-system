from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.warehouse import Warehouse
from app.models.warehouse_user import WarehouseUser


class WarehouseRepository:

    @staticmethod
    def get_by_id(
        db: Session,
        warehouse_id: int,
    ) -> Warehouse | None:
        return db.scalar(
            select(Warehouse).where(
                Warehouse.id == warehouse_id
            )
        )

    @staticmethod
    def get_by_code(
        db: Session,
        code: str,
    ) -> Warehouse | None:
        return db.scalar(
            select(Warehouse).where(
                Warehouse.code == code
            )
        )

    @staticmethod
    def list_all(
        db: Session,
    ) -> list[Warehouse]:
        return list(
            db.scalars(
                select(Warehouse)
                .order_by(Warehouse.id)
            ).all()
        )

    @staticmethod
    def create(
        db: Session,
        warehouse: Warehouse,
    ) -> Warehouse:
        db.add(warehouse)
        db.flush()
        db.refresh(warehouse)
        return warehouse

    @staticmethod
    def get_assignment(
        db: Session,
        warehouse_id: int,
        user_id: int,
    ) -> WarehouseUser | None:
        return db.scalar(
            select(WarehouseUser).where(
                WarehouseUser.warehouse_id == warehouse_id,
                WarehouseUser.user_id == user_id,
            )
        )

    @staticmethod
    def create_assignment(
        db: Session,
        assignment: WarehouseUser,
    ) -> WarehouseUser:
        db.add(assignment)
        db.flush()
        db.refresh(assignment)
        return assignment

    @staticmethod
    def get_user_warehouses(
        db: Session,
        user_id: int,
    ) -> list[Warehouse]:
        statement = (
            select(Warehouse)
            .join(
                WarehouseUser,
                WarehouseUser.warehouse_id == Warehouse.id,
            )
            .where(
                WarehouseUser.user_id == user_id,
                WarehouseUser.is_active.is_(True),
                Warehouse.is_active.is_(True),
            )
            .order_by(Warehouse.id)
        )

        return list(db.scalars(statement).all())