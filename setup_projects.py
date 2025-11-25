"""
Check existing projects and create some if needed
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from extensions import db
from models import Project, User
from datetime import datetime, timezone

def setup_projects():
    from app import create_app
    app = create_app()
    
    with app.app_context():
        print("\n" + "="*60)
        print("Checking Projects")
        print("="*60)
        
        projects = Project.query.all()
        print(f"Total projects in database: {len(projects)}")
        
        if projects:
            for p in projects:
                print(f"  - {p.name} (Status: {p.status})")
        
        # Update existing projects to "In Progress" or create new ones
        active_count = Project.query.filter_by(status='In Progress').count()
        
        if active_count == 0:
            print("\nNo active projects. Updating/creating projects...")
            
            if projects:
                # Update existing projects
                for project in projects[:5]:
                    project.status = 'In Progress'
                    print(f"  ✓ Updated {project.name} to 'In Progress'")
                db.session.commit()
            else:
                # Create new sample projects
                user = User.query.first()
                if not user:
                    print("  ⚠ No users found. Cannot create projects.")
                    return
                
                project_names = [
                    "Road Construction Project - Lagos",
                    "Bridge Building Project - Abuja",
                    "Housing Development - Port Harcourt",
                    "Commercial Complex - Kano",
                    "Industrial Park - Ibadan"
                ]
                
                for name in project_names:
                    project = Project(
                        name=name,
                        description=f"Construction project: {name}",
                        location=name.split('-')[-1].strip(),
                        status='In Progress',
                        start_date=datetime.now(timezone.utc),
                        created_by=user.id
                    )
                    db.session.add(project)
                    print(f"  ✓ Created {name}")
                
                db.session.commit()
        
        active_projects = Project.query.filter_by(status='In Progress').all()
        print(f"\n✓ Active projects ready: {len(active_projects)}")
        print("="*60 + "\n")

if __name__ == '__main__':
    setup_projects()
