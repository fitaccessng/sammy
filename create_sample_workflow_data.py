"""
Create sample approval workflow data for testing
"""
from app import create_app
from extensions import db
from models import (ApprovalWorkflow, WorkflowStep, Notification, PurchaseOrder, 
                    PurchaseOrderLineItem, User, Supplier, Project, PayrollApproval, Employee)
from datetime import datetime, timedelta
from utils.workflow import create_approval_workflow
import random

def create_sample_workflows():
    """Create sample purchase orders and payroll approvals with workflows"""
    app = create_app()
    
    with app.app_context():
        print("Creating sample approval workflow data...")
        
        # Get users
        procurement_user = User.query.filter_by(role='Procurement Manager').first()
        cost_control_user = User.query.filter_by(role='Cost Control Manager').first()
        finance_user = User.query.filter_by(role='Finance Manager').first()
        hr_user = User.query.filter_by(role='HR Manager').first()
        admin_user = User.query.filter_by(role='Super HQ').first()
        
        if not procurement_user:
            print("Creating sample users...")
            procurement_user = User(
                name="John Procurement",
                email="procurement@test.com",
                role="Procurement Manager",
                phone="08012345678"
            )
            procurement_user.set_password("password123")
            db.session.add(procurement_user)
        
        if not cost_control_user:
            cost_control_user = User(
                name="Sarah CostControl",
                email="costcontrol@test.com",
                role="Cost Control Manager",
                phone="08012345679"
            )
            cost_control_user.set_password("password123")
            db.session.add(cost_control_user)
        
        if not finance_user:
            finance_user = User(
                name="Michael Finance",
                email="finance@test.com",
                role="Finance Manager",
                phone="08012345680"
            )
            finance_user.set_password("password123")
            db.session.add(finance_user)
        
        if not hr_user:
            hr_user = User(
                name="Lisa HR",
                email="hr@test.com",
                role="HR Manager",
                phone="08012345681"
            )
            hr_user.set_password("password123")
            db.session.add(hr_user)
        
        if not admin_user:
            admin_user = User(
                name="Admin User",
                email="admin@test.com",
                role="Super HQ",
                phone="08012345682"
            )
            admin_user.set_password("password123")
            db.session.add(admin_user)
        
        db.session.commit()
        print(f"Users ready: Procurement={procurement_user.id}, CostControl={cost_control_user.id}, Finance={finance_user.id}")
        
        # Get or create supplier
        supplier = Supplier.query.first()
        if not supplier:
            print("Creating sample supplier...")
            supplier = Supplier(
                name="ABC Suppliers Ltd",
                email="info@abcsuppliers.com",
                phone="08098765432",
                address="123 Industrial Avenue, Lagos",
                contact_person="Mr. Supplier",
                payment_terms="Net 30",
                rating=4.5
            )
            db.session.add(supplier)
            db.session.commit()
        
        # Get or create project
        project = Project.query.first()
        if not project:
            print("Creating sample project...")
            project = Project(
                name="Sample Construction Project",
                location="Lagos",
                start_date=datetime.now() - timedelta(days=30),
                end_date=datetime.now() + timedelta(days=180),
                budget=50000000.00,
                status="Active",
                description="Sample project for testing"
            )
            db.session.add(project)
            db.session.commit()
        
        # Create PO #1 - Pending at Cost Control
        print("\nCreating PO #1 - Pending Cost Control Approval...")
        po1 = PurchaseOrder(
            po_number=f"PO-{datetime.now().strftime('%Y%m%d')}-001",
            supplier_id=supplier.id,
            project_id=project.id,
            requested_by=procurement_user.id,
            order_date=datetime.now() - timedelta(days=2),
            delivery_date=datetime.now() + timedelta(days=14),
            total_amount=1250000.00,
            status="Pending_Cost_Control",
            priority="high",
            delivery_address=project.location,
            notes="Urgent materials needed for foundation work",
            approval_status="pending"
        )
        db.session.add(po1)
        db.session.flush()
        
        # Add line items to PO1
        item1 = PurchaseOrderLineItem(
            purchase_order_id=po1.id,
            item_description="Portland Cement (50kg bags)",
            quantity=500,
            unit_price=2500.00,
            total_price=1250000.00
        )
        db.session.add(item1)
        
        # Create workflow for PO1
        workflow1 = create_approval_workflow(
            workflow_type='purchase_order',
            reference_id=po1.id,
            reference_number=po1.po_number,
            initiated_by=procurement_user.id,
            total_amount=po1.total_amount,
            priority='high'
        )
        po1.workflow_id = workflow1.id
        
        # Create PO #2 - Pending at Finance
        print("Creating PO #2 - Approved by Cost Control, Pending Finance...")
        po2 = PurchaseOrder(
            po_number=f"PO-{datetime.now().strftime('%Y%m%d')}-002",
            supplier_id=supplier.id,
            project_id=project.id,
            requested_by=procurement_user.id,
            order_date=datetime.now() - timedelta(days=5),
            delivery_date=datetime.now() + timedelta(days=10),
            total_amount=3500000.00,
            status="Pending_Finance",
            priority="urgent",
            delivery_address=project.location,
            notes="Critical equipment for site setup",
            approval_status="pending",
            cost_control_approved_by=cost_control_user.id,
            cost_control_approved_at=datetime.now() - timedelta(days=1),
            cost_control_comments="Approved. Prices verified and within budget."
        )
        db.session.add(po2)
        db.session.flush()
        
        # Add line items to PO2
        item2 = PurchaseOrderLineItem(
            purchase_order_id=po2.id,
            item_description="Concrete Mixer - Industrial Grade",
            quantity=2,
            unit_price=1750000.00,
            total_price=3500000.00
        )
        db.session.add(item2)
        
        # Create workflow for PO2
        workflow2 = create_approval_workflow(
            workflow_type='purchase_order',
            reference_id=po2.id,
            reference_number=po2.po_number,
            initiated_by=procurement_user.id,
            total_amount=po2.total_amount,
            priority='urgent'
        )
        po2.workflow_id = workflow2.id
        
        # Update workflow to reflect Cost Control approval
        step1 = WorkflowStep.query.filter_by(
            workflow_id=workflow2.id,
            step_name='Cost Control Approval'
        ).first()
        if step1:
            step1.status = 'approved'
            step1.approver_id = cost_control_user.id
            step1.action_taken_at = datetime.now() - timedelta(days=1)
            step1.comments = "Approved. Prices verified and within budget."
        
        workflow2.current_stage = 'Finance Approval'
        workflow2.overall_status = 'in_progress'
        
        # Create PO #3 - Fully Approved
        print("Creating PO #3 - Fully Approved...")
        po3 = PurchaseOrder(
            po_number=f"PO-{datetime.now().strftime('%Y%m%d')}-003",
            supplier_id=supplier.id,
            project_id=project.id,
            requested_by=procurement_user.id,
            order_date=datetime.now() - timedelta(days=10),
            delivery_date=datetime.now() + timedelta(days=5),
            total_amount=850000.00,
            status="Approved",
            priority="normal",
            delivery_address=project.location,
            notes="Standard materials order",
            approval_status="approved",
            cost_control_approved_by=cost_control_user.id,
            cost_control_approved_at=datetime.now() - timedelta(days=8),
            cost_control_comments="Approved.",
            finance_approved_by=finance_user.id,
            finance_approved_at=datetime.now() - timedelta(days=7),
            finance_comments="Approved. Funds released."
        )
        db.session.add(po3)
        db.session.flush()
        
        item3 = PurchaseOrderLineItem(
            purchase_order_id=po3.id,
            item_description="Reinforcement Steel Bars (12mm)",
            quantity=1000,
            unit_price=850.00,
            total_price=850000.00
        )
        db.session.add(item3)
        
        workflow3 = create_approval_workflow(
            workflow_type='purchase_order',
            reference_id=po3.id,
            reference_number=po3.po_number,
            initiated_by=procurement_user.id,
            total_amount=po3.total_amount,
            priority='normal'
        )
        po3.workflow_id = workflow3.id
        
        # Mark all steps as approved
        for step in workflow3.steps:
            step.status = 'approved'
            if 'Cost Control' in step.step_name:
                step.approver_id = cost_control_user.id
                step.action_taken_at = datetime.now() - timedelta(days=8)
                step.comments = "Approved."
            elif 'Finance' in step.step_name:
                step.approver_id = finance_user.id
                step.action_taken_at = datetime.now() - timedelta(days=7)
                step.comments = "Approved. Funds released."
        
        workflow3.current_stage = 'Completed'
        workflow3.overall_status = 'completed'
        workflow3.completed_at = datetime.now() - timedelta(days=7)
        
        # Create PO #4 - Rejected by Finance
        print("Creating PO #4 - Rejected by Finance...")
        po4 = PurchaseOrder(
            po_number=f"PO-{datetime.now().strftime('%Y%m%d')}-004",
            supplier_id=supplier.id,
            requested_by=procurement_user.id,
            order_date=datetime.now() - timedelta(days=6),
            delivery_date=datetime.now() + timedelta(days=20),
            total_amount=5000000.00,
            status="Rejected",
            priority="high",
            delivery_address=project.location,
            notes="Large equipment purchase",
            approval_status="rejected"
        )
        db.session.add(po4)
        db.session.flush()
        
        item4 = PurchaseOrderLineItem(
            purchase_order_id=po4.id,
            item_description="Tower Crane",
            quantity=1,
            unit_price=5000000.00,
            total_price=5000000.00
        )
        db.session.add(item4)
        
        workflow4 = create_approval_workflow(
            workflow_type='purchase_order',
            reference_id=po4.id,
            reference_number=po4.po_number,
            initiated_by=procurement_user.id,
            total_amount=po4.total_amount,
            priority='high'
        )
        po4.workflow_id = workflow4.id
        
        # Mark Cost Control as approved, Finance as rejected
        for step in workflow4.steps:
            if 'Cost Control' in step.step_name:
                step.status = 'approved'
                step.approver_id = cost_control_user.id
                step.action_taken_at = datetime.now() - timedelta(days=4)
                step.comments = "Approved with concerns about budget."
            elif 'Finance' in step.step_name:
                step.status = 'rejected'
                step.approver_id = finance_user.id
                step.action_taken_at = datetime.now() - timedelta(days=2)
                step.comments = "Rejected - Exceeds current budget allocation. Please resubmit with revised amount or seek budget adjustment."
        
        workflow4.current_stage = 'Finance Approval'
        workflow4.overall_status = 'rejected'
        workflow4.completed_at = datetime.now() - timedelta(days=2)
        
        # Create Payroll #1 - Pending Finance Approval
        print("\nCreating Payroll #1 - Pending Finance Approval...")
        
        # Get or create employee
        employee = Employee.query.first()
        if not employee:
            employee = Employee(
                first_name="Test",
                last_name="Employee",
                email="employee@test.com",
                phone="08011111111",
                department="Construction",
                position="Site Engineer",
                hire_date=datetime.now() - timedelta(days=365),
                salary=250000.00,
                status="Active"
            )
            db.session.add(employee)
            db.session.flush()
        
        payroll1 = PayrollApproval(
            month=datetime.now().strftime('%B'),
            year=datetime.now().year,
            total_amount=5000000.00,
            employee_count=20,
            prepared_by=hr_user.id,
            prepared_at=datetime.now() - timedelta(days=1),
            status="pending_finance",
            notes="Monthly payroll for all departments"
        )
        db.session.add(payroll1)
        db.session.flush()
        
        # Create workflow for payroll
        workflow5 = create_approval_workflow(
            workflow_type='payroll',
            reference_id=payroll1.id,
            reference_number=f"PAYROLL-{payroll1.year}-{payroll1.month}",
            initiated_by=hr_user.id,
            total_amount=payroll1.total_amount,
            priority='high'
        )
        payroll1.workflow_id = workflow5.id
        
        db.session.commit()
        
        print("\n" + "="*60)
        print("Sample data created successfully!")
        print("="*60)
        print(f"\nPurchase Orders:")
        print(f"  - {po1.po_number}: ₦{po1.total_amount:,.2f} (Pending Cost Control)")
        print(f"  - {po2.po_number}: ₦{po2.total_amount:,.2f} (Pending Finance)")
        print(f"  - {po3.po_number}: ₦{po3.total_amount:,.2f} (Approved)")
        print(f"  - {po4.po_number}: ₦{po4.total_amount:,.2f} (Rejected)")
        print(f"\nPayroll Approvals:")
        print(f"  - {payroll1.month} {payroll1.year}: ₦{payroll1.total_amount:,.2f} (Pending Finance)")
        print(f"\nTest Users Created:")
        print(f"  - Procurement: {procurement_user.email} / password123")
        print(f"  - Cost Control: {cost_control_user.email} / password123")
        print(f"  - Finance: {finance_user.email} / password123")
        print(f"  - HR: {hr_user.email} / password123")
        print(f"  - Admin: {admin_user.email} / password123")
        print("\n" + "="*60)
        print("You can now test the approval workflows!")
        print("="*60)

if __name__ == '__main__':
    create_sample_workflows()
