"""
Comprehensive workflow test
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from extensions import db
from models import PurchaseOrder, ApprovalWorkflow, WorkflowStep, User
from app import create_app

app = create_app()

with app.app_context():
    print("\n" + "="*80)
    print("COMPREHENSIVE WORKFLOW TEST")
    print("="*80)
    
    # Test 1: Users
    print("\n=== USERS ===")
    users = User.query.all()
    for u in users:
        print(f"ID {u.id}: {u.name} - Role: {u.role}")
    
    # Test 2: Purchase Orders
    print("\n=== PURCHASE ORDERS ===")
    pos = PurchaseOrder.query.all()
    print(f"Total POs: {len(pos)}\n")
    
    for po in pos:
        print(f"PO ID: {po.id}")
        print(f"  Number: {po.order_number}")
        print(f"  Status: {po.status}")
        print(f"  Workflow ID: {po.workflow_id}")
        print(f"  Requested By: {po.requested_by}")
        
        # Test workflow access
        if po.workflow_id:
            try:
                workflow = po.workflow
                print(f"  Workflow: {workflow.reference_number if workflow else 'NOT FOUND'}")
                
                if workflow:
                    try:
                        steps = workflow.steps
                        print(f"  Steps: {len(steps) if steps else 0}")
                        for step in steps:
                            print(f"    - {step.step_name}: {step.status}")
                    except Exception as e:
                        print(f"  ERROR accessing steps: {e}")
            except Exception as e:
                print(f"  ERROR accessing workflow: {e}")
        print()
    
    # Test 3: Check what Procurement user would see
    print("\n=== PROCUREMENT USER VIEW (ID 3) ===")
    procurement_user = User.query.get(3)
    if procurement_user:
        print(f"User: {procurement_user.name} ({procurement_user.role})")
        my_pos = PurchaseOrder.query.filter_by(requested_by=procurement_user.id).all()
        print(f"My POs: {len(my_pos)}")
        for po in my_pos:
            print(f"  - {po.order_number}: {po.status}")
            if po.workflow:
                print(f"    Workflow Status: {po.workflow.overall_status}")
    
    # Test 4: Check what Cost Control would see
    print("\n=== COST CONTROL USER VIEW (ID 4) ===")
    cc_user = User.query.get(4)
    if cc_user:
        print(f"User: {cc_user.name} ({cc_user.role})")
        
        # Simulate get_pending_approvals_for_user
        workflows = ApprovalWorkflow.query.join(
            WorkflowStep, WorkflowStep.workflow_id == ApprovalWorkflow.id
        ).filter(
            ApprovalWorkflow.overall_status.in_(['pending', 'in_progress']),
            WorkflowStep.required_role == cc_user.role,
            WorkflowStep.status == 'pending'
        ).all()
        
        print(f"Pending Workflows: {len(workflows)}")
        for wf in workflows:
            if wf.workflow_type == 'purchase_order':
                po = PurchaseOrder.query.get(wf.reference_id)
                if po:
                    print(f"  - {wf.reference_number}: ₦{po.total_amount:,.2f}")
    
    print("\n" + "="*80)
