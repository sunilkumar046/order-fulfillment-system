from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.inventory import Inventory
from app.models.inventory_transaction import InventoryTransaction


class InventoryRepository:
    @staticmethod
    def get_by_id(
        db: Session,
        inventory_id: int,
    ) -> Inventory | None:
        return db.scalar(
            select(Inventory).where(
                Inventory.id == inventory_id
            )
        )

    @staticmethod
    def get_by_product_and_warehouse(
        db: Session,
        product_id: int,
        warehouse_id: int,
    ) -> Inventory | None:
        return db.scalar(
            select(Inventory).where(
                Inventory.product_id == product_id,
                Inventory.warehouse_id == warehouse_id,
            )
        )

    @staticmethod
    def create(
        db: Session,
        inventory: Inventory,
    ) -> Inventory:
        db.add(inventory)
        db.flush()
        db.refresh(inventory)

        return inventory

    @staticmethod
    def update(
        db: Session,
        inventory: Inventory,
    ) -> Inventory:
        db.add(inventory)
        db.flush()
        db.refresh(inventory)

        return inventory

    @staticmethod
    def delete(
        db: Session,
        inventory: Inventory,
    ) -> None:
        db.delete(inventory)
        db.flush()

    @staticmethod
    def list_inventory(
        db: Session,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Inventory]:
        statement = (
            select(Inventory)
            .order_by(Inventory.id)
            .offset(skip)
            .limit(limit)
        )

        return list(db.scalars(statement).all())

    @staticmethod
    def count(
        db: Session,
    ) -> int:
        from sqlalchemy import func

        return db.scalar(
            select(func.count(Inventory.id))
        ) or 0

    @staticmethod
    def get_transactions(
        db: Session,
        inventory_id: int,
        skip: int = 0,
        limit: int = 20,
    ) -> list[InventoryTransaction]:
        statement = (
            select(InventoryTransaction)
            .where(
                InventoryTransaction.inventory_id
                == inventory_id
            )
            .order_by(
                InventoryTransaction.created_at.desc()
            )
            .offset(skip)
            .limit(limit)
        )

        return list(db.scalars(statement).all())