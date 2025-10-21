#!/usr/bin/env python3
"""
Debug script to check employee roles in the database
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import Employee
from utils.constants import Roles

# Create app context
app = create_app()

with app.app_context():
    print("=== ROLE DEBUG ANALYSIS ===")
    
    # Get all employees
    employees = Employee.query.all()
    print(f"Total employees in database: {len(employees)}")
    
    if employees:
        print("\nEmployee role values:")
        for emp in employees:
            print(f"- Employee: {emp.name}")
            print(f"  Email: {emp.email}")
            print(f"  Role: '{emp.role}' (type: {type(emp.role)})")
            print(f"  Role repr: {repr(emp.role)}")
    
    # Get available system roles
    print("\nAvailable system roles:")
    for attr_name in dir(Roles):
        if not attr_name.startswith('_'):
            role_value = getattr(Roles, attr_name)
            print(f"- {attr_name}: '{role_value}' (type: {type(role_value)})")
    
    # Check exact matches
    print("\nRole matching analysis:")
    for attr_name in dir(Roles):
        if not attr_name.startswith('_'):
            role_value = getattr(Roles, attr_name)
            matching_employees = Employee.query.filter_by(role=role_value).all()
            print(f"- Role '{role_value}': {len(matching_employees)} employees")
            if matching_employees:
                for emp in matching_employees:
                    print(f"  * {emp.name}")
    
    # Check for employees with no valid role
    valid_roles = [getattr(Roles, attr) for attr in dir(Roles) if not attr.startswith('_')]
    unassigned = Employee.query.filter(~Employee.role.in_(valid_roles)).all()
    print(f"\nEmployees with invalid/unassigned roles: {len(unassigned)}")
    for emp in unassigned:
        print(f"- {emp.name}: '{emp.role}'")
    
    print("=== END DEBUG ANALYSIS ===")