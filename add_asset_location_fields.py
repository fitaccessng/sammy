#!/usr/bin/env python
"""Add location tracking fields to inventory_items table"""

from flask import Flask
from extensions import db
from sqlalchemy import text

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sammy.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    # Add new columns to inventory_items table
    try:
        with db.engine.connect() as conn:
            # Check if columns already exist
            result = conn.execute(text("PRAGMA table_info(inventory_items)"))
            existing_columns = [row[1] for row in result.fetchall()]
            
            if 'location' not in existing_columns:
                conn.execute(text("ALTER TABLE inventory_items ADD COLUMN location VARCHAR(255)"))
                print("✓ Added 'location' column")
            else:
                print("  'location' column already exists")
            
            if 'latitude' not in existing_columns:
                conn.execute(text("ALTER TABLE inventory_items ADD COLUMN latitude FLOAT"))
                print("✓ Added 'latitude' column")
            else:
                print("  'latitude' column already exists")
            
            if 'longitude' not in existing_columns:
                conn.execute(text("ALTER TABLE inventory_items ADD COLUMN longitude FLOAT"))
                print("✓ Added 'longitude' column")
            else:
                print("  'longitude' column already exists")
            
            if 'status' not in existing_columns:
                conn.execute(text("ALTER TABLE inventory_items ADD COLUMN status VARCHAR(32) DEFAULT 'Active'"))
                print("✓ Added 'status' column")
            else:
                print("  'status' column already exists")
            
            if 'last_location_update' not in existing_columns:
                conn.execute(text("ALTER TABLE inventory_items ADD COLUMN last_location_update DATETIME"))
                print("✓ Added 'last_location_update' column")
            else:
                print("  'last_location_update' column already exists")
            
            conn.commit()
            
        print("\n✓ Asset location tracking fields added successfully!")
        print("\nYou can now:")
        print("  1. Update asset locations from the Asset Tracking page")
        print("  2. View assets on the map with their GPS coordinates")
        print("  3. Track asset status (Active, In Transit, In Maintenance)")
        
    except Exception as e:
        print(f"✗ Error adding columns: {str(e)}")
        import traceback
        traceback.print_exc()
