"""
Create sample cost control data for testing
"""
import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from extensions import db
from models import (
    CostTrackingEntry, CostApproval, BudgetAdjustment, 
    Project, Budget, User
)
from utils.constants import Roles
from datetime import datetime, timedelta, timezone
import random

def create_sample_data():
    # Import app after models are loaded
    from app import create_app
    app = create_app()
    
    with app.app_context():
        print("\n" + "="*60)
        print("Creating Sample Cost Control Data")
        print("="*60)
        
        # Get existing projects and user
        projects = Project.query.filter_by(status='In Progress').all()
        if not projects:
            print("⚠ No active projects found. Please create projects first.")
            return
        
        user = User.query.filter_by(role=Roles.HQ_COST_CONTROL).first()
        if not user:
            user = User.query.first()
        
        if not user:
            print("⚠ No users found in database.")
            return
        
        print(f"✓ Found {len(projects)} active projects")
        print(f"✓ Using user: {user.email}")
        
        # Create sample cost tracking entries
        cost_types = ['material', 'labor', 'equipment', 'overhead']
        descriptions = [
            'Cement and building materials',
            'Construction labor costs',
            'Equipment rental - excavator',
            'Site supervision and management',
            'Steel reinforcement bars',
            'Electrical wiring and fixtures',
            'Plumbing materials and installation',
            'Transportation and logistics',
            'Safety equipment and PPE',
            'Quality control testing'
        ]
        
        entries_created = 0
        for project in projects[:5]:  # Sample for first 5 projects
            # Create 5-10 entries per project
            num_entries = random.randint(5, 10)
            
            for i in range(num_entries):
                planned = random.uniform(100000, 5000000)
                # Create some variance (80-120% of planned)
                actual = planned * random.uniform(0.8, 1.2)
                
                entry = CostTrackingEntry(
                    project_id=project.id,
                    entry_date=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 90)),
                    description=random.choice(descriptions),
                    planned_cost=planned,
                    actual_cost=actual,
                    cost_type=random.choice(cost_types),
                    quantity=random.uniform(1, 100),
                    unit='unit',
                    unit_cost=random.uniform(1000, 50000),
                    status=random.choice(['pending', 'approved', 'approved', 'approved']),  # More approved
                    created_by=user.id
                )
                
                entry.calculate_variance()
                db.session.add(entry)
                entries_created += 1
        
        db.session.commit()
        print(f"✓ Created {entries_created} cost tracking entries")
        
        # Create sample budget data if missing
        budgets_created = 0
        for project in projects:
            existing_budget = Budget.query.filter_by(project_id=project.id).first()
            if not existing_budget:
                allocated = random.uniform(10000000, 50000000)
                spent = allocated * random.uniform(0.3, 0.9)
                
                budget = Budget(
                    project_id=project.id,
                    category='General Budget',
                    allocated_amount=allocated,
                    spent_amount=spent
                )
                db.session.add(budget)
                budgets_created += 1
        
        if budgets_created > 0:
            db.session.commit()
            print(f"✓ Created {budgets_created} project budgets")
        
        # Create some pending approvals
        approvals_created = 0
        high_variance_entries = CostTrackingEntry.query.filter(
            CostTrackingEntry.variance_percentage > 10
        ).limit(5).all()
        
        for entry in high_variance_entries:
            existing = CostApproval.query.filter_by(
                reference_type='cost_entry',
                reference_id=entry.id
            ).first()
            
            if not existing:
                approval = CostApproval(
                    reference_type='cost_entry',
                    reference_id=entry.id,
                    project_id=entry.project_id,
                    required_role=Roles.HQ_COST_CONTROL,
                    amount=entry.actual_cost,
                    description=f"Cost variance approval needed: {entry.description}",
                    status='pending',
                    created_by=user.id
                )
                db.session.add(approval)
                approvals_created += 1
        
        if approvals_created > 0:
            db.session.commit()
            print(f"✓ Created {approvals_created} pending approvals")
        
        # Create sample budget adjustments
        adjustments_created = 0
        for project in projects[:3]:
            budget = Budget.query.filter_by(project_id=project.id).first()
            if budget:
                old_amount = budget.allocated_amount
                adjustment_amount = old_amount * random.uniform(0.05, 0.15)
                new_amount = old_amount + adjustment_amount
                
                adjustment = BudgetAdjustment(
                    project_id=project.id,
                    budget_id=budget.id,
                    category=budget.category,
                    old_amount=old_amount,
                    new_amount=new_amount,
                    adjustment_amount=adjustment_amount,
                    adjustment_type='increase',
                    reason='Additional funding required due to scope changes',
                    impact_analysis='This increase will cover additional material costs',
                    status='pending',
                    requested_by=user.id
                )
                db.session.add(adjustment)
                adjustments_created += 1
        
        if adjustments_created > 0:
            db.session.commit()
            print(f"✓ Created {adjustments_created} budget adjustments")
        
        # Display summary
        print("\n" + "-"*60)
        print("Summary:")
        print(f"  Total Cost Entries: {CostTrackingEntry.query.count()}")
        print(f"  Pending Approvals: {CostApproval.query.filter_by(status='pending').count()}")
        print(f"  Pending Adjustments: {BudgetAdjustment.query.filter_by(status='pending').count()}")
        print(f"  Total Projects with Budgets: {Budget.query.count()}")
        print("-"*60 + "\n")
        
        print("✓ Sample data creation completed successfully!")
        print("="*60 + "\n")

if __name__ == '__main__':
    create_sample_data()
