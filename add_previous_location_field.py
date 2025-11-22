"""
Migration script to add previous_location field to inventory_items table
"""
from app import create_app
from extensions import db
from sqlalchemy import text

def add_previous_location_field():
    """Add previous_location column to inventory_items table"""
    app = create_app()
    with app.app_context():
        try:
            # Check if column exists
            check_query = text("""
                SELECT COUNT(*) as count 
                FROM pragma_table_info('inventory_items') 
                WHERE name='previous_location'
            """)
            result = db.session.execute(check_query).fetchone()
            
            if result[0] == 0:
                # Add previous_location column
                alter_query = text("""
                    ALTER TABLE inventory_items 
                    ADD COLUMN previous_location VARCHAR(255)
                """)
                db.session.execute(alter_query)
                db.session.commit()
                print("✓ Added 'previous_location' column to inventory_items table")
            else:
                print("✓ 'previous_location' column already exists")
                
        except Exception as e:
            db.session.rollback()
            print(f"✗ Error adding previous_location field: {str(e)}")
            raise

if __name__ == '__main__':
    print("\n=== Adding Previous Location Field ===\n")
    add_previous_location_field()
    print("\n✓ Migration completed successfully!\n")
