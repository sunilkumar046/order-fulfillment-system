from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.auth import require_role
from app.models.user import User
from app.schemas.inventory_transfer import (
    InventoryTransferCreate,
    InventoryTransferResponse,
)
from app.services.inventory_transfer_service import (
    InventoryTransferService,
)


router = APIRouter(
    prefix="/api/inventory-transfers",
    tags=["Inventory Transfers"],
)


@router.post(
    "",
    response_model=InventoryTransferResponse,
    status_code=status.HTTP_201_CREATED,
)
def transfer_inventory(
    data: InventoryTransferCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(
            "Admin",
            "Warehouse Manager",
        )
    ),
):
    return InventoryTransferService.transfer_inventory(
        db=db,
        data=data,
        current_user=current_user,
    )