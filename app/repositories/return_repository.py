from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.return_request import (
    ReturnRequest,
    ReturnItem,
)


class ReturnRepository:

    @staticmethod
    def get_by_id(
        db: Session,
        return_id: int,
    ) -> ReturnRequest | None:

        return db.scalar(
            select(ReturnRequest)
            .where(ReturnRequest.id == return_id)
        )

    @staticmethod
    def get_by_order_id(
        db: Session,
        order_id: int,
    ) -> ReturnRequest | None:

        return db.scalar(
            select(ReturnRequest)
            .where(ReturnRequest.order_id == order_id)
        )

    @staticmethod
    def get_by_id_for_update(
        db: Session,
        return_id: int,
    ) -> ReturnRequest | None:

        return db.scalar(
            select(ReturnRequest)
            .where(ReturnRequest.id == return_id)
            .with_for_update()
        )

    @staticmethod
    def create(
        db: Session,
        return_request: ReturnRequest,
    ) -> ReturnRequest:

        db.add(return_request)
        db.flush()

        return return_request

    @staticmethod
    def create_item(
        db: Session,
        item: ReturnItem,
    ) -> ReturnItem:

        db.add(item)
        db.flush()

        return item