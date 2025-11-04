#!/usr/bin/env python3
"""
Comprehensive Material Schedule Template Generator
Creates detailed material schedules linked to construction BOQ items
"""

from app import create_app
from extensions import db
from models import MaterialSchedule

# Bridge Material Schedule Templates
BRIDGE_MATERIAL_TEMPLATES = [
    # Concrete Materials
    {"material_name": "Ordinary Portland Cement (42.5N)", "required_qty": 285, "unit": "bags", "unit_cost": 3500, "specification": "Complying with BS EN 197-1, for all concrete works", "status": "Planned", "supplier_name": "Dangote Cement", "supplier_contact": "0801-234-5678"},
    {"material_name": "Sharp Sand (Washed)", "required_qty": 125, "unit": "m³", "unit_cost": 8000, "specification": "Clean sharp sand, well graded, free from clay and organic matter", "status": "Planned", "supplier_name": "River Sand Ltd", "supplier_contact": "0802-345-6789"},
    {"material_name": "Granite Chippings 20mm", "required_qty": 95, "unit": "m³", "unit_cost": 12000, "specification": "Crushed granite aggregate for concrete", "status": "Planned", "supplier_name": "Granite Quarry Co", "supplier_contact": "0803-456-7890"},
    {"material_name": "Granite Chippings 10mm", "required_qty": 68, "unit": "m³", "unit_cost": 12500, "specification": "Fine aggregate for high grade concrete", "status": "Planned", "supplier_name": "Granite Quarry Co", "supplier_contact": "0803-456-7890"},
    
    # Steel Reinforcement
    {"material_name": "High Tensile Steel Bars 12mm", "required_qty": 2850, "unit": "kg", "unit_cost": 180, "specification": "Grade 60 deformed bars to BS 4449", "status": "Planned", "supplier_name": "Steel Masters Ltd", "supplier_contact": "0804-567-8901"},
    {"material_name": "High Tensile Steel Bars 16mm", "required_qty": 2450, "unit": "kg", "unit_cost": 175, "specification": "Grade 60 deformed bars to BS 4449", "status": "Planned", "supplier_name": "Steel Masters Ltd", "supplier_contact": "0804-567-8901"},
    {"material_name": "High Tensile Steel Bars 20mm", "required_qty": 1850, "unit": "kg", "unit_cost": 170, "specification": "Grade 60 deformed bars to BS 4449", "status": "Planned", "supplier_name": "Steel Masters Ltd", "supplier_contact": "0804-567-8901"},
    {"material_name": "High Tensile Steel Bars 25mm", "required_qty": 950, "unit": "kg", "unit_cost": 165, "specification": "Grade 60 deformed bars to BS 4449", "status": "Planned", "supplier_name": "Steel Masters Ltd", "supplier_contact": "0804-567-8901"},
    {"material_name": "Binding Wire 16 gauge", "required_qty": 85, "unit": "kg", "unit_cost": 450, "specification": "Galvanized binding wire for reinforcement", "status": "Planned", "supplier_name": "Wire Products", "supplier_contact": "0805-678-9012"},
    
    # Prestressing Materials
    {"material_name": "Prestressing Tendons 15.2mm", "required_qty": 2400, "unit": "m", "unit_cost": 850, "specification": "7-wire strand for post-tensioned construction", "status": "Planned", "supplier_name": "Prestress Systems", "supplier_contact": "0806-789-0123"},
    {"material_name": "Prestressing Anchorages", "required_qty": 48, "unit": "No", "unit_cost": 25000, "specification": "Complete anchorage system with stressing equipment", "status": "Planned", "supplier_name": "Prestress Systems", "supplier_contact": "0806-789-0123"},
    {"material_name": "Prestressing Ducts", "required_qty": 285, "unit": "m", "unit_cost": 1250, "specification": "Galvanized steel ducts for tendon placement", "status": "Planned", "supplier_name": "Prestress Systems", "supplier_contact": "0806-789-0123"},
    
    # Formwork Materials
    {"material_name": "Marine Plywood 18mm", "required_qty": 145, "unit": "sheets", "unit_cost": 12500, "specification": "Waterproof plywood for concrete formwork", "status": "Planned", "supplier_name": "Timber Merchants", "supplier_contact": "0807-890-1234"},
    {"material_name": "Scaffold Poles", "required_qty": 285, "unit": "pieces", "unit_cost": 8500, "specification": "Steel scaffold tubes for formwork support", "status": "Planned", "supplier_name": "Scaffold Supply", "supplier_contact": "0808-901-2345"},
    {"material_name": "Form Release Agent", "required_qty": 85, "unit": "litres", "unit_cost": 1850, "specification": "Chemical release agent for smooth concrete finish", "status": "Planned", "supplier_name": "Chemical Supply", "supplier_contact": "0809-012-3456"},
    
    # Specialized Bridge Materials
    {"material_name": "Elastomeric Bearing Pads", "required_qty": 24, "unit": "No", "unit_cost": 75000, "specification": "Laminated rubber bearings for bridge deck support", "status": "Planned", "supplier_name": "Bridge Components", "supplier_contact": "0810-123-4567"},
    {"material_name": "Expansion Joint Systems", "required_qty": 2, "unit": "sets", "unit_cost": 180000, "specification": "Modular expansion joints for bridge deck", "status": "Planned", "supplier_name": "Bridge Components", "supplier_contact": "0810-123-4567"},
    {"material_name": "Waterproofing Membrane", "required_qty": 185, "unit": "m²", "unit_cost": 4500, "specification": "Modified bitumen membrane for bridge deck", "status": "Planned", "supplier_name": "Waterproof Solutions", "supplier_contact": "0811-234-5678"},
    {"material_name": "Bridge Railings (Steel)", "required_qty": 85, "unit": "m", "unit_cost": 12500, "specification": "Galvanized steel railings with posts", "status": "Planned", "supplier_name": "Steel Fabricators", "supplier_contact": "0812-345-6789"},
    
    # Drainage Materials
    {"material_name": "PVC Drainage Pipes 150mm", "required_qty": 45, "unit": "m", "unit_cost": 2850, "specification": "Heavy duty PVC pipes for bridge drainage", "status": "Planned", "supplier_name": "Pipe World", "supplier_contact": "0813-456-7890"},
    {"material_name": "Cast Iron Gully Gratings", "required_qty": 8, "unit": "No", "unit_cost": 25000, "specification": "Heavy duty gratings for drainage inlets", "status": "Planned", "supplier_name": "Metal Works", "supplier_contact": "0814-567-8901"},
]

# Building Material Schedule Templates
BUILDING_MATERIAL_TEMPLATES = [
    # Concrete Materials
    {"material_name": "Ordinary Portland Cement (42.5N)", "required_qty": 485, "unit": "bags", "unit_cost": 3500, "specification": "Complying with BS EN 197-1", "status": "Planned", "supplier_name": "Dangote Cement", "supplier_contact": "0801-234-5678"},
    {"material_name": "Sharp Sand (Fine Aggregate)", "required_qty": 185, "unit": "m³", "unit_cost": 8000, "specification": "Clean sharp sand for concrete", "status": "Planned", "supplier_name": "River Sand Ltd", "supplier_contact": "0802-345-6789"},
    {"material_name": "Granite Chippings 20mm", "required_qty": 145, "unit": "m³", "unit_cost": 12000, "specification": "Coarse aggregate for concrete", "status": "Planned", "supplier_name": "Granite Quarry Co", "supplier_contact": "0803-456-7890"},
    
    # Steel Materials
    {"material_name": "High Tensile Steel Bars 10mm", "required_qty": 2850, "unit": "kg", "unit_cost": 185, "specification": "Grade 60 deformed bars", "status": "Planned", "supplier_name": "Steel Masters Ltd", "supplier_contact": "0804-567-8901"},
    {"material_name": "High Tensile Steel Bars 12mm", "required_qty": 3850, "unit": "kg", "unit_cost": 180, "specification": "Grade 60 deformed bars", "status": "Planned", "supplier_name": "Steel Masters Ltd", "supplier_contact": "0804-567-8901"},
    {"material_name": "High Tensile Steel Bars 16mm", "required_qty": 2950, "unit": "kg", "unit_cost": 175, "specification": "Grade 60 deformed bars", "status": "Planned", "supplier_name": "Steel Masters Ltd", "supplier_contact": "0804-567-8901"},
    {"material_name": "High Tensile Steel Bars 20mm", "required_qty": 1850, "unit": "kg", "unit_cost": 170, "specification": "Grade 60 deformed bars", "status": "Planned", "supplier_name": "Steel Masters Ltd", "supplier_contact": "0804-567-8901"},
    {"material_name": "High Tensile Steel Bars 25mm", "required_qty": 950, "unit": "kg", "unit_cost": 165, "specification": "Grade 60 deformed bars", "status": "Planned", "supplier_name": "Steel Masters Ltd", "supplier_contact": "0804-567-8901"},
    
    # Masonry Materials
    {"material_name": "Sandcrete Blocks 150mm (6 inch)", "required_qty": 2850, "unit": "pieces", "unit_cost": 250, "specification": "Standard hollow blocks", "status": "Planned", "supplier_name": "Block Factory", "supplier_contact": "0805-678-9012"},
    {"material_name": "Sandcrete Blocks 100mm (4 inch)", "required_qty": 1650, "unit": "pieces", "unit_cost": 200, "specification": "Partition wall blocks", "status": "Planned", "supplier_name": "Block Factory", "supplier_contact": "0805-678-9012"},
    {"material_name": "Mortar Sand", "required_qty": 45, "unit": "m³", "unit_cost": 6500, "specification": "Fine sand for masonry mortar", "status": "Planned", "supplier_name": "River Sand Ltd", "supplier_contact": "0802-345-6789"},
    
    # Roofing Materials
    {"material_name": "Steel Roof Trusses", "required_qty": 24, "unit": "sets", "unit_cost": 85000, "specification": "Fabricated steel trusses", "status": "Planned", "supplier_name": "Steel Fabricators", "supplier_contact": "0806-789-0123"},
    {"material_name": "Steel Purlins 100x50mm", "required_qty": 185, "unit": "m", "unit_cost": 3500, "specification": "Galvanized steel purlins", "status": "Planned", "supplier_name": "Steel Fabricators", "supplier_contact": "0806-789-0123"},
    {"material_name": "Long Span Aluminum Sheets 0.55mm", "required_qty": 485, "unit": "m²", "unit_cost": 4500, "specification": "Corrugated roofing sheets", "status": "Planned", "supplier_name": "Roofing Solutions", "supplier_contact": "0807-890-1234"},
    {"material_name": "Ridge Caps", "required_qty": 85, "unit": "m", "unit_cost": 2500, "specification": "Aluminum ridge cappings", "status": "Planned", "supplier_name": "Roofing Solutions", "supplier_contact": "0807-890-1234"},
    {"material_name": "PVC Gutters", "required_qty": 125, "unit": "m", "unit_cost": 3500, "specification": "5 inch PVC gutters", "status": "Planned", "supplier_name": "Roofing Solutions", "supplier_contact": "0807-890-1234"},
    
    # Finishes Materials
    {"material_name": "Ceramic Floor Tiles 400x400mm", "required_qty": 385, "unit": "m²", "unit_cost": 6500, "specification": "Non-slip ceramic tiles", "status": "Planned", "supplier_name": "Tile World", "supplier_contact": "0808-901-2345"},
    {"material_name": "Wall Tiles 300x300mm", "required_qty": 185, "unit": "m²", "unit_cost": 5500, "specification": "Glazed ceramic wall tiles", "status": "Planned", "supplier_name": "Tile World", "supplier_contact": "0808-901-2345"},
    {"material_name": "Emulsion Paint", "required_qty": 285, "unit": "litres", "unit_cost": 2850, "specification": "Interior/exterior emulsion paint", "status": "Planned", "supplier_name": "Paint Express", "supplier_contact": "0809-012-3456"},
    {"material_name": "Primer", "required_qty": 125, "unit": "litres", "unit_cost": 3250, "specification": "Alkali resistant primer", "status": "Planned", "supplier_name": "Paint Express", "supplier_contact": "0809-012-3456"},
    
    # Doors and Windows
    {"material_name": "Flush Doors with Frames", "required_qty": 28, "unit": "sets", "unit_cost": 45000, "specification": "Solid core flush doors", "status": "Planned", "supplier_name": "Door & Window Co", "supplier_contact": "0810-123-4567"},
    {"material_name": "Aluminum Windows", "required_qty": 32, "unit": "m²", "unit_cost": 25000, "specification": "Sliding windows with nets", "status": "Planned", "supplier_name": "Door & Window Co", "supplier_contact": "0810-123-4567"},
    {"material_name": "Door Hardware", "required_qty": 32, "unit": "sets", "unit_cost": 5500, "specification": "Complete ironmongery sets", "status": "Planned", "supplier_name": "Hardware Store", "supplier_contact": "0811-234-5678"},
    
    # Electrical Materials
    {"material_name": "Electrical Cables 2.5mm²", "required_qty": 485, "unit": "m", "unit_cost": 450, "specification": "Copper core PVC cables", "status": "Planned", "supplier_name": "Electric Supply", "supplier_contact": "0812-345-6789"},
    {"material_name": "Electrical Cables 4.0mm²", "required_qty": 285, "unit": "m", "unit_cost": 650, "specification": "Copper core PVC cables", "status": "Planned", "supplier_name": "Electric Supply", "supplier_contact": "0812-345-6789"},
    {"material_name": "PVC Conduits 20mm", "required_qty": 385, "unit": "m", "unit_cost": 350, "specification": "Heavy duty PVC conduits", "status": "Planned", "supplier_name": "Electric Supply", "supplier_contact": "0812-345-6789"},
    {"material_name": "Switch Sockets", "required_qty": 85, "unit": "pieces", "unit_cost": 2500, "specification": "13A switched socket outlets", "status": "Planned", "supplier_name": "Electric Supply", "supplier_contact": "0812-345-6789"},
    
    # Plumbing Materials
    {"material_name": "PVC Pipes 100mm (Soil)", "required_qty": 125, "unit": "m", "unit_cost": 1850, "specification": "Heavy duty soil pipes", "status": "Planned", "supplier_name": "Pipe World", "supplier_contact": "0813-456-7890"},
    {"material_name": "PVC Pipes 50mm (Waste)", "required_qty": 185, "unit": "m", "unit_cost": 850, "specification": "Waste water pipes", "status": "Planned", "supplier_name": "Pipe World", "supplier_contact": "0813-456-7890"},
    {"material_name": "Water Closets", "required_qty": 12, "unit": "sets", "unit_cost": 45000, "specification": "Close coupled WC suites", "status": "Planned", "supplier_name": "Sanitary Ware", "supplier_contact": "0814-567-8901"},
    {"material_name": "Wash Hand Basins", "required_qty": 18, "unit": "pieces", "unit_cost": 25000, "specification": "Vitreous china basins", "status": "Planned", "supplier_name": "Sanitary Ware", "supplier_contact": "0814-567-8901"},
]

# Road Material Schedule Templates
ROAD_MATERIAL_TEMPLATES = [
    # Earthworks Materials
    {"material_name": "Laterite (Sub-base Material)", "required_qty": 2880, "unit": "m³", "unit_cost": 6500, "specification": "Compactable laterite meeting CBR requirements", "status": "Planned", "supplier_name": "Quarry Operators", "supplier_contact": "0801-234-5678"},
    {"material_name": "Crushed Stone Base", "required_qty": 3840, "unit": "m³", "unit_cost": 12500, "specification": "Graded crushed stone aggregate", "status": "Planned", "supplier_name": "Stone Crushers Ltd", "supplier_contact": "0802-345-6789"},
    {"material_name": "Selected Fill Material", "required_qty": 3200, "unit": "m³", "unit_cost": 4500, "specification": "Imported fill material for embankments", "status": "Planned", "supplier_name": "Earth Movers", "supplier_contact": "0803-456-7890"},
    
    # Bituminous Materials
    {"material_name": "Bitumen 60/70 Penetration", "required_qty": 185, "unit": "tonnes", "unit_cost": 450000, "specification": "Penetration grade bitumen", "status": "Planned", "supplier_name": "Bitumen Suppliers", "supplier_contact": "0804-567-8901"},
    {"material_name": "Prime Coat Bitumen", "required_qty": 28, "unit": "tonnes", "unit_cost": 485000, "specification": "Cut-back bitumen for priming", "status": "Planned", "supplier_name": "Bitumen Suppliers", "supplier_contact": "0804-567-8901"},
    {"material_name": "Tack Coat Emulsion", "required_qty": 18, "unit": "tonnes", "unit_cost": 520000, "specification": "Cationic bitumen emulsion", "status": "Planned", "supplier_name": "Bitumen Suppliers", "supplier_contact": "0804-567-8901"},
    {"material_name": "Asphalt Aggregate 14mm", "required_qty": 1150, "unit": "tonnes", "unit_cost": 15500, "specification": "Dense graded aggregate for asphalt", "status": "Planned", "supplier_name": "Asphalt Plants", "supplier_contact": "0805-678-9012"},
    {"material_name": "Asphalt Aggregate 6mm", "required_qty": 850, "unit": "tonnes", "unit_cost": 16500, "specification": "Fine aggregate for wearing course", "status": "Planned", "supplier_name": "Asphalt Plants", "supplier_contact": "0805-678-9012"},
    {"material_name": "Mineral Filler", "required_qty": 125, "unit": "tonnes", "unit_cost": 25000, "specification": "Limestone dust for asphalt", "status": "Planned", "supplier_name": "Asphalt Plants", "supplier_contact": "0805-678-9012"},
    
    # Drainage Materials
    {"material_name": "Concrete Culvert Pipes 900mm", "required_qty": 124, "unit": "m", "unit_cost": 12500, "specification": "Reinforced concrete pipes Class 3", "status": "Planned", "supplier_name": "Concrete Products", "supplier_contact": "0806-789-0123"},
    {"material_name": "Precast U-Drains", "required_qty": 850, "unit": "m", "unit_cost": 8500, "specification": "500x500mm precast concrete drains", "status": "Planned", "supplier_name": "Concrete Products", "supplier_contact": "0806-789-0123"},
    {"material_name": "Stone Pitching", "required_qty": 285, "unit": "m³", "unit_cost": 8500, "specification": "Hand-packed stone for drain lining", "status": "Planned", "supplier_name": "Stone Quarry", "supplier_contact": "0807-890-1234"},
    {"material_name": "Geotextile Fabric", "required_qty": 450, "unit": "m²", "unit_cost": 2500, "specification": "Non-woven geotextile for drainage", "status": "Planned", "supplier_name": "Geosynthetics", "supplier_contact": "0808-901-2345"},
    {"material_name": "Drainage Gravel", "required_qty": 185, "unit": "m³", "unit_cost": 12500, "specification": "Clean graded gravel 5-25mm", "status": "Planned", "supplier_name": "Gravel Pits", "supplier_contact": "0809-012-3456"},
    
    # Road Furniture Materials
    {"material_name": "Thermoplastic Road Marking Paint", "required_qty": 485, "unit": "kg", "unit_cost": 1250, "specification": "Hot-applied thermoplastic marking", "status": "Planned", "supplier_name": "Road Marking Co", "supplier_contact": "0810-123-4567"},
    {"material_name": "Glass Beads", "required_qty": 85, "unit": "kg", "unit_cost": 2850, "specification": "Retro-reflective glass beads", "status": "Planned", "supplier_name": "Road Marking Co", "supplier_contact": "0810-123-4567"},
    {"material_name": "Reflective Road Studs", "required_qty": 185, "unit": "pieces", "unit_cost": 2500, "specification": "Cat's eye road studs", "status": "Planned", "supplier_name": "Safety Equipment", "supplier_contact": "0811-234-5678"},
    {"material_name": "Road Signs (Aluminum)", "required_qty": 24, "unit": "pieces", "unit_cost": 45000, "specification": "Reflective road signs with posts", "status": "Planned", "supplier_name": "Signs & Graphics", "supplier_contact": "0812-345-6789"},
    {"material_name": "Guard Rail Beams", "required_qty": 380, "unit": "m", "unit_cost": 8500, "specification": "Galvanized steel guard rails", "status": "Planned", "supplier_name": "Safety Barriers", "supplier_contact": "0813-456-7890"},
    {"material_name": "Guard Rail Posts", "required_qty": 76, "unit": "pieces", "unit_cost": 12500, "specification": "Steel posts for guard rails", "status": "Planned", "supplier_name": "Safety Barriers", "supplier_contact": "0813-456-7890"},
    
    # Street Lighting Materials
    {"material_name": "Street Light Poles", "required_qty": 48, "unit": "pieces", "unit_cost": 185000, "specification": "10m galvanized steel poles", "status": "Planned", "supplier_name": "Lighting Solutions", "supplier_contact": "0814-567-8901"},
    {"material_name": "LED Street Light Fittings", "required_qty": 48, "unit": "pieces", "unit_cost": 85000, "specification": "150W LED luminaires", "status": "Planned", "supplier_name": "Lighting Solutions", "supplier_contact": "0814-567-8901"},
    {"material_name": "Electrical Cables (Street Lighting)", "required_qty": 2400, "unit": "m", "unit_cost": 850, "specification": "Armored cables for street lighting", "status": "Planned", "supplier_name": "Electric Supply", "supplier_contact": "0815-678-9012"},
]

# Culvert Material Schedule Templates
CULVERT_MATERIAL_TEMPLATES = [
    # Concrete Materials
    {"material_name": "Ordinary Portland Cement (42.5N)", "required_qty": 125, "unit": "bags", "unit_cost": 3500, "specification": "High grade cement for culvert construction", "status": "Planned", "supplier_name": "Dangote Cement", "supplier_contact": "0801-234-5678"},
    {"material_name": "Sharp Sand", "required_qty": 45, "unit": "m³", "unit_cost": 8000, "specification": "Clean washed sand for concrete", "status": "Planned", "supplier_name": "River Sand Ltd", "supplier_contact": "0802-345-6789"},
    {"material_name": "Granite Chippings 20mm", "required_qty": 35, "unit": "m³", "unit_cost": 12000, "specification": "Crushed granite for concrete", "status": "Planned", "supplier_name": "Granite Quarry Co", "supplier_contact": "0803-456-7890"},
    {"material_name": "Granite Dust", "required_qty": 18, "unit": "m³", "unit_cost": 8500, "specification": "Stone dust for leveling and blinding", "status": "Planned", "supplier_name": "Granite Quarry Co", "supplier_contact": "0803-456-7890"},
    
    # Steel Reinforcement
    {"material_name": "High Tensile Steel Bars 12mm", "required_qty": 485, "unit": "kg", "unit_cost": 180, "specification": "Grade 60 deformed bars", "status": "Planned", "supplier_name": "Steel Masters Ltd", "supplier_contact": "0804-567-8901"},
    {"material_name": "High Tensile Steel Bars 16mm", "required_qty": 685, "unit": "kg", "unit_cost": 175, "specification": "Grade 60 deformed bars", "status": "Planned", "supplier_name": "Steel Masters Ltd", "supplier_contact": "0804-567-8901"},
    {"material_name": "High Tensile Steel Bars 20mm", "required_qty": 485, "unit": "kg", "unit_cost": 170, "specification": "Grade 60 deformed bars", "status": "Planned", "supplier_name": "Steel Masters Ltd", "supplier_contact": "0804-567-8901"},
    {"material_name": "High Tensile Steel Bars 25mm", "required_qty": 285, "unit": "kg", "unit_cost": 165, "specification": "Grade 60 deformed bars", "status": "Planned", "supplier_name": "Steel Masters Ltd", "supplier_contact": "0804-567-8901"},
    {"material_name": "Binding Wire", "required_qty": 28, "unit": "kg", "unit_cost": 450, "specification": "16 gauge galvanized wire", "status": "Planned", "supplier_name": "Wire Products", "supplier_contact": "0805-678-9012"},
    
    # Formwork Materials
    {"material_name": "Marine Plywood 15mm", "required_qty": 45, "unit": "sheets", "unit_cost": 12500, "specification": "Waterproof formwork plywood", "status": "Planned", "supplier_name": "Timber Merchants", "supplier_contact": "0806-789-0123"},
    {"material_name": "Timber 50x100mm", "required_qty": 185, "unit": "m", "unit_cost": 1850, "specification": "Sawn hardwood for formwork", "status": "Planned", "supplier_name": "Timber Merchants", "supplier_contact": "0806-789-0123"},
    {"material_name": "Form Ties and Bolts", "required_qty": 125, "unit": "sets", "unit_cost": 850, "specification": "Steel ties for formwork", "status": "Planned", "supplier_name": "Hardware Store", "supplier_contact": "0807-890-1234"},
    
    # Waterproofing Materials
    {"material_name": "Waterproofing Membrane", "required_qty": 125, "unit": "m²", "unit_cost": 4500, "specification": "Modified bitumen membrane", "status": "Planned", "supplier_name": "Waterproof Solutions", "supplier_contact": "0808-901-2345"},
    {"material_name": "Bitumen Primer", "required_qty": 45, "unit": "litres", "unit_cost": 1850, "specification": "Primer for waterproofing", "status": "Planned", "supplier_name": "Waterproof Solutions", "supplier_contact": "0808-901-2345"},
    {"material_name": "PVC Water Stops", "required_qty": 28, "unit": "m", "unit_cost": 2850, "specification": "Expansion joint water stops", "status": "Planned", "supplier_name": "Sealant Specialists", "supplier_contact": "0809-012-3456"},
    {"material_name": "Joint Sealant", "required_qty": 12, "unit": "cartridges", "unit_cost": 2500, "specification": "Polyurethane joint sealant", "status": "Planned", "supplier_name": "Sealant Specialists", "supplier_contact": "0809-012-3456"},
    
    # Backfill and Drainage Materials
    {"material_name": "Selected Backfill Material", "required_qty": 125, "unit": "m³", "unit_cost": 4500, "specification": "Granular material for backfilling", "status": "Planned", "supplier_name": "Quarry Operators", "supplier_contact": "0810-123-4567"},
    {"material_name": "Filter Sand", "required_qty": 28, "unit": "m³", "unit_cost": 8500, "specification": "Graded sand for drainage", "status": "Planned", "supplier_name": "Sand Suppliers", "supplier_contact": "0811-234-5678"},
    {"material_name": "Drainage Gravel", "required_qty": 18, "unit": "m³", "unit_cost": 12500, "specification": "Clean drainage aggregate", "status": "Planned", "supplier_name": "Gravel Pits", "supplier_contact": "0812-345-6789"},
    {"material_name": "Perforated Pipes 100mm", "required_qty": 85, "unit": "m", "unit_cost": 1850, "specification": "Drainage pipes with slots", "status": "Planned", "supplier_name": "Pipe World", "supplier_contact": "0813-456-7890"},
    
    # Protection Works Materials
    {"material_name": "Stone Pitching", "required_qty": 45, "unit": "m³", "unit_cost": 6500, "specification": "Hand-packed stone protection", "status": "Planned", "supplier_name": "Stone Quarry", "supplier_contact": "0814-567-8901"},
    {"material_name": "Gabion Baskets", "required_qty": 24, "unit": "m³", "unit_cost": 12500, "specification": "Wire mesh gabion baskets", "status": "Planned", "supplier_name": "Gabion Systems", "supplier_contact": "0815-678-9012"},
    {"material_name": "Gabion Fill Stone", "required_qty": 36, "unit": "m³", "unit_cost": 8500, "specification": "Graded stone for gabion filling", "status": "Planned", "supplier_name": "Stone Quarry", "supplier_contact": "0814-567-8901"},
    {"material_name": "Geotextile (Under Gabions)", "required_qty": 85, "unit": "m²", "unit_cost": 2500, "specification": "Non-woven geotextile fabric", "status": "Planned", "supplier_name": "Geosynthetics", "supplier_contact": "0816-789-0123"},
]

def create_comprehensive_material_templates():
    """Create comprehensive Material Schedule templates in the database"""
    app = create_app()
    
    with app.app_context():
        # Delete existing material schedule templates (if any)
        existing_materials = MaterialSchedule.query.filter_by(project_id=None).all()
        for material in existing_materials:
            db.session.delete(material)
        
        print(f"Deleted {len(existing_materials)} existing material templates")
        
        # Create Bridge material templates
        bridge_count = 0
        for material_data in BRIDGE_MATERIAL_TEMPLATES:
            material_data["total_cost"] = material_data["required_qty"] * material_data["unit_cost"]
            material_data["project_id"] = None  # Template materials have no project_id
            
            material = MaterialSchedule(**material_data)
            db.session.add(material)
            bridge_count += 1
        
        # Create Building material templates
        building_count = 0
        for material_data in BUILDING_MATERIAL_TEMPLATES:
            material_data["total_cost"] = material_data["required_qty"] * material_data["unit_cost"]
            material_data["project_id"] = None  # Template materials have no project_id
            
            material = MaterialSchedule(**material_data)
            db.session.add(material)
            building_count += 1
        
        # Create Road material templates
        road_count = 0
        for material_data in ROAD_MATERIAL_TEMPLATES:
            material_data["total_cost"] = material_data["required_qty"] * material_data["unit_cost"]
            material_data["project_id"] = None  # Template materials have no project_id
            
            material = MaterialSchedule(**material_data)
            db.session.add(material)
            road_count += 1
        
        # Create Culvert material templates
        culvert_count = 0
        for material_data in CULVERT_MATERIAL_TEMPLATES:
            material_data["total_cost"] = material_data["required_qty"] * material_data["unit_cost"]
            material_data["project_id"] = None  # Template materials have no project_id
            
            material = MaterialSchedule(**material_data)
            db.session.add(material)
            culvert_count += 1
        
        db.session.commit()
        
        print(f"\nCreated comprehensive material templates:")
        print(f"- Bridge materials: {bridge_count}")
        print(f"- Building materials: {building_count}")
        print(f"- Road materials: {road_count}")
        print(f"- Culvert materials: {culvert_count}")
        print(f"Total material templates: {bridge_count + building_count + road_count + culvert_count}")
        
        # Display sample costs
        print(f"\nSample total material costs per project type:")
        bridge_total = sum(t["total_cost"] for t in BRIDGE_MATERIAL_TEMPLATES)
        building_total = sum(t["total_cost"] for t in BUILDING_MATERIAL_TEMPLATES)
        road_total = sum(t["total_cost"] for t in ROAD_MATERIAL_TEMPLATES)
        culvert_total = sum(t["total_cost"] for t in CULVERT_MATERIAL_TEMPLATES)
        
        print(f"- Bridge materials: ₦{bridge_total:,.2f}")
        print(f"- Building materials: ₦{building_total:,.2f}")
        print(f"- Road materials: ₦{road_total:,.2f}")
        print(f"- Culvert materials: ₦{culvert_total:,.2f}")

if __name__ == "__main__":
    create_comprehensive_material_templates()