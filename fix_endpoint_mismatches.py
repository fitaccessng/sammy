"""
Fix endpoint mismatches between templates and actual route definitions
"""
import os
import re

# Map of incorrect endpoints to correct ones
ENDPOINT_FIXES = {
    # HR endpoints
    "url_for('hr.staff')": "url_for('hr.staff_list')",
    'url_for("hr.staff")': 'url_for("hr.staff_list")',
    
    # Add more as discovered
}

def fix_file(filepath):
    """Fix endpoint mismatches in a file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes = []
        
        for wrong, correct in ENDPOINT_FIXES.items():
            if wrong in content:
                content = content.replace(wrong, correct)
                changes.append(f"{wrong} -> {correct}")
        
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return changes
        
        return None
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return None

def main():
    # Fix templates
    templates_dir = 'templates'
    total_files = 0
    total_changes = 0
    
    print("Fixing templates...")
    for root, dirs, files in os.walk(templates_dir):
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(root, file)
                changes = fix_file(filepath)
                if changes:
                    total_files += 1
                    total_changes += len(changes)
                    print(f"\n{filepath}:")
                    for change in changes:
                        print(f"  - {change}")
    
    # Fix app.py
    print("\nFixing app.py...")
    changes = fix_file('app.py')
    if changes:
        total_files += 1
        total_changes += len(changes)
        print(f"\napp.py:")
        for change in changes:
            print(f"  - {change}")
    
    print(f"\n{'='*60}")
    print(f"Fixed {total_files} files with {total_changes} changes")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()
