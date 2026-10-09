from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.auth import get_current_user, require_role
from app.models.user import User
from app.schemas.return_request import (
    ReturnRejectRequest,
    ReturnRequestCreate,
    ReturnRequestResponse,
)
from app.services.return_service import ReturnService


router = APIRouter(
    prefix="/api/returns",
    tags=["Returns"],
)


@router.post(
    "/orders/{order_id}",
    response_model=ReturnRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_return_request(
    order_id: int,
    data: ReturnRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("Customer")
    ),
):

    return ReturnService.create_return_request(
        db=db,
        order_id=order_id,
        customer_id=current_user.id,
        data=data,
    )


@router.get(
    "/{return_id}",
    response_model=ReturnRequestResponse,
)
def get_return_request(
    return_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    return ReturnService.get_return(
        db=db,
        return_id=return_id,
        user=current_user,
    )


@router.post(
    "/{return_id}/approve",
    response_model=ReturnRequestResponse,
)
def approve_return(
    return_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(
            "Admin",
            "Warehouse Manager",
        )
    ),
):

    return ReturnService.approve_return(
        db=db,
        return_id=return_id,
        approved_by=current_user.id,
    )


@router.post(
    "/{return_id}/reject",
    response_model=ReturnRequestResponse,
)
def reject_return(
    return_id: int,
    data: ReturnRejectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(
            "Admin",
            "Warehouse Manager",
        )
    ),
):

    return ReturnService.reject_return(
        db=db,
        return_id=return_id,
        rejected_by=current_user.id,
        reason=data.reason,
    )