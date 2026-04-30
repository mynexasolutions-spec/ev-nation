from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.errors import DomainValidationError, NotFoundError
from app.models.cart import CartItem
from app.repositories.cart_repository import CartRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.cart import CartItemCreate, CartItemRead, CartItemUpdate, CartSummary, CartSyncItem


class CartService:
    def __init__(self) -> None:
        self._cart_repo = CartRepository()
        self._product_repo = ProductRepository()

    # --- helpers ---

    def _enrich_item(self, item: CartItem) -> CartItemRead:
        """Convert a CartItem ORM object into a CartItemRead with product info."""
        product = item.product
        variant = item.variant

        # Determine primary image
        image_path = None
        if product and product.images:
            # Try variant-specific image first
            if variant:
                for img in product.images:
                    if img.variant_id == variant.id:
                        image_path = img.image_path
                        break
            # Fallback to primary image
            if not image_path:
                for img in product.images:
                    if img.is_primary:
                        image_path = img.image_path
                        break
                if not image_path:
                    image_path = product.images[0].image_path

        return CartItemRead(
            id=item.id,
            product_id=item.product_id,
            variant_id=item.variant_id,
            quantity=item.quantity,
            product_name=product.name if product else "Unavailable",
            product_slug=product.slug if product else "",
            variant_name=variant.color_name if variant else None,
            unit_price=product.base_price if product else 0,
            image_path=image_path,
            is_available=product.is_active if product else False,
        )

    # --- public API ---

    def get_cart(self, db: Session, user_id: int) -> CartSummary:
        items = self._cart_repo.get_user_cart(db, user_id)
        enriched = [self._enrich_item(item) for item in items]
        # Only count available items toward subtotal
        subtotal = sum(
            i.unit_price * i.quantity for i in enriched if i.is_available
        )
        return CartSummary(
            items=enriched,
            item_count=len(enriched),
            subtotal=subtotal,
        )

    def add_item(
        self, db: Session, user_id: int, payload: CartItemCreate,
    ) -> CartItemRead:
        # Validate product exists and is active
        product = self._product_repo.get_by_id(db, payload.product_id)
        if not product or not product.is_active:
            raise DomainValidationError("Product is not available.")

        # Validate variant if specified
        if payload.variant_id is not None:
            variant_valid = any(
                v.id == payload.variant_id and v.is_active
                for v in product.variants
            )
            if not variant_valid:
                raise DomainValidationError("Selected variant is not available.")

        item = self._cart_repo.add_item(
            db, user_id, payload.product_id, payload.variant_id, payload.quantity, payload.attributes
        )
        # Reload with relationships
        db.refresh(item, attribute_names=["product", "variant"])
        return self._enrich_item(item)

    def update_item(
        self, db: Session, user_id: int, item_id: int, payload: CartItemUpdate,
    ) -> CartItemRead:
        item = self._cart_repo.update_quantity(
            db, item_id, user_id, payload.quantity,
        )
        if item is None:
            raise NotFoundError("Cart item not found.")
        db.refresh(item, attribute_names=["product", "variant"])
        return self._enrich_item(item)

    def remove_item(self, db: Session, user_id: int, item_id: int) -> None:
        if not self._cart_repo.remove_item(db, item_id, user_id):
            raise NotFoundError("Cart item not found.")

    def clear_cart(self, db: Session, user_id: int) -> int:
        return self._cart_repo.clear_cart(db, user_id)

    def sync_guest_cart(
        self, db: Session, user_id: int, guest_items: list[CartSyncItem],
    ) -> CartSummary:
        """Merge guest localStorage items into the user's DB cart."""
        for guest_item in guest_items:
            try:
                product = self._product_repo.get_by_id(db, guest_item.product_id)
                if not product or not product.is_active:
                    continue
                if guest_item.variant_id is not None:
                    variant_valid = any(
                        v.id == guest_item.variant_id and v.is_active
                        for v in product.variants
                    )
                    if not variant_valid:
                        continue
                self._cart_repo.add_item(
                    db, user_id, guest_item.product_id,
                    guest_item.variant_id, guest_item.quantity,
                    guest_item.attributes,
                )
            except Exception:
                continue  # Skip invalid items gracefully
        return self.get_cart(db, user_id)

    def get_item_count(self, db: Session, user_id: int) -> int:
        return self._cart_repo.count_items(db, user_id)
