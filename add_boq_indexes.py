"""
Add Index for BOQ Template Loading Performance
This script adds database indexes to improve template loading speed
"""

from app import create_app
from extensions import db
from sqlalchemy import text

def add_boq_indexes():
    app = create_app()
    
    with app.app_context():
        try:
            # Add index on is_template and item_type for faster template queries
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_boq_template_type 
                ON boq_items(is_template, item_type) 
                WHERE is_template = true
            """))
            
            # Add index on project_id and item_description for faster duplicate checks
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_boq_project_description 
                ON boq_items(project_id, item_description)
            """))
            
            db.session.commit()
            print("Successfully added database indexes for BOQ performance optimization")
            
        except Exception as e:
            print(f"Error adding indexes: {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    add_boq_indexes()