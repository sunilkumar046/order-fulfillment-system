from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.product import Product
from app.repositories.category_repository import CategoryRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
)


class ProductService:

    @staticmethod
    def create(
        db: Session,
        data: ProductCreate,
    ) -> Product:

        existing = ProductRepository.get_by_sku(
            db=db,
            sku=data.sku,
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Product SKU already exists",
            )

        category = CategoryRepository.get_by_id(
            db=db,
            category_id=data.category_id,
        )

        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found",
            )

        product = Product(
            sku=data.sku.strip().upper(),
            name=data.name.strip(),
            description=(
                data.description.strip()
                if data.description
                else None
            ),
            category_id=data.category_id,
            price=data.price,
            is_active=data.is_active,
        )

        try:
            ProductRepository.create(
                db=db,
                product=product,
            )

            db.commit()
            db.refresh(product)

            return product

        except Exception:
            db.rollback()
            raise

    @staticmethod
    def get(
        db: Session,
        product_id: int,
    ) -> Product:

        product = ProductRepository.get_by_id(
            db=db,
            product_id=product_id,
        )

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found",
            )

        return product

    @staticmethod
    def list_all(
        db: Session,
    ) -> list[Product]:

        return ProductRepository.list_all(db=db)

    @staticmethod
    def list_active(
        db: Session,
    ) -> list[Product]:

        return ProductRepository.list_active(db=db)

    @staticmethod
    def update(
        db: Session,
        product_id: int,
        data: ProductUpdate,
    ) -> Product:

        product = ProductService.get(
            db=db,
            product_id=product_id,
        )

        changes = data.model_dump(
            exclude_unset=True,
            exclude_none=True,
        )

        if not changes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields provided for update",
            )

        if "category_id" in changes:
            category = CategoryRepository.get_by_id(
                db=db,
                category_id=changes["category_id"],
            )

            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Category not found",
                )

        if "name" in changes:
            changes["name"] = changes["name"].strip()

        if "description" in changes:
            changes["description"] = (
                changes["description"].strip()
                if changes["description"]
                else None
            )

        for field, value in changes.items():
            setattr(product, field, value)

        try:
            db.commit()
            db.refresh(product)

            return product

        except Exception:
            db.rollback()
            raise