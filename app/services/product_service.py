import re
from sqlalchemy.orm import Session

from app.core.errors import DomainValidationError, NotFoundError
from app.core.normalization import normalize_slug
from app.models.product import BatteryOption, ExtraSpec, Product, ProductImage, ProductSpec, Variant
from app.repositories.product_repository import ProductRepository
from app.schemas.category import CategoryRead
from app.schemas.product import (
    AdminProductCreate,
    AdminProductDetailRead,
    AdminProductListItem,
    AdminProductUpdate,
    BatteryOptionRead,
    ExtraSpecRead,
    ProductDetailRead,
    ProductImageRead,
    ProductListItem,
    ProductSpecRead,
    VariantRead,
)


class ProductService:
    def __init__(self, repository: ProductRepository | None = None) -> None:
        self.repository = repository or ProductRepository()

    def list_public_products(
        self, 
        db: Session, 
        battery_type: str | None = None,
        body_material: str | None = None,
        range_min: int | None = None,
        range_max: int | None = None,
        speed_min: int | None = None,
        speed_max: int | None = None,
        category_slug: str | None = None
    ) -> list[ProductListItem]:
        products = self.repository.list_active(db)
        
        filtered = []
        for p in products:
            # Filter by Category Slug
            if category_slug and (not p.category or p.category.slug != category_slug):
                continue

            # Filter by Battery Type
            if battery_type and (not p.spec or battery_type.lower() not in (p.spec.battery_type or "").lower()):
                continue

            # Filter by Body Material
            if body_material and (not p.spec or body_material.lower() not in (p.spec.body or "").lower()):
                continue
            
            # Filter by Range
            if (range_min is not None or range_max is not None) and p.spec and p.spec.range:
                try:
                    # Extract the first number from the range string
                    match = re.search(r'\d+', p.spec.range)
                    val = int(match.group()) if match else 0
                    if range_min is not None and val < range_min: continue
                    if range_max is not None and val > range_max: continue
                except (ValueError, TypeError):
                    if range_min is not None: continue
            
            # Filter by Speed
            if (speed_min is not None or speed_max is not None) and p.spec and p.spec.speed:
                try:
                    match = re.search(r'\d+', p.spec.speed)
                    val = int(match.group()) if match else 0
                    if speed_min is not None and val < speed_min: continue
                    if speed_max is not None and val > speed_max: continue
                except (ValueError, TypeError):
                    if speed_min is not None: continue
            
            filtered.append(self._to_product_list_item(p))
            
        return filtered

    def get_public_recommendations(self, db: Session, exclude_id: int, limit: int = 3) -> list[ProductListItem]:
        products = self.repository.get_random_active_exclude(db, exclude_id, limit)
        return [self._to_product_list_item(product) for product in products]

    def list_admin_products(self, db: Session) -> list[AdminProductListItem]:
        products = self.repository.list_all(db)
        return [
            AdminProductListItem(
                **self._to_product_list_item(product).model_dump(),
                is_active=product.is_active,
            )
            for product in products
        ]

    def get_public_product(self, db: Session, slug: str) -> ProductDetailRead:
        product = self.repository.get_active_by_slug(db, slug)
        if product is None:
            raise NotFoundError(f"Product with slug '{slug}' was not found.")
        return self._to_product_detail(product)

    def get_admin_product(self, db: Session, product_id: int) -> AdminProductDetailRead:
        product = self.repository.get_by_id(db, product_id)
        if product is None:
            raise NotFoundError(f"Product with id '{product_id}' was not found.")
        return AdminProductDetailRead(
            **self._to_product_detail(product).model_dump(),
            is_active=product.is_active,
        )

    def create_admin_product(self, db: Session, payload: AdminProductCreate) -> AdminProductDetailRead:
        slug = self._resolve_unique_slug(db, payload.slug, payload.name)

        product = Product(
            name=payload.name,
            slug=slug,
            tagline=payload.tagline,
            short_description=payload.short_description,
            description=payload.description,
            is_active=payload.is_active,
            base_price=payload.base_price,
            sort_order=payload.sort_order,
            category_id=payload.category_id,
        )
        self._apply_product_children(product, payload)
        saved = self.repository.save(db, product)
        return AdminProductDetailRead(
            **self._to_product_detail(saved).model_dump(),
            is_active=saved.is_active,
        )

    def update_admin_product(self, db: Session, product_id: int, payload: AdminProductUpdate) -> AdminProductDetailRead:
        product = self.repository.get_by_id(db, product_id)
        if product is None:
            raise NotFoundError(f"Product with id '{product_id}' was not found.")

        update_data = payload.model_dump(exclude_unset=True)
        if "slug" in update_data:
            product.slug = self._resolve_unique_slug(db, update_data.get("slug"), product.name, exclude_product_id=product.id)

        scalar_fields = ("name", "tagline", "short_description", "description", "is_active", "base_price", "sort_order", "category_id")
        for field in scalar_fields:
            if field in update_data:
                setattr(product, field, update_data[field])

        self._apply_product_children(product, payload, replace_only_provided=True)
        saved = self.repository.save(db, product)
        return AdminProductDetailRead(
            **self._to_product_detail(saved).model_dump(),
            is_active=saved.is_active,
        )

    def delete_admin_product(self, db: Session, product_id: int) -> None:
        import shutil
        from pathlib import Path
        from app.core.config import settings

        product = self.repository.get_by_id(db, product_id)
        if product is None:
            raise NotFoundError(f"Product with id '{product_id}' was not found.")
        
        db.delete(product)
        db.commit()

        product_dir = Path(settings.media_dir) / "products" / str(product_id)
        if product_dir.exists() and product_dir.is_dir():
            shutil.rmtree(product_dir, ignore_errors=True)

    def _to_product_list_item(self, product: Product) -> ProductListItem:
        active_variants = [variant for variant in product.variants if variant.is_active]
        primary_image = next((image for image in product.images if image.is_primary), None)
        if primary_image is None and product.images:
            primary_image = product.images[0]

        return ProductListItem(
            id=product.id,
            name=product.name,
            slug=product.slug,
            tagline=product.tagline,
            short_description=product.short_description,
            base_price=product.base_price,
            sort_order=product.sort_order,
            category=CategoryRead.model_validate(product.category) if product.category else None,
            primary_image=ProductImageRead.model_validate(primary_image) if primary_image else None,
            images=[ProductImageRead.model_validate(image) for image in product.images],
            variants=[VariantRead.model_validate(variant) for variant in active_variants],
            spec=ProductSpecRead.model_validate(product.spec) if product.spec else None,
        )

    def _to_product_detail(self, product: Product) -> ProductDetailRead:
        active_variants = [variant for variant in product.variants if variant.is_active]

        return ProductDetailRead(
            id=product.id,
            name=product.name,
            slug=product.slug,
            tagline=product.tagline,
            short_description=product.short_description,
            description=product.description,
            base_price=product.base_price,
            sort_order=product.sort_order,
            category=CategoryRead.model_validate(product.category) if product.category else None,
            images=[ProductImageRead.model_validate(image) for image in product.images],
            variants=[VariantRead.model_validate(variant) for variant in active_variants],
            spec=ProductSpecRead.model_validate(product.spec) if product.spec else None,
            battery_options=[BatteryOptionRead.model_validate(option) for option in product.battery_options],
            extra_specs=[ExtraSpecRead.model_validate(item) for item in product.extra_specs],
        )

    def _resolve_unique_slug(
        self,
        db: Session,
        explicit_slug: str | None,
        fallback_name: str,
        exclude_product_id: int | None = None,
    ) -> str:
        base_slug = explicit_slug or normalize_slug(fallback_name)
        if not base_slug:
            raise DomainValidationError("Product slug could not be generated.")

        existing = self.repository.get_by_slug(db, base_slug)
        if existing is not None and existing.id != exclude_product_id:
            raise DomainValidationError(f"Product slug '{base_slug}' is already in use.")
        return base_slug

    def _apply_product_children(
        self,
        product: Product,
        payload: AdminProductCreate | AdminProductUpdate,
        replace_only_provided: bool = False,
    ) -> None:
        from sqlalchemy.orm import Session
        db = Session.object_session(product)

        # First, clear the lists and flush to avoid unique constraint violations
        if db:
            if not replace_only_provided or payload.images is not None:
                product.images.clear()
            if not replace_only_provided or payload.battery_options is not None:
                product.battery_options.clear()
            if not replace_only_provided or payload.extra_specs is not None:
                product.extra_specs.clear()
            db.flush()

        if not replace_only_provided or payload.images is not None:
            product.images = [
                ProductImage(
                    image_path=image.image_path,
                    alt_text=image.alt_text,
                    is_primary=image.is_primary,
                    sort_order=image.sort_order,
                )
                for image in (payload.images or [])
            ]

        if not replace_only_provided or payload.variants is not None:
            self._validate_variant_names(payload.variants or [])
            existing_variants = {v.color_name.casefold(): v for v in product.variants}
            new_variants = []
            for v_data in (payload.variants or []):
                v_key = v_data.color_name.casefold()
                if v_key in existing_variants:
                    v = existing_variants[v_key]
                    v.color_name = v_data.color_name
                    v.color_code = v_data.color_code
                    v.image_path = v_data.image_path
                    v.sort_order = v_data.sort_order
                    v.is_active = v_data.is_active
                    new_variants.append(v)
                    del existing_variants[v_key]
                else:
                    new_variants.append(
                        Variant(
                            color_name=v_data.color_name,
                            color_code=v_data.color_code,
                            image_path=v_data.image_path,
                            sort_order=v_data.sort_order,
                            is_active=v_data.is_active,
                        )
                    )
            # Remove un-sent variants
            if db:
                for v in existing_variants.values():
                    db.delete(v)
            product.variants = new_variants

        if not replace_only_provided or payload.spec is not None:
            if payload.spec:
                if product.spec is not None:
                    for key, value in payload.spec.model_dump(exclude={"id"}).items():
                        setattr(product.spec, key, value)
                else:
                    product.spec = ProductSpec(**payload.spec.model_dump(exclude={"id"}))
            else:
                if product.spec is not None and db:
                    db.delete(product.spec)
                product.spec = None

        if not replace_only_provided or payload.battery_options is not None:
            product.battery_options = [
                BatteryOption(
                    capacity=option.capacity,
                    range=option.range,
                    sort_order=option.sort_order,
                )
                for option in (payload.battery_options or [])
            ]

        if not replace_only_provided or payload.extra_specs is not None:
            self._validate_extra_spec_keys(payload.extra_specs or [])
            product.extra_specs = [
                ExtraSpec(
                    key=item.key,
                    label=item.label,
                    value=item.value,
                    sort_order=item.sort_order,
                )
                for item in (payload.extra_specs or [])
            ]

    def _validate_variant_names(self, variants) -> None:
        names = [variant.color_name.casefold() for variant in variants]
        if len(names) != len(set(names)):
            raise DomainValidationError("Variant color names must be unique per product.")

    def _validate_extra_spec_keys(self, extra_specs) -> None:
        keys = [item.key for item in extra_specs]
        if len(keys) != len(set(keys)):
            raise DomainValidationError("Extra spec keys must be unique per product.")
