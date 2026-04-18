from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import NotFoundError
from app.db.session import get_db
from app.services.product_service import ProductService
from app.web.templating import templates

router = APIRouter()
product_service = ProductService()


@router.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    products = product_service.list_public_products(db)
    return templates.TemplateResponse(
        "storefront/home.html",
        {
            "request": request,
            "products": products,
            "page_title": "EV Nation – Electric Bikes",
            "whatsapp_number": settings.whatsapp_number,
        },
    )


@router.get("/bikes/{slug}", response_class=HTMLResponse)
def product_detail(slug: str, request: Request, db: Session = Depends(get_db)):
    try:
        product = product_service.get_public_product(db, slug)
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
            "page_title": f"{product.name} – EV Nation",
            "whatsapp_number": settings.whatsapp_number,
        },
    )
