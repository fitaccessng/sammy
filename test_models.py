from app import create_app
from extensions import db
from models import Project, BOQItem, ProjectActivity, ProjectDocument

app = create_app()

with app.app_context():
    try:
        print("Testing basic project query...")
        project = Project.query.first()
        if project:
            print(f"Found project: {project.name} (ID: {project.id})")
        else:
            print("No projects found in database")
            
        print("\nTesting BOQItem query...")
        boq_count = BOQItem.query.count()
        print(f"BOQItem count: {boq_count}")
        
        print("\nTesting ProjectActivity query...")
        activity_count = ProjectActivity.query.count()
        print(f"ProjectActivity count: {activity_count}")
        
        print("\nTesting ProjectDocument query...")
        doc_count = ProjectDocument.query.count()
        print(f"ProjectDocument count: {doc_count}")
        
        print("\nAll model tests passed!")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()