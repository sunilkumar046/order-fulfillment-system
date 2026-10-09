from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.auth import require_role
from app.models.user import User
from app.schemas.inventory import (
    InventoryCreate,
    InventoryListResponse,
    InventoryResponse,
    InventoryTransactionResponse,
    InventoryUpdate,
)
from app.services.inventory_service import InventoryService


router = APIRouter(
    prefix="/api/inventory",
    tags=["Inventory"],
)


@router.post(
    "",
    response_model=InventoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_inventory(
    data: InventoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("Admin", "Warehouse Manager")
    ),
):
    return InventoryService.create_inventory(
        db=db,
        data=data,
        user_id=current_user.id,
        current_user=current_user,
    )


@router.get(
    "",
    response_model=InventoryListResponse,
)
def list_inventory(
    warehouse_id: int | None = Query(
        default=None,
        gt=0,
    ),
    page: int = Query(
        default=1,
        ge=1,
    ),
    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(
            "Admin",
            "Warehouse Manager",
            "Fulfillment Agent",
        )
    ),
):
    items, total = InventoryService.list_inventory(
        db=db,
        current_user=current_user,
        page=page,
        page_size=page_size,
        warehouse_id=warehouse_id,
    )

    return InventoryListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/product/{product_id}/warehouse/{warehouse_id}",
    response_model=InventoryResponse,
)
def get_inventory_by_product_and_warehouse(
    product_id: int,
    warehouse_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(
            "Admin",
            "Warehouse Manager",
            "Fulfillment Agent",
        )
    ),
):
    return InventoryService.get_inventory_by_product_and_warehouse(
        db=db,
        product_id=product_id,
        warehouse_id=warehouse_id,
        current_user=current_user,
    )


@router.post(
    "/{inventory_id}/reserve",
    response_model=InventoryResponse,
)
def reserve_inventory(
    inventory_id: int,
    quantity: int = Query(..., gt=0),
    reference_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(
            "Admin",
            "Warehouse Manager",
            "Fulfillment Agent",
        )
    ),
):
    return InventoryService.reserve_inventory(
        db=db,
        inventory_id=inventory_id,
        quantity=quantity,
        user_id=current_user.id,
        current_user=current_user,
        reference_id=reference_id,
    )


@router.post(
    "/{inventory_id}/release",
    response_model=InventoryResponse,
)
def release_inventory(
    inventory_id: int,
    quantity: int = Query(..., gt=0),
    reference_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(
            "Admin",
            "Warehouse Manager",
            "Fulfillment Agent",
        )
    ),
):
    return InventoryService.release_inventory(
        db=db,
        inventory_id=inventory_id,
        quantity=quantity,
        user_id=current_user.id,
        current_user=current_user,
        reference_id=reference_id,
    )


@router.get(
    "/{inventory_id}/transactions",
    response_model=list[InventoryTransactionResponse],
)
def get_inventory_transactions(
    inventory_id: int,
    page: int = Query(
        default=1,
        ge=1,
    ),
    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(
            "Admin",
            "Warehouse Manager",
            "Fulfillment Agent",
        )
    ),
):
    return InventoryService.get_transactions(
        db=db,
        inventory_id=inventory_id,
        current_user=current_user,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{inventory_id}",
    response_model=InventoryResponse,
)
def get_inventory(
    inventory_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(
            "Admin",
            "Warehouse Manager",
            "Fulfillment Agent",
        )
    ),
):
    return InventoryService.get_inventory(
        db=db,
        inventory_id=inventory_id,
        current_user=current_user,
    )


@router.patch(
    "/{inventory_id}",
    response_model=InventoryResponse,
)
def update_inventory(
    inventory_id: int,
    data: InventoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(
            "Admin",
            "Warehouse Manager",
        )
    ),
):
    return InventoryService.update_inventory(
        db=db,
        inventory_id=inventory_id,
        data=data,
        user_id=current_user.id,
        current_user=current_user,
    )