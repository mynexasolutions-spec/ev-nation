from __future__ import annotations

import json
import shutil
import uuid
from json import JSONDecodeError
from pathlib import Path

from fastapi import APIRouter, Cookie, Depends, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import DomainValidationError, NotFoundError
from app.models.product import ProductImage
from app.db.session import get_db
from app.models.admin_user import AdminUser
from app.models.enums import LeadSource, LeadStatus
from app.schemas.admin_auth import AdminLoginRequest
from app.schemas.lead import AdminLeadStatusUpdate
from app.schemas.product import AdminProductCreate, AdminProductUpdate
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.services.admin_auth_service import AdminAuthService
from app.services.lead_service import LeadService
from app.services.product_service import ProductService
from app.services.category_service import category_service
from app.web.templating import templates

router = APIRouter(prefix="/admin")
auth_service = AdminAuthService()
product_service = ProductService()
lead_service = LeadService()


def _redirect_to_login() -> RedirectResponse:
    return RedirectResponse(url="/admin/login", status_code=status.HTTP_303_SEE_OTHER)


def _get_current_admin_from_cookie(
    admin_token: str | None,
    db: Session,
) -> AdminUser | None:
    if not admin_token:
        return None
    try:
        return auth_service.get_current_admin(db, admin_token)
    except (DomainValidationError, NotFoundError):
        return None


def _require_admin(request: Request, db: Session) -> AdminUser:
    token = request.cookies.get(settings.admin_cookie_name)
    admin_user = _get_current_admin_from_cookie(token, db)
    if admin_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return admin_user


def _base_context(request: Request, current_admin: AdminUser, **extra: object) -> dict[str, object]:
    def to_ist_format(dt) -> str:
        if not dt:
            return ""
        from datetime import timezone, timedelta
        ist = timezone(timedelta(hours=5, minutes=30))
        # Account for naive dt
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(ist).strftime("%d %b %Y, %I:%M %p")

    context = {
        "request": request,
        "current_admin": current_admin,
        "to_ist": to_ist_format,
    }
    context.update(extra)
    return context


@router.get("", response_class=HTMLResponse)
def admin_index(request: Request, db: Session = Depends(get_db)):
    if _get_current_admin_from_cookie(request.cookies.get(settings.admin_cookie_name), db) is None:
        return _redirect_to_login()
    return RedirectResponse(url="/admin/products", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, db: Session = Depends(get_db)):
    current_admin = _get_current_admin_from_cookie(request.cookies.get(settings.admin_cookie_name), db)
    if current_admin is not None:
        return RedirectResponse(url="/admin/products", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse("admin/login.html", {"request": request, "page_title": "Admin Login"})


@router.post("/login")
async def login_submit(request: Request, db: Session = Depends(get_db)) -> JSONResponse:
    payload = AdminLoginRequest.model_validate(await request.json())
    token_response = auth_service.login(db, payload)
    response = JSONResponse({"ok": True, "redirect_url": "/admin/products"})
    response.set_cookie(
        key=settings.admin_cookie_name,
        value=token_response.access_token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=settings.access_token_expire_minutes * 60,
    )
    return response


@router.post("/logout")
def logout() -> RedirectResponse:
    response = RedirectResponse(url="/admin/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(settings.admin_cookie_name)
    return response


@router.get("/products", response_class=HTMLResponse)
def admin_products_page(request: Request, db: Session = Depends(get_db)):
    try:
        current_admin = _require_admin(request, db)
    except HTTPException:
        return _redirect_to_login()

    products = product_service.list_admin_products(db)
    categories = category_service.get_all_admin(db)
    return templates.TemplateResponse(
        "admin/products.html",
        _base_context(
            request,
            current_admin,
            page_title="Products",
            products=products,
            categories=categories,
        ),
    )


@router.get("/products/{product_id}/json")
def admin_product_json(product_id: int, request: Request, db: Session = Depends(get_db)) -> JSONResponse:
    try:
        _require_admin(request, db)
        product = product_service.get_admin_product(db, product_id)
    except HTTPException:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return JSONResponse(product.model_dump(mode="json"))


@router.post("/products/save")
async def admin_product_save(request: Request, db: Session = Depends(get_db)) -> JSONResponse:
    try:
        _require_admin(request, db)
    except HTTPException:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")

    payload = await request.json()
    product_id = payload.pop("id", None)
    try:
        if product_id is None:
            created = product_service.create_admin_product(db, AdminProductCreate.model_validate(payload))
            return JSONResponse({"ok": True, "product": created.model_dump(mode="json")})
        updated = product_service.update_admin_product(db, int(product_id), AdminProductUpdate.model_validate(payload))
        return JSONResponse({"ok": True, "product": updated.model_dump(mode="json")})
    except (DomainValidationError, ValueError, TypeError, JSONDecodeError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/products/{product_id}/delete")
def admin_product_delete(product_id: int, request: Request, db: Session = Depends(get_db)) -> JSONResponse:
    try:
        _require_admin(request, db)
        product_service.delete_admin_product(db, product_id)
    except HTTPException:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return JSONResponse({"ok": True})


ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".svg"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


@router.post("/products/{product_id}/upload-image")
async def admin_upload_image(
    product_id: int,
    request: Request,
    file: UploadFile,
    variant_id: int | None = Form(None),
    db: Session = Depends(get_db),
) -> JSONResponse:
    try:
        _require_admin(request, db)
    except HTTPException:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")

    try:
        product = product_service.get_admin_product(db, product_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '{suffix}' is not allowed. Use: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds {MAX_FILE_SIZE // (1024 * 1024)} MB limit.",
        )

    product_dir = Path(settings.media_dir) / "products" / str(product_id)
    product_dir.mkdir(parents=True, exist_ok=True)

    unique_name = f"{uuid.uuid4().hex[:12]}{suffix}"
    dest = product_dir / unique_name
    dest.write_bytes(contents)

    media_path = f"/media/products/{product_id}/{unique_name}"

    existing_images = db.query(ProductImage).filter(ProductImage.product_id == product_id).all()
    is_primary = len(existing_images) == 0

    image_record = ProductImage(
        product_id=product_id,
        variant_id=variant_id,
        image_path=media_path,
        alt_text=product.name,
        is_primary=is_primary,
        sort_order=len(existing_images),
    )
    db.add(image_record)
    db.commit()
    db.refresh(image_record)

    return JSONResponse({
        "ok": True,
        "image": {
            "id": image_record.id,
            "variant_id": image_record.variant_id,
            "image_path": image_record.image_path,
            "alt_text": image_record.alt_text,
            "is_primary": image_record.is_primary,
            "sort_order": image_record.sort_order,
        },
    })


@router.post("/products/{product_id}/delete-image/{image_id}")
def admin_delete_image(
    product_id: int,
    image_id: int,
    request: Request,
    db: Session = Depends(get_db),
) -> JSONResponse:
    try:
        _require_admin(request, db)
    except HTTPException:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")

    image = db.query(ProductImage).filter(
        ProductImage.id == image_id,
        ProductImage.product_id == product_id,
    ).first()

    if image is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found.")

    was_primary = image.is_primary

    relative = image.image_path.removeprefix("/media/")
    file_path = Path(settings.media_dir) / relative
    if file_path.exists():
        file_path.unlink()

    db.delete(image)
    
    # If the deleted image was primary, nominate a new one automatically
    if was_primary:
        next_image = db.query(ProductImage).filter(ProductImage.product_id == product_id).order_by(ProductImage.sort_order).first()
        if next_image:
            next_image.is_primary = True

    db.commit()

    return JSONResponse({"ok": True})


@router.post("/products/{product_id}/images/{image_id}/primary")
def admin_set_primary_image(
    product_id: int,
    image_id: int,
    request: Request,
    db: Session = Depends(get_db),
) -> JSONResponse:
    try:
        _require_admin(request, db)
    except HTTPException:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")

    # Find target image
    target = db.query(ProductImage).filter(
        ProductImage.id == image_id,
        ProductImage.product_id == product_id,
    ).first()

    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found.")

    # Remove primary flag from all other images for this product
    db.query(ProductImage).filter(
        ProductImage.product_id == product_id,
        ProductImage.id != image_id
    ).update({"is_primary": False})

    # Set new primary
    target.is_primary = True
    db.commit()

    return JSONResponse({"ok": True})


@router.get("/leads", response_class=HTMLResponse)
def admin_leads_page(request: Request, db: Session = Depends(get_db)):
    try:
        current_admin = _require_admin(request, db)
    except HTTPException:
        return _redirect_to_login()

    search_term = request.query_params.get("search", "").strip()
    status_filter_raw = request.query_params.get("status")
    source_filter_raw = request.query_params.get("source")
    
    page = int(request.query_params.get("page", "1"))
    if page < 1:
        page = 1
    
    limit = 50
    offset = (page - 1) * limit

    status_filter = LeadStatus(status_filter_raw) if status_filter_raw else None
    source_filter = LeadSource(source_filter_raw) if source_filter_raw else None
    
    leads, total_count = lead_service.list_admin_leads(
        db, 
        status=status_filter, 
        source=source_filter,
        search=search_term if search_term else None,
        limit=limit,
        offset=offset
    )
    
    from math import ceil
    total_pages = ceil(total_count / limit) if total_count > 0 else 1

    return templates.TemplateResponse(
        "admin/leads.html",
        _base_context(
            request,
            current_admin,
            page_title="Leads",
            leads=leads,
            lead_statuses=list(LeadStatus),
            lead_sources=list(LeadSource),
            selected_status=status_filter_raw or "",
            selected_source=source_filter_raw or "",
            search_term=search_term,
            current_page=page,
            total_pages=total_pages,
            total_count=total_count,
        ),
    )


@router.post("/leads/{lead_id}/status")
async def admin_lead_status_update(lead_id: int, request: Request, db: Session = Depends(get_db)) -> JSONResponse:
    try:
        _require_admin(request, db)
        payload = AdminLeadStatusUpdate.model_validate(await request.json())
        lead = lead_service.update_admin_lead_status(db, lead_id, payload)
    except HTTPException:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return JSONResponse({"ok": True, "lead": lead.model_dump(mode="json")})
@router.delete("/leads/{lead_id}")
async def admin_lead_delete(lead_id: int, request: Request, db: Session = Depends(get_db)) -> JSONResponse:
    try:
        _require_admin(request, db)
        deleted = lead_service.delete_admin_lead(db, lead_id)
        if not deleted:
            raise NotFoundError(f"Lead {lead_id} not found.")
    except HTTPException:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return JSONResponse({"ok": True})


# ── Categories ──

@router.get("/categories", response_class=HTMLResponse)
def admin_categories_ui(request: Request, db: Session = Depends(get_db)):
    try:
        current_admin = _require_admin(request, db)
    except HTTPException:
        return _redirect_to_login()
        
    products = product_service.list_admin_products(db)
        
    return templates.TemplateResponse(
        "admin/categories.html", 
        _base_context(
            request, 
            current_admin, 
            page_title="Admin - Categories",
            products=products
        )
    )


@router.get("/categories/json")
def admin_categories_json(request: Request, db: Session = Depends(get_db)) -> JSONResponse:
    try:
        _require_admin(request, db)
    except HTTPException:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")
    
    categories = category_service.get_all_admin(db)
    return JSONResponse({"ok": True, "categories": [c.slug for c in categories]})  # Dummy for now, actual serialization later if needed


@router.get("/categories/list-json")
def admin_categories_list_json(request: Request, db: Session = Depends(get_db)) -> JSONResponse:
    # Used by the frontend tables
    try:
        _require_admin(request, db)
    except HTTPException:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")
    
    from app.schemas.category import CategoryRead
    categories = category_service.get_all_admin(db)
    return JSONResponse({"ok": True, "categories": [CategoryRead.model_validate(c).model_dump(mode="json") for c in categories]})


@router.post("/categories/save")
async def admin_category_save(request: Request, db: Session = Depends(get_db)) -> JSONResponse:
    try:
        _require_admin(request, db)
    except HTTPException:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")

    payload = await request.json()
    category_id = payload.pop("id", None)
    
    try:
        if category_id is None:
            created = category_service.create(db, CategoryCreate.model_validate(payload))
            return JSONResponse({"ok": True, "id": created.id})
        updated = category_service.update(db, int(category_id), CategoryUpdate.model_validate(payload))
        return JSONResponse({"ok": True, "id": updated.id})
    except (DomainValidationError, ValidationError, ValueError, TypeError, JSONDecodeError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/categories/{category_id}/delete")
def admin_category_delete(category_id: int, request: Request, db: Session = Depends(get_db)) -> JSONResponse:
    try:
        _require_admin(request, db)
        category_service.delete(db, category_id)
    except HTTPException:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return JSONResponse({"ok": True})

