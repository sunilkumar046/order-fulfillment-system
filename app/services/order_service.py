import hashlib
import json

from decimal import Decimal
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
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
from app.models.user import User
from app.models.warehouse import Warehouse
from app.models.warehouse_user import WarehouseUser
from app.schemas.order import OrderCreate


class OrderService:

    # =========================================================
    # ORDER NUMBER
    # =========================================================

    @staticmethod
    def _generate_order_number() -> str:
        return f"ORD-{uuid4().hex[:8].upper()}"

    @staticmethod
    def _generate_request_hash(
        data: OrderCreate,
    ) -> str:
        payload = data.model_dump(mode="json")

        normalized_payload = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        )

        return hashlib.sha256(
            normalized_payload.encode("utf-8")
        ).hexdigest()

    # =========================================================
    # CREATE ORDER
    # =========================================================

    @staticmethod
    def create_order(
        db: Session,
        data: OrderCreate,
        customer_id: int,
        idempotency_key: str | None = None,
    ) -> Order:

        request_hash: str | None = None

        try:
            # -------------------------------------------------
            # Idempotency
            # -------------------------------------------------

            if idempotency_key is not None:
                idempotency_key = idempotency_key.strip()

                if not idempotency_key:
                    raise HTTPException(
                        status_code=400,
                        detail="Idempotency-Key cannot be empty",
                    )

                request_hash = (
                    OrderService._generate_request_hash(data)
                )

                existing_order = db.scalar(
                    select(Order).where(
                        Order.customer_id == customer_id,
                        Order.idempotency_key == idempotency_key,
                    )
                )

                if existing_order:
                    if (
                        existing_order.idempotency_request_hash
                        != request_hash
                    ):
                        raise HTTPException(
                            status_code=409,
                            detail=(
                                "The Idempotency-Key has already "
                                "been used for a different request"
                            ),
                        )

                    return existing_order

            warehouse = db.scalar(
                select(Warehouse).where(
                    Warehouse.id == data.warehouse_id
                )
            )

            if not warehouse:
                raise HTTPException(
                    status_code=404,
                    detail="Warehouse not found",
                )

            if not warehouse.is_active:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Cannot create an order using "
                        "an inactive warehouse"
                    ),
                )

            # -------------------------------------------------
            # Combine duplicate products
            # -------------------------------------------------

            product_quantities: dict[int, int] = {}

            for item in data.items:
                product_quantities[item.product_id] = (
                    product_quantities.get(
                        item.product_id,
                        0,
                    )
                    + item.quantity
                )

            product_ids = list(
                product_quantities.keys()
            )

            # -------------------------------------------------
            # Get products
            # -------------------------------------------------

            products = list(
                db.scalars(
                    select(Product).where(
                        Product.id.in_(product_ids)
                    )
                ).all()
            )

            products_by_id = {
                product.id: product
                for product in products
            }

            missing_products = [
                product_id
                for product_id in product_ids
                if product_id not in products_by_id
            ]

            if missing_products:
                raise HTTPException(
                    status_code=404,
                    detail=(
                        f"Products not found: "
                        f"{missing_products}"
                    ),
                )

            inactive_products = [
                product.id
                for product in products
                if not product.is_active
            ]

            if inactive_products:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Inactive products cannot be ordered: "
                        f"{inactive_products}"
                    ),
                )

            # -------------------------------------------------
            # Lock inventory rows
            # -------------------------------------------------

            inventory_rows = list(
                db.scalars(
                    select(Inventory)
                    .where(
                        Inventory.warehouse_id
                        == data.warehouse_id,
                        Inventory.product_id.in_(
                            product_ids
                        ),
                    )
                    .with_for_update()
                ).all()
            )

            inventory_by_product_id = {
                inventory.product_id: inventory
                for inventory in inventory_rows
            }

            missing_inventory = [
                product_id
                for product_id in product_ids
                if product_id not in inventory_by_product_id
            ]

            if missing_inventory:
                raise HTTPException(
                    status_code=409,
                    detail=(
                        "Inventory is not configured "
                        "for products: "
                        f"{missing_inventory}"
                    ),
                )

            # -------------------------------------------------
            # Check inventory and calculate subtotal
            # -------------------------------------------------

            subtotal = Decimal("0.00")

            for product_id, quantity in (
                product_quantities.items()
            ):

                inventory = (
                    inventory_by_product_id[
                        product_id
                    ]
                )

                product = products_by_id[
                    product_id
                ]

                available_to_reserve = (
                    inventory.available_quantity
                    - inventory.reserved_quantity
                )

                if quantity > available_to_reserve:
                    raise HTTPException(
                        status_code=409,
                        detail=(
                            f"Insufficient inventory "
                            f"for product "
                            f"'{product.name}'. "
                            f"Requested: {quantity}, "
                            f"available to reserve: "
                            f"{available_to_reserve}"
                        ),
                    )

                subtotal += (
                    product.price * quantity
                )

            # -------------------------------------------------
            # Create order
            # -------------------------------------------------

            order = Order(
                order_number=(
                    OrderService._generate_order_number()
                ),
                customer_id=customer_id,
                idempotency_key=idempotency_key,
                idempotency_request_hash=request_hash,
                warehouse_id=data.warehouse_id,
                assigned_agent_id=None,
                status=OrderStatus.PENDING.value,
                subtotal=subtotal,
                total=subtotal,
                shipping_address=(
                    data.shipping_address.strip()
                ),
                notes=(
                    data.notes.strip()
                    if data.notes
                    else None
                ),
            )

            db.add(order)
            db.flush()

            # -------------------------------------------------
            # Create order items + reserve inventory
            # -------------------------------------------------

            for product_id, quantity in (
                product_quantities.items()
            ):

                product = products_by_id[
                    product_id
                ]

                inventory = (
                    inventory_by_product_id[
                        product_id
                    ]
                )

                unit_price = product.price

                item_subtotal = (
                    unit_price * quantity
                )

                order_item = OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=quantity,
                    unit_price=unit_price,
                    subtotal=item_subtotal,
                )

                db.add(order_item)

                previous_reserved = (
                    inventory.reserved_quantity
                )

                inventory.reserved_quantity += (
                    quantity
                )

                db.flush()

                inventory_transaction = (
                    InventoryTransaction(
                        inventory_id=inventory.id,
                        transaction_type=(
                            InventoryTransactionType
                            .RESERVATION
                            .value
                        ),
                        quantity=quantity,
                        previous_quantity=(
                            previous_reserved
                        ),
                        new_quantity=(
                            inventory.reserved_quantity
                        ),
                        amount=(
                            unit_price * quantity
                        ),
                        reason=(
                            "Inventory reserved "
                            "for order"
                        ),
                        reference_id=(
                            order.order_number
                        ),
                        user_id=customer_id,
                    )
                )

                db.add(
                    inventory_transaction
                )

            # -------------------------------------------------
            # Initial status history
            # -------------------------------------------------

            status_history = (
                OrderStatusHistory(
                    order_id=order.id,
                    old_status=None,
                    new_status=(
                        OrderStatus.PENDING.value
                    ),
                    changed_by=customer_id,
                    reason="Order created",
                )
            )

            db.add(status_history)

            db.commit()

            db.refresh(order)

            return order

        except HTTPException:
            db.rollback()
            raise

        except IntegrityError:
            db.rollback()

            # A database-level unique constraint protects against
            # two identical requests arriving at the same time.
            if idempotency_key and request_hash:
                existing_order = db.scalar(
                    select(Order).where(
                        Order.customer_id == customer_id,
                        Order.idempotency_key == idempotency_key,
                    )
                )

                if existing_order:
                    if (
                        existing_order.idempotency_request_hash
                        == request_hash
                    ):
                        return existing_order

                    raise HTTPException(
                        status_code=409,
                        detail=(
                            "The Idempotency-Key has already "
                            "been used for a different request"
                        ),
                    )

            raise HTTPException(
                status_code=409,
                detail="Duplicate order request",
            )

        except Exception:
            db.rollback()

            raise HTTPException(
                status_code=500,
                detail="Failed to create order",
            )

    # =========================================================
    # GET ORDER
    # =========================================================

    @staticmethod
    def get_order(
        db: Session,
        order_id: int,
        customer_id: int | None = None,
    ) -> Order:

        statement = select(Order).where(
            Order.id == order_id
        )

        if customer_id is not None:
            statement = statement.where(
                Order.customer_id == customer_id
            )

        order = db.scalar(statement)

        if not order:
            raise HTTPException(
                status_code=404,
                detail="Order not found",
            )

        return order

    # =========================================================
    # LIST CUSTOMER ORDERS
    # =========================================================

    @staticmethod
    def list_customer_orders(
        db: Session,
        customer_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Order], int]:

        if page < 1:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Page must be greater than 0"
                ),
            )

        if page_size < 1 or page_size > 100:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Page size must be between "
                    "1 and 100"
                ),
            )

        offset = (
            (page - 1) * page_size
        )

        from app.repositories.order_repository import (
            OrderRepository,
        )

        items = (
            OrderRepository.list_customer_orders(
                db=db,
                customer_id=customer_id,
                skip=offset,
                limit=page_size,
            )
        )

        total = (
            OrderRepository.count_customer_orders(
                db=db,
                customer_id=customer_id,
            )
        )

        return items, total

    # =========================================================
    # ORDER HISTORY
    # =========================================================

    @staticmethod
    def get_status_history(
        db: Session,
        order_id: int,
        customer_id: int | None = None,
    ) -> list[OrderStatusHistory]:

        OrderService.get_order(
            db=db,
            order_id=order_id,
            customer_id=customer_id,
        )

        from app.repositories.order_repository import (
            OrderRepository,
        )

        return (
            OrderRepository.get_status_history(
                db=db,
                order_id=order_id,
            )
        )

    # =========================================================
    # ORDER STATE MACHINE
    # =========================================================

    ALLOWED_TRANSITIONS = {

        OrderStatus.PENDING.value: {
            OrderStatus.CONFIRMED.value,
            OrderStatus.CANCELLED.value,
        },

        OrderStatus.CONFIRMED.value: {
            OrderStatus.PROCESSING.value,
            OrderStatus.CANCELLED.value,
        },

        OrderStatus.PROCESSING.value: {
            OrderStatus.PACKED.value,
            OrderStatus.CANCELLED.value,
        },

        OrderStatus.PACKED.value: {
            OrderStatus.SHIPPED.value,
        },

        OrderStatus.SHIPPED.value: {
            OrderStatus.DELIVERED.value,
        },

        OrderStatus.DELIVERED.value: {
            OrderStatus.RETURNED.value,
        },

        OrderStatus.CANCELLED.value: set(),

        OrderStatus.FAILED.value: set(),

        OrderStatus.RETURNED.value: set(),
    }

    # =========================================================
    # UPDATE ORDER STATUS
    # =========================================================

    @staticmethod
    def update_status(
        db: Session,
        order_id: int,
        new_status: str,
        changed_by: int,
        reason: str | None = None,
    ) -> Order:

        try:
            new_status = new_status.upper().strip()

            valid_statuses = {
                status.value
                for status in OrderStatus
            }

            if new_status not in valid_statuses:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Invalid order status "
                        f"'{new_status}'. "
                        f"Allowed statuses: "
                        f"{sorted(valid_statuses)}"
                    ),
                )

            # Lock order row.
            order = db.scalar(
                select(Order)
                .where(
                    Order.id == order_id
                )
                .with_for_update()
            )

            if not order:
                raise HTTPException(
                    status_code=404,
                    detail="Order not found",
                )

            current_status = order.status

            if current_status == new_status:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Order is already in "
                        f"{current_status} status"
                    ),
                )

            allowed_next_statuses = (
                OrderService.ALLOWED_TRANSITIONS.get(
                    current_status,
                    set(),
                )
            )

            if (
                new_status
                not in allowed_next_statuses
            ):
                raise HTTPException(
                    status_code=409,
                    detail=(
                        "Invalid status transition: "
                        f"{current_status} "
                        f"-> {new_status}"
                    ),
                )

            old_status = order.status

            order.status = new_status

            history = OrderStatusHistory(
                order_id=order.id,
                old_status=old_status,
                new_status=new_status,
                changed_by=changed_by,
                reason=reason,
            )

            db.add(history)

            db.commit()

            db.refresh(order)

            return order

        except HTTPException:
            db.rollback()
            raise

        except Exception:
            db.rollback()

            raise HTTPException(
                status_code=500,
                detail=(
                    "Failed to update order status"
                ),
            )

    # =========================================================
    # CANCEL ORDER + RELEASE INVENTORY
    # =========================================================

    @staticmethod
    def cancel_order(
        db: Session,
        order_id: int,
        cancelled_by: int,
        reason: str | None = None,
    ) -> Order:

        try:
            # -------------------------------------------------
            # Lock order AND verify customer ownership
            # -------------------------------------------------

            order = db.scalar(
                select(Order)
                .where(
                    Order.id == order_id,
                    Order.customer_id == cancelled_by,
                )
                .with_for_update()
            )

            if not order:
                raise HTTPException(
                    status_code=404,
                    detail="Order not found",
                )

            # -------------------------------------------------
            # Check cancellation eligibility
            # -------------------------------------------------

            cancellable_statuses = {
                OrderStatus.PENDING.value,
                OrderStatus.CONFIRMED.value,
                OrderStatus.PROCESSING.value,
            }

            if (
                order.status
                not in cancellable_statuses
            ):
                raise HTTPException(
                    status_code=409,
                    detail=(
                        "Order cannot be cancelled "
                        f"from {order.status} status"
                    ),
                )

            # -------------------------------------------------
            # Get order items
            # -------------------------------------------------

            order_items = list(
                db.scalars(
                    select(OrderItem)
                    .where(
                        OrderItem.order_id
                        == order.id
                    )
                ).all()
            )

            if not order_items:
                raise HTTPException(
                    status_code=409,
                    detail=(
                        "Order has no items "
                        "to cancel"
                    ),
                )

            # -------------------------------------------------
            # Release inventory
            # -------------------------------------------------

            for order_item in order_items:

                inventory = db.scalar(
                    select(Inventory)
                    .where(
                        Inventory.product_id
                        == order_item.product_id,
                        Inventory.warehouse_id
                        == order.warehouse_id,
                    )
                    .with_for_update()
                )

                if not inventory:
                    raise HTTPException(
                        status_code=409,
                        detail=(
                            "Inventory not found "
                            "for product "
                            f"{order_item.product_id}"
                        ),
                    )

                quantity_to_release = (
                    order_item.quantity
                )

                if (
                    inventory.reserved_quantity
                    < quantity_to_release
                ):
                    raise HTTPException(
                        status_code=409,
                        detail=(
                            f"Cannot release "
                            f"{quantity_to_release} "
                            f"units for product "
                            f"{order_item.product_id}. "
                            f"Reserved quantity is only "
                            f"{inventory.reserved_quantity}"
                        ),
                    )

                previous_reserved = (
                    inventory.reserved_quantity
                )

                inventory.reserved_quantity -= (
                    quantity_to_release
                )

                db.flush()

                release_transaction = (
                    InventoryTransaction(
                        inventory_id=inventory.id,
                        transaction_type=(
                            InventoryTransactionType
                            .RELEASE
                            .value
                        ),
                        quantity=(
                            quantity_to_release
                        ),
                        previous_quantity=(
                            previous_reserved
                        ),
                        new_quantity=(
                            inventory.reserved_quantity
                        ),
                        amount=(
                            order_item.unit_price
                            * quantity_to_release
                        ),
                        reason=(
                            reason
                            or
                            "Inventory reservation "
                            "released because "
                            "order was cancelled"
                        ),
                        reference_id=(
                            order.order_number
                        ),
                        user_id=cancelled_by,
                    )
                )

                db.add(
                    release_transaction
                )

            # -------------------------------------------------
            # Change order status
            # -------------------------------------------------

            old_status = order.status

            order.status = (
                OrderStatus.CANCELLED.value
            )

            # -------------------------------------------------
            # Create status history
            # -------------------------------------------------

            history = OrderStatusHistory(
                order_id=order.id,
                old_status=old_status,
                new_status=(
                    OrderStatus.CANCELLED.value
                ),
                changed_by=cancelled_by,
                reason=(
                    reason
                    or "Order cancelled"
                ),
            )

            db.add(history)

            # -------------------------------------------------
            # Atomic commit
            # -------------------------------------------------

            db.commit()

            db.refresh(order)

            return order

        except HTTPException:
            db.rollback()
            raise

        except Exception:
            db.rollback()

            raise HTTPException(
                status_code=500,
                detail=(
                    "Failed to cancel order"
                ),
            )

    # =========================================================
    # ASSIGN FULFILLMENT AGENT
    # =========================================================

    @staticmethod
    def assign_agent(
        db: Session,
        order_id: int,
        agent_id: int,
        assigned_by: int,
    ) -> Order:

        try:
            # -------------------------------------------------
            # Lock order
            # -------------------------------------------------

            order = db.scalar(
                select(Order)
                .where(
                    Order.id == order_id
                )
                .with_for_update()
            )

            if not order:
                raise HTTPException(
                    status_code=404,
                    detail="Order not found",
                )

            # -------------------------------------------------
            # Get agent
            # -------------------------------------------------

            agent = db.scalar(
                select(User)
                .where(
                    User.id == agent_id
                )
            )

            if not agent:
                raise HTTPException(
                    status_code=404,
                    detail=(
                        "Fulfillment agent "
                        "not found"
                    ),
                )

            if not agent.is_active:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Fulfillment agent "
                        "is inactive"
                    ),
                )

            if not agent.role:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Agent role is not "
                        "configured"
                    ),
                )

            if (
                agent.role.name
                != "Fulfillment Agent"
            ):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Selected user is not "
                        "a Fulfillment Agent"
                    ),
                )

            # -------------------------------------------------
            # Verify warehouse assignment
            # -------------------------------------------------

            assignment = db.scalar(
                select(WarehouseUser)
                .where(
                    WarehouseUser.user_id
                    == agent_id,
                    WarehouseUser.warehouse_id
                    == order.warehouse_id,
                    WarehouseUser.is_active.is_(
                        True
                    ),
                )
            )

            if not assignment:
                raise HTTPException(
                    status_code=403,
                    detail=(
                        "Fulfillment Agent is not "
                        "assigned to this order's "
                        "warehouse"
                    ),
                )

            # -------------------------------------------------
            # Assign agent
            # -------------------------------------------------

            previous_agent_id = (
                order.assigned_agent_id
            )

            order.assigned_agent_id = agent_id

            history_reason = (
                f"Fulfillment Agent {agent_id} "
                f"assigned"
            )

            if previous_agent_id:
                history_reason = (
                    f"Fulfillment Agent changed "
                    f"from {previous_agent_id} "
                    f"to {agent_id}"
                )

            history = OrderStatusHistory(
                order_id=order.id,
                old_status=order.status,
                new_status=order.status,
                changed_by=assigned_by,
                reason=history_reason,
            )

            db.add(history)

            db.commit()

            db.refresh(order)

            return order

        except HTTPException:
            db.rollback()
            raise

        except Exception:
            db.rollback()

            raise HTTPException(
                status_code=500,
                detail=(
                    "Failed to assign "
                    "fulfillment agent"
                ),
            )