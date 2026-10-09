from datetime import datetime, timezone
import hashlib
import secrets

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories.auth_repository import AuthRepository
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
)


class AuthService:

    @staticmethod
    def _hash_refresh_token(token: str) -> str:
        return hashlib.sha256(
            token.encode("utf-8")
        ).hexdigest()

    @staticmethod
    def _generate_refresh_token(
        db: Session,
        user_id: int,
    ) -> str:

        raw_token = secrets.token_urlsafe(64)

        token_hash = AuthService._hash_refresh_token(
            raw_token
        )

        expires_at = (
            datetime.now(timezone.utc)
            .replace(microsecond=0)
        )

        from datetime import timedelta

        expires_at = expires_at + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

        refresh_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )

        AuthRepository.create_refresh_token(
            db,
            refresh_token,
        )

        return raw_token

    @staticmethod
    def register(
        db: Session,
        data: RegisterRequest,
    ) -> User:

        existing_user = AuthRepository.get_user_by_email(
            db,
            data.email,
        )

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email is already registered",
            )

        role = AuthRepository.get_role_by_name(
            db,
            data.role,
        )

        if not role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role: {data.role}",
            )

        user = User(
            full_name=data.full_name.strip(),
            email=data.email.lower(),
            password_hash=hash_password(data.password),
            role_id=role.id,
            is_active=True,
        )

        try:
            user = AuthRepository.create_user(
                db,
                user,
            )

            db.commit()
            db.refresh(user)

            return user

        except Exception:
            db.rollback()
            raise

    @staticmethod
    def login(
        db: Session,
        data: LoginRequest,
    ) -> dict:

        user = AuthRepository.get_user_by_email(
            db,
            data.email,
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not verify_password(
            data.password,
            user.password_hash,
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )

        access_token = create_access_token(
            user_id=user.id,
            role=user.role.name,
        )

        refresh_token = AuthService._generate_refresh_token(
            db,
            user.id,
        )

        try:
            db.commit()
        except Exception:
            db.rollback()
            raise

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    @staticmethod
    def refresh(
        db: Session,
        data: RefreshTokenRequest,
    ) -> dict:

        token_hash = AuthService._hash_refresh_token(
            data.refresh_token
        )

        stored_token = (
            AuthRepository.get_refresh_token_by_hash(
                db,
                token_hash,
            )
        )

        if not stored_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        now = datetime.now(timezone.utc)

        if stored_token.revoked_at is not None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked",
            )

        if stored_token.expires_at <= now:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired",
            )

        user = AuthRepository.get_user_by_id(
            db,
            stored_token.user_id,
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User associated with token was not found",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )

        # Rotate the refresh token.
        AuthRepository.revoke_refresh_token(
            db,
            stored_token,
        )

        access_token = create_access_token(
            user_id=user.id,
            role=user.role.name,
        )

        new_refresh_token = AuthService._generate_refresh_token(
            db,
            user.id,
        )

        try:
            db.commit()
        except Exception:
            db.rollback()
            raise

        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        }

    @staticmethod
    def logout(
        db: Session,
        data: RefreshTokenRequest,
    ) -> None:

        token_hash = AuthService._hash_refresh_token(
            data.refresh_token
        )

        stored_token = (
            AuthRepository.get_refresh_token_by_hash(
                db,
                token_hash,
            )
        )

        if not stored_token:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Refresh token not found",
            )

        if stored_token.revoked_at is not None:
            return

        AuthRepository.revoke_refresh_token(
            db,
            stored_token,
        )

        db.commit()

    @staticmethod
    def get_current_user(
        db: Session,
        user_id: int,
    ) -> User:

        user = AuthRepository.get_user_by_id(
            db,
            user_id,
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )

        return user

    @staticmethod
    def change_password(
        db: Session,
        user: User,
        data: ChangePasswordRequest,
    ) -> None:

        if not verify_password(
            data.current_password,
            user.password_hash,
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect",
            )

        if data.current_password == data.new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be different from current password",
            )

        user.password_hash = hash_password(
            data.new_password
        )

        # Changing a password invalidates existing refresh
        # sessions for security.
        AuthRepository.revoke_all_user_refresh_tokens(
            db,
            user.id,
        )

        db.add(user)

        try:
            db.commit()
        except Exception:
            db.rollback()
            raise