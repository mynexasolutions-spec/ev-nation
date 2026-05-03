from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import NotFoundError
from app.db.session import get_db
from app.services.product_service import ProductService
from app.services.category_service import category_service
from app.services.blog_service import blog_service
from app.api.deps import get_current_user_web
from app.web.templating import templates

router = APIRouter()
product_service = ProductService()

@router.get("/about", response_class=HTMLResponse)
def about(request: Request, user=Depends(get_current_user_web)):
    return templates.TemplateResponse(
        request,
        "storefront/about.html",
        {
            "request": request,
            "user": user,
            "page_title": "About Us — EV Nation",
        },
    )


@router.get("/contact", response_class=HTMLResponse)
def contact(request: Request, user=Depends(get_current_user_web)):
    return templates.TemplateResponse(
        request,
        "storefront/contact.html",
        {
            "request": request,
            "user": user,
            "page_title": "Contact Us — EV Nation",
        },
    )


@router.get("/legal", response_class=HTMLResponse)
def legal(request: Request, user=Depends(get_current_user_web)):
    return templates.TemplateResponse(
        request,
        "storefront/legal.html",
        {
            "request": request,
            "user": user,
            "page_title": "Legal — EV Nation",
        },
    )


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
        request,
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
    speed_type: str | None = None,
    category: str | None = None
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
        speed_max=speed_max,
        category_slug=category
    )
    
    categories = category_service.get_all_active(db)
    
    return templates.TemplateResponse(
        request,
        "storefront/collection.html",
        {
            "request": request,
            "products": products,
            "selected_battery": battery,
            "selected_body": body_material,
            "selected_range": range_type,
            "selected_speed": speed_type,
            "selected_category": category,
            "categories": categories,
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
            request,
            "storefront/404.html",
            {"request": request, "page_title": "Not Found"},
            status_code=404,
        )
    return templates.TemplateResponse(
        request,
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


@router.get("/cart", response_class=HTMLResponse)
def cart_page(request: Request, user=Depends(get_current_user_web)):
    return templates.TemplateResponse(
        request,
        "storefront/cart.html",
        {
            "request": request,
            "user": user,
            "page_title": "Cart — EV Nation",
        },
    )


@router.get("/checkout", response_class=HTMLResponse)
def checkout_page(request: Request, user=Depends(get_current_user_web)):
    if not user:
        return RedirectResponse(url="/login?next=/checkout")
    return templates.TemplateResponse(
        request,
        "storefront/checkout.html",
        {
            "request": request,
            "user": user,
            "page_title": "Checkout — EV Nation",
        },
    )


@router.get("/orders/{order_number}/confirmation", response_class=HTMLResponse)
def order_confirmation_page(order_number: str, request: Request, user=Depends(get_current_user_web)):
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse(
        request,
        "storefront/order_confirmation.html",
        {
            "request": request,
            "user": user,
            "order_number": order_number,
            "page_title": "Order Confirmed — EV Nation",
        },
    )


@router.get("/blog", response_class=HTMLResponse)
def blog_listing(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user_web),
    category: str | None = None,
):
    posts = blog_service.list_published(db, category_slug=category)
    featured = blog_service.get_featured(db, limit=3)
    latest = blog_service.get_latest(db, limit=5)
    categories = blog_service.get_all_categories(db)
    return templates.TemplateResponse(
        request,
        "storefront/blog.html",
        {
            "request": request,
            "user": user,
            "posts": posts,
            "featured": featured,
            "latest": latest,
            "categories": categories,
            "selected_category": category,
            "page_title": "Blog — EV Nation",
        },
    )


@router.get("/blog/{slug}", response_class=HTMLResponse)
def blog_detail(slug: str, request: Request, db: Session = Depends(get_db), user=Depends(get_current_user_web)):
    post = blog_service.get_by_slug(db, slug)
    if not post or not post.is_published:
        return templates.TemplateResponse(
            request, "storefront/404.html", {"request": request, "page_title": "Not Found"}, status_code=404
        )
    related = blog_service.get_related(db, post_id=post.id, category_id=post.category_id, limit=4)
    latest = blog_service.get_latest(db, limit=5)
    return templates.TemplateResponse(
        request,
        "storefront/blog_detail.html",
        {
            "request": request,
            "user": user,
            "post": post,
            "related": related,
            "latest": latest,
            "page_title": f"{post.title} — EV Nation Blog",
        },
    )
