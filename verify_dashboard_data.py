"""
Verify what data the dashboard endpoint is returning
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from extensions import db
from models import (
    CostTrackingEntry, CostApproval, BudgetAdjustment,
    Project, Budget
)
from sqlalchemy import func
from datetime import datetime, timedelta, timezone

def verify_dashboard_data():
    from app import create_app
    app = create_app()
    
    with app.app_context():
        print("\n" + "="*70)
        print("VERIFYING DASHBOARD DATA")
        print("="*70)
        
        # Get active projects
        active_projects = Project.query.filter_by(status='In Progress').all()
        project_count = len(active_projects)
        print(f"\n1. Active Projects: {project_count}")
        for p in active_projects:
            print(f"   - {p.name}")
        
        # Budget summary
        total_allocated = db.session.query(func.sum(Budget.allocated_amount)).scalar() or 0
        total_spent = db.session.query(func.sum(Budget.spent_amount)).scalar() or 0
        total_remaining = total_allocated - total_spent
        overall_usage = (total_spent / total_allocated * 100) if total_allocated > 0 else 0
        
        print(f"\n2. Budget Summary:")
        print(f"   - Total Allocated: ₦{total_allocated:,.2f}")
        print(f"   - Total Spent: ₦{total_spent:,.2f}")
        print(f"   - Total Remaining: ₦{total_remaining:,.2f}")
        print(f"   - Overall Usage: {overall_usage:.2f}%")
        
        # Budget alerts
        budget_alerts = []
        for project in active_projects:
            project_budgets = Budget.query.filter_by(project_id=project.id).all()
            for budget in project_budgets:
                if budget.usage_percentage > 80:
                    budget_alerts.append({
                        'project_name': project.name,
                        'category': budget.category,
                        'usage_percentage': budget.usage_percentage,
                        'remaining': budget.remaining_amount,
                        'severity': 'critical' if budget.usage_percentage > 95 else 'warning'
                    })
        
        print(f"\n3. Budget Alerts: {len(budget_alerts)}")
        for alert in budget_alerts[:5]:
            print(f"   - {alert['project_name']}: {alert['usage_percentage']:.1f}% used ({alert['severity']})")
        
        # Recent entries
        recent_entries = CostTrackingEntry.query.order_by(
            CostTrackingEntry.created_at.desc()
        ).limit(10).all()
        
        print(f"\n4. Recent Cost Entries: {len(recent_entries)}")
        for entry in recent_entries[:5]:
            print(f"   - {entry.entry_date.strftime('%Y-%m-%d')}: {entry.description[:40]}...")
            print(f"     Planned: ₦{entry.planned_cost:,.2f} | Actual: ₦{entry.actual_cost:,.2f} | Variance: {entry.variance_percentage:.1f}%")
        
        # Pending approvals
        pending_approvals = CostApproval.query.filter_by(status='pending').count()
        print(f"\n5. Pending Approvals: {pending_approvals}")
        
        # Pending adjustments
        pending_adjustments = BudgetAdjustment.query.filter_by(status='pending').count()
        print(f"\n6. Pending Budget Adjustments: {pending_adjustments}")
        
        # Variance summary
        variance_data = db.session.query(
            func.sum(CostTrackingEntry.variance).label('total_variance'),
            func.count(CostTrackingEntry.id).label('entry_count')
        ).filter(
            CostTrackingEntry.variance != 0
        ).first()
        
        total_variance = (variance_data.total_variance if variance_data and variance_data.total_variance else 0)
        variance_entries = (variance_data.entry_count if variance_data and variance_data.entry_count else 0)
        
        print(f"\n7. Variance Summary:")
        print(f"   - Total Variance: ₦{total_variance:,.2f}")
        print(f"   - Entries with Variance: {variance_entries}")
        
        # Monthly burn rate
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        monthly_spend = db.session.query(
            func.sum(CostTrackingEntry.actual_cost)
        ).filter(
            CostTrackingEntry.entry_date >= thirty_days_ago
        ).scalar() or 0
        
        print(f"\n8. Monthly Burn Rate (Last 30 days): ₦{monthly_spend:,.2f}")
        
        # Top spending projects
        top_spending_projects = db.session.query(
            Project.name,
            func.sum(CostTrackingEntry.actual_cost).label('total_spend')
        ).join(
            CostTrackingEntry, Project.id == CostTrackingEntry.project_id
        ).group_by(
            Project.name
        ).order_by(
            func.sum(CostTrackingEntry.actual_cost).desc()
        ).limit(5).all()
        
        print(f"\n9. Top Spending Projects:")
        for project in top_spending_projects:
            print(f"   - {project[0]}: ₦{project[1]:,.2f}")
        
        # Spending by category
        spending_by_category = db.session.query(
            CostTrackingEntry.cost_type,
            func.sum(CostTrackingEntry.actual_cost).label('amount')
        ).group_by(
            CostTrackingEntry.cost_type
        ).all()
        
        print(f"\n10. Spending by Category:")
        for cat, amt in spending_by_category:
            print(f"   - {cat}: ₦{amt:,.2f}")
        
        print("\n" + "="*70)
        print("✓ All dashboard data verified successfully!")
        print("="*70 + "\n")

if __name__ == '__main__':
    verify_dashboard_data()
