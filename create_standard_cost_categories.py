"""Create standard cost categories for existing projects"""
from app import create_app
from extensions import db
from models import CostCategory, Project

app = create_app()

# Standard cost category types
STANDARD_CATEGORIES = [
    {'name': 'Direct Materials', 'type': 'material'},
    {'name': 'Direct Labor', 'type': 'labor'},
    {'name': 'Equipment & Machinery', 'type': 'equipment'},
    {'name': 'Subcontractor Services', 'type': 'subcontractor'},
    {'name': 'Overhead Costs', 'type': 'overhead'},
    {'name': 'Transportation & Logistics', 'type': 'transportation'},
    {'name': 'Professional Services', 'type': 'professional_services'},
    {'name': 'Safety & Compliance', 'type': 'safety'},
    {'name': 'Utilities', 'type': 'utilities'},
    {'name': 'Miscellaneous', 'type': 'miscellaneous'}
]

with app.app_context():
    projects = Project.query.all()
    
    print(f"Found {len(projects)} project(s)")
    
    for project in projects:
        print(f"\nCreating categories for project: {project.name} (ID: {project.id})")
        
        # Check if project already has categories
        existing_categories = CostCategory.query.filter_by(project_id=project.id).count()
        if existing_categories > 0:
            print(f"  ⚠️  Project already has {existing_categories} categories. Skipping...")
            continue
        
        # Create standard categories for this project
        for cat_data in STANDARD_CATEGORIES:
            category = CostCategory(
                project_id=project.id,
                name=cat_data['name'],
                type=cat_data['type']
            )
            db.session.add(category)
            print(f"  ✓ Created: {cat_data['name']} ({cat_data['type']})")
        
        db.session.commit()
        print(f"  Successfully created {len(STANDARD_CATEGORIES)} categories")
    
    # Summary
    total_categories = CostCategory.query.count()
    print(f"\n{'='*60}")
    print(f"Total cost categories in database: {total_categories}")
    print(f"{'='*60}")
    
    # Show all categories
    all_categories = CostCategory.query.all()
    for cat in all_categories:
        project = Project.query.get(cat.project_id)
        print(f"  - {cat.name} ({cat.type}) - Project: {project.name if project else 'Unknown'}")
