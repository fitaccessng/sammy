#!/usr/bin/env python3
"""
Database migration script to update UploadedFile table
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from extensions import db
from models import UploadedFile

def migrate_database():
    app = create_app()
    
    with app.app_context():
        print("Checking current database schema...")
        
        # Check if the table exists and what columns it has
        try:
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"Available tables: {tables}")
            
            if 'uploaded_file' in tables:
                columns = inspector.get_columns('uploaded_file')
                column_names = [col['name'] for col in columns]
                print(f"Current UploadedFile columns: {column_names}")
                
                # Check if we need to add the missing columns
                required_columns = ['filename', 'file_size', 'file_type', 'uploaded_by']
                missing_columns = [col for col in required_columns if col not in column_names]
                
                if missing_columns:
                    print(f"Missing columns: {missing_columns}")
                    print("Adding missing columns...")
                    
                    # Add missing columns using raw SQL
                    with db.engine.connect() as connection:
                        trans = connection.begin()
                        try:
                            if 'filename' not in column_names:
                                connection.execute(db.text("ALTER TABLE uploaded_file ADD COLUMN filename VARCHAR(255)"))
                                # Copy name to filename for existing records
                                connection.execute(db.text("UPDATE uploaded_file SET filename = name WHERE filename IS NULL"))
                                
                            if 'file_size' not in column_names:
                                connection.execute(db.text("ALTER TABLE uploaded_file ADD COLUMN file_size INTEGER"))
                                
                            if 'file_type' not in column_names:
                                connection.execute(db.text("ALTER TABLE uploaded_file ADD COLUMN file_type VARCHAR(100)"))
                                
                            if 'uploaded_by' not in column_names:
                                connection.execute(db.text("ALTER TABLE uploaded_file ADD COLUMN uploaded_by INTEGER"))
                                
                            if 'folder' not in column_names:
                                connection.execute(db.text("ALTER TABLE uploaded_file ADD COLUMN folder VARCHAR(255)"))
                                
                            trans.commit()
                            print("Database schema updated successfully!")
                            
                        except Exception as e:
                            trans.rollback()
                            print(f"Error updating schema: {e}")
                            raise
                else:
                    print("All required columns already exist!")
                    
            else:
                print("UploadedFile table doesn't exist. Creating all tables (including Leave)...")
                db.create_all()
                print("All tables created successfully!")
                
        except Exception as e:
            print(f"Error during migration: {e}")
            raise

if __name__ == "__main__":
    migrate_database()
    app = create_app()
    with app.app_context():
        db.create_all()  # Ensure all tables, including Query, are created
        print("All tables created successfully!")