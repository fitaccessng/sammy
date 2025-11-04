#!/usr/bin/env python3
"""
Create Material Schedule templates using direct SQL
"""

import sqlite3
from datetime import datetime

# Material templates data
BRIDGE_MATERIALS = [
    ("Ordinary Portland Cement (42.5N)", 285, "bags", 3500, "Complying with BS EN 197-1, for all concrete works", "Planned", "Dangote Cement", "0801-234-5678"),
    ("Sharp Sand (Washed)", 125, "m³", 8000, "Clean sharp sand, well graded, free from clay and organic matter", "Planned", "River Sand Ltd", "0802-345-6789"),
    ("Granite Chippings 20mm", 95, "m³", 12000, "Crushed granite aggregate for concrete", "Planned", "Granite Quarry Co", "0803-456-7890"),
    ("High Tensile Steel Bars 12mm", 2850, "kg", 180, "Grade 60 deformed bars to BS 4449", "Planned", "Steel Masters Ltd", "0804-567-8901"),
    ("High Tensile Steel Bars 16mm", 2450, "kg", 175, "Grade 60 deformed bars to BS 4449", "Planned", "Steel Masters Ltd", "0804-567-8901"),
    ("Prestressing Tendons 15.2mm", 2400, "m", 850, "7-wire strand for post-tensioned construction", "Planned", "Prestress Systems", "0806-789-0123"),
    ("Marine Plywood 18mm", 145, "sheets", 12500, "Waterproof plywood for concrete formwork", "Planned", "Timber Merchants", "0807-890-1234"),
    ("Elastomeric Bearing Pads", 24, "No", 75000, "Laminated rubber bearings for bridge deck support", "Planned", "Bridge Components", "0810-123-4567"),
    ("Expansion Joint Systems", 2, "sets", 180000, "Modular expansion joints for bridge deck", "Planned", "Bridge Components", "0810-123-4567"),
    ("Waterproofing Membrane", 185, "m²", 4500, "Modified bitumen membrane for bridge deck", "Planned", "Waterproof Solutions", "0811-234-5678"),
]

BUILDING_MATERIALS = [
    ("Ordinary Portland Cement (42.5N)", 485, "bags", 3500, "Complying with BS EN 197-1", "Planned", "Dangote Cement", "0801-234-5678"),
    ("Sharp Sand (Fine Aggregate)", 185, "m³", 8000, "Clean sharp sand for concrete", "Planned", "River Sand Ltd", "0802-345-6789"),
    ("Sandcrete Blocks 150mm (6 inch)", 2850, "pieces", 250, "Standard hollow blocks", "Planned", "Block Factory", "0805-678-9012"),
    ("Steel Roof Trusses", 24, "sets", 85000, "Fabricated steel trusses", "Planned", "Steel Fabricators", "0806-789-0123"),
    ("Long Span Aluminum Sheets 0.55mm", 485, "m²", 4500, "Corrugated roofing sheets", "Planned", "Roofing Solutions", "0807-890-1234"),
    ("Ceramic Floor Tiles 400x400mm", 385, "m²", 6500, "Non-slip ceramic tiles", "Planned", "Tile World", "0808-901-2345"),
    ("Flush Doors with Frames", 28, "sets", 45000, "Solid core flush doors", "Planned", "Door & Window Co", "0810-123-4567"),
    ("Aluminum Windows", 32, "m²", 25000, "Sliding windows with nets", "Planned", "Door & Window Co", "0810-123-4567"),
    ("PVC Pipes 100mm (Soil)", 125, "m", 1850, "Heavy duty soil pipes", "Planned", "Pipe World", "0813-456-7890"),
    ("Water Closets", 12, "sets", 45000, "Close coupled WC suites", "Planned", "Sanitary Ware", "0814-567-8901"),
]

ROAD_MATERIALS = [
    ("Laterite (Sub-base Material)", 2880, "m³", 6500, "Compactable laterite meeting CBR requirements", "Planned", "Quarry Operators", "0801-234-5678"),
    ("Crushed Stone Base", 3840, "m³", 12500, "Graded crushed stone aggregate", "Planned", "Stone Crushers Ltd", "0802-345-6789"),
    ("Bitumen 60/70 Penetration", 185, "tonnes", 450000, "Penetration grade bitumen", "Planned", "Bitumen Suppliers", "0804-567-8901"),
    ("Asphalt Aggregate 14mm", 1150, "tonnes", 15500, "Dense graded aggregate for asphalt", "Planned", "Asphalt Plants", "0805-678-9012"),
    ("Concrete Culvert Pipes 900mm", 124, "m", 12500, "Reinforced concrete pipes Class 3", "Planned", "Concrete Products", "0806-789-0123"),
    ("Thermoplastic Road Marking Paint", 485, "kg", 1250, "Hot-applied thermoplastic marking", "Planned", "Road Marking Co", "0810-123-4567"),
    ("Street Light Poles", 48, "pieces", 185000, "10m galvanized steel poles", "Planned", "Lighting Solutions", "0814-567-8901"),
    ("LED Street Light Fittings", 48, "pieces", 85000, "150W LED luminaires", "Planned", "Lighting Solutions", "0814-567-8901"),
    ("Guard Rail Beams", 380, "m", 8500, "Galvanized steel guard rails", "Planned", "Safety Barriers", "0813-456-7890"),
    ("Road Signs (Aluminum)", 24, "pieces", 45000, "Reflective road signs with posts", "Planned", "Signs & Graphics", "0812-345-6789"),
]

CULVERT_MATERIALS = [
    ("Ordinary Portland Cement (42.5N)", 125, "bags", 3500, "High grade cement for culvert construction", "Planned", "Dangote Cement", "0801-234-5678"),
    ("Sharp Sand", 45, "m³", 8000, "Clean washed sand for concrete", "Planned", "River Sand Ltd", "0802-345-6789"),
    ("High Tensile Steel Bars 16mm", 685, "kg", 175, "Grade 60 deformed bars", "Planned", "Steel Masters Ltd", "0804-567-8901"),
    ("Marine Plywood 15mm", 45, "sheets", 12500, "Waterproof formwork plywood", "Planned", "Timber Merchants", "0806-789-0123"),
    ("Waterproofing Membrane", 125, "m²", 4500, "Modified bitumen membrane", "Planned", "Waterproof Solutions", "0808-901-2345"),
    ("Selected Backfill Material", 125, "m³", 4500, "Granular material for backfilling", "Planned", "Quarry Operators", "0810-123-4567"),
    ("Stone Pitching", 45, "m³", 6500, "Hand-packed stone protection", "Planned", "Stone Quarry", "0814-567-8901"),
    ("Gabion Baskets", 24, "m³", 12500, "Wire mesh gabion baskets", "Planned", "Gabion Systems", "0815-678-9012"),
    ("Perforated Pipes 100mm", 85, "m", 1850, "Drainage pipes with slots", "Planned", "Pipe World", "0813-456-7890"),
    ("Geotextile (Under Gabions)", 85, "m²", 2500, "Non-woven geotextile fabric", "Planned", "Geosynthetics", "0816-789-0123"),
]

def create_material_templates():
    """Create material templates directly in SQLite"""
    conn = sqlite3.connect('sammy.db')
    cursor = conn.cursor()
    
    try:
        # Delete existing template materials
        cursor.execute("DELETE FROM material_schedules WHERE project_id IS NULL")
        existing_count = cursor.rowcount
        print(f"Deleted {existing_count} existing template materials")
        
        # Insert bridge materials
        bridge_count = 0
        for material in BRIDGE_MATERIALS:
            name, qty, unit, cost, spec, status, supplier, contact = material
            total_cost = qty * cost
            now = datetime.now().isoformat()
            
            cursor.execute("""
                INSERT INTO material_schedules 
                (project_id, boq_item_id, material_name, specification, required_qty, 
                 ordered_qty, received_qty, used_qty, unit, unit_cost, total_cost, 
                 status, supplier_name, supplier_contact, created_at, updated_at)
                VALUES (NULL, NULL, ?, ?, ?, 0.0, 0.0, 0.0, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, spec, qty, unit, cost, total_cost, status, supplier, contact, now, now))
            bridge_count += 1
        
        # Insert building materials
        building_count = 0
        for material in BUILDING_MATERIALS:
            name, qty, unit, cost, spec, status, supplier, contact = material
            total_cost = qty * cost
            now = datetime.now().isoformat()
            
            cursor.execute("""
                INSERT INTO material_schedules 
                (project_id, boq_item_id, material_name, specification, required_qty, 
                 ordered_qty, received_qty, used_qty, unit, unit_cost, total_cost, 
                 status, supplier_name, supplier_contact, created_at, updated_at)
                VALUES (NULL, NULL, ?, ?, ?, 0.0, 0.0, 0.0, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, spec, qty, unit, cost, total_cost, status, supplier, contact, now, now))
            building_count += 1
            
        # Insert road materials
        road_count = 0
        for material in ROAD_MATERIALS:
            name, qty, unit, cost, spec, status, supplier, contact = material
            total_cost = qty * cost
            now = datetime.now().isoformat()
            
            cursor.execute("""
                INSERT INTO material_schedules 
                (project_id, boq_item_id, material_name, specification, required_qty, 
                 ordered_qty, received_qty, used_qty, unit, unit_cost, total_cost, 
                 status, supplier_name, supplier_contact, created_at, updated_at)
                VALUES (NULL, NULL, ?, ?, ?, 0.0, 0.0, 0.0, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, spec, qty, unit, cost, total_cost, status, supplier, contact, now, now))
            road_count += 1
            
        # Insert culvert materials
        culvert_count = 0
        for material in CULVERT_MATERIALS:
            name, qty, unit, cost, spec, status, supplier, contact = material
            total_cost = qty * cost
            now = datetime.now().isoformat()
            
            cursor.execute("""
                INSERT INTO material_schedules 
                (project_id, boq_item_id, material_name, specification, required_qty, 
                 ordered_qty, received_qty, used_qty, unit, unit_cost, total_cost, 
                 status, supplier_name, supplier_contact, created_at, updated_at)
                VALUES (NULL, NULL, ?, ?, ?, 0.0, 0.0, 0.0, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, spec, qty, unit, cost, total_cost, status, supplier, contact, now, now))
            culvert_count += 1
        
        conn.commit()
        
        print(f"\nCreated comprehensive material templates:")
        print(f"- Bridge materials: {bridge_count}")
        print(f"- Building materials: {building_count}")
        print(f"- Road materials: {road_count}")
        print(f"- Culvert materials: {culvert_count}")
        print(f"Total material templates: {bridge_count + building_count + road_count + culvert_count}")
        
        # Calculate sample costs
        bridge_total = sum(qty * cost for _, qty, _, cost, _, _, _, _ in BRIDGE_MATERIALS)
        building_total = sum(qty * cost for _, qty, _, cost, _, _, _, _ in BUILDING_MATERIALS)
        road_total = sum(qty * cost for _, qty, _, cost, _, _, _, _ in ROAD_MATERIALS)
        culvert_total = sum(qty * cost for _, qty, _, cost, _, _, _, _ in CULVERT_MATERIALS)
        
        print(f"\nSample total material costs per project type:")
        print(f"- Bridge materials: ₦{bridge_total:,.2f}")
        print(f"- Building materials: ₦{building_total:,.2f}")
        print(f"- Road materials: ₦{road_total:,.2f}")
        print(f"- Culvert materials: ₦{culvert_total:,.2f}")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    create_material_templates()