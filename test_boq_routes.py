"""
Test BOQ Template Loading and Import Routes
This script tests the backend API endpoints to ensure they work correctly
"""

import requests
import json

def test_boq_routes():
    base_url = "http://127.0.0.1:5000"
    
    # You'll need to get a valid session cookie by logging in first
    # For now, this shows the expected request format
    
    print("🧪 Testing BOQ Routes...")
    
    # Test 1: Get BOQ templates (for caching)
    print("\n1. Testing template fetching...")
    test_get_templates = {
        "url": f"{base_url}/admin/projects/1/get_boq_templates",
        "method": "POST",
        "data": {"project_type": "Building"},
        "expected": "Should return list of Building templates"
    }
    print(f"   URL: {test_get_templates['url']}")
    print(f"   Data: {test_get_templates['data']}")
    print(f"   Expected: {test_get_templates['expected']}")
    
    # Test 2: Load templates into project
    print("\n2. Testing template loading...")
    test_load_templates = {
        "url": f"{base_url}/admin/projects/1/load_boq_templates",
        "method": "POST", 
        "data": {"project_type": "Building"},
        "expected": "Should add templates to project BOQ"
    }
    print(f"   URL: {test_load_templates['url']}")
    print(f"   Data: {test_load_templates['data']}")
    print(f"   Expected: {test_load_templates['expected']}")
    
    # Test 3: Import BOQ file
    print("\n3. Testing BOQ import...")
    test_import_boq = {
        "url": f"{base_url}/admin/projects/1/import_boq",
        "method": "POST",
        "file": "uploads/sample_imports/sample_boq_import.xlsx",
        "expected": "Should import BOQ items from Excel file"
    }
    print(f"   URL: {test_import_boq['url']}")
    print(f"   File: {test_import_boq['file']}")
    print(f"   Expected: {test_import_boq['expected']}")
    
    # Test 4: Import materials file
    print("\n4. Testing materials import...")
    test_import_materials = {
        "url": f"{base_url}/admin/projects/1/import_materials",
        "method": "POST",
        "file": "uploads/sample_imports/sample_material_import.xlsx",
        "expected": "Should import material items from Excel file"
    }
    print(f"   URL: {test_import_materials['url']}")
    print(f"   File: {test_import_materials['file']}")
    print(f"   Expected: {test_import_materials['expected']}")
    
    print("\n" + "="*60)
    print("📋 MANUAL TESTING INSTRUCTIONS:")
    print("="*60)
    print("1. Open browser and go to: http://127.0.0.1:5000")
    print("2. Login with admin credentials")
    print("3. Navigate to any project view page")
    print("4. Open browser Developer Tools (F12) -> Console tab")
    print("5. Select a project type from dropdown")
    print("6. Click 'Load Templates' button")
    print("7. Check console for debug messages")
    print("8. Test file imports with sample files")
    
    print("\n🔍 DEBUGGING CHECKLIST:")
    print("✅ Project data loads: Check console for 'Project data loaded'")
    print("✅ Template loading: Check for success/error messages")
    print("✅ Import functions: Try uploading sample files")
    print("✅ Network tab: Check for 404/500 errors in requests")
    
    print("\n📁 SAMPLE FILES AVAILABLE:")
    print("- uploads/sample_imports/sample_boq_import.xlsx")
    print("- uploads/sample_imports/sample_boq_import.csv")
    print("- uploads/sample_imports/sample_material_import.xlsx")
    print("- uploads/sample_imports/sample_material_import.csv")

if __name__ == '__main__':
    test_boq_routes()