#!/usr/bin/env python3
"""
Script to check current database schema
"""

import sqlite3
import os

def check_employee_schema():
    """Check current Employee table schema"""
    db_path = os.path.join('instance', 'sammy.db')
    
    if not os.path.exists(db_path):
        print("Database file not found!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get Employee table schema
    cursor.execute("PRAGMA table_info(employee)")
    columns = cursor.fetchall()
    
    print("Current Employee table columns:")
    for col in columns:
        print(f"  {col[1]} - {col[2]} {'(NOT NULL)' if col[3] else '(NULL)'}")
    
    # Check if our salary fields exist
    salary_fields = [
        'basic_salary', 'housing_allowance', 'transport_allowance', 
        'medical_allowance', 'special_allowance', 'overtime_rate',
        'tax_number', 'pension_number', 'bank_name', 'bank_account_number',
        'employment_type', 'grade_level'
    ]
    
    existing_columns = [col[1] for col in columns]
    
    print("\nSalary field status:")
    for field in salary_fields:
        status = "EXISTS" if field in existing_columns else "MISSING"
        print(f"  {field}: {status}")
    
    conn.close()

if __name__ == "__main__":
    check_employee_schema()