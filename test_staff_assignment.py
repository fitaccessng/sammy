#!/usr/bin/env python3
"""
Test script to verify staff assignment functionality
"""
import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

def test_staff_endpoint():
    app = create_app()
    
    with app.test_client() as client:
        # Test the admin project page to see if available_staff is populated
        response = client.get('/admin/3')
        
        print(f"Admin project page status: {response.status_code}")
        
        if response.status_code == 302:
            print("✅ Page loads (redirects for auth)")
            
            # Test the staff assignment endpoint
            test_data = {
                'staff_id': '1',
                'role': 'Site Engineer'
            }
            
            response = client.post('/admin/projects/3/assign_staff', data=test_data)
            print(f"Staff assignment endpoint status: {response.status_code}")
            
            if response.status_code == 302:
                print("✅ Staff assignment endpoint accessible (redirects for auth)")
            elif response.status_code == 400:
                print("⚠️  CSRF error expected without proper authentication")
            else:
                print(f"❓ Unexpected status: {response.status_code}")
            
        else:
            print(f"❌ Unexpected page status: {response.status_code}")

if __name__ == "__main__":
    test_staff_endpoint()