from app.routers.auth import router as auth_router
from app.routers.inventory import router as inventory_router
from app.routers.warehouse import router as warehouse_router
from app.routers.category import router as category_router
from app.routers.product import router as product_router
from app.routers.order import router as order_router

__all__ = [
    "auth_router",
    "inventory_router",
    "warehouse_router",
    "category_router",
    "product_router",
]