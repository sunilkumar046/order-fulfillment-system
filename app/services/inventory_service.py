from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.inventory import Inventory
from app.models.inventory_transaction import (
    InventoryTransaction,
    InventoryTransactionType,
)
from app.schemas.inventory import InventoryCreate, InventoryUpdate


class InventoryService:

    @staticmethod
    def create_inventory(
        db: Session,
        data: InventoryCreate,
        user_id: int,
    ) -> Inventory:

        existing = db.scalar(
            select(Inventory).where(
                Inventory.product_id == data.product_id,
                Inventory.warehouse_id == data.warehouse_id,
            )
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Inventory already exists for this product and warehouse",
            )

        inventory = Inventory(
            product_id=data.product_id,
            warehouse_id=data.warehouse_id,
            available_quantity=data.available_quantity,
            reserved_quantity=data.reserved_quantity,
            damaged_quantity=data.damaged_quantity,
            reorder_level=data.reorder_level,
            unit_cost=data.unit_cost,
        )

        db.add(inventory)
        db.flush()

        transaction = InventoryTransaction(
            inventory_id=inventory.id,
            transaction_type=InventoryTransactionType.PURCHASE.value,
            quantity=data.available_quantity,
            previous_quantity=0,
            new_quantity=data.available_quantity,
            amount=(
                data.unit_cost * data.available_quantity
                if data.available_quantity > 0
                else Decimal("0.00")
            ),
            reason="Initial inventory creation",
            user_id=user_id,
        )

        db.add(transaction)
        db.commit()
        db.refresh(inventory)

        return inventory

    @staticmethod
    def get_inventory(
        db: Session,
        inventory_id: int,
    ) -> Inventory:

        inventory = db.scalar(
            select(Inventory).where(
                Inventory.id == inventory_id
            )
        )

        if not inventory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Inventory not found",
            )

        return inventory

    @staticmethod
    def get_inventory_by_product_and_warehouse(
        db: Session,
        product_id: int,
        warehouse_id: int,
    ) -> Inventory:

        inventory = db.scalar(
            select(Inventory).where(
                Inventory.product_id == product_id,
                Inventory.warehouse_id == warehouse_id,
            )
        )

        if not inventory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Inventory not found for this product and warehouse",
            )

        return inventory

    @staticmethod
    def list_inventory(
        db: Session,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Inventory], int]:

        if page < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page must be greater than 0",
            )

        if page_size < 1 or page_size > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page size must be between 1 and 100",
            )

        offset = (page - 1) * page_size

        items = list(
            db.scalars(
                select(Inventory)
                .order_by(Inventory.id)
                .offset(offset)
                .limit(page_size)
            ).all()
        )

        from sqlalchemy import func

        total = db.scalar(
            select(func.count(Inventory.id))
        ) or 0

        return items, total

    @staticmethod
    def update_inventory(
        db: Session,
        inventory_id: int,
        data: InventoryUpdate,
        user_id: int,
    ) -> Inventory:

        inventory = db.scalar(
            select(Inventory).where(
                Inventory.id == inventory_id
            )
        )

        if not inventory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Inventory not found",
            )

        changes = data.model_dump(
            exclude_unset=True,
            exclude_none=True,
        )

        if not changes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields provided for update",
            )

        old_available = inventory.available_quantity

        for field, value in changes.items():
            setattr(inventory, field, value)

        db.flush()

        if "available_quantity" in changes:
            transaction = InventoryTransaction(
                inventory_id=inventory.id,
                transaction_type=InventoryTransactionType.ADJUSTMENT.value,
                quantity=abs(
                    inventory.available_quantity
                    - old_available
                ),
                previous_quantity=old_available,
                new_quantity=inventory.available_quantity,
                reason="Manual inventory adjustment",
                user_id=user_id,
            )

            db.add(transaction)

        db.commit()
        db.refresh(inventory)

        return inventory

    @staticmethod
    def reserve_inventory(
        db: Session,
        inventory_id: int,
        quantity: int,
        user_id: int,
        reference_id: str | None = None,
    ) -> Inventory:

        if quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reservation quantity must be greater than 0",
            )

        # PostgreSQL row-level lock.
        # This prevents two concurrent requests from
        # reserving the same stock at the same time.
        inventory = db.scalar(
            select(Inventory)
            .where(Inventory.id == inventory_id)
            .with_for_update()
        )

        if not inventory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Inventory not found",
            )

        available_to_reserve = (
            inventory.available_quantity
            - inventory.reserved_quantity
        )

        if quantity > available_to_reserve:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Insufficient inventory. "
                    f"Available to reserve: {available_to_reserve}"
                ),
            )

        previous_reserved = inventory.reserved_quantity

        inventory.reserved_quantity += quantity

        db.flush()

        transaction = InventoryTransaction(
            inventory_id=inventory.id,
            transaction_type=InventoryTransactionType.RESERVATION.value,
            quantity=quantity,
            previous_quantity=previous_reserved,
            new_quantity=inventory.reserved_quantity,
            reason="Inventory reserved",
            reference_id=reference_id,
            user_id=user_id,
        )

        db.add(transaction)
        db.commit()
        db.refresh(inventory)

        return inventory

    @staticmethod
    def release_inventory(
        db: Session,
        inventory_id: int,
        quantity: int,
        user_id: int,
        reference_id: str | None = None,
    ) -> Inventory:

        if quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Release quantity must be greater than 0",
            )

        inventory = db.scalar(
            select(Inventory)
            .where(Inventory.id == inventory_id)
            .with_for_update()
        )

        if not inventory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Inventory not found",
            )

        if quantity > inventory.reserved_quantity:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Cannot release {quantity} units. "
                    f"Reserved quantity is "
                    f"{inventory.reserved_quantity}"
                ),
            )

        previous_reserved = inventory.reserved_quantity

        inventory.reserved_quantity -= quantity

        db.flush()

        transaction = InventoryTransaction(
            inventory_id=inventory.id,
            transaction_type=InventoryTransactionType.RELEASE.value,
            quantity=quantity,
            previous_quantity=previous_reserved,
            new_quantity=inventory.reserved_quantity,
            reason="Inventory reservation released",
            reference_id=reference_id,
            user_id=user_id,
        )

        db.add(transaction)
        db.commit()
        db.refresh(inventory)

        return inventory

    @staticmethod
    def get_transactions(
        db: Session,
        inventory_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> list[InventoryTransaction]:

        inventory = db.scalar(
            select(Inventory).where(
                Inventory.id == inventory_id
            )
        )

        if not inventory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Inventory not found",
            )

        if page < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page must be greater than 0",
            )

        if page_size < 1 or page_size > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page size must be between 1 and 100",
            )

        offset = (page - 1) * page_size

        return list(
            db.scalars(
                select(InventoryTransaction)
                .where(
                    InventoryTransaction.inventory_id
                    == inventory_id
                )
                .order_by(
                    InventoryTransaction.created_at.desc()
                )
                .offset(offset)
                .limit(page_size)
            ).all()
        )