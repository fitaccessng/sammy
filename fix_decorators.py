"""
Fix decorator names in consolidated app.py
Replace all @*app.route with @app.route
"""
import re

filepath = r"c:\Users\Nwakanma\Desktop\Fitaccess\sammy\app.py"

# Read the file
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace all *app.route decorators with app.route
patterns = [
    (r'@mainapp\.route', '@app.route'),
    (r'@filesapp\.route', '@app.route'),
    (r'@dashboardapp\.route', '@app.route'),
    (r'@cost_controlapp\.route', '@app.route'),
    (r'@hqapp\.route', '@app.route'),
    (r'@procurementapp\.route', '@app.route'),
    (r'@quarryapp\.route', '@app.route'),
    (r'@financeapp\.route', '@app.route'),
    (r'@hrapp\.route', '@app.route'),
    (r'@adminapp\.route', '@app.route'),
    (r'@projectapp\.route', '@app.route'),
]

for pattern, replacement in patterns:
    content = re.sub(pattern, replacement, content)

# Write back
with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ Fixed all decorator names")
