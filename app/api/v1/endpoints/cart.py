from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_required
from app.core.errors import DomainValidationError, NotFoundError
from app.db.session import get_db
from app.models.user import User
from app.schemas.cart import CartItemCreate, CartItemRead, CartItemUpdate, CartSummary, CartSyncItem
from app.services.cart_service import CartService

router = APIRouter(prefix="/cart")
service = CartService()


@router.get("", response_model=CartSummary)
def get_cart(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_required),
):
    return service.get_cart(db, user.id)


@router.post("/items", response_model=CartItemRead, status_code=status.HTTP_201_CREATED)
def add_item(
    payload: CartItemCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_required),
):
    try:
        return service.add_item(db, user.id, payload)
    except DomainValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.patch("/items/{item_id}", response_model=CartItemRead)
def update_item(
    item_id: int,
    payload: CartItemUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_required),
):
    try:
        return service.update_item(db, user.id, item_id, payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_item(
    item_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_required),
):
    try:
        service.remove_item(db, user.id, item_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def clear_cart(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_required),
):
    service.clear_cart(db, user.id)


@router.post("/sync", response_model=CartSummary)
def sync_guest_cart(
    guest_items: list[CartSyncItem],
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_required),
):
    """Sync guest localStorage cart items into the user's DB cart on login."""
    return service.sync_guest_cart(db, user.id, guest_items)


@router.get("/count")
def get_cart_count(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_required),
):
    return {"count": service.get_item_count(db, user.id)}
