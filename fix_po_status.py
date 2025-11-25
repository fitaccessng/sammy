"""
Fix PO status inconsistency
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from extensions import db
from models import PurchaseOrder, ApprovalWorkflow, WorkflowStep
from app import create_app

app = create_app()

with app.app_context():
    print("\n" + "="*60)
    print("FIXING PO STATUS")
    print("="*60)
    
    # Fix PO 1
    po1 = PurchaseOrder.query.get(1)
    if po1:
        workflow = ApprovalWorkflow.query.get(po1.workflow_id)
        if workflow:
            print(f"\nPO 1: {po1.order_number}")
            print(f"  Current Status: {po1.status}")
            print(f"  Workflow Status: {workflow.overall_status}")
            print(f"  Workflow Stage: {workflow.current_stage}")
            
            # Check steps
            cc_step = WorkflowStep.query.filter_by(
                workflow_id=workflow.id,
                step_order=1
            ).first()
            
            if cc_step and cc_step.status == 'approved':
                print(f"  Cost Control step is approved")
                print(f"  Updating PO status to Pending_Finance...")
                po1.status = 'Pending_Finance'
                workflow.current_stage = 'hq_finance'
                db.session.commit()
                print(f"  ✓ Fixed!")
    
    print("\n" + "="*60)
