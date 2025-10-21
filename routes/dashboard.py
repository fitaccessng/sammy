from flask import Blueprint, render_template
from utils.decorators import role_required
from utils.constants import Roles

dashboard_bp = Blueprint('dashboard', __name__)

# Super HQ Dashboard
@dashboard_bp.route('/super-hq')
@role_required([Roles.SUPER_HQ])
def super_hq_dashboard():
    from datetime import datetime
    from models import Role, Employee, Project, PurchaseOrder
    
    # Get summary data for the dashboard
    current_datetime = datetime.now()
    
    # Calculate summary statistics
    summary = {
        'total_roles': Role.query.count(),
        'total_employees': Employee.query.count(),
        'total_projects': Project.query.count(),
        'total_orders': PurchaseOrder.query.count()
    }
    
    return render_template('admin/index.html', 
                         current_datetime=current_datetime,
                         summary=summary)

# HQ Dashboards
@dashboard_bp.route('/hq-finance')
@role_required([Roles.SUPER_HQ, Roles.HQ_FINANCE])
def hq_finance_dashboard():
    return render_template('finance/index.html')

@dashboard_bp.route('/hq-hr')
@role_required([Roles.SUPER_HQ, Roles.HQ_HR])
def hq_hr_dashboard():
    return render_template('hr/index.html')

@dashboard_bp.route('/hq-procurement')
@role_required([Roles.SUPER_HQ, Roles.HQ_PROCUREMENT])
def hq_procurement_dashboard():
    return render_template('procurement/index.html')

@dashboard_bp.route('/hq-quarry')
@role_required([Roles.SUPER_HQ, Roles.HQ_QUARRY])
def hq_quarry_dashboard():
    return render_template('quarry/hq_quarry.html')

@dashboard_bp.route('/hq-project')
@role_required([Roles.SUPER_HQ, Roles.HQ_PROJECT])
def hq_project_dashboard():
    return render_template('project/index.html')

# Staff Dashboards
@dashboard_bp.route('/finance-staff')
@role_required([Roles.SUPER_HQ, Roles.HQ_FINANCE, Roles.FINANCE_STAFF])
def finance_staff_dashboard():
    return render_template('finance/index.html')

@dashboard_bp.route('/hr-staff')
@role_required([Roles.SUPER_HQ, Roles.HQ_HR, Roles.HR_STAFF])
def hr_staff_dashboard():
    return render_template('staff/hr_staff.html')

@dashboard_bp.route('/procurement-staff')
@role_required([Roles.SUPER_HQ, Roles.HQ_PROCUREMENT, Roles.PROCUREMENT_STAFF])
def procurement_staff_dashboard():
    return render_template('staff/procurement_staff.html')

@dashboard_bp.route('/quarry-staff')
@role_required([Roles.SUPER_HQ, Roles.HQ_QUARRY, Roles.QUARRY_STAFF])
def quarry_staff_dashboard():
    return render_template('staff/quarry_staff.html')

@dashboard_bp.route('/project-staff')
@role_required([Roles.SUPER_HQ, Roles.HQ_PROJECT, Roles.PROJECT_STAFF])
def project_staff_dashboard():
    return render_template('staff/project_staff.html')