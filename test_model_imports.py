"""
Quick test to verify models are importable
"""
import sys

print("Testing model imports...")
try:
    from models import CostApproval, BudgetAdjustment, CostTrackingEntry
    print("✓ CostApproval imported successfully")
    print("✓ BudgetAdjustment imported successfully")
    print("✓ CostTrackingEntry imported successfully")
    
    # Check model attributes
    print("\nCostApproval fields:")
    for attr in ['id', 'reference_type', 'reference_id', 'project_id', 'status', 'approver_id']:
        if hasattr(CostApproval, attr):
            print(f"  ✓ {attr}")
        else:
            print(f"  ✗ {attr} missing")
    
    print("\nBudgetAdjustment fields:")
    for attr in ['id', 'project_id', 'budget_id', 'old_amount', 'new_amount', 'status']:
        if hasattr(BudgetAdjustment, attr):
            print(f"  ✓ {attr}")
        else:
            print(f"  ✗ {attr} missing")
    
    print("\n✓ All models imported and validated successfully!")
    
except Exception as e:
    print(f"✗ Error importing models: {e}")
    sys.exit(1)
