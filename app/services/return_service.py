from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.inventory import Inventory
from app.models.inventory_transaction import (
    InventoryTransaction,
    InventoryTransactionType,
)
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.models.order_status_history import OrderStatusHistory
from app.models.product import Product
from app.models.return_request import (
    ReturnCondition,
    ReturnItem,
    ReturnRequest,
    ReturnStatus,
)
from app.models.user import User
from app.repositories.return_repository import ReturnRepository
from app.schemas.return_request import (
    ReturnRejectRequest,
    ReturnRequestCreate,
)


class ReturnService:

    @staticmethod
    def create_return_request(
        db: Session,
        order_id: int,
        customer_id: int,
        data: ReturnRequestCreate,
    ):
        # ---------------------------------------------------------
        # 1. Get order
        # ---------------------------------------------------------
        order = db.scalar(
            select(Order).where(
                Order.id == order_id,
                Order.customer_id == customer_id,
            )
        )

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )

        # ---------------------------------------------------------
        # 2. Only delivered orders can be returned
        # ---------------------------------------------------------
        if order.status != OrderStatus.DELIVERED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only delivered orders can be returned",
            )

        # ---------------------------------------------------------
        # 3. Check if return already exists
        # ---------------------------------------------------------
        existing_return = ReturnRepository.get_by_order_id(
            db,
            order_id,
        )

        if existing_return:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A return request already exists for this order",
            )

        # ---------------------------------------------------------
        # 4. Get order items
        # ---------------------------------------------------------
        order_items = db.scalars(
            select(OrderItem).where(
                OrderItem.order_id == order_id
            )
        ).all()

        if not order_items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order has no items",
            )

        order_item_map = {
            item.product_id: item
            for item in order_items
        }

        # ---------------------------------------------------------
        # 5. Validate return items
        # ---------------------------------------------------------
        if not data.items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one item is required for return",
            )

        seen_products = set()

        for item_data in data.items:

            if item_data.product_id in seen_products:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Duplicate product in return request",
                )

            seen_products.add(item_data.product_id)

            order_item = order_item_map.get(
                item_data.product_id
            )

            if not order_item:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Product {item_data.product_id} "
                        "does not belong to this order"
                    ),
                )

            if item_data.quantity <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Return quantity must be greater than zero",
                )

            if item_data.quantity > order_item.quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Return quantity for product "
                        f"{item_data.product_id} cannot exceed "
                        f"ordered quantity"
                    ),
                )

        # ---------------------------------------------------------
        # 6. Create return request
        # ---------------------------------------------------------
        return_request = ReturnRequest(
            order_id=order.id,
            customer_id=customer_id,
            status=ReturnStatus.REQUESTED,
            reason=data.reason,
        )

        db.add(return_request)
        db.flush()

        # ---------------------------------------------------------
        # 7. Create return items
        # ---------------------------------------------------------
        for item_data in data.items:
            return_item = ReturnItem(
                return_request_id=return_request.id,
                product_id=item_data.product_id,
                quantity=item_data.quantity,
                condition=item_data.condition,
            )

            db.add(return_item)

        db.commit()
        db.refresh(return_request)

        return return_request

    # =============================================================
    # GET RETURN
    # =============================================================

    @staticmethod
    def get_return(
        db: Session,
        return_id: int,
        current_user: User,
    ):
        return_request = ReturnRepository.get_by_id(
            db,
            return_id,
        )

        if not return_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Return request not found",
            )

        # Customer can only see own return
        if (
            current_user.role.value == "Customer"
            and return_request.customer_id != current_user.id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to view this return request",
            )

        return return_request

    # =============================================================
    # APPROVE RETURN
    # =============================================================

    @staticmethod
    def approve_return(
        db: Session,
        return_id: int,
        approved_by: int,
    ):
        # ---------------------------------------------------------
        # 1. Lock return request
        # ---------------------------------------------------------
        return_request = ReturnRepository.get_by_id_for_update(
            db,
            return_id,
        )

        if not return_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Return request not found",
            )

        # ---------------------------------------------------------
        # 2. Return must be REQUESTED
        # ---------------------------------------------------------
        if return_request.status != ReturnStatus.REQUESTED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only requested returns can be approved",
            )

        # ---------------------------------------------------------
        # 3. Lock order
        # ---------------------------------------------------------
        order = db.scalar(
            select(Order)
            .where(Order.id == return_request.order_id)
            .with_for_update()
        )

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )

        # ---------------------------------------------------------
        # 4. Order must be DELIVERED
        # ---------------------------------------------------------
        if order.status != OrderStatus.DELIVERED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only delivered orders can be approved for return",
            )

        # ---------------------------------------------------------
        # 5. Get return items
        # ---------------------------------------------------------
        return_items = db.scalars(
            select(ReturnItem).where(
                ReturnItem.return_request_id == return_id
            )
        ).all()

        if not return_items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Return request has no items",
            )

        # ---------------------------------------------------------
        # 6. Process inventory
        # ---------------------------------------------------------
        for item in return_items:

            inventory = db.scalar(
                select(Inventory)
                .where(
                    Inventory.product_id == item.product_id,
                    Inventory.warehouse_id == order.warehouse_id,
                )
                .with_for_update()
            )

            if not inventory:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Inventory not found for product "
                        f"{item.product_id}"
                    ),
                )

            previous_quantity = inventory.available_quantity

            # -----------------------------------------------------
            # GOOD item
            # Goes back into available inventory
            # -----------------------------------------------------
            if item.condition == ReturnCondition.GOOD:
                inventory.available_quantity += item.quantity

            # -----------------------------------------------------
            # DAMAGED item
            # Goes into damaged inventory
            # -----------------------------------------------------
            elif item.condition == ReturnCondition.DAMAGED:
                inventory.damaged_quantity += item.quantity

            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid return condition",
                )

            new_quantity = inventory.available_quantity

            # -----------------------------------------------------
            # Create immutable inventory transaction
            # -----------------------------------------------------
            transaction = InventoryTransaction(
                inventory_id=inventory.id,
                transaction_type=InventoryTransactionType.RETURN,
                quantity=item.quantity,
                previous_quantity=previous_quantity,
                new_quantity=new_quantity,
                reason=f"Return approved for order {order.order_number}",
                reference_id=str(return_request.id),
                user_id=approved_by,
            )

            db.add(transaction)

        # ---------------------------------------------------------
        # 7. Update return request
        # ---------------------------------------------------------
        return_request.status = ReturnStatus.APPROVED
        return_request.approved_by = approved_by
        return_request.approved_at = datetime.now(timezone.utc)

        # ---------------------------------------------------------
        # 8. Update order status
        # ---------------------------------------------------------
        old_status = order.status
        order.status = OrderStatus.RETURNED

        # ---------------------------------------------------------
        # 9. Create order status history
        # ---------------------------------------------------------
        history = OrderStatusHistory(
            order_id=order.id,
            old_status=old_status,
            new_status=OrderStatus.RETURNED,
            changed_by=approved_by,
            reason="Return request approved",
        )

        db.add(history)

        # ---------------------------------------------------------
        # 10. Commit everything atomically
        # ---------------------------------------------------------
        db.commit()

        db.refresh(return_request)

        return return_request

    # =============================================================
    # REJECT RETURN
    # =============================================================

    @staticmethod
    def reject_return(
        db: Session,
        return_id: int,
        rejected_by: int,
        data: ReturnRejectRequest,
    ):
        # ---------------------------------------------------------
        # 1. Lock return request
        # ---------------------------------------------------------
        return_request = ReturnRepository.get_by_id_for_update(
            db,
            return_id,
        )

        if not return_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Return request not found",
            )

        # ---------------------------------------------------------
        # 2. Only REQUESTED returns can be rejected
        # ---------------------------------------------------------
        if return_request.status != ReturnStatus.REQUESTED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only requested returns can be rejected",
            )

        # ---------------------------------------------------------
        # 3. Validate reason
        # ---------------------------------------------------------
        if not data.reason or not data.reason.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rejection reason is required",
            )

        # ---------------------------------------------------------
        # 4. Update return request
        # ---------------------------------------------------------
        return_request.status = ReturnStatus.REJECTED
        return_request.rejection_reason = data.reason.strip()

        # ---------------------------------------------------------
        # 5. Commit
        # ---------------------------------------------------------
        db.commit()

        db.refresh(return_request)

        return return_request