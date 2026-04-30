from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.api.deps import get_current_user_web
from app.db.session import get_db
from app.services.order_service import OrderService

router = APIRouter()
templates = Jinja2Templates(directory="app/web/templates")
order_service = OrderService()


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, user=Depends(get_current_user_web)):
    if user:
        return RedirectResponse(url="/profile")
    return templates.TemplateResponse("storefront/login.html", {"request": request, "user": user})


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, user=Depends(get_current_user_web)):
    if user:
        return RedirectResponse(url="/profile")
    return templates.TemplateResponse("storefront/register.html", {"request": request, "user": user})


@router.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request, user=Depends(get_current_user_web), db: Session = Depends(get_db)):
    if not user:
        return RedirectResponse(url="/login")
    
    orders = order_service.get_user_orders(db, user.id)
    
    return templates.TemplateResponse(
        "storefront/profile.html", 
        {
            "request": request, 
            "user": user, 
            "orders": orders,
            "page_title": "My Dashboard — EV Nation"
        }
    )


@router.get("/orders/{order_number}", response_class=HTMLResponse)
async def order_detail_page(order_number: str, request: Request, user=Depends(get_current_user_web), db: Session = Depends(get_db)):
    if not user:
        return RedirectResponse(url="/login")
    
    try:
        order = order_service.get_order(db, order_number, user.id)
    except Exception:
        return RedirectResponse(url="/profile")
        
    return templates.TemplateResponse(
        "storefront/order_detail.html",
        {
            "request": request,
            "user": user,
            "order": order,
            "page_title": f"Order {order_number} — EV Nation",
        }
    )
