from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.auth import require_role
from app.models.user import User
from app.schemas.product import (
    ProductCreate,
    ProductResponse,
    ProductUpdate,
)
from app.services.product_service import ProductService


router = APIRouter(
    prefix="/api/products",
    tags=["Products"],
)


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_product(
    data: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(
            "Admin",
            "Warehouse Manager",
        )
    ),
):
    return ProductService.create(
        db=db,
        data=data,
    )


@router.get(
    "",
    response_model=list[ProductResponse],
)
def list_products(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(
            "Admin",
            "Warehouse Manager",
            "Fulfillment Agent",
            "Customer",
        )
    ),
):
    return ProductService.list_all(db=db)


@router.get(
    "/active",
    response_model=list[ProductResponse],
)
def list_active_products(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(
            "Admin",
            "Warehouse Manager",
            "Fulfillment Agent",
            "Customer",
        )
    ),
):
    return ProductService.list_active(db=db)


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(
            "Admin",
            "Warehouse Manager",
            "Fulfillment Agent",
            "Customer",
        )
    ),
):
    return ProductService.get(
        db=db,
        product_id=product_id,
    )


@router.patch(
    "/{product_id}",
    response_model=ProductResponse,
)
def update_product(
    product_id: int,
    data: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(
            "Admin",
            "Warehouse Manager",
        )
    ),
):
    return ProductService.update(
        db=db,
        product_id=product_id,
        data=data,
    )