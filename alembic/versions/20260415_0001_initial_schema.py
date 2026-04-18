"""Initial EV Nation schema."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260415_0001"
down_revision = None
branch_labels = None
depends_on = None


lead_source_enum = sa.Enum("whatsapp", "call", name="lead_source_enum")
lead_status_enum = sa.Enum("new", "contacted", "closed", name="lead_status_enum")


def upgrade() -> None:
    op.create_table(
        "admin_users",
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("is_superuser", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_admin_users")),
    )
    op.create_index(op.f("ix_admin_users_email"), "admin_users", ["email"], unique=True)

    op.create_table(
        "products",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("tagline", sa.String(length=255), nullable=True),
        sa.Column("short_description", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_products")),
    )
    op.create_index(op.f("ix_products_is_active"), "products", ["is_active"], unique=False)
    op.create_index(op.f("ix_products_slug"), "products", ["slug"], unique=True)
    op.create_index(op.f("ix_products_sort_order"), "products", ["sort_order"], unique=False)

    op.create_table(
        "battery_options",
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("capacity", sa.String(length=100), nullable=False),
        sa.Column("range", sa.String(length=100), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name=op.f("fk_battery_options_product_id_products"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_battery_options")),
    )
    op.create_index(op.f("ix_battery_options_product_id"), "battery_options", ["product_id"], unique=False)
    op.create_index(
        "ix_battery_options_product_id_sort_order",
        "battery_options",
        ["product_id", "sort_order"],
        unique=False,
    )

    op.create_table(
        "extra_specs",
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("label", sa.String(length=120), nullable=False),
        sa.Column("value", sa.String(length=500), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name=op.f("fk_extra_specs_product_id_products"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_extra_specs")),
    )
    op.create_index(op.f("ix_extra_specs_product_id"), "extra_specs", ["product_id"], unique=False)
    op.create_index("ix_extra_specs_product_id_key", "extra_specs", ["product_id", "key"], unique=False)
    op.create_index(
        "ix_extra_specs_product_id_sort_order",
        "extra_specs",
        ["product_id", "sort_order"],
        unique=False,
    )

    op.create_table(
        "product_images",
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("image_path", sa.String(length=500), nullable=False),
        sa.Column("alt_text", sa.String(length=255), nullable=True),
        sa.Column("is_primary", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name=op.f("fk_product_images_product_id_products"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_product_images")),
    )
    op.create_index(op.f("ix_product_images_product_id"), "product_images", ["product_id"], unique=False)
    op.create_index(
        "ix_product_images_product_id_sort_order",
        "product_images",
        ["product_id", "sort_order"],
        unique=False,
    )

    op.create_table(
        "product_specs",
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("weight", sa.String(length=100), nullable=True),
        sa.Column("speed", sa.String(length=100), nullable=True),
        sa.Column("range", sa.String(length=100), nullable=True),
        sa.Column("rated_power", sa.String(length=100), nullable=True),
        sa.Column("peak_power", sa.String(length=100), nullable=True),
        sa.Column("carrying_capacity", sa.String(length=100), nullable=True),
        sa.Column("motor", sa.String(length=255), nullable=True),
        sa.Column("battery_type", sa.String(length=255), nullable=True),
        sa.Column("charging_time", sa.String(length=100), nullable=True),
        sa.Column("body", sa.String(length=255), nullable=True),
        sa.Column("ground_clearance", sa.String(length=100), nullable=True),
        sa.Column("seat_height", sa.String(length=100), nullable=True),
        sa.Column("wheel_type", sa.String(length=100), nullable=True),
        sa.Column("brake_system", sa.String(length=255), nullable=True),
        sa.Column("tyre_size", sa.String(length=100), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name=op.f("fk_product_specs_product_id_products"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_product_specs")),
    )
    op.create_index(op.f("ix_product_specs_product_id"), "product_specs", ["product_id"], unique=True)

    op.create_table(
        "variants",
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("color_name", sa.String(length=100), nullable=False),
        sa.Column("color_code", sa.String(length=7), nullable=True),
        sa.Column("image_path", sa.String(length=500), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name=op.f("fk_variants_product_id_products"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_variants")),
        sa.UniqueConstraint("product_id", "color_name", name="uq_variants_product_id_color_name"),
    )
    op.create_index(op.f("ix_variants_product_id"), "variants", ["product_id"], unique=False)
    op.create_index("ix_variants_product_id_sort_order", "variants", ["product_id", "sort_order"], unique=False)

    op.create_table(
        "leads",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=True),
        sa.Column("variant_id", sa.Integer(), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("source", lead_source_enum, nullable=False),
        sa.Column("status", lead_status_enum, server_default="new", nullable=False),
        sa.Column("preferred_contact_time", sa.String(length=255), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name=op.f("fk_leads_product_id_products"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["variant_id"],
            ["variants.id"],
            name=op.f("fk_leads_variant_id_variants"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_leads")),
    )
    op.create_index(op.f("ix_leads_created_at"), "leads", ["created_at"], unique=False)
    op.create_index(op.f("ix_leads_product_id"), "leads", ["product_id"], unique=False)
    op.create_index(op.f("ix_leads_source"), "leads", ["source"], unique=False)
    op.create_index(op.f("ix_leads_status"), "leads", ["status"], unique=False)
    op.create_index(op.f("ix_leads_variant_id"), "leads", ["variant_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_leads_variant_id"), table_name="leads")
    op.drop_index(op.f("ix_leads_status"), table_name="leads")
    op.drop_index(op.f("ix_leads_source"), table_name="leads")
    op.drop_index(op.f("ix_leads_product_id"), table_name="leads")
    op.drop_index(op.f("ix_leads_created_at"), table_name="leads")
    op.drop_table("leads")

    op.drop_index("ix_variants_product_id_sort_order", table_name="variants")
    op.drop_index(op.f("ix_variants_product_id"), table_name="variants")
    op.drop_table("variants")

    op.drop_index(op.f("ix_product_specs_product_id"), table_name="product_specs")
    op.drop_table("product_specs")

    op.drop_index("ix_product_images_product_id_sort_order", table_name="product_images")
    op.drop_index(op.f("ix_product_images_product_id"), table_name="product_images")
    op.drop_table("product_images")

    op.drop_index("ix_extra_specs_product_id_sort_order", table_name="extra_specs")
    op.drop_index("ix_extra_specs_product_id_key", table_name="extra_specs")
    op.drop_index(op.f("ix_extra_specs_product_id"), table_name="extra_specs")
    op.drop_table("extra_specs")

    op.drop_index("ix_battery_options_product_id_sort_order", table_name="battery_options")
    op.drop_index(op.f("ix_battery_options_product_id"), table_name="battery_options")
    op.drop_table("battery_options")

    op.drop_index(op.f("ix_products_sort_order"), table_name="products")
    op.drop_index(op.f("ix_products_slug"), table_name="products")
    op.drop_index(op.f("ix_products_is_active"), table_name="products")
    op.drop_table("products")

    op.drop_index(op.f("ix_admin_users_email"), table_name="admin_users")
    op.drop_table("admin_users")

    bind = op.get_bind()
    lead_status_enum.drop(bind, checkfirst=True)
    lead_source_enum.drop(bind, checkfirst=True)
