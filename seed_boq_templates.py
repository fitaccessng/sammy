"""
Seed BOQ (Bill of Quantities) template data for different project types
"""
from app import create_app
from extensions import db
from models import BOQItem

def seed_bridge_boq():
    """Seed BOQ template for Bridge projects - BILL NO. 4 PAVEMENTS AND SURFACING"""
    bridge_items = [
        {
            'bill_no': 'BILL NO. 4',
            'item_no': '4.01',
            'item_description': 'Laterite',
            'quantity': 1500.0,
            'unit': 'm³',
            'unit_price': 5000.0,
            'item_type': 'Bridge',
            'category': 'Pavements and Surfacing',
            'is_template': True
        },
        {
            'bill_no': 'BILL NO. 4',
            'item_no': '4.02',
            'item_description': 'Crushed Stone Base Course',
            'quantity': 800.0,
            'unit': 'm³',
            'unit_price': 12000.0,
            'item_type': 'Bridge',
            'category': 'Pavements and Surfacing',
            'is_template': True
        },
        {
            'bill_no': 'BILL NO. 4',
            'item_no': '4.04.1',
            'item_description': 'Asphaltic Concrete Wearing Course (50mm thick)',
            'quantity': 600.0,
            'unit': 'm²',
            'unit_price': 8500.0,
            'item_type': 'Bridge',
            'category': 'Pavements and Surfacing',
            'is_template': True
        },
        {
            'bill_no': 'BILL NO. 4',
            'item_no': '4.04.2',
            'item_description': 'Asphaltic Concrete Binder Course (75mm thick)',
            'quantity': 600.0,
            'unit': 'm²',
            'unit_price': 7500.0,
            'item_type': 'Bridge',
            'category': 'Pavements and Surfacing',
            'is_template': True
        },
        {
            'bill_no': 'BILL NO. 5',
            'item_no': '5.01',
            'item_description': 'Bridge Deck (Reinforced Concrete)',
            'quantity': 200.0,
            'unit': 'm²',
            'unit_price': 45000.0,
            'item_type': 'Bridge',
            'category': 'Bridge Structure',
            'is_template': True
        },
        {
            'bill_no': 'BILL NO. 5',
            'item_no': '5.02',
            'item_description': 'Bridge Piers (Concrete)',
            'quantity': 8.0,
            'unit': 'nos',
            'unit_price': 350000.0,
            'item_type': 'Bridge',
            'category': 'Bridge Structure',
            'is_template': True
        },
        {
            'bill_no': 'BILL NO. 5',
            'item_no': '5.03',
            'item_description': 'Bridge Abutments',
            'quantity': 2.0,
            'unit': 'nos',
            'unit_price': 500000.0,
            'item_type': 'Bridge',
            'category': 'Bridge Structure',
            'is_template': True
        }
    ]
    return bridge_items


def seed_building_boq():
    """Seed BOQ template for Building projects"""
    building_items = [
        # SUBSTRUCTURE
        {
            'bill_no': 'SUBSTRUCTURE',
            'item_no': 'A1',
            'item_description': 'Excavation for foundation',
            'quantity': 150.0,
            'unit': 'm³',
            'unit_price': 2500.0,
            'item_type': 'Building',
            'category': 'Substructure',
            'is_template': True
        },
        {
            'bill_no': 'SUBSTRUCTURE',
            'item_no': 'A2',
            'item_description': 'Concrete foundation (1:2:4 mix)',
            'quantity': 120.0,
            'unit': 'm³',
            'unit_price': 35000.0,
            'item_type': 'Building',
            'category': 'Substructure',
            'is_template': True
        },
        {
            'bill_no': 'SUBSTRUCTURE',
            'item_no': 'A3',
            'item_description': 'Reinforcement steel for foundation',
            'quantity': 5000.0,
            'unit': 'kg',
            'unit_price': 450.0,
            'item_type': 'Building',
            'category': 'Substructure',
            'is_template': True
        },
        {
            'bill_no': 'SUBSTRUCTURE',
            'item_no': 'A4',
            'item_description': 'DPC (Damp Proof Course)',
            'quantity': 300.0,
            'unit': 'm²',
            'unit_price': 2500.0,
            'item_type': 'Building',
            'category': 'Substructure',
            'is_template': True
        },
        # SUPERSTRUCTURE
        {
            'bill_no': 'SUPERSTRUCTURE',
            'item_no': 'B1',
            'item_description': 'Blockwork (225mm thick)',
            'quantity': 800.0,
            'unit': 'm²',
            'unit_price': 8500.0,
            'item_type': 'Building',
            'category': 'Superstructure',
            'is_template': True
        },
        {
            'bill_no': 'SUPERSTRUCTURE',
            'item_no': 'B2',
            'item_description': 'Concrete columns (230mm x 230mm)',
            'quantity': 45.0,
            'unit': 'm',
            'unit_price': 12000.0,
            'item_type': 'Building',
            'category': 'Superstructure',
            'is_template': True
        },
        {
            'bill_no': 'SUPERSTRUCTURE',
            'item_no': 'B3',
            'item_description': 'Concrete beams (230mm x 450mm)',
            'quantity': 120.0,
            'unit': 'm',
            'unit_price': 15000.0,
            'item_type': 'Building',
            'category': 'Superstructure',
            'is_template': True
        },
        {
            'bill_no': 'SUPERSTRUCTURE',
            'item_no': 'B4',
            'item_description': 'Floor slab (150mm thick)',
            'quantity': 500.0,
            'unit': 'm²',
            'unit_price': 18000.0,
            'item_type': 'Building',
            'category': 'Superstructure',
            'is_template': True
        },
        # ROOF
        {
            'bill_no': 'ROOF',
            'item_no': 'C1',
            'item_description': 'Steel roof trusses',
            'quantity': 25.0,
            'unit': 'nos',
            'unit_price': 45000.0,
            'item_type': 'Building',
            'category': 'Roof',
            'is_template': True
        },
        {
            'bill_no': 'ROOF',
            'item_no': 'C2',
            'item_description': 'Roofing sheets (0.55mm gauge)',
            'quantity': 600.0,
            'unit': 'm²',
            'unit_price': 3500.0,
            'item_type': 'Building',
            'category': 'Roof',
            'is_template': True
        },
        {
            'bill_no': 'ROOF',
            'item_no': 'C3',
            'item_description': 'Rain water gutters (PVC)',
            'quantity': 80.0,
            'unit': 'm',
            'unit_price': 2500.0,
            'item_type': 'Building',
            'category': 'Roof',
            'is_template': True
        },
        {
            'bill_no': 'ROOF',
            'item_no': 'C4',
            'item_description': 'Fascia boards',
            'quantity': 80.0,
            'unit': 'm',
            'unit_price': 3000.0,
            'item_type': 'Building',
            'category': 'Roof',
            'is_template': True
        },
        # FINISHES
        {
            'bill_no': 'FINISHES',
            'item_no': 'D1',
            'item_description': 'Plastering (internal walls)',
            'quantity': 800.0,
            'unit': 'm²',
            'unit_price': 3500.0,
            'item_type': 'Building',
            'category': 'Finishes',
            'is_template': True
        },
        {
            'bill_no': 'FINISHES',
            'item_no': 'D2',
            'item_description': 'Painting (emulsion)',
            'quantity': 800.0,
            'unit': 'm²',
            'unit_price': 2000.0,
            'item_type': 'Building',
            'category': 'Finishes',
            'is_template': True
        },
        {
            'bill_no': 'FINISHES',
            'item_no': 'D3',
            'item_description': 'Floor tiles (600x600mm)',
            'quantity': 500.0,
            'unit': 'm²',
            'unit_price': 6500.0,
            'item_type': 'Building',
            'category': 'Finishes',
            'is_template': True
        }
    ]
    return building_items


def seed_road_boq():
    """Seed BOQ template for Road projects"""
    road_items = [
        {
            'bill_no': 'EARTHWORKS',
            'item_no': 'R1',
            'item_description': 'Site clearing',
            'quantity': 5000.0,
            'unit': 'm²',
            'unit_price': 500.0,
            'item_type': 'Road',
            'category': 'Earthworks',
            'is_template': True
        },
        {
            'bill_no': 'EARTHWORKS',
            'item_no': 'R2',
            'item_description': 'Excavation in soft material',
            'quantity': 2000.0,
            'unit': 'm³',
            'unit_price': 1500.0,
            'item_type': 'Road',
            'category': 'Earthworks',
            'is_template': True
        },
        {
            'bill_no': 'BASE COURSE',
            'item_no': 'R3',
            'item_description': 'Laterite sub-base',
            'quantity': 3000.0,
            'unit': 'm³',
            'unit_price': 5000.0,
            'item_type': 'Road',
            'category': 'Base Course',
            'is_template': True
        },
        {
            'bill_no': 'BASE COURSE',
            'item_no': 'R4',
            'item_description': 'Crushed stone base (150mm)',
            'quantity': 2500.0,
            'unit': 'm³',
            'unit_price': 12000.0,
            'item_type': 'Road',
            'category': 'Base Course',
            'is_template': True
        },
        {
            'bill_no': 'SURFACING',
            'item_no': 'R5',
            'item_description': 'Prime coat',
            'quantity': 10000.0,
            'unit': 'm²',
            'unit_price': 800.0,
            'item_type': 'Road',
            'category': 'Surfacing',
            'is_template': True
        },
        {
            'bill_no': 'SURFACING',
            'item_no': 'R6',
            'item_description': 'Asphaltic concrete (50mm)',
            'quantity': 10000.0,
            'unit': 'm²',
            'unit_price': 8500.0,
            'item_type': 'Road',
            'category': 'Surfacing',
            'is_template': True
        }
    ]
    return road_items


def seed_culvert_boq():
    """Seed BOQ template for Culvert projects"""
    culvert_items = [
        {
            'bill_no': 'EXCAVATION',
            'item_no': 'V1',
            'item_description': 'Excavation for culvert',
            'quantity': 50.0,
            'unit': 'm³',
            'unit_price': 3000.0,
            'item_type': 'Culvert',
            'category': 'Excavation',
            'is_template': True
        },
        {
            'bill_no': 'CONCRETE WORK',
            'item_no': 'V2',
            'item_description': 'Concrete for culvert base (1:2:4)',
            'quantity': 30.0,
            'unit': 'm³',
            'unit_price': 35000.0,
            'item_type': 'Culvert',
            'category': 'Concrete Work',
            'is_template': True
        },
        {
            'bill_no': 'CONCRETE WORK',
            'item_no': 'V3',
            'item_description': 'Reinforcement steel',
            'quantity': 1500.0,
            'unit': 'kg',
            'unit_price': 450.0,
            'item_type': 'Culvert',
            'category': 'Concrete Work',
            'is_template': True
        },
        {
            'bill_no': 'CULVERT STRUCTURE',
            'item_no': 'V4',
            'item_description': 'Precast concrete pipes (900mm dia)',
            'quantity': 20.0,
            'unit': 'm',
            'unit_price': 25000.0,
            'item_type': 'Culvert',
            'category': 'Culvert Structure',
            'is_template': True
        },
        {
            'bill_no': 'HEADWALLS',
            'item_no': 'V5',
            'item_description': 'Concrete headwalls and wingwalls',
            'quantity': 4.0,
            'unit': 'nos',
            'unit_price': 85000.0,
            'item_type': 'Culvert',
            'category': 'Headwalls',
            'is_template': True
        }
    ]
    return culvert_items


def seed_all_boq_templates():
    """Seed all BOQ templates"""
    app = create_app()
    with app.app_context():
        # Check if templates already exist
        existing = BOQItem.query.filter_by(is_template=True).first()
        if existing:
            print("BOQ templates already exist. Skipping...")
            return
        
        all_items = []
        
        # Add all templates
        all_items.extend(seed_bridge_boq())
        all_items.extend(seed_building_boq())
        all_items.extend(seed_road_boq())
        all_items.extend(seed_culvert_boq())
        
        # Calculate total costs for each item
        for item_data in all_items:
            # Set project_id to None for templates (they're not tied to specific projects)
            item_data['project_id'] = None
            item = BOQItem(**item_data)
            item.calculate_total_cost()
            db.session.add(item)
        
        try:
            db.session.commit()
            print(f"Successfully seeded {len(all_items)} BOQ template items:")
            print(f"  - Bridge: {len(seed_bridge_boq())} items")
            print(f"  - Building: {len(seed_building_boq())} items")
            print(f"  - Road: {len(seed_road_boq())} items")
            print(f"  - Culvert: {len(seed_culvert_boq())} items")
        except Exception as e:
            db.session.rollback()
            print(f"Error seeding BOQ templates: {e}")


if __name__ == '__main__':
    seed_all_boq_templates()
