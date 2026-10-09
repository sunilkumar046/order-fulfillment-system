from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.inventory_transfer import InventoryTransfer


class InventoryTransferRepository:

    @staticmethod
    def create(
        db: Session,
        transfer: InventoryTransfer,
    ) -> InventoryTransfer:
        db.add(transfer)
        db.flush()
        db.refresh(transfer)

        return transfer

    @staticmethod
    def get_by_id(
        db: Session,
        transfer_id: int,
    ) -> InventoryTransfer | None:
        return db.scalar(
            select(InventoryTransfer).where(
                InventoryTransfer.id == transfer_id
            )
        )

    @staticmethod
    def list_all(
        db: Session,
        skip: int = 0,
        limit: int = 20,
    ) -> list[InventoryTransfer]:
        return list(
            db.scalars(
                select(InventoryTransfer)
                .order_by(
                    InventoryTransfer.created_at.desc()
                )
                .offset(skip)
                .limit(limit)
            ).all()
        )