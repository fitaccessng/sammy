#!/usr/bin/env python3
"""Script to update template references in admin routes"""

# Read the file
with open('routes/admin.py', 'r') as f:
    content = f.read()

# Replace all instances
content = content.replace("admin/add_project.html", "admin/create_project.html")

# Write back to file
with open('routes/admin.py', 'w') as f:
    f.write(content)

print("✓ Updated all template references from add_project.html to create_project.html")