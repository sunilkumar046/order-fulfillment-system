from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.refresh_token import RefreshToken
from app.models.role import Role
from app.models.user import User


class AuthRepository:

    @staticmethod
    def get_user_by_id(
        db: Session,
        user_id: int,
    ) -> User | None:
        return db.scalar(
            select(User).where(User.id == user_id)
        )

    @staticmethod
    def get_user_by_email(
        db: Session,
        email: str,
    ) -> User | None:
        return db.scalar(
            select(User).where(User.email == email.lower())
        )

    @staticmethod
    def get_role_by_name(
        db: Session,
        role_name: str,
    ) -> Role | None:
        return db.scalar(
            select(Role).where(Role.name == role_name)
        )

    @staticmethod
    def create_user(
        db: Session,
        user: User,
    ) -> User:
        db.add(user)
        db.flush()
        db.refresh(user)
        return user

    @staticmethod
    def create_refresh_token(
        db: Session,
        refresh_token: RefreshToken,
    ) -> RefreshToken:
        db.add(refresh_token)
        db.flush()
        db.refresh(refresh_token)
        return refresh_token

    @staticmethod
    def get_refresh_token_by_hash(
        db: Session,
        token_hash: str,
    ) -> RefreshToken | None:
        return db.scalar(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash
            )
        )

    @staticmethod
    def revoke_refresh_token(
        db: Session,
        refresh_token: RefreshToken,
    ) -> RefreshToken:
        from datetime import datetime, timezone

        refresh_token.revoked_at = datetime.now(timezone.utc)

        db.add(refresh_token)
        db.flush()
        db.refresh(refresh_token)

        return refresh_token

    @staticmethod
    def revoke_all_user_refresh_tokens(
        db: Session,
        user_id: int,
    ) -> None:
        from datetime import datetime, timezone

        tokens = list(
            db.scalars(
                select(RefreshToken).where(
                    RefreshToken.user_id == user_id,
                    RefreshToken.revoked_at.is_(None),
                )
            ).all()
        )

        now = datetime.now(timezone.utc)

        for token in tokens:
            token.revoked_at = now

        db.flush()