#!/usr/bin/env python3
"""
Script to create database migration for Employee salary fields
"""

import os
import sys
from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the app and models
from app import create_app, db
from models import Employee  # Import to ensure model is loaded

def create_migration():
    """Create migration for Employee salary fields"""
    app = create_app()
    
    with app.app_context():
        # Initialize migration
        from flask_migrate import init, migrate, upgrade
        from alembic import command
        from alembic.config import Config
        
        # Create migration
        try:
            os.system('flask db migrate -m "add_comprehensive_employee_salary_fields"')
            print("Migration created successfully!")
        except Exception as e:
            print(f"Error creating migration: {e}")
            # Alternative method using direct alembic
            try:
                from migrations import env
                config = Config("alembic.ini")
                command.revision(config, message="add_comprehensive_employee_salary_fields", autogenerate=True)
                print("Migration created using direct alembic!")
            except Exception as e2:
                print(f"Alternative method also failed: {e2}")

if __name__ == "__main__":
    create_migration()