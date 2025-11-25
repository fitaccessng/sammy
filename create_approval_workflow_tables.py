"""
Create approval workflow, notification, and audit log tables
"""
from extensions import db
from models import ApprovalWorkflow, WorkflowStep, Notification, AuditLog

def create_tables():
    from app import create_app
    app = create_app()
    
    with app.app_context():
        # Create the new tables
        print("Creating approval workflow tables...")
        
        # Create tables
        db.create_all()
        
        print("✅ Tables created successfully!")
        
        # Verify tables
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        
        tables = ['approval_workflows', 'workflow_steps', 'notifications', 'audit_logs']
        for table in tables:
            if table in inspector.get_table_names():
                print(f"✅ {table} table exists")
                # Show columns
                columns = inspector.get_columns(table)
                print(f"   Columns: {', '.join([col['name'] for col in columns])}")
            else:
                print(f"❌ {table} table NOT found")
        
        return True

if __name__ == '__main__':
    create_tables()
