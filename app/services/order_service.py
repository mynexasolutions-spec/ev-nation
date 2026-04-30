from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import DomainValidationError, NotFoundError
from app.models.enums import OrderStatus, PaymentStatus
from app.models.order import Order, OrderItem
from app.repositories.cart_repository import CartRepository
from app.repositories.order_repository import OrderRepository
from app.schemas.order import (
    OrderCreate,
    OrderListItem,
    OrderRead,
    OrderItemRead,
    PaymentInitResponse,
    PaymentVerify,
)
from app.services.cart_service import CartService
from app.services.payment_service import PaymentService


class OrderService:
    def __init__(self) -> None:
        self._order_repo = OrderRepository()
        self._cart_repo = CartRepository()
        self._cart_service = CartService()
        self._payment_service = PaymentService()

    def _generate_order_number(self, db: Session) -> str:
        """Generate a unique order number like EVN-20260430-0001."""
        today = datetime.now(timezone.utc).strftime("%Y%m%d")
        prefix = f"EVN-{today}-"
        # Find the highest order number for today
        existing = self._order_repo.get_all_orders(db, limit=1000)
        today_orders = [
            o for o in existing if o.order_number.startswith(prefix)
        ]
        next_seq = len(today_orders) + 1
        return f"{prefix}{next_seq:04d}"

    def _to_order_read(self, order: Order) -> OrderRead:
        return OrderRead(
            id=order.id,
            order_number=order.order_number,
            status=order.status.value if isinstance(order.status, OrderStatus) else order.status,
            payment_status=order.payment_status.value if isinstance(order.payment_status, PaymentStatus) else order.payment_status,
            subtotal=order.subtotal,
            total=order.total,
            customer_name=order.customer_name,
            customer_phone=order.customer_phone,
            notes=order.notes,
            razorpay_order_id=order.razorpay_order_id,
            items=[
                OrderItemRead(
                    id=item.id,
                    product_id=item.product_id,
                    variant_id=item.variant_id,
                    product_name=item.product_name,
                    variant_name=item.variant_name,
                    unit_price=item.unit_price,
                    quantity=item.quantity,
                    image_path=item.image_path,
                    attributes=item.attributes,
                )
                for item in order.items
            ],
            created_at=order.created_at,
            paid_at=order.paid_at,
            confirmed_at=order.confirmed_at,
            ready_at=order.ready_at,
            completed_at=order.completed_at,
            cancelled_at=order.cancelled_at,
        )

    def _to_order_list_item(self, order: Order) -> OrderListItem:
        return OrderListItem(
            id=order.id,
            order_number=order.order_number,
            status=order.status.value if isinstance(order.status, OrderStatus) else order.status,
            payment_status=order.payment_status.value if isinstance(order.payment_status, PaymentStatus) else order.payment_status,
            total=order.total,
            item_count=len(order.items) if order.items else 0,
            created_at=order.created_at,
        )

    def create_order_from_cart(
        self, db: Session, user_id: int, payload: OrderCreate,
    ) -> OrderRead:
        """Snapshot the user's cart into an order."""
        cart_summary = self._cart_service.get_cart(db, user_id)
        available_items = [i for i in cart_summary.items if i.is_available]

        if not available_items:
            raise DomainValidationError("Your cart is empty or has no available items.")

        order_number = self._generate_order_number(db)
        subtotal = sum(i.unit_price * i.quantity for i in available_items)

        order = Order(
            order_number=order_number,
            user_id=user_id,
            status=OrderStatus.PENDING,
            payment_status=PaymentStatus.PENDING,
            subtotal=subtotal,
            total=subtotal,  # No shipping cost
            customer_name=payload.customer_name,
            customer_phone=payload.customer_phone,
            notes=payload.notes,
        )

        order.items = [
            OrderItem(
                product_id=item.product_id,
                variant_id=item.variant_id,
                product_name=item.product_name,
                variant_name=item.variant_name,
                unit_price=item.unit_price,
                quantity=item.quantity,
                image_path=item.image_path,
                attributes=item.attributes,
            )
            for item in available_items
        ]

        saved = self._order_repo.create(db, order)

        return self._to_order_read(saved)

    def initiate_payment(self, db: Session, order_number: str, user_id: int) -> PaymentInitResponse:
        """Create a Razorpay order for payment."""
        order = self._order_repo.get_by_order_number(db, order_number)
        if order is None or order.user_id != user_id:
            raise NotFoundError("Order not found.")
        if order.status != OrderStatus.PENDING:
            raise DomainValidationError("Order is not in a payable state.")

        # Create Razorpay order
        rzp_order = self._payment_service.create_order(
            amount_paise=order.total,
            receipt=order.order_number,
        )

        # Store Razorpay order ID
        order.razorpay_order_id = rzp_order["id"]
        self._order_repo.save(db, order)

        return PaymentInitResponse(
            razorpay_order_id=rzp_order["id"],
            razorpay_key_id=settings.razorpay_key_id,
            amount=order.total,
            currency="INR",
            order_number=order.order_number,
            customer_name=order.customer_name,
            customer_phone=order.customer_phone,
        )

    def verify_payment(self, db: Session, payload: PaymentVerify, user_id: int) -> OrderRead:
        """Verify Razorpay payment signature and mark order as paid."""
        order = self._order_repo.get_by_razorpay_order_id(db, payload.razorpay_order_id)
        if order is None or order.user_id != user_id:
            raise NotFoundError("Order not found.")

        is_valid = self._payment_service.verify_signature(
            razorpay_order_id=payload.razorpay_order_id,
            razorpay_payment_id=payload.razorpay_payment_id,
            razorpay_signature=payload.razorpay_signature,
        )

        if not is_valid:
            order.payment_status = PaymentStatus.FAILED
            self._order_repo.save(db, order)
            raise DomainValidationError("Payment verification failed.")

        now = datetime.now(timezone.utc)
        order.razorpay_payment_id = payload.razorpay_payment_id
        order.razorpay_signature = payload.razorpay_signature
        order.payment_status = PaymentStatus.PAID
        order.status = OrderStatus.PAID
        order.paid_at = now
        self._order_repo.save(db, order)

        # Clear the cart ONLY after successful payment
        self._cart_repo.clear_cart(db, user_id)

        return self._to_order_read(order)

    def get_order(self, db: Session, order_number: str, user_id: int) -> OrderRead:
        order = self._order_repo.get_by_order_number(db, order_number)
        if order is None or order.user_id != user_id:
            raise NotFoundError("Order not found.")
        return self._to_order_read(order)

    def get_user_orders(self, db: Session, user_id: int) -> list[OrderListItem]:
        orders = self._order_repo.get_user_orders(db, user_id)
        return [self._to_order_list_item(o) for o in orders]

    def cancel_order(self, db: Session, order_number: str, user_id: int) -> OrderRead:
        order = self._order_repo.get_by_order_number(db, order_number)
        if order is None or order.user_id != user_id:
            raise NotFoundError("Order not found.")
        if order.status not in (OrderStatus.PENDING,):
            raise DomainValidationError("Only pending orders can be cancelled.")
        order.status = OrderStatus.CANCELLED
        order.cancelled_at = datetime.now(timezone.utc)
        self._order_repo.save(db, order)
        return self._to_order_read(order)

    # --- Admin methods ---

    def admin_get_all_orders(
        self, db: Session, status_filter: str | None = None,
    ) -> list[OrderListItem]:
        orders = self._order_repo.get_all_orders(db, status_filter=status_filter)
        return [self._to_order_list_item(o) for o in orders]

    def admin_get_order(self, db: Session, order_number: str) -> OrderRead:
        order = self._order_repo.get_by_order_number(db, order_number)
        if order is None:
            raise NotFoundError("Order not found.")
        return self._to_order_read(order)

    def admin_update_status(
        self, db: Session, order_number: str, new_status: str,
    ) -> OrderRead:
        order = self._order_repo.get_by_order_number(db, order_number)
        if order is None:
            raise NotFoundError("Order not found.")

        now = datetime.now(timezone.utc)
        try:
            status = OrderStatus(new_status)
        except ValueError:
            raise DomainValidationError(f"Invalid order status: {new_status}")

        order.status = status
        if status == OrderStatus.CONFIRMED:
            order.confirmed_at = now
        elif status == OrderStatus.READY:
            order.ready_at = now
        elif status == OrderStatus.COMPLETED:
            order.completed_at = now
        elif status == OrderStatus.CANCELLED:
            order.cancelled_at = now

        self._order_repo.save(db, order)
        return self._to_order_read(order)
