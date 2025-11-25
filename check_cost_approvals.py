"""
Check cost approvals in database
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from extensions import db
from models import CostApproval, CostTrackingEntry, Project, User
from app import create_app

app = create_app()

with app.app_context():
    print("\n" + "="*60)
    print("COST APPROVALS CHECK")
    print("="*60)
    
    # Check CostApproval records
    approvals = CostApproval.query.all()
    print(f"\n📋 Total Cost Approvals: {len(approvals)}")
    
    if approvals:
        for approval in approvals:
            project = Project.query.get(approval.project_id) if approval.project_id else None
            print(f"\nApproval ID: {approval.id}")
            print(f"  Project: {project.name if project else 'N/A'}")
            print(f"  Type: {approval.reference_type}")
            print(f"  Description: {approval.description}")
            print(f"  Amount: ₦{approval.amount:,.2f}")
            print(f"  Status: {approval.status}")
            print(f"  Required Role: {approval.required_role}")
            print(f"  Created: {approval.created_at}")
    else:
        print("\n✓ No cost approvals in database (this is normal)")
    
    # Check Cost Tracking Entries
    entries = CostTrackingEntry.query.all()
    print(f"\n📊 Total Cost Tracking Entries: {len(entries)}")
    
    if entries:
        pending = [e for e in entries if e.status == 'pending']
        print(f"  Pending: {len(pending)}")
        print(f"  Approved: {len([e for e in entries if e.status == 'approved'])}")
        
        if pending:
            print("\n  Pending Entries:")
            for entry in pending[:5]:  # Show first 5
                project = Project.query.get(entry.project_id) if entry.project_id else None
                print(f"    - {entry.description} (₦{entry.actual_cost:,.2f}) - {project.name if project else 'N/A'}")
    
    print("\n" + "="*60)
