#!/usr/bin/env python3
"""
Migration script to add status column to BOQItem table
This script adds the material status tracking functionality to existing BOQ items
"""

import os
import sys
from sqlalchemy import text

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import Flask app and database
from app import create_app
from extensions import db

def add_boq_status_column():
    """Add status column to boq_items table"""
    
    app = create_app()
    with app.app_context():
        try:
            print("Adding status column to boq_items table...")
            
            # Check if column already exists (SQLite version)
            result = db.session.execute(text("""
                PRAGMA table_info(boq_items)
            """))
            
            columns = result.fetchall()
            column_exists = any(col[1] == 'status' for col in columns)
            
            if column_exists:
                print("✓ Status column already exists in boq_items table")
                return True
            
            # Add the status column (SQLite version)
            db.session.execute(text("""
                ALTER TABLE boq_items 
                ADD COLUMN status VARCHAR(20) DEFAULT 'Pending'
            """))
            
            # Update existing records to have 'Pending' status
            db.session.execute(text("""
                UPDATE boq_items 
                SET status = 'Pending' 
                WHERE status IS NULL OR status = ''
            """))
            
            db.session.commit()
            print("✓ Successfully added status column to boq_items table")
            print("✓ All existing BOQ items set to 'Pending' status")
            
            return True
            
        except Exception as e:
            print(f"✗ Error adding status column: {str(e)}")
            db.session.rollback()
            return False

def verify_migration():
    """Verify the migration was successful"""
    
    app = create_app()
    with app.app_context():
        try:
            # Test the new column
            result = db.session.execute(text("""
                SELECT id, item_description, status 
                FROM boq_items 
                LIMIT 5
            """))
            
            rows = result.fetchall()
            
            print("\n--- Migration Verification ---")
            print("Sample BOQ items with status:")
            
            if rows:
                for row in rows:
                    print(f"ID: {row[0]}, Item: {row[1][:50]}..., Status: {row[2]}")
            else:
                print("No BOQ items found (this is normal for new installations)")
            
            print("✓ Migration verification completed successfully")
            return True
            
        except Exception as e:
            print(f"✗ Verification failed: {str(e)}")
            return False

if __name__ == "__main__":
    print("=== BOQ Status Column Migration ===")
    print("This script will add a 'status' column to the boq_items table")
    print("for material schedule tracking functionality.")
    print()
    
    # Run migration
    success = add_boq_status_column()
    
    if success:
        # Verify migration
        verify_migration()
        print("\n✓ Migration completed successfully!")
        print("The system now supports material status tracking.")
    else:
        print("\n✗ Migration failed. Please check the error messages above.")
        sys.exit(1)