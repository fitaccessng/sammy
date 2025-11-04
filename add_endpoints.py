"""
Script to add unique endpoint names to routes to avoid conflicts
This allows url_for() in templates to work correctly
"""
import re

def add_unique_endpoints():
    """Add unique endpoint names to all routes"""
    
    with open('app.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    changes = 0
    current_section = 'unknown'
    section_map = {
        'ROUTES FROM MAIN.PY': 'main',
        'ROUTES FROM FILES.PY': 'files',
        'ROUTES FROM DASHBOARD.PY': 'dashboard',
        'ROUTES FROM COST_CONTROL.PY': 'cost_control',
        'ROUTES FROM HQ.PY': 'hq',
        'ROUTES FROM PROCUREMENT.PY': 'procurement',
        'ROUTES FROM QUARRY.PY': 'quarry',
        'ROUTES FROM FINANCE.PY': 'finance',
        'ROUTES FROM HR.PY': 'hr',
        'ROUTES FROM ADMIN.PY': 'admin',
        'ROUTES FROM ADMIN_CLEAN.PY': 'admin',
        'ROUTES FROM PROJECT.PY': 'project'
    }
    
    new_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check if we're entering a new section
        for marker, prefix in section_map.items():
            if marker in line:
                current_section = prefix
                break
        
        # Check if line is a route decorator without endpoint
        if '@app.route(' in line and 'endpoint=' not in line:
            # Get the next non-decorator line to find function name
            j = i + 1
            while j < len(lines) and (lines[j].strip().startswith('@') or not lines[j].strip()):
                j += 1
            
            if j < len(lines):
                func_match = re.search(r'def\s+(\w+)\s*\(', lines[j])
                if func_match:
                    func_name = func_match.group(1)
                    endpoint_name = f"{current_section}.{func_name}" if current_section != 'main' else func_name
                    
                    # Modify the route decorator to include endpoint
                    # Handle both single and multi-line decorators
                    if line.rstrip().endswith(')'):
                        # Single line: @app.route('/path')
                        line = line.rstrip()[:-1] + f", endpoint='{endpoint_name}')\n"
                    else:
                        # Multi-line decorator - add endpoint before the closing )
                        # Find the line with closing )
                        k = i
                        while k < len(lines) and ')' not in lines[k]:
                            k += 1
                        if k < len(lines):
                            lines[k] = lines[k].replace(')', f", endpoint='{endpoint_name}')")
                    
                    changes += 1
        
        new_lines.append(line)
        i += 1
    
    # Write the updated content
    with open('app.py', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    return changes

if __name__ == "__main__":
    print("="*80)
    print("ADDING UNIQUE ENDPOINT NAMES TO ROUTES")
    print("="*80)
    
    changes = add_unique_endpoints()
    
    print(f"\n✓ Added endpoint names to {changes} routes")
    print("✓ Templates can now use url_for('prefix.route_name')")
    print("="*80)
