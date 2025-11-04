#!/usr/bin/env python3
"""
Fix MaterialSchedule table to allow nullable project_id for templates
"""

import sqlite3
from app import create_app
from extensions import db

def fix_material_schedule_table():
    """Fix the material_schedules table to allow NULL project_id"""
    app = create_app()
    
    with app.app_context():
        # Get database path
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        if db_uri.startswith('sqlite:///'):
            db_path = db_uri[10:]  # Remove 'sqlite:///'
        else:
            db_path = 'sammy.db'  # Default path
        
        print(f"Using database: {db_path}")
        
        # Connect to database directly
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Drop existing new table if it exists
            cursor.execute("DROP TABLE IF EXISTS material_schedules_new")
            
            # Check current table structure
            cursor.execute("PRAGMA table_info(material_schedules)")
            columns = cursor.fetchall()
            print("Current table structure:")
            for col in columns:
                print(f"  {col}")
            
            # Create new table with nullable project_id
            create_table_sql = """
            CREATE TABLE material_schedules_new (
                id INTEGER PRIMARY KEY,
                project_id INTEGER,
                boq_item_id INTEGER,
                material_name VARCHAR(255) NOT NULL,
                specification TEXT,
                required_qty FLOAT DEFAULT 0.0,
                ordered_qty FLOAT DEFAULT 0.0,
                received_qty FLOAT DEFAULT 0.0,
                used_qty FLOAT DEFAULT 0.0,
                unit VARCHAR(50),
                unit_cost FLOAT DEFAULT 0.0,
                total_cost FLOAT DEFAULT 0.0,
                required_date DATETIME,
                delivery_date DATETIME,
                status VARCHAR(50) DEFAULT 'Planned',
                supplier_name VARCHAR(255),
                supplier_contact VARCHAR(100),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id),
                FOREIGN KEY (boq_item_id) REFERENCES boq_items(id)
            )
            """
            
            cursor.execute(create_table_sql)
            print("Created new table with nullable project_id")
            
            # Copy existing data (if any)
            cursor.execute("SELECT COUNT(*) FROM material_schedules")
            count = cursor.fetchone()[0]
            
            if count > 0:
                cursor.execute("""
                INSERT INTO material_schedules_new 
                SELECT * FROM material_schedules
                """)
                print(f"Copied {count} existing records")
            
            # Drop old table and rename new one
            cursor.execute("DROP TABLE material_schedules")
            cursor.execute("ALTER TABLE material_schedules_new RENAME TO material_schedules")
            
            print("Successfully updated material_schedules table")
            
            conn.commit()
            
        except Exception as e:
            print(f"Error: {e}")
            conn.rollback()
        finally:
            conn.close()

if __name__ == "__main__":
    fix_material_schedule_table()