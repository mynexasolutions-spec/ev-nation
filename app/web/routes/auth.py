from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.api.deps import get_current_user_web
from app.db.session import get_db

router = APIRouter()
templates = Jinja2Templates(directory="app/web/templates")


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
async def profile_page(request: Request, user=Depends(get_current_user_web)):
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("storefront/profile.html", {"request": request, "user": user})
