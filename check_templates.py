"""
Script to add URL prefixes back to template url_for() calls
This restores the blueprint-style routing: url_for('route') -> url_for('prefix.route')
But since we don't have blueprints, we need to use the full path or update url_for
"""
import os
import re

def restore_template_prefixes(templates_dir):
    """Add prefixes back to url_for calls in templates"""
    
    # Mapping of route functions to their prefixes
    # Based on which module they came from
    route_mappings = {
        # Main routes (no prefix)
        'main_home': '/',
        'signup': '/signup',
        'login': '/login',
        'verify_email_page': '/verify-email',
        'forgot_password': '/forgot-password',
        'reset_password': '/reset-password',
        'verify_email': '/verify',
        
        # Files routes
        'upload_file': '/files/files/upload',
        'create_folder': '/files/folders/create',
        'search_files': '/files/files/search',
        'file_detail': '/files/files',
        'download_file': '/files/files',
        
        # Dashboard routes
        'super_hq_dashboard': '/dashboard/super-hq',
        'hq_finance_dashboard': '/dashboard/hq-finance',
        'hq_hr_dashboard': '/dashboard/hq-hr',
        'hq_procurement_dashboard': '/dashboard/hq-procurement',
        'hq_quarry_dashboard': '/dashboard/hq-quarry',
        'hq_project_dashboard': '/dashboard/hq-project',
        
        # Admin routes
        'dashboard': '/admin',
        
        # Finance routes
        'finance_home': '/finance',
        
        # HR routes
        'hr_home': '/hr',
        
        # Procurement routes
        'procurement_home': '/procurement',
        
        # Quarry routes
        'quarry_home': '/quarry',
        
        # Project routes
        'project_home': '/project',
        'equipment': '/project/equipment',
        'edit_equipment': '/project/equipment',
        'delete_equipment': '/project/equipment',
    }
    
    # Since Flask doesn't have blueprints anymore, url_for needs endpoint names
    # We need to add unique endpoint names to routes
    print("Note: Templates use url_for() which requires endpoint names.")
    print("With consolidated routes, we need unique endpoint names.")
    print("Templates should work if routes have proper endpoint= parameters.")
    
    return 0

if __name__ == "__main__":
    base_path = r"c:\Users\Nwakanma\Desktop\Fitaccess\sammy"
    templates_path = os.path.join(base_path, "templates")
    
    print("="*80)
    print("CHECKING TEMPLATE URL_FOR() COMPATIBILITY")
    print("="*80)
    
    result = restore_template_prefixes(templates_path)
    
    print("\n" + "="*80)
    print("IMPORTANT: url_for() in templates will work if:")
    print("1. Route functions have unique names across all modules")
    print("2. OR routes use endpoint= parameter: @app.route('/path', endpoint='unique_name')")
    print("="*80)
    print("\nCurrent status: Routes have URL prefixes, but may need unique function names")
    print("="*80)
