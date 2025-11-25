"""Create workflows for existing POs"""
from app import create_app
from extensions import db
from models import PurchaseOrder, ApprovalWorkflow, User
from utils.workflow import create_approval_workflow, send_approval_notification

app = create_app()

with app.app_context():
    # Get all POs without workflows
    pos_without_workflow = PurchaseOrder.query.filter(
        (PurchaseOrder.workflow_id == None) | (PurchaseOrder.workflow_id == 0)
    ).all()
    
    if not pos_without_workflow:
        print("✅ All POs already have workflows!")
    else:
        print(f"Found {len(pos_without_workflow)} POs without workflows\n")
        
        for po in pos_without_workflow:
            print(f"Creating workflow for {po.order_number}...")
            
            # Get the user who requested it
            initiator_id = po.requested_by if po.requested_by else 3  # Default to procurement user
            
            # Create workflow
            workflow = create_approval_workflow(
                workflow_type='purchase_order',
                reference_id=po.id,
                reference_number=po.order_number,
                initiated_by=initiator_id,
                total_amount=po.total_amount,
                description=f"Purchase Order from {po.supplier_name}",
                priority='normal'
            )
            
            # Link workflow to PO
            po.workflow_id = workflow.id
            po.status = 'Pending_Cost_Control'
            
            print(f"  ✓ Created workflow ID: {workflow.id}")
            print(f"  ✓ Updated PO status to: {po.status}")
            
            # Send notification to Cost Control
            try:
                send_approval_notification(
                    workflow_id=workflow.id,
                    step_order=1,
                    action='request'
                )
                print(f"  ✓ Sent notification to Cost Control")
            except Exception as e:
                print(f"  ⚠ Notification error: {e}")
        
        db.session.commit()
        print(f"\n✅ Successfully created workflows for {len(pos_without_workflow)} POs!")
        
        # Verify
        print("\n" + "=" * 60)
        print("VERIFICATION:")
        print("=" * 60)
        for po in PurchaseOrder.query.all():
            print(f"{po.order_number}: workflow_id={po.workflow_id}, status={po.status}")
