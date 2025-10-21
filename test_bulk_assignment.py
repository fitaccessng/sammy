#!/usr/bin/env python3
"""
Simple test script to verify bulk role assignment functionality
"""

import requests
import json

# Test the bulk assignment endpoint
def test_bulk_assignment():
    url = "http://127.0.0.1:5000/admin/bulk-assign-roles"
    
    # Test data
    test_data = {
        "user_ids": [1, 2],  # Assuming these user IDs exist
        "role": "hr_staff"   # Test role
    }
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    try:
        print(f"Testing bulk assignment with data: {test_data}")
        response = requests.post(url, json=test_data, headers=headers)
        
        print(f"Response status code: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success! Response: {result}")
        else:
            print(f"Error response: {response.text}")
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_bulk_assignment()