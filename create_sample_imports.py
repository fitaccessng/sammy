"""
Create Sample BOQ Import Files
This script creates sample Excel and CSV files for testing the import functionality
"""

import pandas as pd
import os

def create_sample_import_files():
    # Sample BOQ data
    boq_data = {
        'item_description': [
            'Concrete Foundation Work',
            'Steel Reinforcement Bars',
            'Masonry Block Work',
            'Roofing Materials',
            'Electrical Wiring'
        ],
        'quantity': [50, 2000, 100, 150, 1],
        'unit': ['m³', 'kg', 'm²', 'm²', 'lot'],
        'unit_price': [15000.00, 800.00, 8000.00, 12000.00, 300000.00],
        'item_type': ['Building', 'Building', 'Building', 'Building', 'Building'],
        'category': ['Foundation', 'Materials', 'Masonry', 'Roofing', 'Services'],
        'bill_no': ['BD001', 'BD001', 'BD001', 'BD001', 'BD001'],
        'item_no': ['001', '002', '003', '004', '005']
    }
    
    # Sample Material Schedule data
    material_data = {
        'item_description': [
            'Portland Cement',
            'Steel Bars (12mm)',
            'Concrete Blocks',
            'Aluminum Roofing Sheets',
            'Electrical Cables'
        ],
        'quantity': [100, 500, 200, 50, 1000],
        'unit': ['bags', 'pieces', 'pieces', 'sheets', 'meters'],
        'unit_cost': [3500.00, 2500.00, 1200.00, 8000.00, 450.00],
        'item_type': ['Building', 'Building', 'Building', 'Building', 'Building'],
        'status': ['Pending', 'Pending', 'Ordered', 'Pending', 'Delivered']
    }
    
    # Create uploads directory if it doesn't exist
    uploads_dir = 'uploads/sample_imports'
    os.makedirs(uploads_dir, exist_ok=True)
    
    # Create BOQ files
    boq_df = pd.DataFrame(boq_data)
    boq_df.to_excel(f'{uploads_dir}/sample_boq_import.xlsx', index=False)
    boq_df.to_csv(f'{uploads_dir}/sample_boq_import.csv', index=False)
    
    # Create Material Schedule files
    material_df = pd.DataFrame(material_data)
    material_df.to_excel(f'{uploads_dir}/sample_material_import.xlsx', index=False)
    material_df.to_csv(f'{uploads_dir}/sample_material_import.csv', index=False)
    
    print("Sample import files created successfully:")
    print(f"- {uploads_dir}/sample_boq_import.xlsx")
    print(f"- {uploads_dir}/sample_boq_import.csv")
    print(f"- {uploads_dir}/sample_material_import.xlsx")
    print(f"- {uploads_dir}/sample_material_import.csv")
    
    print("\nFile contents preview:")
    print("\nBOQ Import Sample:")
    print(boq_df.to_string(index=False))
    
    print("\nMaterial Schedule Import Sample:")
    print(material_df.to_string(index=False))

if __name__ == '__main__':
    create_sample_import_files()