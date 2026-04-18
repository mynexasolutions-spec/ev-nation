from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.db.session import get_db
from app.schemas.product import ProductDetailRead, ProductListItem
from app.services.product_service import ProductService

router = APIRouter(prefix="/products")
service = ProductService()


@router.get("", response_model=list[ProductListItem], summary="List active products")
def list_products(db: Session = Depends(get_db)) -> list[ProductListItem]:
    return service.list_public_products(db)


@router.get("/{slug}", response_model=ProductDetailRead, summary="Get product by slug")
def get_product(slug: str, db: Session = Depends(get_db)) -> ProductDetailRead:
    try:
        return service.get_public_product(db, slug)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
