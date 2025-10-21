from app import create_app
from flask import url_for

app = create_app()
with app.app_context():
    # Test all the routes used in the staff details template
    try:
        routes_to_test = [
            ('hr.assign_role', {'staff_id': 1}),
            ('hr.leave_management', {}),
            ('hr.tasks', {}),
            ('hr.attendance', {}),
            ('project.documents', {}),
            ('hr.analytics', {}),
            ('files.upload_file', {}),
            ('hr.import_staff', {}),
            ('hr.add_staff_payroll', {'staff_id': 1}),
            ('hr.edit_staff', {'staff_id': 1})
        ]
        
        print("Testing route endpoints:")
        for route, kwargs in routes_to_test:
            try:
                url = url_for(route, **kwargs)
                print(f"✅ {route}: {url}")
            except Exception as e:
                print(f"❌ {route}: {e}")
                
    except Exception as e:
        print(f"Error testing routes: {e}")