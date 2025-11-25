"""
Check and create cost control user if needed
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from extensions import db
from models import User
from utils.constants import Roles
from werkzeug.security import generate_password_hash

def setup_cost_control_user():
    from app import create_app
    app = create_app()
    
    with app.app_context():
        print("\n" + "="*60)
        print("Checking Cost Control User")
        print("="*60)
        
        # Check for existing cost control user
        cost_control_user = User.query.filter_by(role=Roles.HQ_COST_CONTROL).first()
        
        if cost_control_user:
            print(f"\n✓ Cost Control user found:")
            print(f"   ID: {cost_control_user.id}")
            print(f"   Email: {cost_control_user.email}")
            print(f"   Name: {cost_control_user.name}")
            print(f"   Role: {cost_control_user.role}")
        else:
            print("\n⚠ No Cost Control user found. Creating one...")
            
            # Create cost control user
            new_user = User(
                email="costcontrol@sammya.com",
                password_hash=generate_password_hash("CostControl@123"),
                name="Cost Control Manager",
                role=Roles.HQ_COST_CONTROL,
                is_verified=True
            )
            
            db.session.add(new_user)
            db.session.commit()
            
            print(f"\n✓ Created Cost Control user:")
            print(f"   Email: costcontrol@sammya.com")
            print(f"   Password: CostControl@123")
            print(f"   Name: Cost Control Manager")
            print(f"   Role: {Roles.HQ_COST_CONTROL}")
        
        # List all HQ users
        print("\n" + "-"*60)
        print("All HQ-level users:")
        print("-"*60)
        hq_roles = [
            Roles.SUPER_HQ, 
            Roles.HQ_COST_CONTROL,
            Roles.HQ_FINANCE,
            Roles.HQ_HR,
            Roles.HQ_PROCUREMENT
        ]
        
        hq_users = User.query.filter(User.role.in_(hq_roles)).all()
        for user in hq_users:
            print(f"   {user.role:25} - {user.email:30} - {user.name}")
        
        print("="*60 + "\n")

if __name__ == '__main__':
    setup_cost_control_user()
