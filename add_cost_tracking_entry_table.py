"""
Migration script to add cost_tracking_entries table
"""
from app import create_app
from extensions import db
from sqlalchemy import text

def add_cost_tracking_entries_table():
    """Add cost_tracking_entries table to database"""
    app = create_app()
    with app.app_context():
        try:
            # Check if table exists
            check_query = text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='cost_tracking_entries'
            """)
            result = db.session.execute(check_query).fetchone()
            
            if not result:
                # Create cost_tracking_entries table
                create_table_query = text("""
                    CREATE TABLE cost_tracking_entries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        project_id INTEGER NOT NULL,
                        category_id INTEGER,
                        entry_date DATE NOT NULL,
                        description VARCHAR(500) NOT NULL,
                        planned_cost FLOAT DEFAULT 0.0,
                        actual_cost FLOAT DEFAULT 0.0,
                        variance FLOAT DEFAULT 0.0,
                        variance_percentage FLOAT DEFAULT 0.0,
                        cost_type VARCHAR(50) NOT NULL,
                        quantity FLOAT,
                        unit VARCHAR(50),
                        unit_cost FLOAT,
                        status VARCHAR(32) DEFAULT 'pending',
                        approval_required BOOLEAN DEFAULT 0,
                        approved_by INTEGER,
                        approved_at DATETIME,
                        created_by INTEGER NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (project_id) REFERENCES projects(id),
                        FOREIGN KEY (category_id) REFERENCES cost_category(id),
                        FOREIGN KEY (approved_by) REFERENCES user(id),
                        FOREIGN KEY (created_by) REFERENCES user(id)
                    )
                """)
                db.session.execute(create_table_query)
                db.session.commit()
                print("✓ Created 'cost_tracking_entries' table")
            else:
                print("✓ 'cost_tracking_entries' table already exists")
                
        except Exception as e:
            db.session.rollback()
            print(f"✗ Error creating cost_tracking_entries table: {str(e)}")
            raise

if __name__ == '__main__':
    print("\n=== Adding Cost Tracking Entries Table ===\n")
    add_cost_tracking_entries_table()
    print("\n✓ Migration completed successfully!\n")
