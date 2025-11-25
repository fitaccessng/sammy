"""
Clear sample/test cost control data
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from extensions import db
from models import CostApproval, CostTrackingEntry, BudgetAdjustment
from app import create_app

app = create_app()

with app.app_context():
    print("\n" + "="*60)
    print("CLEARING SAMPLE COST CONTROL DATA")
    print("="*60)
    
    # Count before deletion
    approval_count = CostApproval.query.count()
    entry_count = CostTrackingEntry.query.count()
    adjustment_count = BudgetAdjustment.query.count()
    
    print(f"\n📊 Current Records:")
    print(f"  Cost Approvals: {approval_count}")
    print(f"  Cost Tracking Entries: {entry_count}")
    print(f"  Budget Adjustments: {adjustment_count}")
    
    if approval_count == 0 and entry_count == 0 and adjustment_count == 0:
        print("\n✓ Database is already clean - no sample data found")
    else:
        confirm = input("\n⚠ Are you sure you want to delete ALL cost control data? (yes/no): ")
        
        if confirm.lower() == 'yes':
            # Delete all cost approvals
            CostApproval.query.delete()
            print(f"✓ Deleted {approval_count} cost approvals")
            
            # Delete all cost tracking entries
            CostTrackingEntry.query.delete()
            print(f"✓ Deleted {entry_count} cost tracking entries")
            
            # Delete all budget adjustments
            BudgetAdjustment.query.delete()
            print(f"✓ Deleted {adjustment_count} budget adjustments")
            
            db.session.commit()
            
            print("\n✅ All sample cost control data has been cleared")
            print("   The system is now ready for real cost control operations")
        else:
            print("\n❌ Operation cancelled - no data was deleted")
    
    print("\n" + "="*60)
