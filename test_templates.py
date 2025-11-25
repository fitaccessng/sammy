"""
Test template loading
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

app = create_app()

with app.app_context():
    env = app.jinja_env
    
    print("\n=== Testing Templates ===\n")
    
    templates = [
        'procurement/my_approvals.html',
        'cost_control/manager/purchase_order_approvals.html'
    ]
    
    for template_path in templates:
        try:
            template = env.get_template(template_path)
            print(f"✓ {template_path} - OK")
        except Exception as e:
            print(f"✗ {template_path} - ERROR: {e}")
    
    print("\n" + "="*60)
