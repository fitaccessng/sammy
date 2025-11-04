"""
Create BOQ Templates
This script creates sample BOQ templates for different project types
"""

from app import create_app
from extensions import db
from models import BOQItem

def create_boq_templates():
    app = create_app()
    
    with app.app_context():
        # Bridge Project Templates
        bridge_templates = [
            {
                'item_description': 'Reinforced Concrete Bridge Deck',
                'quantity': 1,
                'unit': 'm²',
                'unit_price': 25000.00,
                'total_cost': 25000.00,
                'item_type': 'Bridge',
                'category': 'Structural',
                'bill_no': 'B001',
                'item_no': '001'
            },
            {
                'item_description': 'Bridge Abutment Construction',
                'quantity': 2,
                'unit': 'units',
                'unit_price': 150000.00,
                'total_cost': 300000.00,
                'item_type': 'Bridge',
                'category': 'Foundation',
                'bill_no': 'B001',
                'item_no': '002'
            },
            {
                'item_description': 'Steel Reinforcement Bars',
                'quantity': 5000,
                'unit': 'kg',
                'unit_price': 800.00,
                'total_cost': 4000000.00,
                'item_type': 'Bridge',
                'category': 'Materials',
                'bill_no': 'B001',
                'item_no': '003'
            },
            {
                'item_description': 'Bridge Expansion Joints',
                'quantity': 4,
                'unit': 'units',
                'unit_price': 50000.00,
                'total_cost': 200000.00,
                'item_type': 'Bridge',
                'category': 'Accessories',
                'bill_no': 'B001',
                'item_no': '004'
            }
        ]
        
        # Building Project Templates
        building_templates = [
            {
                'item_description': 'Foundation Excavation',
                'quantity': 100,
                'unit': 'm³',
                'unit_price': 2500.00,
                'total_cost': 250000.00,
                'item_type': 'Building',
                'category': 'Earthworks',
                'bill_no': 'BD001',
                'item_no': '001'
            },
            {
                'item_description': 'Concrete Block Work',
                'quantity': 500,
                'unit': 'm²',
                'unit_price': 8000.00,
                'total_cost': 4000000.00,
                'item_type': 'Building',
                'category': 'Masonry',
                'bill_no': 'BD001',
                'item_no': '002'
            },
            {
                'item_description': 'Roofing with Aluminum Sheets',
                'quantity': 200,
                'unit': 'm²',
                'unit_price': 12000.00,
                'total_cost': 2400000.00,
                'item_type': 'Building',
                'category': 'Roofing',
                'bill_no': 'BD001',
                'item_no': '003'
            },
            {
                'item_description': 'Electrical Installation',
                'quantity': 1,
                'unit': 'lot',
                'unit_price': 500000.00,
                'total_cost': 500000.00,
                'item_type': 'Building',
                'category': 'Services',
                'bill_no': 'BD001',
                'item_no': '004'
            }
        ]
        
        # Road Project Templates
        road_templates = [
            {
                'item_description': 'Road Base Course',
                'quantity': 1000,
                'unit': 'm³',
                'unit_price': 15000.00,
                'total_cost': 15000000.00,
                'item_type': 'Road',
                'category': 'Base',
                'bill_no': 'R001',
                'item_no': '001'
            },
            {
                'item_description': 'Asphalt Surface Course',
                'quantity': 500,
                'unit': 'm³',
                'unit_price': 35000.00,
                'total_cost': 17500000.00,
                'item_type': 'Road',
                'category': 'Surface',
                'bill_no': 'R001',
                'item_no': '002'
            },
            {
                'item_description': 'Road Drainage System',
                'quantity': 100,
                'unit': 'm',
                'unit_price': 25000.00,
                'total_cost': 2500000.00,
                'item_type': 'Road',
                'category': 'Drainage',
                'bill_no': 'R001',
                'item_no': '003'
            },
            {
                'item_description': 'Road Marking and Signage',
                'quantity': 1,
                'unit': 'lot',
                'unit_price': 200000.00,
                'total_cost': 200000.00,
                'item_type': 'Road',
                'category': 'Safety',
                'bill_no': 'R001',
                'item_no': '004'
            }
        ]
        
        # Culvert Project Templates
        culvert_templates = [
            {
                'item_description': 'Concrete Culvert Box',
                'quantity': 10,
                'unit': 'm',
                'unit_price': 75000.00,
                'total_cost': 750000.00,
                'item_type': 'Culvert',
                'category': 'Structure',
                'bill_no': 'C001',
                'item_no': '001'
            },
            {
                'item_description': 'Culvert Inlet/Outlet Works',
                'quantity': 2,
                'unit': 'units',
                'unit_price': 100000.00,
                'total_cost': 200000.00,
                'item_type': 'Culvert',
                'category': 'Accessories',
                'bill_no': 'C001',
                'item_no': '002'
            },
            {
                'item_description': 'Culvert Backfill Material',
                'quantity': 50,
                'unit': 'm³',
                'unit_price': 5000.00,
                'total_cost': 250000.00,
                'item_type': 'Culvert',
                'category': 'Earthworks',
                'bill_no': 'C001',
                'item_no': '003'
            }
        ]
        
        all_templates = bridge_templates + building_templates + road_templates + culvert_templates
        
        # Clear existing templates
        existing_templates = BOQItem.query.filter_by(is_template=True).all()
        for template in existing_templates:
            db.session.delete(template)
        
        # Add new templates
        for template_data in all_templates:
            template = BOQItem(
                project_id=None,  # Templates don't belong to specific projects
                is_template=True,
                **template_data
            )
            db.session.add(template)
        
        db.session.commit()
        print(f"Successfully created {len(all_templates)} BOQ templates")
        
        # Print summary
        for project_type in ['Bridge', 'Building', 'Road', 'Culvert']:
            count = BOQItem.query.filter_by(is_template=True, item_type=project_type).count()
            print(f"- {project_type}: {count} templates")

if __name__ == '__main__':
    create_boq_templates()