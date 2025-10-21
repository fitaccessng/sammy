#!/usr/bin/env python3
"""
Script to initialize sample data for testing the admin functionality
"""
from wsgi import app
from extensions import db
from models import Project, User
from datetime import datetime, date
import sys

def create_sample_data():
    """Create sample data for testing"""
    try:
        with app.app_context():
            # Create sample project
            existing_project = Project.query.filter_by(name='Sample Construction Project').first()
            if not existing_project:
                project = Project(
                    name='Sample Construction Project',
                    description='A sample project for testing the admin functionality',
                    start_date=date(2025, 1, 1),
                    end_date=date(2025, 12, 31),
                    status='Active',
                    project_manager='John Doe',
                    budget=1000000.0,
                    progress=25.0
                )
                db.session.add(project)
                print("✓ Sample project created")
            else:
                print("✓ Sample project already exists")
            
            # Create sample user (admin)
            existing_user = User.query.filter_by(email='admin@fitaccess.com').first()
            if not existing_user:
                from werkzeug.security import generate_password_hash
                user = User(
                    name='Admin User',
                    email='admin@fitaccess.com',
                    password_hash=generate_password_hash('admin123'),
                    role='SUPER_HQ',
                    is_verified=True
                )
                db.session.add(user)
                print("✓ Sample admin user created")
                print("  Email: admin@fitaccess.com")
                print("  Password: admin123")
            else:
                print("✓ Sample admin user already exists")
            
            db.session.commit()
            print("\n🎉 Sample data initialization completed successfully!")
            
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        db.session.rollback()
        sys.exit(1)

if __name__ == '__main__':
    create_sample_data()