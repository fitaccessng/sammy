"""Check cost categories and projects in database"""
from app import create_app
from extensions import db
from models import CostCategory, Project

app = create_app()

with app.app_context():
    # Check cost categories
    categories = CostCategory.query.all()
    print(f"\nCost Categories: {len(categories)}")
    for cat in categories:
        print(f"  - ID: {cat.id}, Name: {cat.name}, Project: {cat.project_id}, Type: {cat.type}")
    
    # Check active projects
    active_projects = Project.query.filter_by(status='In Progress').all()
    print(f"\nActive Projects (In Progress): {len(active_projects)}")
    for proj in active_projects:
        print(f"  - ID: {proj.id}, Name: {proj.name}, Status: {proj.status}")
    
    # Check all projects
    all_projects = Project.query.all()
    print(f"\nAll Projects: {len(all_projects)}")
    for proj in all_projects:
        print(f"  - ID: {proj.id}, Name: {proj.name}, Status: {proj.status}")
