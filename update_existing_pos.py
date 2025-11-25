"""
Update existing purchase orders to link them to the current procurement user
"""
from app import create_app
from extensions import db
from models import PurchaseOrder, User
from utils.constants import Roles

app = create_app()

with app.app_context():
    # Find the procurement user (hq_procurement role)
    procurement_user = User.query.filter_by(role=Roles.HQ_PROCUREMENT).first()
    
    if not procurement_user:
        print("❌ No procurement user found!")
        print("Available users:")
        for user in User.query.all():
            print(f"  - {user.name} ({user.email}) - role: {user.role}")
    else:
        print(f"✓ Found procurement user: {procurement_user.name} (ID: {procurement_user.id})")
        
        # Find all POs without a requested_by value
        unlinked_pos = PurchaseOrder.query.filter(
            (PurchaseOrder.requested_by == None) | (PurchaseOrder.requested_by == 0)
        ).all()
        
        if not unlinked_pos:
            print("\n✓ All purchase orders are already linked to users!")
        else:
            print(f"\nFound {len(unlinked_pos)} purchase orders without a user link")
            print("\nUpdating purchase orders...")
            
            for po in unlinked_pos:
                po.requested_by = procurement_user.id
                print(f"  ✓ Linked {po.order_number} to {procurement_user.name}")
            
            db.session.commit()
            print(f"\n✅ Successfully updated {len(unlinked_pos)} purchase orders!")
            
        # Verify the update
        print("\n" + "="*60)
        print("VERIFICATION:")
        print("="*60)
        all_pos = PurchaseOrder.query.all()
        for po in all_pos:
            if po.requested_by:
                user = User.query.get(po.requested_by)
                print(f"✓ {po.order_number} -> Requested by: {user.name if user else 'Unknown'}")
            else:
                print(f"✗ {po.order_number} -> No user linked")
