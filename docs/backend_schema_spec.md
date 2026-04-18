# EV Nation Backend Schema Spec

## Goal

Define the initial database and domain design for a FastAPI backend that powers:

- public EV bike catalog browsing
- product detail pages
- color variant selection
- WhatsApp and schedule-call lead capture
- admin-side product and lead management

This spec is intentionally simple, relational, and ready for PostgreSQL locally or on Supabase later.

## Design Principles

- Use relational tables for stable product data.
- Keep public API consumption simple for the frontend.
- Store messy optional specs in a flexible table without polluting core fields.
- Store image references as local paths or URLs for now.
- Avoid hard deletes for product content where possible.
- Keep the schema easy to migrate later to Cloudinary and Supabase.

## Main Entities

- `admin_users`
- `products`
- `product_images`
- `variants`
- `product_specs`
- `battery_options`
- `extra_specs`
- `leads`

## Shared Conventions

- Primary keys use integer IDs.
- Public product routing uses `slug`.
- Most content tables include `created_at` and `updated_at`.
- Product-facing sort order is explicit with `sort_order`.
- Product activation uses `is_active`.
- Image fields store a string path or URL, not binary data.

## Enums

### LeadSource

- `whatsapp`
- `call`

### LeadStatus

- `new`
- `contacted`
- `closed`

## Table Definitions

### `admin_users`

Purpose: authenticate admin API access.

Fields:

- `id` - integer primary key
- `email` - string, unique, indexed, required
- `password_hash` - string, required
- `full_name` - string, nullable
- `is_active` - boolean, default true
- `is_superuser` - boolean, default false
- `last_login_at` - datetime, nullable
- `created_at` - datetime, required
- `updated_at` - datetime, required

Constraints and indexes:

- unique index on `email`

Notes:

- Keep auth minimal in v1.
- One admin account is enough to start.

### `products`

Purpose: main product identity and public catalog content.

Fields:

- `id` - integer primary key
- `name` - string, required
- `slug` - string, unique, indexed, required
- `tagline` - string, nullable
- `short_description` - text, nullable
- `description` - text, nullable
- `is_active` - boolean, default true
- `sort_order` - integer, default 0
- `created_at` - datetime, required
- `updated_at` - datetime, required

Constraints and indexes:

- unique index on `slug`
- index on `is_active`
- index on `sort_order`

Notes:

- `slug` is the public identifier used by the website.
- `short_description` is useful for listing cards.
- `description` supports the full detail page.

### `product_images`

Purpose: store product gallery images and hero image ordering.

Fields:

- `id` - integer primary key
- `product_id` - foreign key to `products.id`, required
- `image_path` - string, required
- `alt_text` - string, nullable
- `is_primary` - boolean, default false
- `sort_order` - integer, default 0
- `created_at` - datetime, required
- `updated_at` - datetime, required

Constraints and indexes:

- index on `product_id`
- index on `(product_id, sort_order)`

Notes:

- `image_path` can hold a local path like `/media/products/model-x/main.webp` or a full URL later.
- Only one image should normally be primary per product.

### `variants`

Purpose: represent product color variants selectable on the frontend.

Fields:

- `id` - integer primary key
- `product_id` - foreign key to `products.id`, required
- `color_name` - string, required
- `color_code` - string, nullable
- `image_path` - string, nullable
- `sort_order` - integer, default 0
- `is_active` - boolean, default true
- `created_at` - datetime, required
- `updated_at` - datetime, required

Constraints and indexes:

- index on `product_id`
- index on `(product_id, sort_order)`
- optional unique constraint on `(product_id, color_name)` if client data is clean enough

Notes:

- `color_code` should accept a normalized hex value like `#1F1F1F`.
- `image_path` can override the general gallery if a color-specific preview exists.

### `product_specs`

Purpose: one-to-one structured specs for commonly shared product attributes.

Fields:

- `id` - integer primary key
- `product_id` - foreign key to `products.id`, unique, required
- `weight` - string, nullable
- `speed` - string, nullable
- `range` - string, nullable
- `rated_power` - string, nullable
- `peak_power` - string, nullable
- `carrying_capacity` - string, nullable
- `motor` - string, nullable
- `battery_type` - string, nullable
- `charging_time` - string, nullable
- `body` - string, nullable
- `ground_clearance` - string, nullable
- `seat_height` - string, nullable
- `wheel_type` - string, nullable
- `brake_system` - string, nullable
- `tyre_size` - string, nullable
- `created_at` - datetime, required
- `updated_at` - datetime, required

Constraints and indexes:

- unique index on `product_id`

Notes:

- All fields remain nullable because raw client data may be incomplete.
- Keep values as strings in v1 to avoid premature unit normalization.
- `range` here represents the general marketed range, not the per-battery range rows.

### `battery_options`

Purpose: repeated battery configurations for a product.

Fields:

- `id` - integer primary key
- `product_id` - foreign key to `products.id`, required
- `capacity` - string, required
- `range` - string, required
- `sort_order` - integer, default 0
- `created_at` - datetime, required
- `updated_at` - datetime, required

Constraints and indexes:

- index on `product_id`
- index on `(product_id, sort_order)`

Notes:

- Example `capacity`: `60V32AH`
- Example `range`: `70-80 KM`

### `extra_specs`

Purpose: flexible key-value specs for fields that do not fit the structured model.

Fields:

- `id` - integer primary key
- `product_id` - foreign key to `products.id`, required
- `key` - string, required
- `label` - string, required
- `value` - string, required
- `sort_order` - integer, default 0
- `created_at` - datetime, required
- `updated_at` - datetime, required

Constraints and indexes:

- index on `product_id`
- index on `(product_id, sort_order)`
- index on `(product_id, key)`

Notes:

- `key` should be normalized and stable, for example `charger`, `display`, `controller`.
- `label` is presentation-friendly text shown in the UI.
- This table is the pressure-release valve for inconsistent source data.

### `leads`

Purpose: store all product enquiries from the site.

Fields:

- `id` - integer primary key
- `name` - string, required
- `phone` - string, required
- `product_id` - foreign key to `products.id`, nullable
- `variant_id` - foreign key to `variants.id`, nullable
- `message` - text, nullable
- `source` - enum `LeadSource`, required
- `status` - enum `LeadStatus`, default `new`
- `preferred_contact_time` - string, nullable
- `created_at` - datetime, required
- `updated_at` - datetime, required

Constraints and indexes:

- index on `product_id`
- index on `variant_id`
- index on `source`
- index on `status`
- index on `created_at`

Notes:

- `product_id` and `variant_id` stay nullable so the lead table can still handle generic brand enquiries.
- `preferred_contact_time` is useful for schedule-call flow without introducing a calendar subsystem.
- No email fields are needed for this project.

## Relationships

- `Product` has many `ProductImage`
- `Product` has many `Variant`
- `Product` has one `ProductSpec`
- `Product` has many `BatteryOption`
- `Product` has many `ExtraSpec`
- `Product` has many `Lead`
- `Variant` belongs to one `Product`
- `Variant` has many `Lead`

## Recommended Delete Behavior

- Deleting a `Product` should cascade to:
  - `product_images`
  - `variants`
  - `product_specs`
  - `battery_options`
  - `extra_specs`
- Leads should usually be preserved for audit history.

Recommended approach:

- use `is_active` for products instead of deleting in normal admin flow
- block deleting a product that has associated leads, or set `product_id` in leads to null only if explicit deletion is allowed later

## Normalization Rules

### Slugs

- lowercase
- hyphen-separated
- unique
- generated from product name with admin override allowed

### Extra Spec Keys

- lowercase
- snake_case
- normalized once before saving

Examples:

- `Charger` -> `charger`
- `USB Port` -> `usb_port`
- `Cruise Control` -> `cruise_control`

### Color Codes

- validate hex format such as `#FFFFFF`
- store uppercase or lowercase consistently

### Phone Numbers

- trim whitespace
- preserve country code when available
- store a normalized dialable string

## Public API Shape Goals

The schema should support a product detail response shaped roughly like:

- product basics
- gallery images
- color variants
- structured specs
- battery options
- extra specs

This keeps the frontend simple and avoids multiple public API calls for one product page.

## Admin Editing Strategy

Even though the schema uses separate tables, admin editing should behave like editing one product aggregate:

- base product fields
- images
- variants
- structured specs
- battery options
- extra specs

This will make your future admin UI or admin API clients much easier to build.

## Local Images Now, Cloudinary Later

Current plan:

- store relative or absolute image paths in DB
- serve local media in development

Future-safe decision:

- keep image columns generic as `image_path`
- allow them to later hold Cloudinary URLs without schema changes

No separate media provider table is needed in v1.

## PostgreSQL and Supabase Compatibility

This schema works well for:

- local PostgreSQL development
- Supabase-hosted PostgreSQL later

No Supabase-specific design is required right now.

If Supabase auth is added later, it can remain separate from this v1 admin auth model.

## Suggested Build Order After This

1. create SQLAlchemy base, mixins, enums, and models
2. add Alembic initial migration
3. add Pydantic schemas for public and admin flows
4. build product read services
5. build lead creation service
6. add admin authentication and CRUD APIs
