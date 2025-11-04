"""
Script to update all template url_for() calls to remove blueprint prefixes
Changes url_for('blueprint.route') to url_for('route')
"""
import os
import re

def update_template_file(filepath):
    """Update url_for calls in a single template file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Pattern to match url_for('blueprint.route_name')
        # Matches: url_for('main.login'), url_for('admin.dashboard'), etc.
        patterns = [
            (r"url_for\('main\.(\w+)'", r"url_for('\1'"),
            (r"url_for\('admin\.(\w+)'", r"url_for('\1'"),
            (r"url_for\('finance\.(\w+)'", r"url_for('\1'"),
            (r"url_for\('hr\.(\w+)'", r"url_for('\1'"),
            (r"url_for\('procurement\.(\w+)'", r"url_for('\1'"),
            (r"url_for\('quarry\.(\w+)'", r"url_for('\1'"),
            (r"url_for\('project\.(\w+)'", r"url_for('\1'"),
            (r"url_for\('files\.(\w+)'", r"url_for('\1'"),
            (r"url_for\('dashboard\.(\w+)'", r"url_for('\1'"),
            (r"url_for\('cost_control\.(\w+)'", r"url_for('\1'"),
            (r'url_for\("main\.(\w+)"', r'url_for("\1"'),
            (r'url_for\("admin\.(\w+)"', r'url_for("\1"'),
            (r'url_for\("finance\.(\w+)"', r'url_for("\1"'),
            (r'url_for\("hr\.(\w+)"', r'url_for("\1"'),
            (r'url_for\("procurement\.(\w+)"', r'url_for("\1"'),
            (r'url_for\("quarry\.(\w+)"', r'url_for("\1"'),
            (r'url_for\("project\.(\w+)"', r'url_for("\1"'),
            (r'url_for\("files\.(\w+)"', r'url_for("\1"'),
            (r'url_for\("dashboard\.(\w+)"', r'url_for("\1"'),
            (r'url_for\("cost_control\.(\w+)"', r'url_for("\1"'),
        ]
        
        changes_made = 0
        for pattern, replacement in patterns:
            new_content, count = re.subn(pattern, replacement, content)
            if count > 0:
                changes_made += count
                content = new_content
        
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return changes_made
        
        return 0
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return 0

def update_all_templates(templates_dir):
    """Recursively update all HTML template files"""
    total_changes = 0
    files_updated = 0
    
    for root, dirs, files in os.walk(templates_dir):
        for file in files:
            if file.endswith(('.html', '.htm', '.jinja2', '.j2')):
                filepath = os.path.join(root, file)
                changes = update_template_file(filepath)
                if changes > 0:
                    files_updated += 1
                    total_changes += changes
                    print(f"✓ Updated {filepath}: {changes} changes")
    
    return files_updated, total_changes

if __name__ == "__main__":
    base_path = r"c:\Users\Nwakanma\Desktop\Fitaccess\sammy"
    templates_path = os.path.join(base_path, "templates")
    
    print("="*80)
    print("UPDATING TEMPLATE URL_FOR() CALLS")
    print("="*80)
    print(f"Templates directory: {templates_path}")
    print("\nProcessing templates...\n")
    
    files_updated, total_changes = update_all_templates(templates_path)
    
    print("\n" + "="*80)
    print(f"✓ COMPLETED")
    print(f"✓ Files updated: {files_updated}")
    print(f"✓ Total changes: {total_changes}")
    print("="*80)
