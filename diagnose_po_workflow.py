"""
Diagnose PO and Workflow relationship issues
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
    print("PURCHASE ORDERS vs WORKFLOWS DIAGNOSIS")
    print("="*80)
    
    print("\n=== PURCHASE ORDERS TABLE ===")
    pos = PurchaseOrder.query.all()
    for po in pos:
        print(f"PO Table ID: {po.id}")
        print(f"  Order Number: {po.order_number}")
        print(f"  Status: {po.status}")
        print(f"  Workflow ID: {po.workflow_id}")
        print(f"  Amount: ₦{po.total_amount:,.2f}")
        print()
    
    print("\n=== APPROVAL WORKFLOWS TABLE ===")
    workflows = ApprovalWorkflow.query.filter_by(workflow_type='purchase_order').all()
    for w in workflows:
        print(f"Workflow ID: {w.id}")
        print(f"  Reference Number: {w.reference_number}")
        print(f"  Reference ID (points to PO): {w.reference_id}")
        print(f"  Status: {w.overall_status}")
        print(f"  Current Stage: {w.current_stage}")
        
        # Try to find the PO
        po = PurchaseOrder.query.get(w.reference_id)
        if po:
            print(f"  ✓ PO FOUND: {po.order_number}")
        else:
            print(f"  ✗ PO NOT FOUND! (looking for ID {w.reference_id})")
        print()
    
    print("\n=== WORKFLOW STEPS (Pending Cost Control) ===")
    steps = WorkflowStep.query.filter_by(
        required_role='hq_cost_control',
        status='pending'
    ).all()
    
    for step in steps:
        workflow = ApprovalWorkflow.query.get(step.workflow_id)
        print(f"Step in Workflow {step.workflow_id}")
        if workflow:
            print(f"  Workflow Ref: {workflow.reference_number}")
            print(f"  Points to PO ID: {workflow.reference_id}")
            po = PurchaseOrder.query.get(workflow.reference_id)
            if po:
                print(f"  ✓ Will show PO: {po.order_number} (₦{po.total_amount:,.2f})")
            else:
                print(f"  ✗ Will NOT show - PO {workflow.reference_id} doesn't exist")
        print()
    
    print("\n=== SUMMARY ===")
    print(f"Total POs in database: {len(pos)}")
    print(f"Total PO workflows: {len(workflows)}")
    print(f"Workflows pending Cost Control: {len(steps)}")
    
    # Find orphaned workflows
    orphaned = []
    for w in workflows:
        if not PurchaseOrder.query.get(w.reference_id):
            orphaned.append(w)
    
    if orphaned:
        print(f"\n⚠️ PROBLEM: {len(orphaned)} workflows point to non-existent POs!")
        print("These workflows should be deleted or fixed:")
        for w in orphaned:
            print(f"  - Workflow {w.id} points to PO ID {w.reference_id} which doesn't exist")
    
    print("\n" + "="*80)
