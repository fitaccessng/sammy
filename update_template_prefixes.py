"""
Script to update template url_for() calls to use endpoint names with prefixes
Changes url_for('route') to url_for('prefix.route') based on context
"""
import os
import re

def update_template_urls(templates_dir):
    """Update url_for calls to use prefixed endpoint names"""
    
    # Mapping of routes to their prefixed versions
    route_prefix_map = {
        # Main routes (no prefix for main routes)
        'main_home': 'main_home',
        'signup': 'signup',
        'login': 'login',
        'logout': 'logout',
        'verify_email_page': 'verify_email_page',
        'forgot_password': 'forgot_password',
        'reset_password': 'reset_password',
        'verify_email': 'verify_email',
        
        # Files routes
        'upload_file': 'files.upload_file',
        'create_folder': 'files.create_folder',
        'search_files': 'files.search_files',
        'file_detail': 'files.file_detail',
        'download_file': 'files.download_file',
        
        # Admin routes
        'dashboard': 'admin.dashboard',
        'add_project': 'admin.add_project',
        'edit_project': 'admin.edit_project',
        'view_project': 'admin.view_project',
        'projects': 'admin.projects',
        'add_asset': 'admin.add_asset',
        'edit_asset': 'admin.edit_asset',
        'assets': 'admin.assets',
        'add_stock': 'admin.add_stock',
        'edit_stock': 'admin.edit_stock',
        'stock': 'admin.stock',
        'add_supplier': 'admin.add_supplier',
        'suppliers': 'admin.suppliers',
        'add_equipment': 'admin.add_equipment',
        'equipment': 'admin.equipment',
        'add_order': 'admin.add_order',
        'orders': 'admin.orders',
        'schedules': 'admin.schedules',
        'all_milestones': 'admin.all_milestones',
        'user_management': 'admin.user_management',
        'comprehensive_user_management': 'admin.comprehensive_user_management',
        
        # Finance routes  
        'finance_home': 'finance.finance_home',
        'expenses': 'finance.expenses',
        'account_transactions': 'finance.account_transactions',
        'bank_reconciliation': 'finance.bank_reconciliation',
        'expense_details': 'finance.expense_details',
        
        # HR routes
        'hr_home': 'hr.hr_home',
        'staff': 'hr.staff',
        'staff_details': 'hr.staff_details',
        'staff_documents': 'hr.staff_documents',
        'payroll': 'hr.payroll',
        'attendance': 'hr.attendance',
        'deductions': 'hr.deductions',
        'queries': 'hr.queries',
        'tasks': 'hr.tasks',
        'reports': 'hr.reports',
        
        # Procurement routes
        'procurement_home': 'procurement.procurement_home',
        'purchases': 'procurement.purchases',
        'suppliers': 'procurement.suppliers',
        'tracking': 'procurement.tracking',
        'analytics': 'procurement.analytics',
        'budget': 'procurement.budget',
        'maintenance': 'procurement.maintenance',
        'notifications': 'procurement.notifications',
        'search': 'procurement.search',
        'settings': 'procurement.settings',
        'profile': 'procurement.profile',
        
        # Quarry routes
        'quarry_home': 'quarry.quarry_home',
        'workers': 'quarry.workers',
        'materials': 'quarry.materials',
        'safety': 'quarry.safety',
        
        # Project routes
        'project_home': 'project.project_home',
        'create_project': 'project.create_project',
        'list_projects': 'project.list_projects',
        'project_details': 'project.project_details',
        'edit_equipment': 'project.edit_equipment',
        'delete_equipment': 'project.delete_equipment',
        'documents': 'project.documents',
        'dpr': 'project.dpr',
        'dpr_view': 'project.dpr_view',
        'dpr_edit': 'project.dpr_edit',
        'report_view': 'project.report_view',
        'report_edit': 'project.report_edit',
        'settings': 'project.settings',
    }
    
    total_changes = 0
    files_updated = 0
    
    for root, dirs, files in os.walk(templates_dir):
        for file in files:
            if file.endswith(('.html', '.htm')):
                filepath = os.path.join(root, file)
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    original_content = content
                    changes = 0
                    
                    # Update url_for calls
                    for route, prefixed in route_prefix_map.items():
                        # Match url_for('route') and url_for("route")
                        patterns = [
                            (rf"url_for\('{route}'", f"url_for('{prefixed}'"),
                            (rf'url_for\("{route}"', f'url_for("{prefixed}"')
                        ]
                        
                        for pattern, replacement in patterns:
                            new_content, count = re.subn(pattern, replacement, content)
                            if count > 0:
                                changes += count
                                content = new_content
                    
                    if content != original_content:
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(content)
                        files_updated += 1
                        total_changes += changes
                        print(f"✓ Updated {filepath}: {changes} changes")
                
                except Exception as e:
                    print(f"Error processing {filepath}: {e}")
    
    return files_updated, total_changes

if __name__ == "__main__":
    base_path = r"c:\Users\Nwakanma\Desktop\Fitaccess\sammy"
    templates_path = os.path.join(base_path, "templates")
    
    print("="*80)
    print("UPDATING TEMPLATE URL_FOR() TO USE PREFIXED ENDPOINTS")
    print("="*80)
    print(f"Templates directory: {templates_path}")
    print("\nProcessing templates...\n")
    
    files_updated, total_changes = update_template_urls(templates_path)
    
    print("\n" + "="*80)
    print(f"✓ COMPLETED")
    print(f"✓ Files updated: {files_updated}")
    print(f"✓ Total changes: {total_changes}")
    print("="*80)
