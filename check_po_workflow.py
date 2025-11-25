"""Check PO and Workflow data"""
from app import create_app
from extensions import db
from models import PurchaseOrder, ApprovalWorkflow, WorkflowStep, User

app = create_app()

with app.app_context():
    print("=" * 60)
    print("PURCHASE ORDERS:")
    print("=" * 60)
    pos = PurchaseOrder.query.all()
    for po in pos:
        print(f"\nPO: {po.order_number}")
        print(f"  Status: {po.status}")
        print(f"  Workflow ID: {po.workflow_id}")
        print(f"  Requested By: {po.requested_by}")
        if po.requested_by:
            user = User.query.get(po.requested_by)
            print(f"  Requested By User: {user.name if user else 'Unknown'} ({user.role if user else 'N/A'})")
    
    print("\n" + "=" * 60)
    print("APPROVAL WORKFLOWS:")
    print("=" * 60)
    workflows = ApprovalWorkflow.query.filter_by(workflow_type='purchase_order').all()
    for wf in workflows:
        print(f"\nWorkflow ID: {wf.id}")
        print(f"  Reference: {wf.reference_number}")
        print(f"  Status: {wf.overall_status}")
        print(f"  Current Stage: {wf.current_stage}")
        
        steps = WorkflowStep.query.filter_by(workflow_id=wf.id).order_by(WorkflowStep.step_order).all()
        print(f"  Steps:")
        for step in steps:
            print(f"    {step.step_order}. {step.step_name} ({step.required_role}) - Status: {step.status}")
    
    print("\n" + "=" * 60)
    print("USERS:")
    print("=" * 60)
    users = User.query.all()
    for user in users:
        print(f"{user.id}. {user.name} - Role: {user.role}")
