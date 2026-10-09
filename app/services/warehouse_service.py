from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.warehouse import Warehouse
from app.models.warehouse_user import WarehouseUser
from app.repositories.warehouse_repository import WarehouseRepository
from app.schemas.warehouse import WarehouseCreate, WarehouseUpdate


class WarehouseService:

    @staticmethod
    def create(
        db: Session,
        data: WarehouseCreate,
    ) -> Warehouse:

        existing = WarehouseRepository.get_by_code(
            db=db,
            code=data.code.strip().upper(),
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Warehouse code already exists",
            )

        warehouse = Warehouse(
            name=data.name.strip(),
            code=data.code.strip().upper(),
            address=data.address.strip(),
            city=data.city.strip(),
            state=data.state.strip(),
            country=data.country.strip(),
            is_active=True,
        )

        WarehouseRepository.create(
            db=db,
            warehouse=warehouse,
        )

        db.commit()
        db.refresh(warehouse)

        return warehouse

    @staticmethod
    def get(
        db: Session,
        warehouse_id: int,
    ) -> Warehouse:

        warehouse = WarehouseRepository.get_by_id(
            db=db,
            warehouse_id=warehouse_id,
        )

        if not warehouse:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Warehouse not found",
            )

        return warehouse

    @staticmethod
    def list_all(
        db: Session,
    ) -> list[Warehouse]:

        return WarehouseRepository.list_all(db=db)

    @staticmethod
    def update(
        db: Session,
        warehouse_id: int,
        data: WarehouseUpdate,
    ) -> Warehouse:

        warehouse = WarehouseService.get(
            db=db,
            warehouse_id=warehouse_id,
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

        for field, value in changes.items():
            if isinstance(value, str):
                value = value.strip()

            setattr(warehouse, field, value)

        db.add(warehouse)
        db.commit()
        db.refresh(warehouse)

        return warehouse

    @staticmethod
    def assign_user(
        db: Session,
        warehouse_id: int,
        user_id: int,
    ) -> WarehouseUser:

        warehouse = WarehouseService.get(
            db=db,
            warehouse_id=warehouse_id,
        )

        if not warehouse.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot assign users to an inactive warehouse",
            )

        # Verify user exists.
        user = db.scalar(
            select(User).where(User.id == user_id)
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # User must be active.
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot assign an inactive user",
            )

        # Only warehouse-scoped operational roles can be assigned.
        allowed_roles = {
            "Warehouse Manager",
            "Fulfillment Agent",
        }

        if user.role is None or user.role.name not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Only Warehouse Manager or Fulfillment Agent "
                    "users can be assigned to a warehouse"
                ),
            )

        existing = WarehouseRepository.get_assignment(
            db=db,
            warehouse_id=warehouse_id,
            user_id=user_id,
        )

        if existing:

            if existing.is_active:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="User is already assigned to this warehouse",
                )

            # Reactivate previous assignment.
            existing.is_active = True

            db.add(existing)
            db.commit()
            db.refresh(existing)

            return existing

        assignment = WarehouseUser(
            warehouse_id=warehouse_id,
            user_id=user_id,
            is_active=True,
        )

        WarehouseRepository.create_assignment(
            db=db,
            assignment=assignment,
        )

        db.commit()
        db.refresh(assignment)

        return assignment

    @staticmethod
    def get_user_warehouses(
        db: Session,
        user_id: int,
    ) -> list[Warehouse]:

        return WarehouseRepository.get_user_warehouses(
            db=db,
            user_id=user_id,
        )