#!/usr/bin/env python3
"""
Comprehensive BOQ Template Generator for Construction Projects
Creates detailed, realistic BOQ templates based on actual construction business logic
"""

from app import create_app
from extensions import db
from models import BOQItem

# Comprehensive Bridge Construction BOQ
BRIDGE_BOQ_TEMPLATES = [
    # BILL NO. 1: SITE PREPARATION & EARTHWORKS
    {"bill_no": "BILL NO. 1", "item_no": "1.01", "item_description": "Site clearance including removal of vegetation, debris and topsoil", "quantity": 1, "unit": "Ha", "unit_price": 450000, "category": "Site Preparation"},
    {"bill_no": "BILL NO. 1", "item_no": "1.02", "item_description": "Setting out and survey including permanent benchmarks", "quantity": 1, "unit": "Item", "unit_price": 250000, "category": "Site Preparation"},
    {"bill_no": "BILL NO. 1", "item_no": "1.03", "item_description": "Excavation for foundations in soft material", "quantity": 150, "unit": "m³", "unit_price": 3500, "category": "Earthworks"},
    {"bill_no": "BILL NO. 1", "item_no": "1.04", "item_description": "Excavation for foundations in hard material/rock", "quantity": 80, "unit": "m³", "unit_price": 8500, "category": "Earthworks"},
    {"bill_no": "BILL NO. 1", "item_no": "1.05", "item_description": "Disposal of excavated material off-site", "quantity": 180, "unit": "m³", "unit_price": 2500, "category": "Earthworks"},
    {"bill_no": "BILL NO. 1", "item_no": "1.06", "item_description": "Imported filling material (sand/laterite) compacted in layers", "quantity": 200, "unit": "m³", "unit_price": 4500, "category": "Earthworks"},
    
    # BILL NO. 2: CONCRETE WORKS - SUBSTRUCTURE
    {"bill_no": "BILL NO. 2", "item_no": "2.01", "item_description": "Mass concrete grade 15 for leveling", "quantity": 25, "unit": "m³", "unit_price": 85000, "category": "Substructure"},
    {"bill_no": "BILL NO. 2", "item_no": "2.02", "item_description": "Reinforced concrete grade 25 for pile caps", "quantity": 45, "unit": "m³", "unit_price": 120000, "category": "Substructure"},
    {"bill_no": "BILL NO. 2", "item_no": "2.03", "item_description": "Reinforced concrete grade 30 for abutments", "quantity": 85, "unit": "m³", "unit_price": 135000, "category": "Substructure"},
    {"bill_no": "BILL NO. 2", "item_no": "2.04", "item_description": "Reinforced concrete grade 30 for piers/columns", "quantity": 65, "unit": "m³", "unit_price": 135000, "category": "Substructure"},
    {"bill_no": "BILL NO. 2", "item_no": "2.05", "item_description": "High tensile steel reinforcement bars 12mm-32mm", "quantity": 8500, "unit": "kg", "unit_price": 180, "category": "Reinforcement"},
    {"bill_no": "BILL NO. 2", "item_no": "2.06", "item_description": "Formwork for vertical surfaces (abutments/piers)", "quantity": 180, "unit": "m²", "unit_price": 8500, "category": "Formwork"},
    {"bill_no": "BILL NO. 2", "item_no": "2.07", "item_description": "Waterproofing membrane for substructure", "quantity": 85, "unit": "m²", "unit_price": 4500, "category": "Waterproofing"},
    
    # BILL NO. 3: SUPERSTRUCTURE
    {"bill_no": "BILL NO. 3", "item_no": "3.01", "item_description": "Prestressed concrete bridge beams including tendons", "quantity": 12, "unit": "No", "unit_price": 850000, "category": "Superstructure"},
    {"bill_no": "BILL NO. 3", "item_no": "3.02", "item_description": "Reinforced concrete bridge deck slab grade 30", "quantity": 45, "unit": "m³", "unit_price": 145000, "category": "Superstructure"},
    {"bill_no": "BILL NO. 3", "item_no": "3.03", "item_description": "Bridge bearing pads (elastomeric)", "quantity": 24, "unit": "No", "unit_price": 75000, "category": "Bearings"},
    {"bill_no": "BILL NO. 3", "item_no": "3.04", "item_description": "Expansion joints for bridge deck", "quantity": 2, "unit": "No", "unit_price": 180000, "category": "Joints"},
    {"bill_no": "BILL NO. 3", "item_no": "3.05", "item_description": "Bridge railings/parapets including posts", "quantity": 85, "unit": "m", "unit_price": 12500, "category": "Safety Features"},
    
    # BILL NO. 4: DRAINAGE & WATERPROOFING
    {"bill_no": "BILL NO. 4", "item_no": "4.01", "item_description": "Bridge deck waterproofing system", "quantity": 280, "unit": "m²", "unit_price": 6500, "category": "Waterproofing"},
    {"bill_no": "BILL NO. 4", "item_no": "4.02", "item_description": "Drainage spouts and downpipes", "quantity": 8, "unit": "No", "unit_price": 45000, "category": "Drainage"},
    {"bill_no": "BILL NO. 4", "item_no": "4.03", "item_description": "French drains around abutments", "quantity": 65, "unit": "m", "unit_price": 8500, "category": "Drainage"},
    {"bill_no": "BILL NO. 4", "item_no": "4.04", "item_description": "Weep holes in retaining walls", "quantity": 24, "unit": "No", "unit_price": 2500, "category": "Drainage"},
    
    # BILL NO. 5: APPROACH WORKS & SURFACING
    {"bill_no": "BILL NO. 5", "item_no": "5.01", "item_description": "Approach slab construction", "quantity": 35, "unit": "m²", "unit_price": 25000, "category": "Approaches"},
    {"bill_no": "BILL NO. 5", "item_no": "5.02", "item_description": "Asphaltic concrete wearing course 50mm thick", "quantity": 320, "unit": "m²", "unit_price": 8500, "category": "Surfacing"},
    {"bill_no": "BILL NO. 5", "item_no": "5.03", "item_description": "Protective works and erosion control", "quantity": 150, "unit": "m²", "unit_price": 4500, "category": "Protection"},
    {"bill_no": "BILL NO. 5", "item_no": "5.04", "item_description": "Road markings and signage", "quantity": 1, "unit": "Item", "unit_price": 120000, "category": "Road Furniture"},
]

# Comprehensive Building Construction BOQ
BUILDING_BOQ_TEMPLATES = [
    # BILL NO. 1: PRELIMINARIES & EARTHWORKS
    {"bill_no": "BILL NO. 1", "item_no": "1.01", "item_description": "Site clearance and demolition of existing structures", "quantity": 1, "unit": "Item", "unit_price": 350000, "category": "Preliminaries"},
    {"bill_no": "BILL NO. 1", "item_no": "1.02", "item_description": "Setting out building including grid lines", "quantity": 1, "unit": "Item", "unit_price": 180000, "category": "Setting Out"},
    {"bill_no": "BILL NO. 1", "item_no": "1.03", "item_description": "Excavation for foundations maximum depth 2m", "quantity": 180, "unit": "m³", "unit_price": 2800, "category": "Earthworks"},
    {"bill_no": "BILL NO. 1", "item_no": "1.04", "item_description": "Hardcore bed and compaction", "quantity": 85, "unit": "m³", "unit_price": 6500, "category": "Sub-base"},
    {"bill_no": "BILL NO. 1", "item_no": "1.05", "item_description": "Sand blinding to hardcore", "quantity": 12, "unit": "m³", "unit_price": 8500, "category": "Sub-base"},
    
    # BILL NO. 2: CONCRETE WORKS & FOUNDATIONS
    {"bill_no": "BILL NO. 2", "item_no": "2.01", "item_description": "Mass concrete grade 15 for foundation beds", "quantity": 35, "unit": "m³", "unit_price": 75000, "category": "Foundations"},
    {"bill_no": "BILL NO. 2", "item_no": "2.02", "item_description": "Reinforced concrete grade 25 strip foundations", "quantity": 45, "unit": "m³", "unit_price": 115000, "category": "Foundations"},
    {"bill_no": "BILL NO. 2", "item_no": "2.03", "item_description": "Reinforced concrete grade 25 ground floor slab", "quantity": 120, "unit": "m³", "unit_price": 118000, "category": "Floor Slabs"},
    {"bill_no": "BILL NO. 2", "item_no": "2.04", "item_description": "Reinforced concrete grade 30 columns", "quantity": 28, "unit": "m³", "unit_price": 135000, "category": "Structural Frame"},
    {"bill_no": "BILL NO. 2", "item_no": "2.05", "item_description": "Reinforced concrete grade 30 beams", "quantity": 42, "unit": "m³", "unit_price": 142000, "category": "Structural Frame"},
    {"bill_no": "BILL NO. 2", "item_no": "2.06", "item_description": "Reinforced concrete grade 25 suspended slabs", "quantity": 185, "unit": "m³", "unit_price": 125000, "category": "Floor Slabs"},
    {"bill_no": "BILL NO. 2", "item_no": "2.07", "item_description": "High tensile steel reinforcement 10mm-25mm", "quantity": 12500, "unit": "kg", "unit_price": 175, "category": "Reinforcement"},
    {"bill_no": "BILL NO. 2", "item_no": "2.08", "item_description": "Formwork to concrete elements", "quantity": 850, "unit": "m²", "unit_price": 6500, "category": "Formwork"},
    
    # BILL NO. 3: MASONRY & WALLING
    {"bill_no": "BILL NO. 3", "item_no": "3.01", "item_description": "Sandcrete block walls 150mm thick", "quantity": 485, "unit": "m²", "unit_price": 8500, "category": "Walling"},
    {"bill_no": "BILL NO. 3", "item_no": "3.02", "item_description": "Sandcrete block walls 100mm thick (partitions)", "quantity": 280, "unit": "m²", "unit_price": 6500, "category": "Partitions"},
    {"bill_no": "BILL NO. 3", "item_no": "3.03", "item_description": "Lintels over openings", "quantity": 45, "unit": "m", "unit_price": 12500, "category": "Structural Elements"},
    {"bill_no": "BILL NO. 3", "item_no": "3.04", "item_description": "Damp proof course 150mm wide", "quantity": 180, "unit": "m", "unit_price": 2500, "category": "Damp Proofing"},
    
    # BILL NO. 4: ROOFING WORKS
    {"bill_no": "BILL NO. 4", "item_no": "4.01", "item_description": "Steel roof trusses fabricated and erected", "quantity": 24, "unit": "No", "unit_price": 85000, "category": "Roof Structure"},
    {"bill_no": "BILL NO. 4", "item_no": "4.02", "item_description": "Steel purlins 100x50mm", "quantity": 185, "unit": "m", "unit_price": 3500, "category": "Roof Structure"},
    {"bill_no": "BILL NO. 4", "item_no": "4.03", "item_description": "Long span aluminum roofing sheets 0.55mm", "quantity": 485, "unit": "m²", "unit_price": 4500, "category": "Roof Covering"},
    {"bill_no": "BILL NO. 4", "item_no": "4.04", "item_description": "PVC gutters and downpipes", "quantity": 125, "unit": "m", "unit_price": 3500, "category": "Roof Drainage"},
    {"bill_no": "BILL NO. 4", "item_no": "4.05", "item_description": "Ridge and hip cappings", "quantity": 85, "unit": "m", "unit_price": 2500, "category": "Roof Accessories"},
    
    # BILL NO. 5: FINISHES
    {"bill_no": "BILL NO. 5", "item_no": "5.01", "item_description": "Internal wall plastering and screeding", "quantity": 1250, "unit": "m²", "unit_price": 2500, "category": "Wall Finishes"},
    {"bill_no": "BILL NO. 5", "item_no": "5.02", "item_description": "External wall plastering", "quantity": 680, "unit": "m²", "unit_price": 2800, "category": "Wall Finishes"},
    {"bill_no": "BILL NO. 5", "item_no": "5.03", "item_description": "Emulsion paint to walls (3 coats)", "quantity": 1850, "unit": "m²", "unit_price": 1500, "category": "Painting"},
    {"bill_no": "BILL NO. 5", "item_no": "5.04", "item_description": "Ceramic floor tiles 400x400mm", "quantity": 385, "unit": "m²", "unit_price": 6500, "category": "Floor Finishes"},
    {"bill_no": "BILL NO. 5", "item_no": "5.05", "item_description": "Suspended ceiling with mineral fiber tiles", "quantity": 285, "unit": "m²", "unit_price": 8500, "category": "Ceiling"},
    
    # BILL NO. 6: DOORS & WINDOWS
    {"bill_no": "BILL NO. 6", "item_no": "6.01", "item_description": "Solid core flush doors with frames", "quantity": 28, "unit": "No", "unit_price": 45000, "category": "Doors"},
    {"bill_no": "BILL NO. 6", "item_no": "6.02", "item_description": "Aluminum sliding windows with mosquito net", "quantity": 32, "unit": "m²", "unit_price": 25000, "category": "Windows"},
    {"bill_no": "BILL NO. 6", "item_no": "6.03", "item_description": "Security doors (steel)", "quantity": 4, "unit": "No", "unit_price": 85000, "category": "Security"},
    {"bill_no": "BILL NO. 6", "item_no": "6.04", "item_description": "Door and window hardware/ironmongery", "quantity": 1, "unit": "Item", "unit_price": 180000, "category": "Hardware"},
    
    # BILL NO. 7: SERVICES
    {"bill_no": "BILL NO. 7", "item_no": "7.01", "item_description": "Electrical installation complete with fittings", "quantity": 1, "unit": "Item", "unit_price": 850000, "category": "Electrical"},
    {"bill_no": "BILL NO. 7", "item_no": "7.02", "item_description": "Plumbing installation complete with fixtures", "quantity": 1, "unit": "Item", "unit_price": 650000, "category": "Plumbing"},
    {"bill_no": "BILL NO. 7", "item_no": "7.03", "item_description": "Septic tank and soak-away construction", "quantity": 1, "unit": "Item", "unit_price": 280000, "category": "Drainage"},
    {"bill_no": "BILL NO. 7", "item_no": "7.04", "item_description": "Fire detection and safety systems", "quantity": 1, "unit": "Item", "unit_price": 450000, "category": "Safety"},
]

# Comprehensive Road Construction BOQ
ROAD_BOQ_TEMPLATES = [
    # BILL NO. 1: EARTHWORKS & SITE PREPARATION
    {"bill_no": "BILL NO. 1", "item_no": "1.01", "item_description": "Clearing and grubbing including removal of trees", "quantity": 2.5, "unit": "Ha", "unit_price": 380000, "category": "Site Preparation"},
    {"bill_no": "BILL NO. 1", "item_no": "1.02", "item_description": "Strip and stockpile topsoil for reuse", "quantity": 1850, "unit": "m³", "unit_price": 2500, "category": "Earthworks"},
    {"bill_no": "BILL NO. 1", "item_no": "1.03", "item_description": "Excavation of unsuitable material", "quantity": 2450, "unit": "m³", "unit_price": 2800, "category": "Earthworks"},
    {"bill_no": "BILL NO. 1", "item_no": "1.04", "item_description": "Embankment construction with imported material", "quantity": 3200, "unit": "m³", "unit_price": 4500, "category": "Earthworks"},
    {"bill_no": "BILL NO. 1", "item_no": "1.05", "item_description": "Formation preparation and proof rolling", "quantity": 4.8, "unit": "km", "unit_price": 185000, "category": "Formation"},
    
    # BILL NO. 2: SUB-BASE & BASE COURSE
    {"bill_no": "BILL NO. 2", "item_no": "2.01", "item_description": "Laterite sub-base 150mm thick compacted", "quantity": 2880, "unit": "m³", "unit_price": 6500, "category": "Sub-base"},
    {"bill_no": "BILL NO. 2", "item_no": "2.02", "item_description": "Crushed stone base course 200mm thick", "quantity": 3840, "unit": "m³", "unit_price": 12500, "category": "Base Course"},
    {"bill_no": "BILL NO. 2", "item_no": "2.03", "item_description": "Prime coat application", "quantity": 19200, "unit": "m²", "unit_price": 450, "category": "Priming"},
    {"bill_no": "BILL NO. 2", "item_no": "2.04", "item_description": "Tack coat application", "quantity": 19200, "unit": "m²", "unit_price": 350, "category": "Tack Coat"},
    
    # BILL NO. 3: BITUMINOUS WORKS
    {"bill_no": "BILL NO. 3", "item_no": "3.01", "item_description": "Asphaltic concrete binder course 60mm thick", "quantity": 1152, "unit": "m³", "unit_price": 85000, "category": "Binder Course"},
    {"bill_no": "BILL NO. 3", "item_no": "3.02", "item_description": "Asphaltic concrete wearing course 40mm thick", "quantity": 768, "unit": "m³", "unit_price": 95000, "category": "Wearing Course"},
    {"bill_no": "BILL NO. 3", "item_no": "3.03", "item_description": "Stone mastic asphalt for heavy traffic areas", "quantity": 185, "unit": "m³", "unit_price": 125000, "category": "Heavy Duty Surfacing"},
    
    # BILL NO. 4: DRAINAGE WORKS
    {"bill_no": "BILL NO. 4", "item_no": "4.01", "item_description": "Excavation for side drains", "quantity": 1850, "unit": "m³", "unit_price": 2500, "category": "Drainage"},
    {"bill_no": "BILL NO. 4", "item_no": "4.02", "item_description": "Stone pitching to drains", "quantity": 1240, "unit": "m²", "unit_price": 4500, "category": "Drainage Protection"},
    {"bill_no": "BILL NO. 4", "item_no": "4.03", "item_description": "Precast concrete U-drains", "quantity": 850, "unit": "m", "unit_price": 8500, "category": "Drainage"},
    {"bill_no": "BILL NO. 4", "item_no": "4.04", "item_description": "Culvert pipes 900mm diameter", "quantity": 124, "unit": "m", "unit_price": 12500, "category": "Cross Drainage"},
    {"bill_no": "BILL NO. 4", "item_no": "4.05", "item_description": "Culvert headwalls and wingwalls", "quantity": 12, "unit": "No", "unit_price": 185000, "category": "Culvert Works"},
    {"bill_no": "BILL NO. 4", "item_no": "4.06", "item_description": "French drains with geotextile", "quantity": 450, "unit": "m", "unit_price": 6500, "category": "Sub-surface Drainage"},
    
    # BILL NO. 5: ROAD FURNITURE & SAFETY
    {"bill_no": "BILL NO. 5", "item_no": "5.01", "item_description": "Thermoplastic road markings", "quantity": 2450, "unit": "m", "unit_price": 1250, "category": "Road Markings"},
    {"bill_no": "BILL NO. 5", "item_no": "5.02", "item_description": "Reflective road studs", "quantity": 185, "unit": "No", "unit_price": 2500, "category": "Road Markings"},
    {"bill_no": "BILL NO. 5", "item_no": "5.03", "item_description": "Road signs (regulatory and warning)", "quantity": 24, "unit": "No", "unit_price": 45000, "category": "Road Signs"},
    {"bill_no": "BILL NO. 5", "item_no": "5.04", "item_description": "Guard rails/crash barriers", "quantity": 380, "unit": "m", "unit_price": 8500, "category": "Safety Barriers"},
    {"bill_no": "BILL NO. 5", "item_no": "5.05", "item_description": "Street lighting poles and fittings", "quantity": 48, "unit": "No", "unit_price": 185000, "category": "Lighting"},
    {"bill_no": "BILL NO. 5", "item_no": "5.06", "item_description": "Bus stops/lay-bys construction", "quantity": 6, "unit": "No", "unit_price": 285000, "category": "Bus Facilities"},
    
    # BILL NO. 6: LANDSCAPING & RESTORATION
    {"bill_no": "BILL NO. 6", "item_no": "6.01", "item_description": "Topsoil replacement and grassing", "quantity": 1.2, "unit": "Ha", "unit_price": 285000, "category": "Landscaping"},
    {"bill_no": "BILL NO. 6", "item_no": "6.02", "item_description": "Tree planting and landscape restoration", "quantity": 125, "unit": "No", "unit_price": 8500, "category": "Environmental"},
    {"bill_no": "BILL NO. 6", "item_no": "6.03", "item_description": "Erosion control measures", "quantity": 850, "unit": "m²", "unit_price": 3500, "category": "Environmental Protection"},
]

# Comprehensive Culvert Construction BOQ
CULVERT_BOQ_TEMPLATES = [
    # BILL NO. 1: EXCAVATION & EARTHWORKS
    {"bill_no": "BILL NO. 1", "item_no": "1.01", "item_description": "Site clearance and setting out", "quantity": 1, "unit": "Item", "unit_price": 125000, "category": "Preliminaries"},
    {"bill_no": "BILL NO. 1", "item_no": "1.02", "item_description": "Excavation for culvert in ordinary soil", "quantity": 85, "unit": "m³", "unit_price": 2800, "category": "Earthworks"},
    {"bill_no": "BILL NO. 1", "item_no": "1.03", "item_description": "Excavation in rock/hard material", "quantity": 25, "unit": "m³", "unit_price": 8500, "category": "Earthworks"},
    {"bill_no": "BILL NO. 1", "item_no": "1.04", "item_description": "Dewatering and pumping", "quantity": 1, "unit": "Item", "unit_price": 185000, "category": "Temporary Works"},
    {"bill_no": "BILL NO. 1", "item_no": "1.05", "item_description": "Disposal of excavated material", "quantity": 95, "unit": "m³", "unit_price": 2500, "category": "Material Disposal"},
    
    # BILL NO. 2: CONCRETE WORKS
    {"bill_no": "BILL NO. 2", "item_no": "2.01", "item_description": "Mass concrete grade 15 for leveling", "quantity": 8, "unit": "m³", "unit_price": 75000, "category": "Foundation"},
    {"bill_no": "BILL NO. 2", "item_no": "2.02", "item_description": "Reinforced concrete grade 25 for base slab", "quantity": 18, "unit": "m³", "unit_price": 115000, "category": "Base Slab"},
    {"bill_no": "BILL NO. 2", "item_no": "2.03", "item_description": "Reinforced concrete grade 30 for walls", "quantity": 32, "unit": "m³", "unit_price": 135000, "category": "Walls"},
    {"bill_no": "BILL NO. 2", "item_no": "2.04", "item_description": "Reinforced concrete grade 25 for top slab", "quantity": 16, "unit": "m³", "unit_price": 125000, "category": "Top Slab"},
    {"bill_no": "BILL NO. 2", "item_no": "2.05", "item_description": "High tensile steel reinforcement", "quantity": 1850, "unit": "kg", "unit_price": 180, "category": "Reinforcement"},
    {"bill_no": "BILL NO. 2", "item_no": "2.06", "item_description": "Formwork to concrete surfaces", "quantity": 185, "unit": "m²", "unit_price": 6500, "category": "Formwork"},
    
    # BILL NO. 3: WATERPROOFING & JOINTS
    {"bill_no": "BILL NO. 3", "item_no": "3.01", "item_description": "Waterproofing membrane to walls", "quantity": 125, "unit": "m²", "unit_price": 4500, "category": "Waterproofing"},
    {"bill_no": "BILL NO. 3", "item_no": "3.02", "item_description": "Expansion joints with water stops", "quantity": 4, "unit": "No", "unit_price": 25000, "category": "Joints"},
    {"bill_no": "BILL NO. 3", "item_no": "3.03", "item_description": "Construction joints treatment", "quantity": 85, "unit": "m", "unit_price": 3500, "category": "Joints"},
    
    # BILL NO. 4: BACKFILLING & APPROACHES
    {"bill_no": "BILL NO. 4", "item_no": "4.01", "item_description": "Selected backfill material compacted", "quantity": 125, "unit": "m³", "unit_price": 4500, "category": "Backfilling"},
    {"bill_no": "BILL NO. 4", "item_no": "4.02", "item_description": "Filter material around culvert", "quantity": 28, "unit": "m³", "unit_price": 8500, "category": "Drainage"},
    {"bill_no": "BILL NO. 4", "item_no": "4.03", "item_description": "Approach slabs construction", "quantity": 24, "unit": "m²", "unit_price": 18500, "category": "Approaches"},
    {"bill_no": "BILL NO. 4", "item_no": "4.04", "item_description": "Wing walls and headwalls", "quantity": 4, "unit": "No", "unit_price": 125000, "category": "Retaining Structures"},
    
    # BILL NO. 5: PROTECTION WORKS
    {"bill_no": "BILL NO. 5", "item_no": "5.01", "item_description": "Inlet and outlet protection (stone pitching)", "quantity": 45, "unit": "m²", "unit_price": 6500, "category": "Erosion Protection"},
    {"bill_no": "BILL NO. 5", "item_no": "5.02", "item_description": "Energy dissipators at outlet", "quantity": 1, "unit": "Item", "unit_price": 85000, "category": "Energy Dissipation"},
    {"bill_no": "BILL NO. 5", "item_no": "5.03", "item_description": "Gabion baskets for protection", "quantity": 24, "unit": "m³", "unit_price": 12500, "category": "Flexible Protection"},
    {"bill_no": "BILL NO. 5", "item_no": "5.04", "item_description": "Geotextile fabric under protection", "quantity": 85, "unit": "m²", "unit_price": 2500, "category": "Geotextiles"},
]

def create_comprehensive_templates():
    """Create comprehensive BOQ templates in the database"""
    app = create_app()
    
    with app.app_context():
        # Delete existing templates
        existing_templates = BOQItem.query.filter_by(is_template=True).all()
        for template in existing_templates:
            db.session.delete(template)
        
        print(f"Deleted {len(existing_templates)} existing templates")
        
        # Create Bridge templates
        bridge_count = 0
        for template_data in BRIDGE_BOQ_TEMPLATES:
            template_data["total_cost"] = template_data["quantity"] * template_data["unit_price"]
            template_data["item_type"] = "Bridge"
            template_data["is_template"] = True
            template_data["status"] = "Template"
            
            template = BOQItem(**template_data)
            db.session.add(template)
            bridge_count += 1
        
        # Create Building templates
        building_count = 0
        for template_data in BUILDING_BOQ_TEMPLATES:
            template_data["total_cost"] = template_data["quantity"] * template_data["unit_price"]
            template_data["item_type"] = "Building"
            template_data["is_template"] = True
            template_data["status"] = "Template"
            
            template = BOQItem(**template_data)
            db.session.add(template)
            building_count += 1
        
        # Create Road templates
        road_count = 0
        for template_data in ROAD_BOQ_TEMPLATES:
            template_data["total_cost"] = template_data["quantity"] * template_data["unit_price"]
            template_data["item_type"] = "Road"
            template_data["is_template"] = True
            template_data["status"] = "Template"
            
            template = BOQItem(**template_data)
            db.session.add(template)
            road_count += 1
        
        # Create Culvert templates
        culvert_count = 0
        for template_data in CULVERT_BOQ_TEMPLATES:
            template_data["total_cost"] = template_data["quantity"] * template_data["unit_price"]
            template_data["item_type"] = "Culvert"
            template_data["is_template"] = True
            template_data["status"] = "Template"
            
            template = BOQItem(**template_data)
            db.session.add(template)
            culvert_count += 1
        
        db.session.commit()
        
        print(f"\nCreated comprehensive templates:")
        print(f"- Bridge templates: {bridge_count}")
        print(f"- Building templates: {building_count}")
        print(f"- Road templates: {road_count}")
        print(f"- Culvert templates: {culvert_count}")
        print(f"Total templates: {bridge_count + building_count + road_count + culvert_count}")
        
        # Display sample costs
        print(f"\nSample total costs per project type:")
        bridge_total = sum(t["total_cost"] for t in BRIDGE_BOQ_TEMPLATES)
        building_total = sum(t["total_cost"] for t in BUILDING_BOQ_TEMPLATES)
        road_total = sum(t["total_cost"] for t in ROAD_BOQ_TEMPLATES)
        culvert_total = sum(t["total_cost"] for t in CULVERT_BOQ_TEMPLATES)
        
        print(f"- Bridge project: ₦{bridge_total:,.2f}")
        print(f"- Building project: ₦{building_total:,.2f}")
        print(f"- Road project: ₦{road_total:,.2f}")
        print(f"- Culvert project: ₦{culvert_total:,.2f}")

if __name__ == "__main__":
    create_comprehensive_templates()