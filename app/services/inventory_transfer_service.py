from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.inventory import Inventory
from app.models.inventory_transaction import (
    InventoryTransaction,
    InventoryTransactionType,
)
from app.models.inventory_transfer import (
    InventoryTransfer,
    InventoryTransferStatus,
)
from app.models.product import Product
from app.models.warehouse import Warehouse
from app.schemas.inventory_transfer import (
    InventoryTransferCreate,
)
from app.dependencies.warehouse import ensure_warehouse_access


class InventoryTransferService:

    @staticmethod
    def transfer_inventory(
        db: Session,
        data: InventoryTransferCreate,
        current_user,
    ) -> InventoryTransfer:

        if (
            data.source_warehouse_id
            == data.destination_warehouse_id
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Source and destination warehouses "
                    "must be different"
                ),
            )

        if data.quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transfer quantity must be greater than 0",
            )

        try:
            # -------------------------------------------------
            # 1. Check warehouse authorization
            # -------------------------------------------------

            ensure_warehouse_access(
                db=db,
                current_user=current_user,
                warehouse_id=data.source_warehouse_id,
            )

            ensure_warehouse_access(
                db=db,
                current_user=current_user,
                warehouse_id=data.destination_warehouse_id,
            )

            # -------------------------------------------------
            # 2. Check warehouses
            # -------------------------------------------------

            source_warehouse = db.scalar(
                select(Warehouse).where(
                    Warehouse.id == data.source_warehouse_id,
                    Warehouse.is_active.is_(True),
                )
            )

            if not source_warehouse:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Source warehouse not found or inactive",
                )

            destination_warehouse = db.scalar(
                select(Warehouse).where(
                    Warehouse.id
                    == data.destination_warehouse_id,
                    Warehouse.is_active.is_(True),
                )
            )

            if not destination_warehouse:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=(
                        "Destination warehouse "
                        "not found or inactive"
                    ),
                )

            # -------------------------------------------------
            # 3. Check product
            # -------------------------------------------------

            product = db.scalar(
                select(Product).where(
                    Product.id == data.product_id
                )
            )

            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product not found",
                )

            if not product.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Product is inactive",
                )

            # -------------------------------------------------
            # 4. Lock inventories
            # -------------------------------------------------
            #
            # IMPORTANT:
            # Always lock in deterministic order.
            # This reduces the possibility of deadlocks
            # when two transfers happen simultaneously.
            # -------------------------------------------------

            first_warehouse_id = min(
                data.source_warehouse_id,
                data.destination_warehouse_id,
            )

            second_warehouse_id = max(
                data.source_warehouse_id,
                data.destination_warehouse_id,
            )

            first_inventory = db.scalar(
                select(Inventory)
                .where(
                    Inventory.product_id == data.product_id,
                    Inventory.warehouse_id
                    == first_warehouse_id,
                )
                .with_for_update()
            )

            second_inventory = db.scalar(
                select(Inventory)
                .where(
                    Inventory.product_id == data.product_id,
                    Inventory.warehouse_id
                    == second_warehouse_id,
                )
                .with_for_update()
            )

            # -------------------------------------------------
            # 5. Make sure both inventory records exist
            # -------------------------------------------------

            if not first_inventory:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=(
                        "Inventory does not exist for "
                        f"warehouse {first_warehouse_id}"
                    ),
                )

            if not second_inventory:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=(
                        "Inventory does not exist for "
                        f"warehouse {second_warehouse_id}"
                    ),
                )

            # Identify source and destination objects
            if (
                data.source_warehouse_id
                == first_warehouse_id
            ):
                source_inventory = first_inventory
                destination_inventory = second_inventory
            else:
                source_inventory = second_inventory
                destination_inventory = first_inventory

            # -------------------------------------------------
            # 6. Check available stock
            # -------------------------------------------------

            available_stock = (
                source_inventory.available_quantity
                - source_inventory.reserved_quantity
            )

            if data.quantity > available_stock:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        "Insufficient available inventory. "
                        f"Available: {available_stock}, "
                        f"Requested: {data.quantity}"
                    ),
                )

            # -------------------------------------------------
            # 7. Save old quantities
            # -------------------------------------------------

            source_previous = (
                source_inventory.available_quantity
            )

            destination_previous = (
                destination_inventory.available_quantity
            )

            # -------------------------------------------------
            # 8. Update inventory
            # -------------------------------------------------

            source_inventory.available_quantity -= (
                data.quantity
            )

            destination_inventory.available_quantity += (
                data.quantity
            )

            db.flush()

            # -------------------------------------------------
            # 9. Create TRANSFER_OUT transaction
            # -------------------------------------------------

            transfer_out = InventoryTransaction(
                inventory_id=source_inventory.id,
                transaction_type=(
                    InventoryTransactionType.TRANSFER_OUT.value
                ),
                quantity=data.quantity,
                previous_quantity=source_previous,
                new_quantity=(
                    source_inventory.available_quantity
                ),
                reason=(
                    data.reason
                    or "Inventory transferred to another warehouse"
                ),
                reference_id=data.reference_id,
                user_id=current_user.id,
            )

            db.add(transfer_out)

            # -------------------------------------------------
            # 10. Create TRANSFER_IN transaction
            # -------------------------------------------------

            transfer_in = InventoryTransaction(
                inventory_id=destination_inventory.id,
                transaction_type=(
                    InventoryTransactionType.TRANSFER_IN.value
                ),
                quantity=data.quantity,
                previous_quantity=destination_previous,
                new_quantity=(
                    destination_inventory.available_quantity
                ),
                reason=(
                    data.reason
                    or "Inventory received from another warehouse"
                ),
                reference_id=data.reference_id,
                user_id=current_user.id,
            )

            db.add(transfer_in)

            # -------------------------------------------------
            # 11. Create transfer record
            # -------------------------------------------------

            transfer = InventoryTransfer(
                product_id=data.product_id,
                source_warehouse_id=(
                    data.source_warehouse_id
                ),
                destination_warehouse_id=(
                    data.destination_warehouse_id
                ),
                quantity=data.quantity,
                status=(
                    InventoryTransferStatus.COMPLETED.value
                ),
                reference_id=data.reference_id,
                reason=data.reason,
                transferred_by=current_user.id,
            )

            db.add(transfer)

            db.flush()

            # -------------------------------------------------
            # 12. Commit everything together
            # -------------------------------------------------

            db.commit()
            db.refresh(transfer)

            return transfer

        except HTTPException:
            db.rollback()
            raise

        except Exception:
            db.rollback()
            raise