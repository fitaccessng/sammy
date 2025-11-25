"""
Check workflow step names
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from extensions import db
from models import WorkflowStep
from app import create_app

app = create_app()

with app.app_context():
    print("\n" + "="*60)
    print("WORKFLOW STEPS IN DATABASE")
    print("="*60)
    
    steps = WorkflowStep.query.all()
    print(f"\nTotal steps: {len(steps)}\n")
    
    for s in steps:
        print(f"Workflow {s.workflow_id}")
        print(f"  Step Name: '{s.step_name}'")
        print(f"  Required Role: '{s.required_role}'")
        print(f"  Status: {s.status}")
        print()
    
    print("="*60)
