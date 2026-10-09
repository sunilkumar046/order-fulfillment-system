from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.warehouse_user import WarehouseUser


def ensure_warehouse_access(
    db: Session,
    current_user: User,
    warehouse_id: int,
) -> None:
    """
    Verify that the current user can access the specified warehouse.

    Admin:
        Can access every warehouse.

    Warehouse Manager / Fulfillment Agent:
        Can access only warehouses assigned to them.

    Other roles:
        Cannot access warehouses.
    """

    if current_user.role is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User role is not configured",
        )

    # Admin has access to every warehouse.
    if current_user.role.name == "Admin":
        return

    # Only these roles can work with warehouse-scoped resources.
    if current_user.role.name not in {
        "Warehouse Manager",
        "Fulfillment Agent",
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have warehouse access",
        )

    assignment = db.scalar(
        select(WarehouseUser).where(
            WarehouseUser.warehouse_id == warehouse_id,
            WarehouseUser.user_id == current_user.id,
            WarehouseUser.is_active.is_(True),
        )
    )

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this warehouse",
        )


def require_warehouse_access(
    warehouse_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    FastAPI dependency for endpoints where warehouse_id
    is part of the URL path.
    """

    ensure_warehouse_access(
        db=db,
        current_user=current_user,
        warehouse_id=warehouse_id,
    )

    return current_user