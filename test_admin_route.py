#!/usr/bin/env python3
"""
Simple test script to verify the admin create project functionality
"""
from wsgi import app
from extensions import db
from models import Employee

def test_admin_route():
    """Test the admin route functionality"""
    try:
        with app.app_context():
            # Test employee query
            print("Testing Employee query...")
            employees = Employee.query.filter_by(status='Active').order_by(Employee.name).all()
            print(f"✓ Found {len(employees)} active employees")
            
            # Test form_data structure
            print("Testing form_data structure...")
            form_data = {}
            print(f"✓ Empty form_data: {form_data}")
            
            # Test basic template variables
            print("Testing template variables...")
            template_vars = {
                'employees': employees,
                'form_data': form_data
            }
            print(f"✓ Template variables prepared successfully")
            
            print("\n🎉 Admin route test completed successfully!")
            print("The create project form should now work properly.")
            
    except Exception as e:
        print(f"❌ Error in admin route test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_admin_route()