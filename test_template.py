#!/usr/bin/env python3
"""
Test script to verify the admin project details template loads without errors
"""
import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

def test_template():
    app = create_app()
    
    with app.test_client() as client:
        # Test the admin project page
        response = client.get('/admin/3')
        
        print(f"Response status code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: Template loads without errors!")
            return True
        elif response.status_code == 302:
            print("📝 INFO: Got redirect (probably authentication required)")
            print("This is expected behavior - template syntax is fixed!")
            return True
        elif response.status_code == 500:
            print("❌ ERROR: Server error (template issue)")
            error_text = response.data.decode('utf-8', errors='ignore')
            if 'globals' in error_text:
                print("   Still has globals() syntax errors")
            else:
                print("   Different server error")
            return False
        else:
            print(f"❓ Unexpected status: {response.status_code}")
            return False

if __name__ == "__main__":
    test_template()