"""
Script to add URL prefixes to routes in consolidated app.py
This preserves the original blueprint URL structure
"""
import re

def add_url_prefixes():
    """Add URL prefixes to routes based on their original blueprint"""
    
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Define the sections and their prefixes
    sections = [
        {
            'marker': '# ROUTES FROM MAIN.PY',
            'end_marker': '# ROUTES FROM FILES.PY',
            'prefix': '',  # Main routes have no prefix
            'name': 'main'
        },
        {
            'marker': '# ROUTES FROM FILES.PY',
            'end_marker': '# ROUTES FROM DASHBOARD.PY',
            'prefix': '/files',
            'name': 'files'
        },
        {
            'marker': '# ROUTES FROM DASHBOARD.PY',
            'end_marker': '# ROUTES FROM COST_CONTROL.PY',
            'prefix': '/dashboard',
            'name': 'dashboard'
        },
        {
            'marker': '# ROUTES FROM COST_CONTROL.PY',
            'end_marker': '# ROUTES FROM HQ.PY',
            'prefix': '/cost-control',
            'name': 'cost_control'
        },
        {
            'marker': '# ROUTES FROM HQ.PY',
            'end_marker': '# ROUTES FROM PROCUREMENT.PY',
            'prefix': '/hq',
            'name': 'hq'
        },
        {
            'marker': '# ROUTES FROM PROCUREMENT.PY',
            'end_marker': '# ROUTES FROM QUARRY.PY',
            'prefix': '/procurement',
            'name': 'procurement'
        },
        {
            'marker': '# ROUTES FROM QUARRY.PY',
            'end_marker': '# ROUTES FROM FINANCE.PY',
            'prefix': '/quarry',
            'name': 'quarry'
        },
        {
            'marker': '# ROUTES FROM FINANCE.PY',
            'end_marker': '# ROUTES FROM HR.PY',
            'prefix': '/finance',
            'name': 'finance'
        },
        {
            'marker': '# ROUTES FROM HR.PY',
            'end_marker': '# ROUTES FROM ADMIN.PY',
            'prefix': '/hr',
            'name': 'hr'
        },
        {
            'marker': '# ROUTES FROM ADMIN.PY',
            'end_marker': '# ROUTES FROM ADMIN_CLEAN.PY',
            'prefix': '/admin',
            'name': 'admin'
        },
        {
            'marker': '# ROUTES FROM ADMIN_CLEAN.PY',
            'end_marker': '# ROUTES FROM PROJECT.PY',
            'prefix': '/admin',
            'name': 'admin_clean'
        },
        {
            'marker': '# ROUTES FROM PROJECT.PY',
            'end_marker': 'return app',
            'prefix': '/project',
            'name': 'project'
        }
    ]
    
    changes = 0
    
    for section in sections:
        marker_pos = content.find(section['marker'])
        if marker_pos == -1:
            print(f"Warning: Could not find marker {section['marker']}")
            continue
            
        end_pos = content.find(section['end_marker'], marker_pos)
        if end_pos == -1:
            end_pos = len(content)
        
        section_content = content[marker_pos:end_pos]
        prefix = section['prefix']
        
        if not prefix:  # Skip main routes (no prefix)
            continue
        
        # Find all @app.route decorators in this section
        # Pattern matches: @app.route('/path') or @app.route("/path")
        pattern = r"@app\.route\(['\"]([^'\"]+)['\"]"
        
        def add_prefix(match):
            nonlocal changes
            path = match.group(1)
            # Don't add prefix if it already has one
            if path.startswith(prefix):
                return match.group(0)
            # Handle root path
            if path == '/':
                new_path = prefix
            else:
                new_path = prefix + path
            changes += 1
            return f"@app.route('{new_path}'"
        
        new_section = re.sub(pattern, add_prefix, section_content)
        content = content[:marker_pos] + new_section + content[end_pos:]
    
    # Write the updated content
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    return changes

if __name__ == "__main__":
    print("="*80)
    print("ADDING URL PREFIXES TO ROUTES")
    print("="*80)
    
    changes = add_url_prefixes()
    
    print(f"\n✓ Added prefixes to {changes} routes")
    print("✓ URL structure now matches original blueprint organization")
    print("="*80)
