from app import create_app
from models import Budget
from datetime import datetime

app = create_app()

with app.app_context():
    budgets = Budget.query.all()
    print(f'\n=== Total Budgets in Database: {len(budgets)} ===\n')
    
    if budgets:
        for budget in budgets:
            print(f'ID: {budget.id}')
            print(f'Name: {budget.budget_name}')
            print(f'Code: {budget.budget_code}')
            print(f'Fiscal Year: {budget.fiscal_year}')
            print(f'Status: {budget.status}')
            print(f'Total Budget: ₦{budget.total_budget:,.2f}')
            print(f'Created: {budget.created_at}')
            print('-' * 50)
    else:
        print('No budgets found in database!')
    
    # Check the current year filter
    current_year = datetime.now().year
    current_year_budgets = Budget.query.filter_by(fiscal_year=current_year).all()
    print(f'\n=== Budgets for Fiscal Year {current_year}: {len(current_year_budgets)} ===\n')
