"""Create sample budget data for HR Operations project"""
from app import create_app
from extensions import db
from models import Budget, Project
from datetime import datetime

app = create_app()

# Budget allocation for HR Operations project
BUDGET_DATA = [
    {'category': 'material', 'allocated': 500000.00},
    {'category': 'labor', 'allocated': 1000000.00},
    {'category': 'equipment', 'allocated': 300000.00},
    {'category': 'subcontractor', 'allocated': 200000.00},
    {'category': 'overhead', 'allocated': 150000.00},
    {'category': 'transportation', 'allocated': 100000.00},
    {'category': 'professional_services', 'allocated': 250000.00},
    {'category': 'safety', 'allocated': 75000.00},
    {'category': 'utilities', 'allocated': 125000.00},
    {'category': 'miscellaneous', 'allocated': 50000.00},
]

with app.app_context():
    # Get HR Operations project
    project = Project.query.filter_by(name='HR Operations').first()
    
    if not project:
        print("❌ HR Operations project not found!")
        exit(1)
    
    print(f"Creating budgets for: {project.name} (ID: {project.id})")
    
    # Check existing budgets
    existing_budgets = Budget.query.filter_by(project_id=project.id).all()
    if existing_budgets:
        print(f"\n⚠️  Found {len(existing_budgets)} existing budgets. Deleting...")
        for budget in existing_budgets:
            db.session.delete(budget)
        db.session.commit()
    
    # Create new budgets
    print("\nCreating budgets:")
    total_allocated = 0
    
    for budget_data in BUDGET_DATA:
        budget = Budget(
            project_id=project.id,
            category=budget_data['category'],
            allocated_amount=budget_data['allocated'],
            spent_amount=0.0,
            status='active',
            fiscal_year=datetime.now().year,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.session.add(budget)
        total_allocated += budget_data['allocated']
        print(f"  ✓ {budget_data['category']}: ₦{budget_data['allocated']:,.2f}")
    
    db.session.commit()
    
    print(f"\n{'='*60}")
    print(f"✅ Successfully created {len(BUDGET_DATA)} budget categories")
    print(f"Total Budget Allocated: ₦{total_allocated:,.2f}")
    print(f"{'='*60}")
    
    # Verify
    all_budgets = Budget.query.filter_by(project_id=project.id).all()
    print(f"\nVerification: {len(all_budgets)} budgets in database")
    for budget in all_budgets:
        print(f"  - {budget.category}: ₦{budget.allocated_amount:,.2f} allocated, "
              f"₦{budget.spent_amount:,.2f} spent, ₦{budget.remaining_amount:,.2f} remaining")
