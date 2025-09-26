from flask import Blueprint, render_template, redirect, url_for, session, flash, request, current_app
from utils.decorators import role_required
from utils.constants import Roles
from werkzeug.utils import secure_filename
from extensions import db
import os
import uuid
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, FileField, SelectField, DateField
from wtforms.validators import DataRequired, Length
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from mimetypes import guess_type
from datetime import datetime, timedelta
from flask_login import login_required, current_user
from flask_mail import Message
from models import User, Employee, Project, db, Attendance, Equipment, PurchaseOrder, Payroll, Checkbook, Expense, Task, Audit, Inspection, PayrollHistory, EmployeeSalaryHistory, PayrollTransaction, MonthlyPayrollSummary

# Import blueprints
from .hr import hr_bp
from .project import project_bp
from .finance import finance_bp
from .files import files_bp

csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address)

admin_bp = Blueprint('admin', __name__)

# Register blueprints (to be done in app.py or wsgi.py)
# app.register_blueprint(admin_bp)
# app.register_blueprint(hr_bp)
# app.register_blueprint(projects_bp)
# app.register_blueprint(finance_bp)
# app.register_blueprint(files_bp)

@admin_bp.route('/')
@role_required([Roles.SUPER_HQ])
def index():
    try:
        # Key Metrics
        # Active projects change: compare current count to last month's
        today = datetime.today()
        first_of_month = today.replace(day=1)
        last_month = first_of_month - timedelta(days=1)
        first_of_last_month = last_month.replace(day=1)
        last_of_last_month = last_month.replace(day=last_month.day)
        current_active = Project.query.filter_by(status='Active').count()
        last_month_active = Project.query.filter(Project.status=='Active', Project.created_at >= first_of_last_month, Project.created_at <= last_of_last_month).count()
        active_projects = {
            "count": current_active,
            "change": current_active - last_month_active
        }
        # Attendance percent: percent of present employees today
        today_date = today.date()
        attendance_records = Attendance.query.filter_by(date=today_date).all()
        present = sum(1 for a in attendance_records if a.status == 'Present')
        total_attendance = len(attendance_records) if attendance_records else Employee.query.count()
        attendance_percent = int((present / total_attendance) * 100) if total_attendance else 0
        total_workers = {
            "count": Employee.query.count(),
            "attendance_percent": attendance_percent
        }
        equipment_status = {
            "available": Equipment.query.filter_by(status='Active').count(),
            "total": Equipment.query.count(),
            "maintenance": Equipment.query.filter_by(status='Maintenance').count()
        }
        pending_orders = {
            "count": PurchaseOrder.query.filter_by(status='Pending').count(),
            "urgent": PurchaseOrder.query.filter_by(status='Urgent').count()
        }

        # Project Progress
        project_progress = [
            {
                "name": p.name,
                "percent": int(p.progress or 0),
                "color": "bg-green-500" if p.progress and p.progress > 70 else "bg-blue-500" if p.progress and p.progress > 50 else "bg-yellow-500" if p.progress and p.progress > 30 else "bg-red-500"
            }
            for p in Project.query.all()
        ]

        # Recent Activity (example, adjust for your models)
        recent_activity = [
            {
                "bg": "bg-blue-100",
                "icon": "bx-task",
                "icon_color": "text-blue-600",
                "title": "Task Completed",
                "description": "Foundation work for Tower B",
                "time": "2 hours ago"
            },
            # TODO: Add more from your models
        ]

        # Quick Actions
        quick_actions = [
            {
                "url": url_for('admin.add_project'),
                "bg": "bg-blue-50",
                "text": "text-blue-700",
                "hover": "bg-blue-100",
                "icon": "bx-plus-circle",
                "label": "New Project"
            },
            {
                "url": url_for('admin.add_employee'),
                "bg": "bg-green-50",
                "text": "text-green-700",
                "hover": "bg-green-100",
                "icon": "bx-user-plus",
                "label": "Add Worker"
            },
            {
                "url": url_for('admin.dashboard_upload'),
                "bg": "bg-yellow-50",
                "text": "text-yellow-700",
                "hover": "bg-yellow-100",
                "icon": "bx-file",
                "label": "Upload File"
            },
            {
                "url": url_for('admin.payroll'),
                "bg": "bg-purple-50",
                "text": "text-purple-700",
                "hover": "bg-purple-100",
                "icon": "bx-credit-card",
                "label": "Payroll"
            },
            {
                "url": url_for('admin.orders'),
                "bg": "bg-red-50",
                "text": "text-red-700",
                "hover": "bg-red-100",
                "icon": "bx-cart",
                "label": "Orders"
            }
        ]

        # Financial Overview
        financial_overview = [
            {
                "label": "Bank Balance",
                "value": f"${Checkbook.query.with_entities(db.func.sum(Checkbook.balance)).scalar() or 0:,.2f}"
            },
            {
                "label": "Monthly Expenses",
                "value": f"${Expense.query.with_entities(db.func.sum(Expense.amount)).scalar() or 0:,.2f}"
            },
            {
                "label": "Pending Payroll",
                "value": f"${Payroll.query.filter_by(status='Generated').with_entities(db.func.sum(Payroll.amount)).scalar() or 0:,.2f}"
            },
            {
                "label": "Outstanding Payments",
                "value": f"${PurchaseOrder.query.filter_by(status='Pending').with_entities(db.func.sum(PurchaseOrder.total_amount)).scalar() or 0:,.2f}"
            }
        ]

        return render_template(
            'admin/index.html',
            active_projects=active_projects,
            total_workers=total_workers,
            equipment_status=equipment_status,
            pending_orders=pending_orders,
            project_progress=project_progress,
            recent_activity=recent_activity,
            quick_actions=quick_actions,
            financial_overview=financial_overview
        )
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'danger')
        # Pass default values for all expected template variables
        return render_template(
            'admin/index.html',
            active_projects={"count": 0, "change": 0},
            total_workers={"count": 0, "attendance_percent": 0},
            equipment_status={"available": 0, "total": 0, "maintenance": 0},
            pending_orders={"count": 0, "urgent": 0},
            project_progress=[],
            recent_activity=[],
            quick_actions=[],
            financial_overview=[]
        )

@admin_bp.route('/profile', methods=['GET', 'POST'])
@role_required([Roles.SUPER_HQ])
def profile():
    try:
        if request.method == 'POST':
            flash('Profile updated!', 'success')
            return redirect(url_for('admin.profile'))
        return render_template('admin/profile.html')
    except Exception as e:
        flash(f'Error updating profile: {str(e)}', 'danger')
        return render_template('admin/profile.html')

@admin_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('main.login'))

@admin_bp.route('/dashboard/data')
@role_required([Roles.SUPER_HQ])
def dashboard_data():
    try:
        # Example: Fetch data from other blueprints' models/services
        hr_data = current_app.hr_service.get_all_employees() if hasattr(current_app, 'hr_service') else []
        projects_data = current_app.projects_service.get_all_projects() if hasattr(current_app, 'projects_service') else []
        finance_data = current_app.finance_service.get_all_financials() if hasattr(current_app, 'finance_service') else []
        files_data = current_app.files_service.get_all_files() if hasattr(current_app, 'files_service') else []
        return render_template('admin/dashboard_data.html', hr=hr_data, projects=projects_data, finance=finance_data, files=files_data)
    except Exception as e:
        flash(f'Error fetching dashboard data: {str(e)}', 'danger')
        return render_template('admin/dashboard_data.html', hr=[], projects=[], finance=[], files=[])

@admin_bp.route('/dashboard/upload', methods=['GET', 'POST'])
@role_required([Roles.SUPER_HQ])
def dashboard_upload():
    class UploadForm(FlaskForm):
        file = FileField('File', validators=[DataRequired()])
    form = UploadForm()
    if form.validate_on_submit():
        file = form.file.data
        filename = secure_filename(file.filename)
        file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
        flash('File uploaded successfully!', 'success')
        return redirect(url_for('admin.dashboard_upload'))
    return render_template('admin/dashboard_upload.html', form=form)

@admin_bp.route('/dashboard/decision', methods=['POST'])
@role_required([Roles.SUPER_HQ])
def dashboard_decision():
    try:
        data_id = request.form.get('data_id')
        action = request.form.get('action')
        data_type = request.form.get('data_type')  # e.g., 'project', 'employee', 'file', 'finance'
        result = None
        # Decision logic for each data type
        if data_type == 'project':
            if action == 'approve':
                result = current_app.projects_service.approve_project(data_id)
            elif action == 'archive':
                result = current_app.projects_service.archive_project(data_id)
            elif action == 'delete':
                result = current_app.projects_service.delete_project(data_id)
        elif data_type == 'employee':
            if action == 'approve':
                result = current_app.hr_service.approve_employee(data_id)
            elif action == 'reject':
                result = current_app.hr_service.reject_employee(data_id)
            elif action == 'assign':
                site = request.form.get('site')
                result = current_app.hr_service.assign_employee_to_site(data_id, site)
            elif action == 'delete':
                result = current_app.hr_service.delete_employee(data_id)
        elif data_type == 'file':
            if action == 'archive':
                result = current_app.files_service.archive_file(data_id)
            elif action == 'delete':
                result = current_app.files_service.delete_file(data_id)
        elif data_type == 'finance':
            if action == 'approve':
                result = current_app.finance_service.approve_transaction(data_id)
            elif action == 'reject':
                result = current_app.finance_service.reject_transaction(data_id)
        # Log the action for audit
        try:
            if hasattr(current_app, 'audit_service'):
                current_app.audit_service.log_action(
                    user=session.get('user'),
                    action=action,
                    data_type=data_type,
                    data_id=data_id
                )
        except Exception:
            pass  # Don't block main action if audit fails
        flash(f'Action {action} on {data_type} performed successfully!', 'success')
    except Exception as e:
        flash(f'Error performing action: {str(e)}', 'danger')
    return redirect(url_for('admin.dashboard_data'))

@admin_bp.route('/dashboard/action-log', methods=['GET'])
@role_required([Roles.SUPER_HQ])
def dashboard_action_log():
    try:
        user = request.args.get('user', '').strip()
        action = request.args.get('action', '').strip()
        data_type = request.args.get('data_type', '').strip()
        page = request.args.get('page', 1, type=int)
        per_page = 20
        logs_query = current_app.audit_service.get_action_log_query() if hasattr(current_app, 'audit_service') else None
        if logs_query:
            if user:
                logs_query = logs_query.filter_by(user=user)
            if action:
                logs_query = logs_query.filter_by(action=action)
            if data_type:
                logs_query = logs_query.filter_by(data_type=data_type)
            logs = logs_query.order_by('timestamp desc').paginate(page=page, per_page=per_page, error_out=False)
            return render_template('admin/action_log.html', logs=logs.items, page=page, pages=logs.pages, user=user, action=action, data_type=data_type)
        else:
            return render_template('admin/action_log.html', logs=[], page=page, pages=0, user=user, action=action, data_type=data_type)
    except Exception as e:
        flash(f'Error loading action log: {str(e)}', 'danger')
        return render_template('admin/action_log.html', logs=[], page=1, pages=0, user='', action='', data_type='')

# Advanced File Management
@admin_bp.route('/files/move', methods=['POST'])
@role_required([Roles.SUPER_HQ])
def move_files():
    try:
        file_ids = request.form.getlist('file_ids')
        target_folder = request.form.get('target_folder')
        if not file_ids or not target_folder:
            flash('File IDs and target folder are required.', 'danger')
            return redirect(url_for('files.search_files'))
        for file_id in file_ids:
            current_app.files_service.move_file(file_id, target_folder)
        flash('Files moved successfully!', 'success')
    except Exception as e:
        flash(f'Error moving files: {str(e)}', 'danger')
    return redirect(url_for('files.search_files'))

@admin_bp.route('/files/bulk-delete', methods=['POST'])
@role_required([Roles.SUPER_HQ])
def bulk_delete_files():
    try:
        file_ids = request.form.getlist('file_ids')
        if not file_ids:
            flash('No files selected for deletion.', 'danger')
            return redirect(url_for('files.search_files'))
        for file_id in file_ids:
            current_app.files_service.delete_file(file_id)
        flash('Files deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting files: {str(e)}', 'danger')
    return redirect(url_for('files.search_files'))

@admin_bp.route('/files/download/<int:file_id>', methods=['GET'])
@role_required([Roles.SUPER_HQ])
def download_file(file_id):
    try:
        file_record = current_app.files_service.get_file(file_id)
        if not file_record:
            flash('File not found.', 'danger')
            return redirect(url_for('files.search_files'))
        return current_app.send_static_file(file_record.path)
    except Exception as e:
        flash(f'Error downloading file: {str(e)}', 'danger')
        return redirect(url_for('files.search_files'))

@admin_bp.route('/files/bulk-tag', methods=['POST'])
@role_required([Roles.SUPER_HQ])
def bulk_tag_files():
    try:
        file_ids = request.form.getlist('file_ids')
        tags = request.form.get('tags', '').strip()
        if not file_ids or not tags:
            flash('File IDs and tags are required.', 'danger')
            return redirect(url_for('files.search_files'))
        for file_id in file_ids:
            current_app.files_service.tag_file(file_id, tags)
        flash('Tags updated for selected files!', 'success')
    except Exception as e:
        flash(f'Error tagging files: {str(e)}', 'danger')
    return redirect(url_for('files.search_files'))

# Advanced Analytics
@admin_bp.route('/analytics/custom', methods=['GET'])
@role_required([Roles.SUPER_HQ])
def analytics_custom():
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        data_type = request.args.get('data_type')
        user = request.args.get('user')
        results = current_app.analytics_service.custom_query(start_date, end_date, data_type, user) if hasattr(current_app, 'analytics_service') else []
        return render_template('admin/analytics_custom.html', results=results, start_date=start_date, end_date=end_date, data_type=data_type, user=user)
    except Exception as e:
        flash(f'Error running custom analytics: {str(e)}', 'danger')
        return render_template('admin/analytics_custom.html', results=[], start_date=None, end_date=None, data_type=None, user=None)

@admin_bp.route('/analytics/export-csv', methods=['GET'])
@role_required([Roles.SUPER_HQ])
def analytics_export_csv():
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        data_type = request.args.get('data_type')
        user = request.args.get('user')
        csv_data = current_app.analytics_service.export_csv(start_date, end_date, data_type, user) if hasattr(current_app, 'analytics_service') else ''
        return render_template('admin/analytics_export_csv.html', csv_data=csv_data)
    except Exception as e:
        flash(f'Error exporting analytics: {str(e)}', 'danger')
        return render_template('admin/analytics_export_csv.html', csv_data=None)

# Custom Dashboard
@admin_bp.route('/dashboard/custom', methods=['GET'])
@role_required([Roles.SUPER_HQ])
def custom_dashboard():
    try:
        widgets = current_app.dashboard_service.get_widgets(session.get('user')) if hasattr(current_app, 'dashboard_service') else []
        return render_template('admin/custom_dashboard.html', widgets=widgets)
    except Exception as e:
        flash(f'Error loading custom dashboard: {str(e)}', 'danger')
        return render_template('admin/custom_dashboard.html', widgets=[])

@admin_bp.route('/dashboard/save-layout', methods=['POST'])
@role_required([Roles.SUPER_HQ])
def save_dashboard_layout():
    try:
        layout = request.form.get('layout')
        current_app.dashboard_service.save_layout(session.get('user'), layout)
        flash('Dashboard layout saved!', 'success')
    except Exception as e:
        flash(f'Error saving dashboard layout: {str(e)}', 'danger')
    return redirect(url_for('admin.custom_dashboard'))

@admin_bp.route('/attendance')
@role_required([Roles.SUPER_HQ])
def attendance():
    try:
        date = request.args.get('date')
        site = request.args.get('site')
        # Get all unique sites from Employee table
        sites = [e.site for e in Employee.query.distinct(Employee.site).all() if e.site]
        query = Attendance.query
        if date:
            query = query.filter_by(date=date)
        if site and site != 'All Sites':
            query = query.join(Employee).filter(Employee.site == site)
        attendance_records = query.all()
        present = sum(1 for a in attendance_records if a.status == 'Present')
        absent = sum(1 for a in attendance_records if a.status == 'Absent')
        late = sum(1 for a in attendance_records if a.status == 'Late')
        on_leave = sum(1 for a in attendance_records if a.status == 'On Leave')
        return render_template(
            'admin/hr/attendance.html',
            attendance_records=attendance_records,
            present=present,
            absent=absent,
            late=late,
            on_leave=on_leave,
            sites=sites
        )
    except Exception as e:
        flash(f'Error loading attendance: {str(e)}', 'danger')
        return render_template('admin/hr/attendance.html', attendance_records=[], present=0, absent=0, late=0, on_leave=0, sites=[])

@admin_bp.route('/employees')
@role_required([Roles.SUPER_HQ])
def employees():
    try:
        employees = Employee.query.all()
        departments = [e.department for e in Employee.query.distinct(Employee.department).all() if e.department]
        return render_template('admin/hr/employees.html', employees=employees, departments=departments)
    except Exception as e:
        flash(f'Error loading employees: {str(e)}', 'danger')
        return render_template('admin/hr/employees.html', employees=[], departments=[])

@admin_bp.route('/payroll')
@role_required([Roles.SUPER_HQ])
def payroll():
    try:
        month = request.args.get('month', default=datetime.now().month, type=int)
        department = request.args.get('department', default='', type=str)
        current_year = datetime.now().year

        # Get all employees and departments
        employees_query = Employee.query
        if department:
            employees_query = employees_query.filter_by(department=department)
        employees = employees_query.all()
        total_staff = len(employees)
        departments = [e.department for e in Employee.query.distinct(Employee.department).all() if e.department]

        # Get payrolls for selected month and year
        payrolls_query = Payroll.query.filter(
            db.extract('month', Payroll.period_end) == month,
            db.extract('year', Payroll.period_end) == current_year
        )
        if department:
            payrolls_query = payrolls_query.join(Employee).filter(Employee.department == department)
        payrolls = payrolls_query.all()
        staff_being_paid = len(set([p.employee_id for p in payrolls]))

        # Calculate total payroll for selected month
        total_payroll = sum([getattr(p, 'amount', 0) + getattr(p, 'overtime', 0) if hasattr(p, 'overtime') else 0 - getattr(p, 'deductions', 0) for p in payrolls])

        # Get the set total salary for the selected month
        month_total_salary = None
        payroll_record = Payroll.query.filter(
            db.extract('month', Payroll.period_end) == month,
            db.extract('year', Payroll.period_end) == current_year
        ).order_by(Payroll.id.desc()).first()
        if payroll_record and payroll_record.amount:
            month_total_salary = payroll_record.amount

        # Pair payrolls with employees for table
        payroll_employee_pairs = []
        for p in payrolls:
            emp = Employee.query.get(p.employee_id)
            if emp:
                payroll_employee_pairs.append((p, emp))

        # Fetch payroll history
        payroll_histories = PayrollHistory.query.order_by(PayrollHistory.created_at.desc()).limit(10).all()
        # Fetch salary history (last 10 records)
        salary_histories = EmployeeSalaryHistory.query.order_by(EmployeeSalaryHistory.created_at.desc()).limit(10).all()
        # Fetch transaction history (last 10 records)
        transaction_histories = PayrollTransaction.query.order_by(PayrollTransaction.transaction_date.desc()).limit(10).all()

        return render_template(
            'admin/hr/payroll.html',
            payrolls=payroll_employee_pairs,
            total_payroll=total_payroll,
            total_staff=total_staff,
            staff_being_paid=staff_being_paid,
            next_payday=datetime.now().strftime('%B %d, %Y'),
            departments=departments,
            selected_department=department,
            current_month=month,
            payroll_histories=payroll_histories,
            salary_histories=salary_histories,
            transaction_histories=transaction_histories,
            employees=employees,
            month_total_salary=month_total_salary,
            payroll={'amount': month_total_salary or 0}
        )
    except Exception as e:
        flash(f'Error loading payroll: {str(e)}', 'danger')
        return render_template('admin/hr/payroll.html', payrolls=[], total_payroll=0, total_staff=0, staff_being_paid=0, next_payday=None, departments=[], selected_department='', current_month=datetime.now().month, employees=[], month_total_salary=None, payroll={'amount': 0})

@admin_bp.route('/dashboard/progress')
@role_required([Roles.SUPER_HQ])
def dashboard_progress():
    try:
        # Fetch actual project progress from Project model
        projects = Project.query.all()
        project_progress = [
            {"name": p.name, "percent": int(p.progress or 0)} for p in projects
        ]
        # Fetch recent site updates (example: last 3 tasks, audits, or inspections)
        recent_tasks = Task.query.order_by(Task.updated_at.desc()).limit(3).all()
        site_updates = []
        for t in recent_tasks:
            site_updates.append({
                "type": "task",
                "title": t.title,
                "desc": f"Task for project {t.project.name}",
                "time": t.updated_at.strftime('%b %d, %H:%M') if t.updated_at else "",
                "icon": "bx-task",
                "color": "blue"
            })
        recent_audits = Audit.query.order_by(Audit.date.desc()).limit(1).all()
        for a in recent_audits:
            site_updates.append({
                "type": "audit",
                "title": "Audit Completed" if a.status == "Approved" else "Audit Pending",
                "desc": a.name,
                "time": a.date.strftime('%b %d'),
                "icon": "bx-clipboard",
                "color": "green" if a.status == "Approved" else "yellow"
            })
        recent_inspections = Inspection.query.order_by(Inspection.date.desc()).limit(1).all()
        for i in recent_inspections:
            site_updates.append({
                "type": "inspection",
                "title": "Inspection Scheduled",
                "desc": i.site,
                "time": i.date.strftime('%b %d'),
                "icon": "bx-search",
                "color": "purple"
            })
        # Only show up to 3 updates
        site_updates = site_updates[:3]

        return render_template('admin/dashboard_progress.html', project_progress=project_progress, site_updates=site_updates)
    except Exception as e:
        flash(f'Error loading project progress: {str(e)}', 'danger')
        return render_template('admin/dashboard_progress.html', project_progress=[], site_updates=[])

@admin_bp.route('/employees/<int:employee_id>/edit', methods=['GET', 'POST'])
@role_required([Roles.SUPER_HQ])
def edit_employee(employee_id):
    try:
        employee = Employee.query.get_or_404(employee_id)
        class EditEmployeeForm(FlaskForm):
            name = StringField('Name', validators=[DataRequired(), Length(max=100)])
            department = StringField('Department', validators=[DataRequired(), Length(max=50)])
            role = StringField('Role', validators=[DataRequired(), Length(max=50)])
        form = EditEmployeeForm(obj=employee)
        if form.validate_on_submit():
            employee.name = form.name.data
            employee.department = form.department.data
            employee.role = form.role.data
            db.session.commit()
            flash('Employee updated successfully!', 'success')
            return redirect(url_for('admin.employees'))
        return render_template('admin/hr/edit_employee.html', form=form, employee=employee)
    except Exception as e:
        flash(f'Error editing employee: {str(e)}', 'danger')
        return render_template('admin/hr/edit_employee.html', form=None, employee=None)

@admin_bp.route('/employees/<int:employee_id>/delete', methods=['POST'])
@role_required([Roles.SUPER_HQ])
def delete_employee(employee_id):
    try:
        employee = Employee.query.get_or_404(employee_id)
        db.session.delete(employee)
        db.session.commit()
        flash('Employee deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting employee: {str(e)}', 'danger')
    return redirect(url_for('admin.employees'))

@admin_bp.route('/employees/<int:employee_id>')
@role_required([Roles.SUPER_HQ])
def view_employee(employee_id):
    try:
        employee = Employee.query.get_or_404(employee_id)
        payroll_history = employee.payrolls.order_by(Payroll.date.desc()).all() if hasattr(employee, 'payrolls') else []
        attendance_history = employee.attendances.order_by(Attendance.date.desc()).all() if hasattr(employee, 'attendances') else []
        return render_template('admin/hr/view_employee.html', employee=employee, payroll_history=payroll_history, attendance_history=attendance_history)
    except Exception as e:
        flash(f'Error loading employee details: {str(e)}', 'danger')
        return render_template('admin/hr/view_employee.html', employee=None, payroll_history=[], attendance_history=[])

@admin_bp.route('/projects')
@role_required([Roles.SUPER_HQ])
def projects():
    try:
        projects = Project.query.all()
        statuses = [p.status for p in Project.query.distinct(Project.status).all() if p.status]
        return render_template('admin/projects/projects.html', projects=projects, statuses=statuses)
    except Exception as e:
        flash(f'Error loading projects: {str(e)}', 'danger')
        return render_template('admin/projects/projects.html', projects=[], statuses=[])

@admin_bp.route('/projects/add', methods=['GET', 'POST'])
@login_required
@role_required([Roles.SUPER_HQ, Roles.HQ])
def add_project():
    try:
        class AddProjectForm(FlaskForm):
            name = StringField('Name', validators=[DataRequired(), Length(max=100)])
            description = StringField('Description', validators=[Length(max=255)])
            budget = StringField('Budget', validators=[DataRequired()])
            start_date = DateField('Start Date', format='%Y-%m-%d')
            end_date = DateField('End Date', format='%Y-%m-%d')
            status = SelectField('Status', choices=[
                ('Active', 'Active'),
                ('Pending', 'Pending'),
                ('Completed', 'Completed'),
                ('On Hold', 'On Hold'),
                ('Cancelled', 'Cancelled')
            ], validators=[DataRequired()])
            image = FileField('Project Image')
            project_manager = SelectField('Project Manager', coerce=int, choices=[], validators=[DataRequired()])
            staff = SelectField('Assign Staff', coerce=int, choices=[], validators=[DataRequired()])
        form = AddProjectForm()
        form.project_manager.choices = [(u.id, u.name) for u in User.query.filter_by(role=Roles.PROJECT_MANAGER).all()]
        form.staff.choices = [(e.id, e.name) for e in Employee.query.all()]
        if form.validate_on_submit():
            # Handle image upload
            image_file = form.image.data
            if image_file:
                filename = secure_filename(image_file.filename)
                image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'projects', 'images', filename)
                os.makedirs(os.path.dirname(image_path), exist_ok=True)
                image_file.save(image_path)
            else:
                filename = 'placeholder.png'
                image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'projects', 'images', filename)
            # Create project
            project = Project(
                name=form.name.data,
                description=form.description.data,
                budget=float(form.budget.data),
                start_date=form.start_date.data,
                end_date=form.end_date.data,
                status=form.status.data,
                project_manager_id=form.project_manager.data,
                image=filename
            )
            db.session.add(project)
            db.session.commit()
            # Assign staff with role
            staff_member = Employee.query.get(form.staff.data)
            staff_role = request.form.get('staff_role', 'Assigned')
            if staff_member:
                from models import ProjectStaff
                assignment = ProjectStaff(project_id=project.id, staff_id=staff_member.id, role=staff_role)
                db.session.add(assignment)
                db.session.commit()
                # Email to staff
                if staff_member.email:
                    msg = Message("Project Assignment", sender="noreply@yourdomain.com", recipients=[staff_member.email])
                    msg.body = f"You have been assigned to the project: {project.name} as {staff_role}."
                    current_app.mail.send(msg)
            # Email to project manager
            manager = User.query.get(form.project_manager.data)
            if manager and manager.email:
                msg = Message("New Project Assigned", sender="noreply@yourdomain.com", recipients=[manager.email])
                msg.body = f"You have been assigned as the manager for project: {project.name}."
                current_app.mail.send(msg)
            # Create project folder
            project_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'projects', str(project.id))
            os.makedirs(project_folder, exist_ok=True)
            flash('Project created successfully!', 'success')
            return redirect(url_for('admin.projects'))
        return render_template('Admin/create_project.html', form=form)
    except Exception as e:
        flash(f'Error adding project: {str(e)}', 'danger')
        return render_template('Admin/create_project.html', form=form)

@admin_bp.route('/projects/<int:project_id>/edit', methods=['GET', 'POST'])
@role_required([Roles.SUPER_HQ])
def edit_project(project_id):
    try:
        project = Project.query.get_or_404(project_id)
        class EditProjectForm(FlaskForm):
            name = StringField('Name', validators=[DataRequired(), Length(max=100)])
            status = StringField('Status', validators=[DataRequired(), Length(max=50)])
        form = EditProjectForm(obj=project)
        if form.validate_on_submit():
            project.name = form.name.data
            project.status = form.status.data
            db.session.commit()
            flash('Project updated successfully!', 'success')
            return redirect(url_for('admin.projects'))
        return render_template('admin/projects/edit_project.html', form=form, project=project)
    except Exception as e:
        flash(f'Error editing project: {str(e)}', 'danger')
        return render_template('admin/projects/edit_project.html', form=None, project=None)

@admin_bp.route('/projects/<int:project_id>/delete', methods=['POST'])
@role_required([Roles.SUPER_HQ])
def delete_project(project_id):
    try:
        project = Project.query.get_or_404(project_id)
        db.session.delete(project)
        db.session.commit()
        flash('Project deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting project: {str(e)}', 'danger')
    return redirect(url_for('admin.projects'))

@admin_bp.route('/projects/<int:project_id>')
@login_required
def view_project(project_id):
    try:
        project = Project.query.get_or_404(project_id)
        from datetime import timedelta
        schedule_items = project.schedules.order_by(Schedule.start_time.asc()).all() if hasattr(project, 'schedules') else []
        # Attach schedule to project for template compatibility
        project.schedule = [
            {
                'title': s.title,
                'date': s.start_time.strftime('%Y-%m-%d'),
                'description': s.description
            } for s in schedule_items
        ]
        return render_template('admin/projects/view_project.html', project=project, timedelta=timedelta)
    except Exception as e:
        flash(f'Error loading project details: {str(e)}', 'danger')
        return render_template('admin/projects/view_project.html', project=None)

@admin_bp.route('/projects/<int:project_id>/assign-staff', methods=['GET', 'POST'])
@login_required
@role_required([Roles.SUPER_HQ, Roles.HQ])
def assign_staff(project_id):
    try:
        project = Project.query.get_or_404(project_id)
        class AssignStaffForm(FlaskForm):
            employee_id = SelectField('Employee', coerce=int, validators=[DataRequired()])
            role = StringField('Role', validators=[DataRequired(), Length(max=50)])
        form = AssignStaffForm()
        form.employee_id.choices = [(e.id, e.name) for e in Employee.query.all()]
        if form.validate_on_submit():
            employee = Employee.query.get(form.employee_id.data)
            if employee:
                project.staff.append(employee)
                db.session.commit()
                flash('Staff assigned to project successfully!', 'success')
                # Send notification email (example)
                msg = Message("Project Assignment",
                              sender="noreply@yourdomain.com",
                              recipients=[employee.email])
                msg.body = f"You have been assigned to the project: {project.name} as {form.role.data}."
                current_app.mail.send(msg)
            else:
                flash('Selected employee not found.', 'danger')
            return redirect(url_for('admin.view_project', project_id=project_id))
        return render_template('admin/projects/assign_staff.html', form=form, project=project)
    except Exception as e:
        flash(f'Error assigning staff: {str(e)}', 'danger')
        return render_template('admin/projects/assign_staff.html', form=None, project=None)

@admin_bp.route('/projects/<int:project_id>/add-schedule', methods=['GET', 'POST'])
@login_required
@role_required([Roles.SUPER_HQ, Roles.HQ, Roles.PROJECT_MANAGER])
def add_schedule(project_id):
    try:
        project = Project.query.get_or_404(project_id)
        class AddScheduleForm(FlaskForm):
            title = StringField('Title', validators=[DataRequired(), Length(max=128)])
            start_time = DateField('Start Time', format='%Y-%m-%d %H:%M', validators=[DataRequired()])
            end_time = DateField('End Time', format='%Y-%m-%d %H:%M', validators=[DataRequired()])
        form = AddScheduleForm()
        if form.validate_on_submit():
            schedule = Schedule(
                title=form.title.data,
                start_time=form.start_time.data,
                end_time=form.end_time.data,
                project=project
            )
            db.session.add(schedule)
            db.session.commit()
            flash('Schedule added to project successfully!', 'success')
            return redirect(url_for('admin.view_project', project_id=project_id))
        return render_template('admin/projects/add_schedule.html', form=form, project=project)
    except Exception as e:
        flash(f'Error adding schedule: {str(e)}', 'danger')
        return render_template('admin/projects/add_schedule.html', form=None, project=None)

@admin_bp.route('/projects/<int:project_id>/add-milestone', methods=['GET', 'POST'])
@login_required
@role_required([Roles.SUPER_HQ, Roles.HQ, Roles.PROJECT_MANAGER])
def add_milestone(project_id):
    try:
        project = Project.query.get_or_404(project_id)
        class AddMilestoneForm(FlaskForm):
            name = StringField('Name', validators=[DataRequired(), Length(max=100)])
            due_date = DateField('Due Date', format='%Y-%m-%d', validators=[DataRequired()])
        form = AddMilestoneForm()
        if form.validate_on_submit():
            milestone = Milestone(
                name=form.name.data,
                due_date=form.due_date.data,
                project=project
            )
            db.session.add(milestone)
            db.session.commit()
            flash('Milestone added to project successfully!', 'success')
            return redirect(url_for('admin.view_project', project_id=project_id))
        return render_template('admin/projects/add_milestone.html', form=form, project=project)
    except Exception as e:
        flash(f'Error adding milestone: {str(e)}', 'danger')
        return render_template('admin/projects/add_milestone.html', form=None, project=None)

@admin_bp.route('/projects/<int:project_id>/upload-document', methods=['GET', 'POST'])
@login_required
@role_required([Roles.SUPER_HQ, Roles.HQ, Roles.HQ_FINANCE, Roles.HQ_PROCUREMENT, Roles.PROJECT_MANAGER])
def upload_document(project_id):
    try:
        project = Project.query.get_or_404(project_id)
        class UploadDocumentForm(FlaskForm):
            file = FileField('File', validators=[DataRequired()])
        form = UploadDocumentForm()
        if form.validate_on_submit():
            file = form.file.data
            filename = secure_filename(file.filename)
            # Save file to project-specific folder
            upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'projects', str(project_id))
            os.makedirs(upload_folder, exist_ok=True)
            file.save(os.path.join(upload_folder, filename))
            flash('Document uploaded successfully!', 'success')
            return redirect(url_for('admin.view_project', project_id=project_id))
        return render_template('admin/projects/upload_document.html', form=form, project=project)
    except Exception as e:
        flash(f'Error uploading document: {str(e)}', 'danger')
        return render_template('admin/projects/upload_document.html', form=None, project=None)

@admin_bp.route('/projects/<int:project_id>/expenses')
@login_required
@role_required([Roles.SUPER_HQ, Roles.HQ, Roles.HQ_FINANCE, Roles.HQ_COST_CONTROL, Roles.PROJECT_MANAGER, Roles.HQ_PROCUREMENT])
def view_expenses(project_id):
    try:
        project = Project.query.get_or_404(project_id)
        expenses = Expense.query.filter_by(project_id=project_id).all()
        total_expenses = sum(e.amount for e in expenses)
        # Budget exceedance alert
        if project.budget and total_expenses > project.budget:
            msg = Message("Budget Exceeded Alert",
                          sender="noreply@yourdomain.com",
                          recipients=[current_user.email])
            msg.body = f"Project '{project.name}' has exceeded its budget. Total expenses: ${total_expenses:,.2f}."
            current_app.mail.send(msg)
        return render_template('admin/projects/view_expenses.html', project=project, expenses=expenses, total_expenses=total_expenses)
    except Exception as e:
        flash(f'Error loading expenses: {str(e)}', 'danger')
        return render_template('admin/projects/view_expenses.html', project=None, expenses=[], total_expenses=0)

@admin_bp.route('/projects/<int:project_id>/ledger')
@login_required
@role_required([Roles.SUPER_HQ, Roles.HQ, Roles.HQ_FINANCE])
def view_ledger(project_id):
    try:
        project = Project.query.get_or_404(project_id)
        ledger_entries = current_app.finance_service.get_ledger_entries(project_id) if hasattr(current_app, 'finance_service') else []
        # Add summary: total credits/debits
        total_credits = sum(e.amount for e in ledger_entries if getattr(e, 'type', None) == 'credit')
        total_debits = sum(e.amount for e in ledger_entries if getattr(e, 'type', None) == 'debit')
        return render_template('admin/projects/view_ledger.html', project=project, ledger_entries=ledger_entries, total_credits=total_credits, total_debits=total_debits)
    except Exception as e:
        flash(f'Error loading ledger: {str(e)}', 'danger')
        return render_template('admin/projects/view_ledger.html', project=None, ledger_entries=[], total_credits=0, total_debits=0)

@admin_bp.route('/projects/<int:project_id>/inventory')
@login_required
@role_required([Roles.SUPER_HQ, Roles.HQ, Roles.PROJECT_MANAGER, Roles.HQ_COST_CONTROL])
def view_inventory(project_id):
    try:
        project = Project.query.get_or_404(project_id)
        inventory_items = current_app.inventory_service.get_inventory_items(project_id) if hasattr(current_app, 'inventory_service') else []
        low_stock_items = [item for item in inventory_items if item.quantity < 100]
        low_stock_alert = bool(low_stock_items)
        # Email alert for low inventory
        if low_stock_alert:
            msg = Message("Low Inventory Alert",
                          sender="noreply@yourdomain.com",
                          recipients=[current_user.email])
            msg.body = f"Project '{project.name}' has items with low stock: " + ", ".join([item.name for item in low_stock_items])
            current_app.mail.send(msg)
        return render_template('admin/projects/view_inventory.html', project=project, inventory_items=inventory_items, low_stock_alert=low_stock_alert)
    except Exception as e:
        flash(f'Error loading inventory: {str(e)}', 'danger')
        return render_template('admin/projects/view_inventory.html', project=None, inventory_items=[])

@admin_bp.route('/projects/<int:project_id>/dashboard')
@login_required
def project_dashboard(project_id):
    try:
        project = Project.query.get_or_404(project_id)
        tasks = Task.query.filter_by(project_id=project_id).all()
        milestones = Milestone.query.filter_by(project_id=project_id).all()
        expenses = Expense.query.filter_by(project_id=project_id).all()
        total_expenses = sum(e.amount for e in expenses)
        payrolls = Payroll.query.filter_by(project_id=project_id).all() if hasattr(Payroll, 'project_id') else []
        total_payroll = sum(p.amount for p in payrolls)
        documents = []
        project_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'projects', str(project.id))
        if os.path.exists(project_folder):
            documents = [f for f in os.listdir(project_folder) if os.path.isfile(os.path.join(project_folder, f))]
        # Milestone update alert (example: if any milestone is due today)
        today = datetime.today().date()
        due_milestones = [m for m in milestones if m.due_date == today]
        if due_milestones:
            msg = Message("Milestone Due Alert",
                          sender="noreply@yourdomain.com",
                          recipients=[current_user.email])
            msg.body = f"Project '{project.name}' has milestones due today: " + ", ".join([m.name for m in due_milestones])
            current_app.mail.send(msg)
        budget_remaining = project.budget - total_expenses if project.budget else None
        return render_template('admin/projects/project_dashboard.html', project=project, tasks=tasks, milestones=milestones, expenses=expenses, total_expenses=total_expenses, payrolls=payrolls, total_payroll=total_payroll, documents=documents, budget_remaining=budget_remaining)
    except Exception as e:
        flash(f'Error loading project dashboard: {str(e)}', 'danger')
        return render_template('admin/projects/project_dashboard.html', project=None, tasks=[], milestones=[], expenses=[], payrolls=[], documents=[], budget_remaining=None)

@admin_bp.route('/projects/<int:project_id>/milestones')
@login_required
def milestones(project_id):
    try:
        project = Project.query.get_or_404(project_id)
        milestones = Milestone.query.filter_by(project_id=project_id).order_by(Milestone.due_date.asc()).all()
        # Calculate milestone progress and overdue status
        for milestone in milestones:
            milestone.is_overdue = milestone.due_date < datetime.today().date() if milestone.due_date else False
            milestone.is_completed = getattr(milestone, 'status', None) == 'Completed'
        return render_template('admin/projects/milestones.html', project=project, milestones=milestones)
    except Exception as e:
        flash(f'Error loading milestones: {str(e)}', 'danger')
        return render_template('admin/projects/milestones.html', project=None, milestones=[])

@admin_bp.route('/assets')
@role_required([Roles.SUPER_HQ])
def assets():
    try:
        assets = Asset.query.all()
        return render_template('admin/inventory/assets.html', assets=assets)
    except Exception as e:
        flash(f'Error loading assets: {str(e)}', 'danger')
        return render_template('admin/inventory/assets.html', assets=[])

@admin_bp.route('/assets/add', methods=['GET', 'POST'])
@role_required([Roles.SUPER_HQ])
def add_asset():
    class AddAssetForm(FlaskForm):
        name = StringField('Asset Name', validators=[DataRequired(), Length(max=100)])
        value = StringField('Value', validators=[DataRequired()])
        location = StringField('Location', validators=[Length(max=100)])
    form = AddAssetForm()
    if form.validate_on_submit():
        asset = Asset(name=form.name.data, value=form.value.data, location=form.location.data)
        db.session.add(asset)
        db.session.commit()
        flash('Asset added successfully!', 'success')
        return redirect(url_for('admin.assets'))
    return render_template('admin/inventory/add_asset.html', form=form)

@admin_bp.route('/stock')
@role_required([Roles.SUPER_HQ])
def stock():
    try:
        stock_items = Stock.query.all()
        return render_template('admin/inventory/stock.html', stock_items=stock_items)
    except Exception as e:
        flash(f'Error loading stock: {str(e)}', 'danger')
        return render_template('admin/inventory/stock.html', stock_items=[])

@admin_bp.route('/stock/add', methods=['GET', 'POST'])
@role_required([Roles.SUPER_HQ])
def add_stock():
    class AddStockForm(FlaskForm):
        name = StringField('Stock Name', validators=[DataRequired(), Length(max=100)])
        quantity = StringField('Quantity', validators=[DataRequired()])
        unit = StringField('Unit', validators=[Length(max=20)])
    form = AddStockForm()
    if form.validate_on_submit():
        stock = Stock(name=form.name.data, quantity=form.quantity.data, unit=form.unit.data)
        db.session.add(stock)
        db.session.commit()
        flash('Stock item added successfully!', 'success')
        return redirect(url_for('admin.stock'))
    return render_template('admin/inventory/add_stock.html', form=form)

@admin_bp.route('/orders')
@role_required([Roles.SUPER_HQ])
def orders():
    try:
        orders = PurchaseOrder.query.all()
        return render_template('admin/orders/orders.html', orders=orders)
    except Exception as e:
        flash(f'Error loading orders: {str(e)}', 'danger')
        return render_template('admin/orders/orders.html', orders=[])

@admin_bp.route('/orders/add', methods=['GET', 'POST'])
@role_required([Roles.SUPER_HQ])
def add_order():
    class AddOrderForm(FlaskForm):
        supplier = StringField('Supplier', validators=[DataRequired(), Length(max=100)])
        total_amount = StringField('Total Amount', validators=[DataRequired()])
        status = SelectField('Status', choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Urgent', 'Urgent')], validators=[DataRequired()])
    form = AddOrderForm()
    if form.validate_on_submit():
        order = PurchaseOrder(supplier=form.supplier.data, total_amount=form.total_amount.data, status=form.status.data)
        db.session.add(order)
        db.session.commit()
        flash('Order added successfully!', 'success')
        return redirect(url_for('admin.orders'))
    return render_template('admin/orders/add_order.html', form=form)

@admin_bp.route('/incidents')
@role_required([Roles.SUPER_HQ])
def incidents():
    try:
        incidents = Incident.query.all()
        return render_template('admin/monitoring/incidents.html', incidents=incidents)
    except Exception as e:
        flash(f'Error loading incidents: {str(e)}', 'danger')
        return render_template('admin/monitoring/incidents.html', incidents=[])

@admin_bp.route('/incidents/add', methods=['GET', 'POST'])
@role_required([Roles.SUPER_HQ])
def add_incident():
    class AddIncidentForm(FlaskForm):
        title = StringField('Title', validators=[DataRequired(), Length(max=100)])
        description = StringField('Description', validators=[Length(max=255)])
        status = SelectField('Status', choices=[('Open', 'Open'), ('Closed', 'Closed')], validators=[DataRequired()])
    form = AddIncidentForm()
    if form.validate_on_submit():
        incident = Incident(title=form.title.data, description=form.description.data, status=form.status.data)
        db.session.add(incident)
        db.session.commit()
        flash('Incident added successfully!', 'success')
        return redirect(url_for('admin.incidents'))
    return render_template('admin/monitoring/add_incident.html', form=form)

@admin_bp.route('/alerts')
@role_required([Roles.SUPER_HQ])
def alerts():
    try:
        alerts = Alert.query.all()
        return render_template('admin/monitoring/alerts.html', alerts=alerts)
    except Exception as e:
        flash(f'Error loading alerts: {str(e)}', 'danger')
        return render_template('admin/monitoring/alerts.html', alerts=[])

@admin_bp.route('/alerts/add', methods=['GET', 'POST'])
@role_required([Roles.SUPER_HQ])
def add_alert():
    class AddAlertForm(FlaskForm):
        message = StringField('Message', validators=[DataRequired(), Length(max=255)])
        level = SelectField('Level', choices=[('Info', 'Info'), ('Warning', 'Warning'), ('Critical', 'Critical')], validators=[DataRequired()])
    form = AddAlertForm()
    if form.validate_on_submit():
        alert = Alert(message=form.message.data, level=form.level.data)
        db.session.add(alert)
        db.session.commit()
        flash('Alert added successfully!', 'success')
        return redirect(url_for('admin.alerts'))
    return render_template('admin/monitoring/add_alert.html', form=form)

@admin_bp.route('/schedules')
@role_required([Roles.SUPER_HQ])
def schedules():
    try:
        schedules = Schedule.query.all()
        return render_template('admin/scheduling/schedules.html', schedules=schedules)
    except Exception as e:
        flash(f'Error loading schedules: {str(e)}', 'danger')
        return render_template('admin/scheduling/schedules.html', schedules=[])

@admin_bp.route('/schedules/add', methods=['GET', 'POST'])
@role_required([Roles.SUPER_HQ])
def add_general_schedule():
    class AddScheduleForm(FlaskForm):
        title = StringField('Title', validators=[DataRequired(), Length(max=128)])
        start_time = DateField('Start Time', format='%Y-%m-%d %H:%M', validators=[DataRequired()])
        end_time = DateField('End Time', format='%Y-%m-%d %H:%M', validators=[DataRequired()])
    form = AddScheduleForm()
    if form.validate_on_submit():
        schedule = Schedule(title=form.title.data, start_time=form.start_time.data, end_time=form.end_time.data)
        db.session.add(schedule)
        db.session.commit()
        flash('Schedule added successfully!', 'success')
        return redirect(url_for('admin.schedules'))
    return render_template('admin/scheduling/add_schedule.html', form=form)

@admin_bp.route('/employees/<int:employee_id>/promote', methods=['GET', 'POST'])
@role_required([Roles.SUPER_HQ])
def promote_employee(employee_id):
    try:
        employee = Employee.query.get_or_404(employee_id)
        class PromoteEmployeeForm(FlaskForm):
            position = StringField('New Position', validators=[DataRequired(), Length(max=100)])
            job_description_upgrade = StringField('New Job Description', validators=[Length(max=255)])
            present_academic_qualification = StringField('Present Academic Qualification', validators=[Length(max=255)])
        form = PromoteEmployeeForm(obj=employee)
        if form.validate_on_submit():
            employee.role = form.position.data
            employee.job_description_upgrade = form.job_description_upgrade.data
            employee.present_academic_qualification = form.present_academic_qualification.data
            db.session.commit()
            flash('Employee promoted successfully!', 'success')
            return redirect(url_for('admin.view_employee', employee_id=employee.id))
        return render_template('admin/hr/promote_employee.html', form=form, employee=employee)
    except Exception as e:
        flash(f'Error promoting employee: {str(e)}', 'danger')
        return render_template('admin/hr/promote_employee.html', form=None, employee=None)

@admin_bp.route('/employees/<int:employee_id>/clock-in', methods=['POST'])
@role_required([Roles.SUPER_HQ])
def clock_in(employee_id):
    try:
        from datetime import datetime
        attendance = Attendance(employee_id=employee_id, date=datetime.today().date(), clock_in=datetime.now(), status='Present')
        db.session.add(attendance)
        db.session.commit()
        flash('Clock-in successful!', 'success')
    except Exception as e:
        flash(f'Error clocking in: {str(e)}', 'danger')
    return redirect(url_for('admin.view_employee', employee_id=employee_id))

@admin_bp.route('/employees/<int:employee_id>/clock-out', methods=['POST'])
@role_required([Roles.SUPER_HQ])
def clock_out(employee_id):
    try:
        from datetime import datetime
        attendance = Attendance.query.filter_by(employee_id=employee_id, date=datetime.today().date()).first()
        if attendance:
            attendance.clock_out = datetime.now()
            db.session.commit()
            flash('Clock-out successful!', 'success')
        else:
            flash('No clock-in record found for today.', 'danger')
    except Exception as e:
        flash(f'Error clocking out: {str(e)}', 'danger')
    return redirect(url_for('admin.view_employee', employee_id=employee_id))

@admin_bp.route('/employees/<int:employee_id>/add-payroll', methods=['POST'])
@role_required([Roles.SUPER_HQ])
def add_payroll(employee_id):
    try:
        amount = request.form.get('amount')
        status = request.form.get('status', 'Generated')
        from datetime import datetime
        payroll = Payroll(employee_id=employee_id, amount=amount, status=status, date=datetime.today().date())
        db.session.add(payroll)
        db.session.commit()
        flash('Payroll added successfully!', 'success')
    except Exception as e:
        flash(f'Error adding payroll: {str(e)}', 'danger')
    return redirect(url_for('admin.view_employee', employee_id=employee_id))

@admin_bp.route('/payroll/export', methods=['GET'])
@role_required([Roles.SUPER_HQ])
def export_payroll():
    import csv
    from io import StringIO
    payrolls = Payroll.query.join(Employee).add_entity(Employee).all()
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['Staff Name', 'Amount', 'Status', 'Date'])
    for p, e in payrolls:
        cw.writerow([e.name, p.amount, p.status, p.date])
    output = si.getvalue()
    return output, 200, {'Content-Type': 'text/csv', 'Content-Disposition': 'attachment; filename=payroll.csv'}

@admin_bp.route('/attendance/export', methods=['GET'])
@role_required([Roles.SUPER_HQ])
def export_attendance():
    import csv
    from io import StringIO
    attendance_records = Attendance.query.join(Employee).add_entity(Employee).all()
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['Staff Name', 'Date', 'Status', 'Clock In', 'Clock Out'])
    for a, e in attendance_records:
        cw.writerow([e.name, a.date, a.status, a.clock_in, a.clock_out])
    output = si.getvalue()
    return output, 200, {'Content-Type': 'text/csv', 'Content-Disposition': 'attachment; filename=attendance.csv'}

@admin_bp.route('/payroll/analytics', methods=['GET'])
@role_required([Roles.SUPER_HQ])
def payroll_analytics():
    from sqlalchemy import func
    total_payroll = db.session.query(func.sum(Payroll.amount)).scalar() or 0
    avg_payroll = db.session.query(func.avg(Payroll.amount)).scalar() or 0
    count_payroll = db.session.query(func.count(Payroll.id)).scalar() or 0
    return {
        'total': total_payroll,
        'average': avg_payroll,
        'count': count_payroll
    }

@admin_bp.route('/attendance/analytics', methods=['GET'])
@role_required([Roles.SUPER_HQ])
def attendance_analytics():
    from sqlalchemy import func
    total_attendance = db.session.query(func.count(Attendance.id)).scalar() or 0
    present_count = db.session.query(func.count(Attendance.id)).filter(Attendance.status=='Present').scalar() or 0
    absent_count = db.session.query(func.count(Attendance.id)).filter(Attendance.status=='Absent').scalar() or 0
    late_count = db.session.query(func.count(Attendance.id)).filter(Attendance.status=='Late').scalar() or 0
    return {
        'total': total_attendance,
        'present': present_count,
        'absent': absent_count,
        'late': late_count
    }

@admin_bp.route('/generate_payroll', methods=['POST'])
@role_required([Roles.SUPER_HQ])
def generate_payroll():
    try:
        # Get total payroll and deductions from form
        total_payroll_input = request.form.get('total_payroll_input', type=float)
        total_deductions_input = request.form.get('total_deductions_input', type=float)
        month = request.args.get('month', default=datetime.now().month, type=int)
        year = datetime.now().year
        period_start = datetime(year, month, 1)
        period_end = datetime(year, month, 28)

        # Create PayrollHistory record
        payroll_history = PayrollHistory(
            period_start=period_start,
            period_end=period_end,
            total_payroll=total_payroll_input or 0,
            total_deductions=total_deductions_input or 0,
            generated_by=current_user.name if hasattr(current_user, 'name') else 'System'
        )
        db.session.add(payroll_history)
        db.session.flush()  # Get payroll_history.id

        employees = Employee.query.all()
        total_employee_net = 0
        for employee in employees:
            salary = request.form.get(f'salary_{employee.id}', type=float)
            deduction = request.form.get(f'deduction_{employee.id}', type=float)
            net_salary = (salary or 0) - (deduction or 0)
            total_employee_net += net_salary
            # Save payroll record for employee
            payroll = Payroll(
                employee_id=employee.id,
                period_start=period_start,
                period_end=period_end,
                amount=salary or 0,
                deductions=deduction or 0,
                status='Generated'
            )
            db.session.add(payroll)
            # Save EmployeeSalaryHistory
            salary_history = EmployeeSalaryHistory(
                payroll_history_id=payroll_history.id,
                employee_id=employee.id,
                salary=salary or 0,
                deduction=deduction or 0,
                net_pay=net_salary
            )
            db.session.add(salary_history)
            # Save PayrollTransaction
            transaction = PayrollTransaction(
                payroll_history_id=payroll_history.id,
                employee_id=employee.id,
                amount_paid=net_salary,
                status='Completed'
            )
            db.session.add(transaction)
        db.session.commit()

        remaining_payroll = (total_payroll_input or 0) - total_employee_net - (total_deductions_input or 0)
        flash(f'Payroll generated! Remaining payroll after payments and deductions: ₦{remaining_payroll:,.2f}', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error generating payroll: {str(e)}', 'danger')
    return redirect(url_for('admin.payroll'))

@admin_bp.route('/employees/add', methods=['GET', 'POST'])
@role_required([Roles.SUPER_HQ])
def add_employee():
    try:
        class AddEmployeeForm(FlaskForm):
            name = StringField('Full Name', validators=[DataRequired(), Length(max=100)])
            dob = DateField('Date of Birth', format='%Y-%m-%d', validators=[DataRequired()])
            email = StringField('Email', validators=[DataRequired(), Length(max=100)])
            department = SelectField('Department', choices=[('HR', 'HR'), ('Finance', 'Finance'), ('Engineering', 'Engineering'), ('Procurement', 'Procurement'), ('Other', 'Other')], validators=[DataRequired()])
            position = SelectField('Position', choices=[('Manager', 'Manager'), ('Staff', 'Staff'), ('Intern', 'Intern'), ('Other', 'Other')], validators=[DataRequired()])
            date_of_employment = DateField('Date of Employment', format='%Y-%m-%d', validators=[DataRequired()])
            employment_letter = SelectField('Employment Letter', choices=[('Yes', 'Yes'), ('No', 'No')])
            next_of_kin_relationship = SelectField('Relationship', choices=[('Parent', 'Parent'), ('Sibling', 'Sibling'), ('Spouse', 'Spouse'), ('Other', 'Other')])
            current_address = StringField('Current Address', validators=[Length(max=255)])
            permanent_address = StringField('Permanent Address', validators=[Length(max=255)])
            phone = StringField('Phone Number', validators=[Length(max=20)])
            next_of_kin = StringField('Next of Kin', validators=[Length(max=100)])
            next_of_kin_address = StringField('Next of Kin Address', validators=[Length(max=255)])
            next_of_kin_phone = StringField('Next of Kin Phone', validators=[Length(max=20)])
            degree = StringField('Degree (if any)', validators=[Length(max=100)])
            institution = StringField('Institution(s) Attended', validators=[Length(max=255)])
            current_certification = StringField('Current Degree/Certification', validators=[Length(max=100)])
            present_assignment = StringField('Place of Present Assignment', validators=[Length(max=100)])
            sectional_head = StringField('Sectional Head', validators=[Length(max=100)])
            employment_dates = StringField('Employment Dates', validators=[Length(max=100)])
            job_description = StringField('Job Description', validators=[Length(max=255)])
            past_job_title = StringField('Past Job Title(s) and Role(s)', validators=[Length(max=100)])
            past_employer_dates = StringField('Employer(s) and Dates', validators=[Length(max=255)])
            past_accomplishments = StringField('Key Accomplishments and Responsibilities', validators=[Length(max=255)])
            technical_skills = StringField('Technical Skills', validators=[Length(max=255)])
            soft_skills = StringField('Soft Skills', validators=[Length(max=255)])
            certifications = StringField('Relevant Certifications or Licenses', validators=[Length(max=255)])
            team_info = StringField('Team Information', validators=[Length(max=100)])
            notes = StringField('Notes', validators=[Length(max=255)])
            sectional_head_upgrade = StringField('Name of Sectional Head', validators=[Length(max=100)])
            job_description_upgrade = StringField('Job Description (Upgrade)', validators=[Length(max=255)])
            academic_qualification_at_employment = StringField('Academic qualification as at time of employment', validators=[Length(max=255)])
            present_academic_qualification = StringField('Present Academic qualification', validators=[Length(max=255)])
        form = AddEmployeeForm()
        if form.validate_on_submit():
            employee = Employee(
                name=form.name.data,
                dob=form.dob.data,
                email=form.email.data,
                department=form.department.data,
                role=form.position.data,
                date_of_employment=form.date_of_employment.data,
                employment_letter=form.employment_letter.data,
                next_of_kin_relationship=form.next_of_kin_relationship.data,
                current_address=form.current_address.data,
                permanent_address=form.permanent_address.data,
                phone=form.phone.data,
                next_of_kin=form.next_of_kin.data,
                next_of_kin_address=form.next_of_kin_address.data,
                next_of_kin_phone=form.next_of_kin_phone.data,
                degree=form.degree.data,
                institution=form.institution.data,
                current_certification=form.current_certification.data,
                present_assignment=form.present_assignment.data,
                sectional_head=form.sectional_head.data,
                employment_dates=form.employment_dates.data,
                job_description=form.job_description.data,
                past_job_title=form.past_job_title.data,
                past_employer_dates=form.past_employer_dates.data,
                past_accomplishments=form.past_accomplishments.data,
                technical_skills=form.technical_skills.data,
                soft_skills=form.soft_skills.data,
                certifications=form.certifications.data,
                team_info=form.team_info.data,
                notes=form.notes.data,
                sectional_head_upgrade=form.sectional_head_upgrade.data,
                job_description_upgrade=form.job_description_upgrade.data,
                academic_qualification_at_employment=form.academic_qualification_at_employment.data,
                present_academic_qualification=form.present_academic_qualification.data
            )
            db.session.add(employee)
            db.session.commit()
            flash('Employee added successfully!', 'success')
            return redirect(url_for('admin.employees'))
        elif request.method == 'POST':
            flash('Please fill all required fields: Name, Email, Department, Position, Date of Birth, Date of Employment.', 'danger')
        return render_template('admin/hr/add_employee.html', form=form)
    except Exception as e:
        flash(f'Error adding employee: {str(e)}', 'danger')
        return render_template('admin/hr/add_employee.html', form=None)

@admin_bp.route('/set_total_salary', methods=['POST'])
@role_required([Roles.SUPER_HQ])
def set_total_salary():
    try:
        month = int(request.form.get('month'))
        total_salary = float(request.form.get('total_salary'))
        current_year = datetime.now().year
        # Find or create a Payroll record for the month
        payroll_record = Payroll.query.filter(
            db.extract('month', Payroll.period_end) == month,
            db.extract('year', Payroll.period_end) == current_year
        ).first()
        if payroll_record:
            payroll_record.amount = total_salary
            payroll_record.period_end = datetime(current_year, month, 28)  # Set to last day of month
        else:
            payroll_record = Payroll(
                amount=total_salary,
                period_end=datetime(current_year, month, 28)
            )
            db.session.add(payroll_record)
        db.session.commit()
        flash(f'Total salary for month {month} saved!', 'success')
    except Exception as e:
        flash(f'Error saving total salary: {str(e)}', 'danger')
    return redirect(url_for('admin.payroll'))
