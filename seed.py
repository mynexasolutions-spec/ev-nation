import json
from pathlib import Path
import sys
import os

# Add the project root to the python path so imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from app.db.session import get_session_factory
from app.core.bootstrap import bootstrap_application
from app.services.product_service import ProductService
from app.schemas.product import AdminProductCreate, ProductSpecWrite, ExtraSpecWrite, BatteryOptionWrite, VariantWrite

def seed():
    print("Bootstrapping application (this creates db tables)...")
    bootstrap_application()
    db_factory = get_session_factory()
    service = ProductService()
    
    data_dir = Path("data")
    if not data_dir.exists():
        print("Data dir not found")
        return
        
    for json_file in sorted(data_dir.glob("bike*.json")):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            model_name = data.get("model", "Unknown Model")
            print(f"Seeding {model_name} from {json_file.name}...")
            
            specs = data.get("specifications", {})
            warranty = data.get("warranty", {})
            
            # Map core specs
            spec_create = ProductSpecWrite(
                weight=str(specs.get("net_weight_with_battery") or specs.get("weight") or ""),
                speed=str(specs.get("top_speed") or ""),
                range=str(specs.get("range_per_charge") or specs.get("range") or ""),
                rated_power=str(specs.get("rated_power") or ""),
                peak_power=str(specs.get("peak_power") or ""),
                carrying_capacity=str(specs.get("carrying_capacity") or ""),
                motor=str(specs.get("motor") or ""),
                battery_type=str(specs.get("battery_type") or ""),
                charging_time=str(specs.get("charging_time") or ""),
                body=str(specs.get("body") or ""),
                ground_clearance=str(specs.get("ground_clearance") or ""),
                seat_height=str(specs.get("seat_height") or ""),
                wheel_type=str(specs.get("wheel_type") or ""),
                brake_system=str(specs.get("brake_system") or ""),
                tyre_size=str(specs.get("tyre_size") or specs.get("tyre_specification") or ""),
            )
            
            # Additional keys that go to extra_specs
            extra_specs = []
            order = 0
            
            # Warranty
            for k, v in warranty.items():
                if v:
                    extra_specs.append(ExtraSpecWrite(
                        key=f"warranty_{k}",
                        label=f"Warranty ({k.title()})",
                        value=str(v),
                        sort_order=order
                    ))
                    order += 1
                
            # Other specs not in core
            other_keys = ["speedometer", "head_light", "tail_light", "charger"]
            for k in other_keys:
                if k in specs and specs[k]:
                    extra_specs.append(ExtraSpecWrite(
                        key=k,
                        label=k.replace('_', ' ').title(),
                        value=str(specs[k]),
                        sort_order=order
                    ))
                    order += 1
                    
            if "suspension" in specs and isinstance(specs["suspension"], dict):
                for k, v in specs["suspension"].items():
                    if v:
                        extra_specs.append(ExtraSpecWrite(
                            key=f"suspension_{k}",
                            label=f"Suspension ({k.title()})",
                            value=str(v),
                            sort_order=order
                        ))
                        order += 1
                    
            # Battery options
            battery_options = []
            if "battery" in specs:
                bats = specs["battery"]
                # Sometimes it's a string, sometimes a list
                if isinstance(bats, list):
                    for i, bat in enumerate(bats):
                        if isinstance(bat, dict) and "type" in bat and "range" in bat:
                            battery_options.append(BatteryOptionWrite(
                                capacity=str(bat["type"]),
                                range=str(bat["range"]),
                                sort_order=i
                            ))
                elif isinstance(bats, dict):
                    if "type" in bats and "range" in bats:
                        battery_options.append(BatteryOptionWrite(
                            capacity=str(bats["type"]),
                            range=str(bats["range"]),
                            sort_order=0
                        ))

            # Variants
            variants = []
            if "colors_available" in data and isinstance(data["colors_available"], list):
                for i, c in enumerate(data["colors_available"]):
                    if c:
                        variants.append(VariantWrite(
                            color_name=str(c),
                            sort_order=i,
                            is_active=True
                        ))
                    
            import re
            
            # Create a simple slug from the name to append file stem if needed
            safe_name = re.sub(r'[^a-z0-9]+', '-', model_name.lower()).strip('-')
            unique_slug = f"{safe_name}-{json_file.stem}"

            product_create = AdminProductCreate(
                name=model_name,
                slug=unique_slug,
                tagline=data.get("tagline"),
                description=data.get("description"),
                is_active=True,
                spec=spec_create,
                extra_specs=extra_specs,
                battery_options=battery_options,
                variants=variants,
            )
            
            with db_factory() as db:
                service.create_admin_product(db, product_create)
                print(f"Success: {model_name}")
                
        except Exception as e:
            print(f"Failed to seed {json_file.name}: {e}")

if __name__ == "__main__":
    seed()
