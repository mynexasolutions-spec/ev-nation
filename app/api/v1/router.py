from fastapi import APIRouter

from app.api.v1.endpoints.admin_auth import router as admin_auth_router
from app.api.v1.endpoints.admin_leads import router as admin_leads_router
from app.api.v1.endpoints.admin_products import router as admin_products_router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.leads import router as leads_router
from app.api.v1.endpoints.products import router as products_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(products_router, tags=["products"])
api_router.include_router(leads_router, tags=["leads"])
api_router.include_router(auth_router, tags=["auth"])
api_router.include_router(admin_auth_router, tags=["admin-auth"])
api_router.include_router(admin_products_router, tags=["admin-products"])
api_router.include_router(admin_leads_router, tags=["admin-leads"])
