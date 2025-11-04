#!/usr/bin/env python3
"""
Simple fix for MaterialSchedule table
"""

import sqlite3

def fix_table():
    conn = sqlite3.connect('sammy.db')
    cursor = conn.cursor()
    
    try:
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='material_schedules'")
        if not cursor.fetchone():
            print("material_schedules table does not exist, creating it...")
            
            create_sql = """
            CREATE TABLE material_schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
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
            cursor.execute(create_sql)
            print("Created material_schedules table")
        else:
            print("Table exists, attempting to modify...")
            # For existing table, we need to recreate it
            
            # Check current data
            cursor.execute("SELECT COUNT(*) FROM material_schedules")
            count = cursor.fetchone()[0]
            print(f"Found {count} existing records")
            
            # Backup data if any
            if count > 0:
                cursor.execute("""
                CREATE TABLE material_schedules_backup AS 
                SELECT * FROM material_schedules
                """)
                print("Created backup table")
            
            # Drop and recreate
            cursor.execute("DROP TABLE material_schedules")
            
            create_sql = """
            CREATE TABLE material_schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
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
            cursor.execute(create_sql)
            print("Recreated material_schedules table with nullable project_id")
            
            # Restore data if any
            if count > 0:
                cursor.execute("""
                INSERT INTO material_schedules 
                SELECT * FROM material_schedules_backup
                """)
                cursor.execute("DROP TABLE material_schedules_backup")
                print(f"Restored {count} records")
        
        conn.commit()
        print("Successfully fixed material_schedules table!")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_table()