from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.config import settings
from app.core.exceptions import AppException
from app.core.exception_handlers import (
    app_exception_handler,
    validation_exception_handler,
    integrity_error_handler,
    sqlalchemy_error_handler,
    general_exception_handler,
)

from app.routers.auth import router as auth_router
from app.routers.inventory import router as inventory_router
from app.routers.warehouse import router as warehouse_router
from app.routers.category import router as category_router
from app.routers.product import router as product_router
from app.routers.order import router as order_router
from app.routers.return_request import router as return_router
from app.routers.inventory_transfer import (
    router as inventory_transfer_router,
)
from app.routers.notification import (
    router as notification_router,
)
from app.routers.audit_log import (
    router as audit_log_router,
)
from app.routers.dashboard import router as dashboard_router
from app.routers.report import router as report_router


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Order Fulfillment & Inventory Management Platform",
)


# ============================================================
# EXCEPTION HANDLERS
# ============================================================

app.add_exception_handler(
    AppException,
    app_exception_handler,
)

app.add_exception_handler(
    RequestValidationError,
    validation_exception_handler,
)

app.add_exception_handler(
    IntegrityError,
    integrity_error_handler,
)

app.add_exception_handler(
    SQLAlchemyError,
    sqlalchemy_error_handler,
)

app.add_exception_handler(
    Exception,
    general_exception_handler,
)


# ============================================================
# ROUTERS
# ============================================================

app.include_router(auth_router)
app.include_router(inventory_router)
app.include_router(warehouse_router)
app.include_router(category_router)
app.include_router(product_router)
app.include_router(order_router)
app.include_router(return_router)
app.include_router(inventory_transfer_router)
app.include_router(notification_router)
app.include_router(audit_log_router)
app.include_router(dashboard_router)
app.include_router(report_router)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "success": True,
        "message": "Order Fulfillment & Inventory Management Platform API",
        "version": settings.APP_VERSION,
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health_check():
    return {
        "success": True,
        "status": "healthy",
    }