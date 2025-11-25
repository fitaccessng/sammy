"""
Check all purchase orders in the database
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from extensions import db
from models import PurchaseOrder, ApprovalWorkflow, WorkflowStep, User
from app import create_app

app = create_app()

with app.app_context():
    print("\n" + "="*60)
    print("ALL PURCHASE ORDERS IN DATABASE")
    print("="*60)
    
    # Get all POs
    all_pos = PurchaseOrder.query.all()
    print(f"\n📦 Total Purchase Orders: {len(all_pos)}")
    
    if all_pos:
        for po in all_pos:
            print(f"\n{'='*60}")
            print(f"PO Number: {po.order_number}")
            print(f"  ID: {po.id}")
            print(f"  Supplier: {po.supplier_name}")
            print(f"  Total Amount: ₦{po.total_amount:,.2f}")
            print(f"  Status: {po.status}")
            print(f"  Created: {po.created_at}")
            print(f"  Requested By: {po.requested_by}")
            if po.requested_by:
                user = User.query.get(po.requested_by)
                if user:
                    print(f"  Requested By User: {user.full_name} ({user.role})")
            print(f"  Workflow ID: {po.workflow_id}")
            
            # Check if workflow exists
            if po.workflow_id:
                workflow = ApprovalWorkflow.query.get(po.workflow_id)
                if workflow:
                    print(f"  Workflow Status: {workflow.overall_status}")
                    print(f"  Current Stage: {workflow.current_stage}")
                    
                    # Check steps
                    steps = WorkflowStep.query.filter_by(workflow_id=workflow.id).all()
                    print(f"  Workflow Steps:")
                    for step in steps:
                        print(f"    {step.step_order}. {step.step_name} ({step.required_role}) - {step.status}")
                else:
                    print(f"  ⚠️ Workflow ID {po.workflow_id} not found in database!")
            else:
                print(f"  ⚠️ NO WORKFLOW - This PO won't show in approval queues!")
    
    print("\n" + "="*60)
    print("WORKFLOWS BY TYPE")
    print("="*60)
    
    po_workflows = ApprovalWorkflow.query.filter_by(workflow_type='purchase_order').all()
    print(f"\nPurchase Order Workflows: {len(po_workflows)}")
    for wf in po_workflows:
        print(f"  - Workflow {wf.id}: {wf.reference_number} (Status: {wf.overall_status}, Stage: {wf.current_stage})")
    
    print("\n" + "="*60)
    print("COST CONTROL PENDING APPROVALS")
    print("="*60)
    
    # Get workflows pending at Cost Control stage
    pending_cc = ApprovalWorkflow.query.filter_by(
        workflow_type='purchase_order',
        current_stage='hq_cost_control',
        overall_status='pending'
    ).all()
    
    print(f"\nPOs Pending Cost Control Approval: {len(pending_cc)}")
    for wf in pending_cc:
        po = PurchaseOrder.query.get(wf.reference_id)
        if po:
            print(f"  ✓ {wf.reference_number} - ₦{po.total_amount:,.2f} - {po.supplier_name}")
        else:
            print(f"  ⚠️ {wf.reference_number} - PO not found!")
    
    print("\n" + "="*60)
