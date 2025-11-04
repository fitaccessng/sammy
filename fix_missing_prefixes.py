"""
Fix missing endpoint prefixes in templates
"""
import os
import re

# Map of endpoints to their correct prefixed versions
ENDPOINT_MAPPINGS = {
    # Project endpoints
    'create_dpr': 'project.create_dpr',
    'dpr_list': 'project.dpr_list',
    'reports_list': 'project.reports_list',
    'create_report': 'project.create_report',
    'reports_index': 'project.reports_index',
    'calendar': 'project.calendar',
    
    # Admin endpoints
    'alerts': 'admin.alerts',
    'add_alert': 'admin.add_alert',
    'add_general_schedule': 'admin.add_general_schedule',
    'roles_view': 'admin.roles_view',
    'reporting_lines_view': 'admin.reporting_lines_view',
    'approval_hierarchy_view': 'admin.approval_hierarchy_view',
    'permissions_view': 'admin.permissions_view',
    'oversight_reports_view': 'admin.oversight_reports_view',
    'assign_user_role': 'admin.assign_user_role',
    'assign_employee_project': 'admin.assign_employee_project',
    'add_incident': 'admin.add_incident',
    'incidents': 'admin.incidents',
    'analytics_custom': 'admin.analytics_custom',
    'analytics_export_csv': 'admin.analytics_export_csv',
    'adjust_stock_quantity': 'admin.adjust_stock_quantity',
    
    # HR endpoints
    'hr_dashboard': 'hr.hr_dashboard',
    'payroll_approvals': 'hr.payroll_approvals',
    'export_attendance': 'hr.export_attendance',
    
    # Finance endpoints
    'audit': 'finance.audit',
    
    # Main endpoints
    'login': 'main.login',
    'logout': 'main.logout',
    'signup': 'main.signup',
    'forgot_password': 'main.forgot_password',
    'dashboard': 'dashboard.dashboard',
}

def fix_template_file(filepath):
    """Fix url_for calls in a single template file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes_made = []
        
        # Fix each endpoint mapping
        for old_endpoint, new_endpoint in ENDPOINT_MAPPINGS.items():
            # Match both single and double quotes
            pattern1 = f"url_for\\('{old_endpoint}'\\)"
            pattern2 = f'url_for\\("{old_endpoint}"\\)'
            replacement1 = f"url_for('{new_endpoint}')"
            replacement2 = f'url_for("{new_endpoint}")'
            
            if pattern1 in content:
                content = content.replace(pattern1, replacement1)
                changes_made.append(f"{old_endpoint} -> {new_endpoint}")
            if pattern2 in content:
                content = content.replace(pattern2, replacement2)
                changes_made.append(f"{old_endpoint} -> {new_endpoint}")
        
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return changes_made
        
        return None
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return None

def main():
    templates_dir = 'templates'
    total_files = 0
    total_changes = 0
    
    for root, dirs, files in os.walk(templates_dir):
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(root, file)
                changes = fix_template_file(filepath)
                if changes:
                    total_files += 1
                    total_changes += len(changes)
                    print(f"\n{filepath}:")
                    for change in set(changes):
                        print(f"  - {change}")
    
    print(f"\n{'='*60}")
    print(f"Updated {total_files} files with {total_changes} endpoint changes")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()
