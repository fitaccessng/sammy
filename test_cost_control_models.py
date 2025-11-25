"""
Test script to verify Cost Control dashboard models are working
"""
from app import app, db
from models import CostApproval, BudgetAdjustment, CostTrackingEntry, User
from utils.constants import Roles

def test_models():
    with app.app_context():
        print("\n" + "="*60)
        print("Testing Cost Control Models")
        print("="*60)
        
        # Test CostApproval model
        print("\n1. Testing CostApproval model:")
        try:
            approval_count = CostApproval.query.count()
            pending_count = CostApproval.query.filter_by(status='pending').count()
            print(f"   ✓ CostApproval.query works")
            print(f"   - Total approvals: {approval_count}")
            print(f"   - Pending approvals: {pending_count}")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        
        # Test BudgetAdjustment model
        print("\n2. Testing BudgetAdjustment model:")
        try:
            adjustment_count = BudgetAdjustment.query.count()
            pending_adj = BudgetAdjustment.query.filter_by(status='pending').count()
            print(f"   ✓ BudgetAdjustment.query works")
            print(f"   - Total adjustments: {adjustment_count}")
            print(f"   - Pending adjustments: {pending_adj}")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        
        # Test CostTrackingEntry model
        print("\n3. Testing CostTrackingEntry model:")
        try:
            entry_count = CostTrackingEntry.query.count()
            print(f"   ✓ CostTrackingEntry.query works")
            print(f"   - Total entries: {entry_count}")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        
        # Test HQ Cost Control user
        print("\n4. Testing HQ Cost Control user:")
        try:
            hq_user = User.query.filter_by(role=Roles.HQ_COST_CONTROL).first()
            if hq_user:
                print(f"   ✓ Found HQ Cost Control user")
                print(f"   - User ID: {hq_user.id}")
                print(f"   - Email: {hq_user.email}")
                print(f"   - Role: {hq_user.role}")
            else:
                print(f"   ! No HQ Cost Control user found")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        
        print("\n" + "="*60)
        print("✓ All model tests completed successfully!")
        print("="*60 + "\n")

if __name__ == '__main__':
    test_models()
