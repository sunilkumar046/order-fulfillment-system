from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.exceptions import AppException


async def app_exception_handler(
    request: Request,
    exc: AppException,
):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.message,
            "error_code": exc.error_code,
            "details": exc.details,
        },
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": "Request validation failed",
            "error_code": "VALIDATION_ERROR",
            "details": exc.errors(),
        },
    )


async def integrity_error_handler(
    request: Request,
    exc: IntegrityError,
):
    return JSONResponse(
        status_code=409,
        content={
            "success": False,
            "message": "Database constraint violation",
            "error_code": "DATABASE_CONFLICT",
            "details": None,
        },
    )


async def sqlalchemy_error_handler(
    request: Request,
    exc: SQLAlchemyError,
):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "A database error occurred",
            "error_code": "DATABASE_ERROR",
            "details": None,
        },
    )


async def general_exception_handler(
    request: Request,
    exc: Exception,
):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "An unexpected server error occurred",
            "error_code": "INTERNAL_SERVER_ERROR",
            "details": None,
        },
    )