from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.category import Category
from app.repositories.category_repository import CategoryRepository
from app.schemas.category import (
    CategoryCreate,
    CategoryUpdate,
)


class CategoryService:

    @staticmethod
    def create(
        db: Session,
        data: CategoryCreate,
    ) -> Category:

        name = data.name.strip()

        existing = CategoryRepository.get_by_name(
            db=db,
            name=name,
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Category already exists",
            )

        category = Category(
            name=name,
            description=(
                data.description.strip()
                if data.description
                else None
            ),
        )

        try:
            category = CategoryRepository.create(
                db=db,
                category=category,
            )

            db.commit()
            db.refresh(category)

            return category

        except Exception:
            db.rollback()
            raise

    @staticmethod
    def get(
        db: Session,
        category_id: int,
    ) -> Category:

        category = CategoryRepository.get_by_id(
            db=db,
            category_id=category_id,
        )

        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found",
            )

        return category

    @staticmethod
    def list_all(
        db: Session,
    ) -> list[Category]:

        return CategoryRepository.list_all(db=db)

    @staticmethod
    def update(
        db: Session,
        category_id: int,
        data: CategoryUpdate,
    ) -> Category:

        category = CategoryService.get(
            db=db,
            category_id=category_id,
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

        if "name" in changes:
            new_name = changes["name"].strip()

            existing = CategoryRepository.get_by_name(
                db=db,
                name=new_name,
            )

            if existing and existing.id != category.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Category name already exists",
                )

            changes["name"] = new_name

        if "description" in changes:
            changes["description"] = (
                changes["description"].strip()
                if changes["description"]
                else None
            )

        for field, value in changes.items():
            setattr(category, field, value)

        try:
            db.commit()
            db.refresh(category)

            return category

        except Exception:
            db.rollback()
            raise