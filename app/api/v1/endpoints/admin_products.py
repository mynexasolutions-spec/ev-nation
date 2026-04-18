from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.core.errors import DomainValidationError, NotFoundError
from app.db.session import get_db
from app.models.admin_user import AdminUser
from app.schemas.product import AdminProductCreate, AdminProductDetailRead, AdminProductListItem, AdminProductUpdate
from app.services.product_service import ProductService

router = APIRouter(prefix="/admin/products")
service = ProductService()


@router.get("", response_model=list[AdminProductListItem], summary="List products for admin")
def list_admin_products(
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> list[AdminProductListItem]:
    return service.list_admin_products(db)


@router.get("/{product_id}", response_model=AdminProductDetailRead, summary="Get product for admin")
def get_admin_product(
    product_id: int,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> AdminProductDetailRead:
    try:
        return service.get_admin_product(db, product_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("", response_model=AdminProductDetailRead, status_code=status.HTTP_201_CREATED, summary="Create product")
def create_admin_product(
    payload: AdminProductCreate,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> AdminProductDetailRead:
    try:
        return service.create_admin_product(db, payload)
    except DomainValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.put("/{product_id}", response_model=AdminProductDetailRead, summary="Update product")
def update_admin_product(
    product_id: int,
    payload: AdminProductUpdate,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> AdminProductDetailRead:
    try:
        return service.update_admin_product(db, product_id, payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except DomainValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Soft delete product")
def delete_admin_product(
    product_id: int,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> Response:
    try:
        service.soft_delete_admin_product(db, product_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
