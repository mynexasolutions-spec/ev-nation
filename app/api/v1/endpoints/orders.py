from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_required
from app.core.errors import DomainValidationError, NotFoundError
from app.db.session import get_db
from app.models.user import User
from app.schemas.order import (
    OrderCreate,
    OrderListItem,
    OrderRead,
    PaymentInitResponse,
    PaymentVerify,
)
from app.services.order_service import OrderService

router = APIRouter(prefix="/orders")
service = OrderService()


@router.post("", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
def create_order(
    payload: OrderCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_required),
):
    """Place an order from the user's cart."""
    try:
        return service.create_order_from_cart(db, user.id, payload)
    except DomainValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("", response_model=list[OrderListItem])
def list_orders(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_required),
):
    return service.get_user_orders(db, user.id)


@router.get("/{order_number}", response_model=OrderRead)
def get_order(
    order_number: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_required),
):
    try:
        return service.get_order(db, order_number, user.id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{order_number}/pay", response_model=PaymentInitResponse)
def initiate_payment(
    order_number: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_required),
):
    """Create a Razorpay order for payment."""
    try:
        return service.initiate_payment(db, order_number, user.id)
    except (NotFoundError, DomainValidationError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/verify-payment", response_model=OrderRead)
def verify_payment(
    payload: PaymentVerify,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_required),
):
    """Verify Razorpay payment callback."""
    try:
        return service.verify_payment(db, payload, user.id)
    except (NotFoundError, DomainValidationError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/{order_number}/cancel", response_model=OrderRead)
def cancel_order(
    order_number: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_required),
):
    try:
        return service.cancel_order(db, order_number, user.id)
    except (NotFoundError, DomainValidationError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
