"""
Route Verification Script
Tests all registered routes and url_for() calls
"""
from flask import Flask
import sys
import os

# Import the app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def verify_routes():
    """Test that all routes are registered correctly"""
    try:
        from app import create_app
        app = create_app()
    except:
        # Fallback to direct import
        import app as app_module
        app = app_module.app if hasattr(app_module, 'app') else Flask(__name__)
    
    print("="*80)
    print("FLASK ROUTE VERIFICATION")
    print("="*80)
    
    # Get all registered routes
    rules = list(app.url_map.iter_rules())
    
    print(f"\n✓ Total registered routes: {len(rules)}")
    print("\nRoute Summary by Blueprint:")
    print("-"*80)
    
    # Group by endpoint prefix (blueprint)
    from collections import defaultdict
    by_prefix = defaultdict(list)
    
    for rule in rules:
        if '.' in rule.endpoint:
            prefix = rule.endpoint.split('.')[0]
        else:
            prefix = 'main'
        by_prefix[prefix].append(rule)
    
    for prefix in sorted(by_prefix.keys()):
        routes = by_prefix[prefix]
        print(f"\n{prefix}: {len(routes)} routes")
        for rule in sorted(routes, key=lambda r: r.rule)[:5]:  # Show first 5
            methods = ','.join(rule.methods - {'HEAD', 'OPTIONS'})
            print(f"  {rule.rule:50} [{methods:10}] -> {rule.endpoint}")
        if len(routes) > 5:
            print(f"  ... and {len(routes)-5} more routes")
    
    print("\n" + "="*80)
    print("ROUTE VERIFICATION COMPLETE")
    print("="*80)
    
    # Export all routes to file
    with open('registered_routes.txt', 'w', encoding='utf-8') as f:
        f.write("ALL REGISTERED ROUTES\n")
        f.write("="*80 + "\n\n")
        for rule in sorted(rules, key=lambda r: r.endpoint):
            methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
            f.write(f"{rule.endpoint:60} {rule.rule:50} [{methods}]\n")
    
    print("\n📄 Complete route list exported to: registered_routes.txt")
    
    return app, rules

if __name__ == '__main__':
    app, rules = verify_routes()
    
    print("\n" + "="*80)
    print("TESTING URL GENERATION")
    print("="*80)
    
    # Test url generation for some common endpoints
    test_endpoints = [
        'main_home',
        'login',
        'logout',
        'dashboard.super_hq_dashboard',
        'project.project_home',
        'admin.dashboard',
        'hr.hr_home',
        'finance.finance_home',
        'procurement.procurement_home',
        'quarry.quarry_home',
    ]
    
    with app.test_request_context():
        from flask import url_for
        
        print("\nTesting sample endpoints:")
        print("-"*80)
        
        for endpoint in test_endpoints:
            try:
                url = url_for(endpoint)
                print(f"  ✓ {endpoint:40} -> {url}")
            except Exception as e:
                print(f"  ✗ {endpoint:40} -> ERROR: {str(e)[:50]}")
    
    print("\n✓ Verification complete!")
