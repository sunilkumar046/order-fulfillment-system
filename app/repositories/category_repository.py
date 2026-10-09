from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.category import Category


class CategoryRepository:

    @staticmethod
    def get_by_id(
        db: Session,
        category_id: int,
    ) -> Category | None:
        return db.scalar(
            select(Category).where(
                Category.id == category_id
            )
        )

    @staticmethod
    def get_by_name(
        db: Session,
        name: str,
    ) -> Category | None:
        return db.scalar(
            select(Category).where(
                Category.name == name
            )
        )

    @staticmethod
    def list_all(
        db: Session,
    ) -> list[Category]:
        return list(
            db.scalars(
                select(Category)
                .order_by(Category.id)
            ).all()
        )

    @staticmethod
    def create(
        db: Session,
        category: Category,
    ) -> Category:
        db.add(category)
        db.flush()
        db.refresh(category)
        return category