from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.auth import get_current_user, require_role
from app.models.user import User
from app.schemas.warehouse import (
    WarehouseAssignmentCreate,
    WarehouseAssignmentResponse,
    WarehouseCreate,
    WarehouseResponse,
    WarehouseUpdate,
)
from app.services.warehouse_service import WarehouseService


router = APIRouter(
    prefix="/api/warehouses",
    tags=["Warehouses"],
)


@router.post(
    "",
    response_model=WarehouseResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_warehouse(
    data: WarehouseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("Admin")
    ),
):
    return WarehouseService.create(
        db=db,
        data=data,
    )


@router.get(
    "",
    response_model=list[WarehouseResponse],
)
def list_warehouses(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(
            "Admin",
            "Warehouse Manager",
            "Fulfillment Agent",
        )
    ),
):
    if current_user.role.name == "Admin":
        return WarehouseService.list_all(db=db)

    return WarehouseService.get_user_warehouses(
        db=db,
        user_id=current_user.id,
    )


@router.get(
    "/{warehouse_id}",
    response_model=WarehouseResponse,
)
def get_warehouse(
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
    warehouse = WarehouseService.get(
        db=db,
        warehouse_id=warehouse_id,
    )

    if current_user.role.name != "Admin":
        assigned_warehouses = WarehouseService.get_user_warehouses(
            db=db,
            user_id=current_user.id,
        )

        if warehouse.id not in [
            item.id for item in assigned_warehouses
        ]:
            from fastapi import HTTPException

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this warehouse",
            )

    return warehouse


@router.patch(
    "/{warehouse_id}",
    response_model=WarehouseResponse,
)
def update_warehouse(
    warehouse_id: int,
    data: WarehouseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("Admin")
    ),
):
    return WarehouseService.update(
        db=db,
        warehouse_id=warehouse_id,
        data=data,
    )


@router.post(
    "/{warehouse_id}/assign",
    response_model=WarehouseAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def assign_user(
    warehouse_id: int,
    data: WarehouseAssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("Admin")
    ),
):
    return WarehouseService.assign_user(
        db=db,
        warehouse_id=warehouse_id,
        data=data,
    )