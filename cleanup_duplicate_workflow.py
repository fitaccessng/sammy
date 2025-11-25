"""
Clean up duplicate workflow
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from extensions import db
from models import ApprovalWorkflow, WorkflowStep, PurchaseOrder
from app import create_app

app = create_app()

with app.app_context():
    print("\n" + "="*60)
    print("CLEANING UP DUPLICATE WORKFLOW")
    print("="*60)
    
    # Find PO 1
    po1 = PurchaseOrder.query.get(1)
    print(f"\nPO ID 1: {po1.order_number}")
    print(f"  Linked to Workflow: {po1.workflow_id}")
    
    # Find workflows pointing to PO 1
    workflows = ApprovalWorkflow.query.filter_by(
        workflow_type='purchase_order',
        reference_id=1
    ).all()
    
    print(f"\n  Workflows pointing to PO 1: {len(workflows)}")
    for w in workflows:
        print(f"    - Workflow ID {w.id}")
    
    # Delete the orphaned workflow (the one not linked from PO)
    for w in workflows:
        if w.id != po1.workflow_id:
            print(f"\n  Deleting orphaned Workflow {w.id}...")
            
            # Delete workflow steps first
            steps = WorkflowStep.query.filter_by(workflow_id=w.id).all()
            for step in steps:
                db.session.delete(step)
            print(f"    Deleted {len(steps)} workflow steps")
            
            # Delete workflow
            db.session.delete(w)
            print(f"    Deleted workflow {w.id}")
    
    db.session.commit()
    
    print("\n✅ Cleanup complete!")
    
    # Verify
    print("\n" + "="*60)
    print("VERIFICATION")
    print("="*60)
    
    remaining_workflows = ApprovalWorkflow.query.filter_by(workflow_type='purchase_order').all()
    print(f"\nRemaining PO workflows: {len(remaining_workflows)}")
    
    for w in remaining_workflows:
        po = PurchaseOrder.query.get(w.reference_id)
        print(f"  Workflow {w.id} -> PO {w.reference_id} ({po.order_number if po else 'NOT FOUND'})")
        if po:
            print(f"    PO links back to Workflow: {po.workflow_id} {'✓' if po.workflow_id == w.id else '✗'}")
    
    print("\n" + "="*60)
