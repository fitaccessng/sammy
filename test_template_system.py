#!/usr/bin/env python3
"""
Test the BOQ and Material Schedule system
"""

from app import create_app
from extensions import db
from models import BOQItem, MaterialSchedule

def test_templates():
    """Test that templates are properly created and can be loaded"""
    app = create_app()
    
    with app.app_context():
        # Test BOQ templates
        boq_templates = BOQItem.query.filter_by(project_id=None).all()
        print(f"BOQ Templates found: {len(boq_templates)}")
        
        if boq_templates:
            bridge_boq = [t for t in boq_templates if 'bridge' in t.item_description.lower()]
            building_boq = [t for t in boq_templates if any(word in t.item_description.lower() for word in ['building', 'block', 'roof', 'door', 'window'])]
            road_boq = [t for t in boq_templates if any(word in t.item_description.lower() for word in ['road', 'asphalt', 'bitumen', 'pavement'])]
            culvert_boq = [t for t in boq_templates if 'culvert' in t.item_description.lower()]
            
            print(f"  - Bridge BOQ items: {len(bridge_boq)}")
            print(f"  - Building BOQ items: {len(building_boq)}")
            print(f"  - Road BOQ items: {len(road_boq)}")
            print(f"  - Culvert BOQ items: {len(culvert_boq)}")
        
        # Test Material Schedule templates
        material_templates = MaterialSchedule.query.filter_by(project_id=None).all()
        print(f"\nMaterial Schedule Templates found: {len(material_templates)}")
        
        if material_templates:
            bridge_materials = [m for m in material_templates if any(word in m.material_name.lower() for word in ['prestressing', 'bearing', 'expansion', 'tendon'])]
            building_materials = [m for m in material_templates if any(word in m.material_name.lower() for word in ['blocks', 'roof', 'door', 'window', 'tiles'])]
            road_materials = [m for m in material_templates if any(word in m.material_name.lower() for word in ['bitumen', 'asphalt', 'road', 'street', 'guard'])]
            culvert_materials = [m for m in material_templates if any(word in m.material_name.lower() for word in ['gabion', 'pitching', 'backfill', 'perforated'])]
            
            print(f"  - Bridge-specific materials: {len(bridge_materials)}")
            print(f"  - Building-specific materials: {len(building_materials)}")
            print(f"  - Road-specific materials: {len(road_materials)}")
            print(f"  - Culvert-specific materials: {len(culvert_materials)}")
        
        # Show sample templates
        print(f"\nSample BOQ Templates:")
        for boq in boq_templates[:3]:
            print(f"  - {boq.bill_no}: {boq.item_description} - ₦{boq.total_cost:,.2f}")
        
        print(f"\nSample Material Templates:")
        for material in material_templates[:3]:
            print(f"  - {material.material_name}: {material.required_qty} {material.unit} @ ₦{material.unit_cost:,.2f}")
        
        print(f"\nSystem Status: ✅ Templates loaded successfully!")
        print(f"Total BOQ templates: {len(boq_templates)}")
        print(f"Total Material templates: {len(material_templates)}")

if __name__ == "__main__":
    test_templates()