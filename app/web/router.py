from fastapi import APIRouter

from app.web.routes import admin, auth, storefront

router = APIRouter()
router.include_router(admin.router)
router.include_router(auth.router)
router.include_router(storefront.router)
