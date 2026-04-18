from fastapi import APIRouter

from app.web.routes import admin, storefront

router = APIRouter()
router.include_router(admin.router)
router.include_router(storefront.router)
