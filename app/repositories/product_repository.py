from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.product import Product


class ProductRepository:

    @staticmethod
    def get_by_id(
        db: Session,
        product_id: int,
    ) -> Product | None:
        return db.scalar(
            select(Product).where(
                Product.id == product_id
            )
        )

    @staticmethod
    def get_by_sku(
        db: Session,
        sku: str,
    ) -> Product | None:
        return db.scalar(
            select(Product).where(
                Product.sku == sku
            )
        )

    @staticmethod
    def list_all(
        db: Session,
    ) -> list[Product]:
        return list(
            db.scalars(
                select(Product)
                .order_by(Product.id)
            ).all()
        )

    @staticmethod
    def list_active(
        db: Session,
    ) -> list[Product]:
        return list(
            db.scalars(
                select(Product)
                .where(Product.is_active.is_(True))
                .order_by(Product.id)
            ).all()
        )

    @staticmethod
    def create(
        db: Session,
        product: Product,
    ) -> Product:
        db.add(product)
        db.flush()
        db.refresh(product)
        return product