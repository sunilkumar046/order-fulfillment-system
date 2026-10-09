from fastapi import (
    APIRouter,
    Depends,
    Header,
    Query,
    status,
)
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.auth import require_role
from app.models.user import User
from app.schemas.order import (
    OrderAssignmentRequest,
    OrderCreate,
    OrderListResponse,
    OrderResponse,
    OrderStatusHistoryResponse,
    OrderStatusUpdate,
)
from app.services.order_service import OrderService


router = APIRouter(
    prefix="/api/orders",
    tags=["Orders"],
)


# =========================================================
# CUSTOMER - CREATE ORDER
# =========================================================


@router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_order(
    data: OrderCreate,
    idempotency_key: str | None = Header(
        default=None,
        alias="Idempotency-Key",
        max_length=100,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("Customer")
    ),
):
    return OrderService.create_order(
        db=db,
        data=data,
        customer_id=current_user.id,
        idempotency_key=idempotency_key,
    )


# =========================================================
# CUSTOMER - LIST MY ORDERS
# =========================================================


@router.get(
    "",
    response_model=OrderListResponse,
)
def list_my_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(
        20,
        ge=1,
        le=100,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("Customer")
    ),
):
    items, total = (
        OrderService.list_customer_orders(
            db=db,
            customer_id=current_user.id,
            page=page,
            page_size=page_size,
        )
    )

    return OrderListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


# =========================================================
# CUSTOMER - ORDER HISTORY
# =========================================================


@router.get(
    "/{order_id}/history",
    response_model=list[
        OrderStatusHistoryResponse
    ],
)
def get_my_order_history(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("Customer")
    ),
):
    return OrderService.get_status_history(
        db=db,
        order_id=order_id,
        customer_id=current_user.id,
    )


# =========================================================
# CUSTOMER - CANCEL ORDER
# =========================================================


@router.post(
    "/{order_id}/cancel",
    response_model=OrderResponse,
)
def cancel_my_order(
    order_id: int,
    reason: str | None = Query(
        default=None,
        max_length=500,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("Customer")
    ),
):
    return OrderService.cancel_order(
        db=db,
        order_id=order_id,
        cancelled_by=current_user.id,
        reason=reason,
    )


# =========================================================
# STAFF - ASSIGN FULFILLMENT AGENT
# =========================================================


@router.post(
    "/{order_id}/assign-agent",
    response_model=OrderResponse,
)
def assign_fulfillment_agent(
    order_id: int,
    data: OrderAssignmentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(
            "Admin",
            "Warehouse Manager",
        )
    ),
):
    return OrderService.assign_agent(
        db=db,
        order_id=order_id,
        agent_id=data.agent_id,
        assigned_by=current_user.id,
    )


# =========================================================
# STAFF - UPDATE ORDER STATUS
# =========================================================


@router.patch(
    "/{order_id}/status",
    response_model=OrderResponse,
)
def update_order_status(
    order_id: int,
    data: OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(
            "Admin",
            "Warehouse Manager",
            "Fulfillment Agent",
        )
    ),
):
    return OrderService.update_status(
        db=db,
        order_id=order_id,
        new_status=data.status,
        changed_by=current_user.id,
        reason=data.reason,
    )


# =========================================================
# CUSTOMER - GET MY ORDER
# =========================================================


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
)
def get_my_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("Customer")
    ),
):
    return OrderService.get_order(
        db=db,
        order_id=order_id,
        customer_id=current_user.id,
    )