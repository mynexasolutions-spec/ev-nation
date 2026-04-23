"""Seed database from JSON files in data/ folder."""
import json
import random
import re
from pathlib import Path

# -- Bootstrap the app so models and DB are available --
from app.core.bootstrap import bootstrap_application
bootstrap_application()

from app.db.session import get_session_factory
from app.models.product import (
    Product, ProductSpec, Variant, BatteryOption, ExtraSpec,
)

# Color name → hex code mapping for swatches
COLOR_MAP = {
    "green": "#2d7a4f",
    "ice blue": "#a2d5f2",
    "wine red": "#722f37",
    "metallic grey": "#8c8c8c",
    "metallic black": "#1a1a1a",
    "ivory white": "#fffff0",
    "yellow": "#ffd700",
    "cherry red": "#de3163",
    "red": "#e63946",
    "blue": "#2a6fdb",
    "pearl white": "#f5f5f0",
    "matte black": "#222222",
    "grey": "#888888",
    "white": "#f0f0f0",
    "black": "#111111",
    "orange": "#ff8c00",
    "silver": "#c0c0c0",
    "midnight blue": "#191970",
    "cosmic blue": "#1e3a5f",
    "blazing orange": "#ff5e0e",
    "coral pink": "#f08080",
    "electric green": "#00ff41",
}


def slugify(name: str) -> str:
    s = name.lower().strip()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[\s_]+', '-', s)
    s = re.sub(r'-+', '-', s)
    return s.strip('-')


def get_range_display(specs: dict) -> str | None:
    """Extract a displayable range string."""
    if "range_per_charge" in specs:
        return specs["range_per_charge"]
    if "battery" in specs and isinstance(specs["battery"], list):
        ranges = [b.get("range", "") for b in specs["battery"]]
        return " / ".join(ranges) if ranges else None
    return None


def seed():
    data_dir = Path(__file__).parent / "data"
    json_files = sorted(data_dir.glob("bike*.json"), key=lambda f: int(re.search(r'\d+', f.stem).group()))

    db = get_session_factory()()
    try:
        # Clear existing data
        db.query(ExtraSpec).delete()
        db.query(BatteryOption).delete()
        db.query(ProductSpec).delete()
        db.query(Variant).delete()
        db.query(Product).delete()
        db.commit()
        print(f"Cleared existing data. Found {len(json_files)} JSON files.\n")

        for i, json_file in enumerate(json_files):
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            model_name = data["model"]
            specs = data.get("specifications", {})
            warranty = data.get("warranty", {})
            description = data.get("description", "")

            # Build a tagline from key spec
            range_str = get_range_display(specs)
            speed = specs.get("top_speed", "")
            tagline_parts = []
            if range_str:
                tagline_parts.append(range_str + " Range")
            if speed:
                tagline_parts.append(speed + " Top Speed")
            tagline = " · ".join(tagline_parts) if tagline_parts else None

            # Short description from motor + battery
            motor = specs.get("motor", "")
            battery_type = specs.get("battery_type", "")
            short_parts = [p for p in [motor, f"{battery_type} Battery" if battery_type else ""] if p]
            short_desc = " | ".join(short_parts) if short_parts else description

            # Ensure unique slug
            base_slug = slugify(model_name)
            slug = base_slug
            suffix = 2
            while db.query(Product).filter(Product.slug == slug).first():
                slug = f"{base_slug}-{suffix}"
                suffix += 1

            product = Product(
                name=model_name,
                slug=slug,
                tagline=tagline,
                short_description=short_desc,
                description=description or f"The {model_name} — an advanced electric scooter by EV Nation.",
                base_price=random.choice([65000, 75000, 85000, 95000, 110000, 125000, 145000]),
                is_active=True,
                sort_order=i,
            )
            db.add(product)
            db.flush()  # get product.id

            # -- ProductSpec --
            suspension = specs.get("suspension", {})
            front_susp = suspension.get("front", "") if isinstance(suspension, dict) else ""
            rear_susp = suspension.get("rear", "") if isinstance(suspension, dict) else ""

            product_spec = ProductSpec(
                product_id=product.id,
                weight=specs.get("net_weight_with_battery"),
                speed=specs.get("top_speed"),
                range=get_range_display(specs),
                rated_power=specs.get("rated_power"),
                peak_power=specs.get("peak_power"),
                carrying_capacity=specs.get("carrying_capacity"),
                motor=specs.get("motor"),
                battery_type=specs.get("battery_type"),
                charging_time=specs.get("charging_time"),
                body=specs.get("body"),
                ground_clearance=specs.get("ground_clearance"),
                seat_height=specs.get("seat_height"),
                wheel_type=specs.get("wheel_type"),
                brake_system=specs.get("brake_system"),
                tyre_size=specs.get("tyre_size"),
            )
            db.add(product_spec)

            # -- ExtraSpec (additional fields) --
            extra_order = 0
            extra_fields = {
                "tyre_specification": ("Tyre Spec", specs.get("tyre_specification")),
                "speedometer": ("Speedometer", specs.get("speedometer")),
                "head_light": ("Head Light", specs.get("head_light")),
                "tail_light": ("Tail Light", specs.get("tail_light")),
                "charger": ("Charger", specs.get("charger")),
                "front_suspension": ("Front Suspension", front_susp),
                "rear_suspension": ("Rear Suspension", rear_susp),
            }
            for key, (label, value) in extra_fields.items():
                if value:
                    db.add(ExtraSpec(
                        product_id=product.id,
                        key=key,
                        label=label,
                        value=value,
                        sort_order=extra_order,
                    ))
                    extra_order += 1

            # -- Warranty as ExtraSpec --
            for wkey, wval in warranty.items():
                if wval:
                    db.add(ExtraSpec(
                        product_id=product.id,
                        key=f"warranty_{wkey}",
                        label=f"Warranty ({wkey.replace('_', ' ').title()})",
                        value=wval,
                        sort_order=extra_order,
                    ))
                    extra_order += 1

            # -- Battery Options --
            batteries = specs.get("battery", [])
            if isinstance(batteries, list):
                for bi, bat in enumerate(batteries):
                    db.add(BatteryOption(
                        product_id=product.id,
                        capacity=bat.get("type", "Standard"),
                        range=bat.get("range", "N/A"),
                        sort_order=bi,
                    ))

            # -- Color Variants --
            colors = data.get("colors_available", [])
            for ci, color_name in enumerate(colors):
                color_code = COLOR_MAP.get(color_name.lower(), "#888888")
                db.add(Variant(
                    product_id=product.id,
                    color_name=color_name,
                    color_code=color_code,
                    sort_order=ci,
                    is_active=True,
                ))

            print(f"  [OK] {model_name} (slug: {product.slug}, {len(colors)} colors, {len(batteries)} battery opts)")

        db.commit()
        print(f"\nSuccessfully seeded {len(json_files)} products!")

    except Exception as e:
        db.rollback()
        print(f"ERROR: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
