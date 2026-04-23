from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import NotFoundError
from app.db.session import get_db
from app.services.product_service import ProductService
from app.services.category_service import category_service
from app.api.deps import get_current_user_web
from app.web.templating import templates

router = APIRouter()
product_service = ProductService()


@router.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db), user=Depends(get_current_user_web)):
    all_active_categories = category_service.get_all_active(db)
    products = product_service.list_public_products(db)

    # Group products by category
    category_groups = []
    uncategorized = []

    for category in all_active_categories:
        cat_products = [p for p in products if p.category and p.category.id == category.id]
        if cat_products:
            category_groups.append({
                "category": category,
                "products": cat_products
            })

    uncategorized = [p for p in products if not p.category]
    if uncategorized:
        category_groups.append({
            "category": None,
            "products": uncategorized
        })

    return templates.TemplateResponse(
        "storefront/home.html",
        {
            "request": request,
            "products": products,
            "category_groups": category_groups,
            "total_products": len(products),
            "page_title": "EV Nation — Electric Reimagined",
            "whatsapp_number": settings.whatsapp_number,
            "user": user,
        },
    )


@router.get("/collection", response_class=HTMLResponse)
def collection(
    request: Request, 
    db: Session = Depends(get_db), 
    user=Depends(get_current_user_web),
    battery: str | None = None,
    body_material: str | None = None,
    range_type: str | None = None,
    speed_type: str | None = None
):
    # Map range buckets
    range_min, range_max = None, None
    if range_type == "low": range_max = 80
    elif range_type == "mid": range_min, range_max = 81, 120
    elif range_type == "high": range_min = 121

    # Map speed buckets
    speed_min, speed_max = None, None
    if speed_type == "low": speed_max = 30
    elif speed_type == "high": speed_min = 31

    products = product_service.list_public_products(
        db, 
        battery_type=battery,
        body_material=body_material,
        range_min=range_min,
        range_max=range_max,
        speed_min=speed_min,
        speed_max=speed_max
    )
    
    return templates.TemplateResponse(
        "storefront/collection.html",
        {
            "request": request,
            "products": products,
            "selected_battery": battery,
            "selected_body": body_material,
            "selected_range": range_type,
            "selected_speed": speed_type,
            "page_title": "Collection — EV Nation",
            "whatsapp_number": settings.whatsapp_number,
            "user": user,
        },
    )


@router.get("/bikes/{slug}", response_class=HTMLResponse)
def product_detail(slug: str, request: Request, db: Session = Depends(get_db), user=Depends(get_current_user_web)):
    try:
        product = product_service.get_public_product(db, slug)
        recommendations = product_service.get_public_recommendations(db, exclude_id=product.id, limit=3)
    except NotFoundError:
        return templates.TemplateResponse(
            "storefront/404.html",
            {"request": request, "page_title": "Not Found"},
            status_code=404,
        )
    return templates.TemplateResponse(
        "storefront/product.html",
        {
            "request": request,
            "product": product,
            "recommendations": recommendations,
            "page_title": f"{product.name} – EV Nation",
            "whatsapp_number": settings.whatsapp_number,
            "user": user,
        },
    )
