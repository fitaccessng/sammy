from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for, session, send_file, current_app
from flask_login import current_user, login_required
from datetime import datetime, timedelta, date
import csv
import io
import os
from werkzeug.utils import secure_filename
from sqlalchemy import func
from extensions import db
from models import (Role, ReportingLine, ApprovalHierarchy, Permission, Payroll, Employee, 
                   Project, Asset, Stock, PurchaseOrder, PurchaseOrderLineItem, Supplier, 
                   Incident, Alert, Schedule, Milestone, User, Budget, Expense, Task, Equipment, 
                   Document, StaffAssignment, EmployeeAssignment, BOQItem, ProjectActivity, ProjectDocument, ProcurementRequest)
from utils.decorators import role_required
from utils.constants import Roles
from utils.email import send_verification_email
from flask_mail import Message
from extensions import mail

def send_order_notification(user_email, order_number, status, reason=None):
    """Send email notification for purchase order status changes"""
    try:
        subject = f"Purchase Order {order_number} - Status Update"
        
        if status == 'Approved':
            body = f"""
Dear User,

Your Purchase Order {order_number} has been APPROVED.

The order is now approved and will proceed to the next stage in the procurement process.

Best regards,
Construction Management Team
            """
        elif status == 'Rejected':
            body = f"""
Dear User,

Your Purchase Order {order_number} has been REJECTED.

Reason: {reason or 'No specific reason provided'}

Please review the rejection reason and resubmit the order with necessary corrections if required.

Best regards,
Construction Management Team
            """
        
        msg = Message(subject,
                     sender=current_app.config['MAIL_DEFAULT_SENDER'],
                     recipients=[user_email])
        msg.body = body
        
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to send order notification: {str(e)}")
        return False

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Dashboard Route
@admin_bp.route('/')
@role_required([Roles.SUPER_HQ])
def dashboard():
    try:
        # Get summary stats for dashboard
        total_roles = Role.query.count()
        total_reporting_lines = ReportingLine.query.count()
        total_approval_hierarchies = ApprovalHierarchy.query.count()
        total_permissions = Permission.query.count()
        total_employees = Employee.query.count()
        
        summary = {
            'total_roles': total_roles,
            'total_reporting_lines': total_reporting_lines,
            'total_approval_hierarchies': total_approval_hierarchies,
            'total_permissions': total_permissions,
            'total_employees': total_employees
        }
        
        return render_template('admin/dashboard.html', summary=summary)
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return render_template('error.html'), 500

# Roles Management Views
@admin_bp.route('/roles-view')
@role_required([Roles.SUPER_HQ])
def roles_view():
    try:
        # Get all employees
        employees = Employee.query.all()
        
        # Get system roles from the Role model
        system_roles = Role.query.all()
        
        # Get available system roles from constants for role assignment
        from utils.constants import Roles
        available_roles = [
            {'id': 1, 'value': Roles.SUPER_HQ, 'name': 'Super HQ Admin'},
            {'id': 2, 'value': Roles.HQ_FINANCE, 'name': 'HQ Finance Manager'},
            {'id': 3, 'value': Roles.HQ, 'name': 'HQ Manager'},
            {'id': 4, 'value': Roles.HQ_HR, 'name': 'HQ HR Manager'},
            {'id': 5, 'value': Roles.HQ_PROCUREMENT, 'name': 'HQ Procurement Manager'},
            {'id': 6, 'value': Roles.QUARRY_MANAGER, 'name': 'Quarry Manager'},
            {'id': 7, 'value': Roles.PROJECT_MANAGER, 'name': 'Project Manager'},
            {'id': 8, 'value': Roles.HQ_COST_CONTROL, 'name': 'HQ Cost Control Manager'},
            {'id': 9, 'value': Roles.FINANCE_STAFF, 'name': 'Finance Staff'},
            {'id': 10, 'value': Roles.HR_STAFF, 'name': 'HR Staff'},
            {'id': 11, 'value': Roles.PROCUREMENT_STAFF, 'name': 'Procurement Staff'},
            {'id': 12, 'value': Roles.PROCUREMENT_OFFICER, 'name': 'Procurement Officer'},
            {'id': 13, 'value': Roles.QUARRY_STAFF, 'name': 'Quarry Staff'},
            {'id': 14, 'value': Roles.PROJECT_STAFF, 'name': 'Project Staff'},
        ]
        
        # Role display names mapping
        role_names = {
            'super_hq': 'Super HQ Admin',
            'hq_finance': 'HQ Finance Manager',
            'hr': 'HQ Manager',
            'hq_hr': 'HQ HR Manager',
            'hq_procurement': 'HQ Procurement Manager',
            'hq_quarry': 'Quarry Manager',
            'hq_project': 'Project Manager',
            'hq_cost_control': 'HQ Cost Control Manager',
            'finance_staff': 'Finance Staff',
            'hr_staff': 'HR Staff',
            'procurement_staff': 'Procurement Staff',
            'procurement_officer': 'Procurement Officer',
            'quarry_staff': 'Quarry Staff',
            'project_staff': 'Project Staff',
        }
        
        # Create employee data with current role information
        employee_data = []
        for emp in employees:
            current_role_name = role_names.get(emp.role, emp.role or 'No Role Assigned')
            
            # Find role ID if employee has a role
            current_role_id = None
            if emp.role:
                # Try to find matching role from available roles
                for role in available_roles:
                    if role['value'] == emp.role:
                        current_role_id = role['id']  # Use the proper role ID
                        break
            
            employee_data.append({
                'id': emp.id,
                'name': emp.name,
                'email': getattr(emp, 'email', 'N/A'),
                'department': getattr(emp, 'department', 'N/A'),
                'position': getattr(emp, 'position', 'N/A'),
                'current_role': current_role_name,
                'current_role_value': emp.role,
                'current_role_id': current_role_id,  # Add current_role_id for template
                'status': getattr(emp, 'status', 'Active'),
                'is_verified': True,
                'created_at': emp.created_at.strftime('%Y-%m-%d') if emp.created_at else 'N/A'
            })
        
        # Count employees by role and get employee lists
        role_counts = {}
        role_users = {}
        
        for role in available_roles:
            employees_with_role = Employee.query.filter_by(role=role['value']).all()
            count = len(employees_with_role)
            role_counts[role['value']] = count
            role_users[role['value']] = [{'id': emp.id, 'name': emp.name, 'email': emp.email} for emp in employees_with_role]
        
        # Also count employees with no role
        unassigned_employees = Employee.query.filter(
            (Employee.role == None) | 
            (Employee.role == '') | 
            (~Employee.role.in_([role['value'] for role in available_roles]))
        ).all()
        
        role_counts['no_role'] = len(unassigned_employees)
        role_users['no_role'] = [{'id': emp.id, 'name': emp.name, 'email': emp.email} for emp in unassigned_employees]

        return render_template('admin/roles.html', 
                             available_roles=available_roles,
                             roles=available_roles,  # Provide roles for template compatibility
                             employees=employee_data,
                             users=employee_data,  # Alias for template compatibility
                             role_counts=role_counts,
                             role_users=role_users)
    except Exception as e:
        flash(f'Error loading roles: {str(e)}', 'error')
        return render_template('error.html'), 500
    except Exception as e:
        flash(f'Error loading roles: {str(e)}', 'error')
        return render_template('error.html'), 500

@admin_bp.route('/assign-role', methods=['POST'])
@role_required([Roles.SUPER_HQ])
def assign_role():
    try:
        current_app.logger.info("=== ASSIGN ROLE DEBUG START ===")
        
        data = request.get_json()
        current_app.logger.info(f"Request data: {data}")
        
        employee_id = data.get('employee_id')
        role_id = data.get('role_id')
        
        current_app.logger.info(f"Employee ID: {employee_id}, Role ID: {role_id}")
        
        # Get the employee
        employee = Employee.query.get(employee_id)
        if not employee:
            current_app.logger.error(f"Employee not found with ID: {employee_id}")
            flash('Employee not found', 'error')
            return redirect(url_for('admin.roles'))
        
        current_app.logger.info(f"Found employee: {employee.name}")
        
        # Get available roles for validation
        from utils.constants import Roles
        available_roles = [
            {'id': 1, 'value': Roles.SUPER_HQ, 'name': 'Super HQ Admin'},
            {'id': 2, 'value': Roles.HQ_FINANCE, 'name': 'HQ Finance Manager'},
            {'id': 3, 'value': Roles.HQ, 'name': 'HQ Manager'},
            {'id': 4, 'value': Roles.HQ_HR, 'name': 'HQ HR Manager'},
            {'id': 5, 'value': Roles.HQ_PROCUREMENT, 'name': 'HQ Procurement Manager'},
            {'id': 6, 'value': Roles.QUARRY_MANAGER, 'name': 'Quarry Manager'},
            {'id': 7, 'value': Roles.PROJECT_MANAGER, 'name': 'Project Manager'},
            {'id': 8, 'value': Roles.HQ_COST_CONTROL, 'name': 'HQ Cost Control Manager'},
            {'id': 9, 'value': Roles.FINANCE_STAFF, 'name': 'Finance Staff'},
            {'id': 10, 'value': Roles.HR_STAFF, 'name': 'HR Staff'},
            {'id': 11, 'value': Roles.PROCUREMENT_STAFF, 'name': 'Procurement Staff'},
            {'id': 12, 'value': Roles.PROCUREMENT_OFFICER, 'name': 'Procurement Officer'},
            {'id': 13, 'value': Roles.QUARRY_STAFF, 'name': 'Quarry Staff'},
            {'id': 14, 'value': Roles.PROJECT_STAFF, 'name': 'Project Staff'},
        ]
        
        # Find the role by ID
        selected_role = None
        if role_id:
            for role in available_roles:
                if role['id'] == role_id:
                    selected_role = role
                    break
            
            if not selected_role:
                current_app.logger.error(f"Invalid role ID: {role_id}")
                flash('Invalid role selected', 'error')
                return redirect(url_for('admin.roles'))
        
        current_app.logger.info(f"Selected role: {selected_role}")
        
        # Update employee role
        old_role = employee.role
        old_role_name = 'No Role' if not old_role else old_role
        
        if selected_role:
            employee.role = selected_role['value']
            new_role_name = selected_role['name']
            message = f"Role assigned successfully! {employee.name} is now assigned as {new_role_name}."
        else:
            employee.role = None
            new_role_name = 'No Role'
            message = f"Role removed successfully! {employee.name} no longer has an assigned role."
        
        current_app.logger.info(f"About to commit changes: {employee.name} -> {new_role_name}")
        db.session.commit()
        current_app.logger.info(f"Changes committed successfully")
        
        # Log the role change
        current_app.logger.info(f"Role assignment: {employee.name} (ID: {employee.id}) - {old_role_name} → {new_role_name}")
        current_app.logger.info("=== ASSIGN ROLE DEBUG END ===")
        
        flash(message, 'success')
        return redirect(url_for('admin.roles'))
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in assign_role: {str(e)}")
        current_app.logger.error(f"Exception type: {type(e)}")
        import traceback
        current_app.logger.error(f"Traceback: {traceback.format_exc()}")
        flash(f'Error assigning role: {str(e)}', 'error')
        return redirect(url_for('admin.roles'))

@admin_bp.route('/assign-employee-role', methods=['POST'])
@role_required([Roles.SUPER_HQ])  
def assign_employee_role():
    # Legacy endpoint - redirect to new assign_role endpoint
    return assign_role()

@admin_bp.route('/remove-employee-role', methods=['POST'])
@role_required([Roles.SUPER_HQ])
def remove_employee_role():
    try:
        data = request.get_json()
        employee_id = data.get('employee_id')
        
        # Get the employee
        employee = Employee.query.get(employee_id)
        if not employee:
            flash('Employee not found', 'error')
            return redirect(url_for('admin.roles'))
        
        # Remove employee role
        old_role = employee.role
        employee.role = None
        db.session.commit()
        
        # Send notification email if employee has email
        try:
            if employee.email:
                from utils.email import send_email
                subject = "Role Removal Notification"
                body = f"""Dear {employee.name},

Your role assignment has been removed from the Construction Management System.

Previous Role: {old_role or 'No Role'}
Current Status: No Role Assigned

Please contact your administrator if you believe this is an error.

Best regards,
Construction Management Team"""
                
                send_email(employee.email, subject, body)
        except Exception as email_error:
            current_app.logger.warning(f'Failed to send role removal email to {employee.email}: {str(email_error)}')
        
        flash(f'Role removed successfully for {employee.name}', 'success')
        return redirect(url_for('admin.roles'))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error removing role: {str(e)}')
        flash(f'Error removing role: {str(e)}', 'error')
        return redirect(url_for('admin.roles'))

# Reporting Lines Management Views
@admin_bp.route('/reporting-lines-view')
@role_required([Roles.SUPER_HQ])
def reporting_lines_view():
    try:
        lines = ReportingLine.query.all()
        employees = Employee.query.all()
        # Create a list with manager and staff names
        reporting_data = []
        for line in lines:
            manager = Employee.query.get(line.manager_id)
            staff = Employee.query.get(line.staff_id)
            reporting_data.append({
                'id': line.id,
                'manager_id': line.manager_id,
                'staff_id': line.staff_id,
                'manager_name': manager.name if manager else 'Unknown',
                'staff_name': staff.name if staff else 'Unknown'
            })
        return render_template('admin/reporting_lines.html', 
                             reporting_data=reporting_data, 
                             employees=employees)
    except Exception as e:
        flash(f'Error loading reporting lines: {str(e)}', 'error')
        return render_template('error.html'), 500

# Approval Hierarchy Management Views
@admin_bp.route('/approval-hierarchy-view')
@role_required([Roles.SUPER_HQ])
def approval_hierarchy_view():
    try:
        hierarchies = ApprovalHierarchy.query.all()
        roles = Role.query.all()
        # Create hierarchy data with role names
        hierarchy_data = []
        for h in hierarchies:
            role = Role.query.get(h.role_id)
            hierarchy_data.append({
                'id': h.id,
                'process': h.process,
                'level': h.level,
                'role_id': h.role_id,
                'role_name': role.name if role else 'Unknown'
            })
        return render_template('admin/approval_hierarchy.html', 
                             hierarchy_data=hierarchy_data, 
                             roles=roles)
    except Exception as e:
        flash(f'Error loading approval hierarchy: {str(e)}', 'error')
        return render_template('error.html'), 500

# Permissions Management Views
@admin_bp.route('/permissions-view')
@role_required([Roles.SUPER_HQ])
def permissions_view():
    try:
        permissions = Permission.query.all()
        roles = Role.query.all()
        # Create permissions data with role names
        permission_data = []
        for p in permissions:
            role = Role.query.get(p.role_id)
            permission_data.append({
                'id': p.id,
                'role_id': p.role_id,
                'resource': p.resource,
                'action': p.action,
                'role_name': role.name if role else 'Unknown'
            })
        return render_template('admin/permissions.html', 
                             permission_data=permission_data, 
                             roles=roles)
    except Exception as e:
        flash(f'Error loading permissions: {str(e)}', 'error')
        return render_template('error.html'), 500

# Oversight Reports View
@admin_bp.route('/oversight-reports-view')
@role_required([Roles.SUPER_HQ])
def oversight_reports_view():
    try:
        # Get actual business metrics from database
        project_count = Project.query.count() or 0
        active_projects = Project.query.filter(
            Project.status.in_(['Active', 'In Progress', 'Ongoing'])
        ).count() or 0
        employee_count = Employee.query.count() or 0
        
        # Get incident data
        open_incidents = Incident.query.filter_by(status='Open').count() or 0
        total_incidents_this_month = Incident.query.filter(
            Incident.date_reported >= datetime.now().replace(day=1).date()
        ).count() or 0
        
        # Calculate actual budget metrics
        total_budget = db.session.query(db.func.sum(Project.budget)).scalar() or 0
        
        # Get equipment/asset counts
        active_equipment = Asset.query.filter_by(status='Active').count() or 0
        maintenance_equipment = Asset.query.filter(
            Asset.status.in_(['Maintenance', 'Under Maintenance'])
        ).count() or 0
        inactive_equipment = Asset.query.filter(
            Asset.status.in_(['Retired', 'Inactive', 'Out of Service'])
        ).count() or 0
        
        # Calculate equipment utilization
        total_equipment = active_equipment + maintenance_equipment + inactive_equipment
        equipment_utilization = round(
            (active_equipment / total_equipment * 100) if total_equipment > 0 else 0, 1
        )
        
        # Get purchase order data
        pending_orders_value = db.session.query(
            db.func.sum(PurchaseOrder.total_amount)
        ).filter_by(status='Pending').scalar() or 0
        
        # Calculate spent amount from completed orders
        spent_amount = db.session.query(
            db.func.sum(PurchaseOrder.total_amount)
        ).filter(PurchaseOrder.status.in_(['Completed', 'Delivered'])).scalar() or 0
        
        # Calculate budget utilization percentage
        budget_percentage = round(
            (spent_amount / total_budget * 100) if total_budget > 0 else 0, 1
        )
        
        # Get recent submissions from multiple sources
        recent_submissions = []
        
        # Add recent projects
        recent_projects = Project.query.order_by(Project.created_at.desc()).limit(3).all()
        for project in recent_projects:
            recent_submissions.append({
                'type': 'project',
                'title': f"Project: {project.name}",
                'department': 'Construction',
                'date': project.created_at.strftime('%Y-%m-%d') if project.created_at else 'N/A',
                'status': project.status or 'Active'
            })
        
        # Add recent incidents
        recent_incidents = Incident.query.order_by(Incident.date_reported.desc()).limit(2).all()
        for incident in recent_incidents:
            recent_submissions.append({
                'type': 'incident',
                'title': f"Safety Report: {incident.title}",
                'department': 'Safety',
                'date': incident.date_reported.strftime('%Y-%m-%d') if incident.date_reported else 'N/A',
                'status': incident.status or 'Open'
            })
        
        # Add recent purchase orders
        recent_orders = PurchaseOrder.query.order_by(PurchaseOrder.created_at.desc()).limit(2).all()
        for order in recent_orders:
            recent_submissions.append({
                'type': 'order',
                'title': f"Purchase Order: {order.order_number}",
                'department': 'Procurement',
                'date': order.created_at.strftime('%Y-%m-%d') if order.created_at else 'N/A',
                'status': order.status or 'Pending'
            })
        
        # Get project progress data for active projects
        project_progress = []
        active_project_list = Project.query.filter(
            Project.status.in_(['Active', 'In Progress', 'Ongoing'])
        ).limit(5).all()
        
        for project in active_project_list:
            # Calculate progress based on timeline if dates are available
            progress = project.progress if hasattr(project, 'progress') and project.progress else 0
            
            if not progress and project.start_date and project.end_date:
                total_days = (project.end_date - project.start_date).days
                if total_days > 0:
                    days_elapsed = (datetime.now().date() - project.start_date).days
                    progress = min(100, max(0, round((days_elapsed / total_days * 100))))
                else:
                    progress = 50  # Default for same-day projects
            elif not progress:
                progress = 25  # Default progress for projects without timeline
            
            project_progress.append({
                'name': project.name,
                'progress': progress,
                'due_date': project.end_date.strftime('%Y-%m-%d') if project.end_date else None,
                'budget': project.budget
            })
        
        # Calculate safety metrics
        recent_incident = Incident.query.order_by(Incident.date_reported.desc()).first()
        days_since_incident = 0
        if recent_incident and recent_incident.date_reported:
            if isinstance(recent_incident.date_reported, datetime):
                days_since_incident = (datetime.now().date() - recent_incident.date_reported.date()).days
            else:
                days_since_incident = (datetime.now().date() - recent_incident.date_reported).days
        
        # Mock safety calculations (could be improved with actual training data)
        safety_training_completion = max(50, 100 - (total_incidents_this_month * 10))
        safety_score = max(40, 100 - (total_incidents_this_month * 8))
        
        # Get recent business activities
        recent_activities = []
        
        # Add recent project activities
        for project in recent_projects[:2]:
            recent_activities.append({
                'type': 'project',
                'description': f'Project created: {project.name}',
                'department': f'Construction - {project.project_manager}' if project.project_manager else 'Construction',
                'timestamp': project.created_at.strftime('%Y-%m-%d %H:%M') if project.created_at else 'N/A',
                'priority': 'High' if project.budget and project.budget > 1000000 else 'Medium'
            })
        
        # Add recent safety activities
        for incident in recent_incidents[:2]:
            recent_activities.append({
                'type': 'safety',
                'description': f'Incident reported: {incident.title}',
                'department': f'Safety - {incident.reported_by}' if incident.reported_by else 'Safety',
                'timestamp': incident.date_reported.strftime('%Y-%m-%d') if incident.date_reported else 'N/A',
                'priority': incident.severity if incident.severity else 'Medium'
            })
        
        # Add recent financial activities
        for order in recent_orders[:2]:
            recent_activities.append({
                'type': 'financial',
                'description': f'Purchase order: {order.order_number}',
                'department': f'Procurement - {order.supplier}' if order.supplier else 'Procurement',
                'timestamp': order.created_at.strftime('%Y-%m-%d %H:%M') if order.created_at else 'N/A',
                'priority': 'High' if order.total_amount and order.total_amount > 500000 else 'Low'
            })
        
        # Generate comprehensive business oversight report
        report_data = {
            # Key metrics for the dashboard cards
            'project_count': project_count,
            'pending_reports': open_incidents,  # Using open incidents as pending reports
            'budget_percentage': budget_percentage,
            'incident_count': total_incidents_this_month,
            'active_equipment': active_equipment,
            
            # Equipment metrics
            'maintenance_equipment': maintenance_equipment,
            'inactive_equipment': inactive_equipment,
            'equipment_utilization': equipment_utilization,
            
            # Financial metrics
            'total_budget': total_budget,
            'spent_amount': spent_amount,
            'pending_orders_value': pending_orders_value,
            
            # Safety metrics
            'days_since_incident': days_since_incident,
            'safety_training_completion': safety_training_completion,
            'safety_score': safety_score,
            
            # Data lists
            'recent_submissions': recent_submissions,
            'project_progress': project_progress,
            'recent_activities': recent_activities
        }
        
        return render_template('admin/oversight_reports.html', report=report_data)
    except Exception as e:
        current_app.logger.error(f'Error in oversight_reports_view: {str(e)}')
        flash(f'Error loading oversight reports: {str(e)}', 'error')
        return render_template('error.html'), 500

# POST/GET /admin/roles
@admin_bp.route('/roles', methods=['POST', 'GET'])
def manage_roles():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        role_name = data.get('name')
        if role_name:
            role = Role(name=role_name)
            db.session.add(role)
            db.session.commit()
            flash(f'Role "{role_name}" created successfully', 'success')
        else:
            flash('Role name is required', 'error')
        return redirect(url_for('admin.roles'))
    
    # For GET requests, redirect to the roles view page
    return redirect(url_for('admin.roles_view'))

# POST/GET /admin/reporting-lines
@admin_bp.route('/reporting-lines', methods=['POST', 'GET'])
def manage_reporting_lines():
    if request.method == 'POST':
        try:
            data = request.get_json()
            manager_id = data.get('manager_id')
            staff_id = data.get('staff_id')
            
            # Validation
            if not manager_id or not staff_id:
                flash('Both manager and staff must be selected', 'error')
                return redirect(url_for('admin.reporting_lines_view'))
                
            if manager_id == staff_id:
                flash('An employee cannot report to themselves', 'error')
                return redirect(url_for('admin.reporting_lines_view'))
                
            # Check if reporting line already exists
            existing = ReportingLine.query.filter_by(manager_id=manager_id, staff_id=staff_id).first()
            if existing:
                flash('This reporting relationship already exists', 'error')
                return redirect(url_for('admin.reporting_lines_view'))
            
            rl = ReportingLine(manager_id=manager_id, staff_id=staff_id)
            db.session.add(rl)
            db.session.commit()
            
            # Notify manager and staff
            from models import Employee
            from utils.email import send_email
            manager = Employee.query.get(manager_id)
            staff = Employee.query.get(staff_id)
            if manager and hasattr(manager, 'email') and manager.email:
                subject = "Reporting Line Assigned"
                body = f"Dear {manager.name},\nYou are now the manager for {staff.name if staff else 'staff member'}."
                send_email(manager.email, subject, body)
            if staff and hasattr(staff, 'email') and staff.email:
                subject = "Reporting Line Assigned"
                body = f"Dear {staff.name},\nYou now report to {manager.name if manager else 'your manager'}."
                send_email(staff.email, subject, body)
                
            current_app.logger.info(f"Reporting line created: {staff.name if staff else staff_id} reports to {manager.name if manager else manager_id}")
            flash('Reporting line created successfully', 'success')
            return redirect(url_for('admin.reporting_lines_view'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating reporting line: {str(e)}")
            flash(f'Error creating reporting line: {str(e)}', 'error')
            return redirect(url_for('admin.reporting_lines_view'))
            
    # For GET requests, redirect to the reporting lines view page
    return redirect(url_for('admin.reporting_lines_view'))

# DELETE /admin/reporting-lines/<id>
@admin_bp.route('/reporting-lines/<int:line_id>', methods=['DELETE'])
def delete_reporting_line(line_id):
    try:
        reporting_line = ReportingLine.query.get_or_404(line_id)
        
        # Get employee details for logging before deletion
        from models import Employee
        manager = Employee.query.get(reporting_line.manager_id)
        staff = Employee.query.get(reporting_line.staff_id)
        
        db.session.delete(reporting_line)
        db.session.commit()
        
        current_app.logger.info(f"Reporting line deleted: {staff.name if staff else reporting_line.staff_id} no longer reports to {manager.name if manager else reporting_line.manager_id}")
        
        flash('Reporting line removed successfully', 'success')
        return redirect(url_for('admin.manage_reporting_lines'))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting reporting line {line_id}: {str(e)}")
        flash(f'Error removing reporting line: {str(e)}', 'error')
        return redirect(url_for('admin.manage_reporting_lines'))

# POST/GET /admin/approval-hierarchy
@admin_bp.route('/approval-hierarchy', methods=['POST', 'GET'])
def manage_approval_hierarchy():
    if request.method == 'POST':
        data = request.get_json()
        ah = ApprovalHierarchy(process=data.get('process'), level=data.get('level'), role_id=data.get('role_id'))
        db.session.add(ah)
        db.session.commit()
        # Notify the user(s) in this role
        from models import Employee, Role
        from utils.email import send_email
        role = Role.query.get(data.get('role_id'))
        if role:
            # Find all employees with this role
            employees = Employee.query.filter_by(role=role.name).all() if hasattr(Employee, 'role') else []
            for emp in employees:
                if hasattr(emp, 'email') and emp.email:
                    subject = f"Approval Level Assigned: {ah.process}"
                    body = f"Dear {emp.name},\nYou have been assigned as an approver for {ah.process} at level {ah.level}."
                    send_email(emp.email, subject, body)
        return jsonify({'status': 'success', 'id': ah.id})
    hierarchy = ApprovalHierarchy.query.all()
    return jsonify([{'id': h.id, 'process': h.process, 'level': h.level, 'role_id': h.role_id} for h in hierarchy])

# POST/GET /admin/permissions
@admin_bp.route('/permissions', methods=['POST', 'GET'])
def manage_permissions():
    if request.method == 'POST':
        data = request.get_json()
        perm = Permission(role_id=data.get('role_id'), resource=data.get('resource'), action=data.get('action'))
        db.session.add(perm)
        db.session.commit()
        # Notify users in this role
        from models import Employee, Role
        from utils.email import send_email
        role = Role.query.get(data.get('role_id'))
        if role:
            employees = Employee.query.filter_by(role=role.name).all() if hasattr(Employee, 'role') else []
            for emp in employees:
                if hasattr(emp, 'email') and emp.email:
                    subject = f"Permission Assigned: {perm.resource}"
                    body = f"Dear {emp.name},\nYou have been granted {perm.action} permission for {perm.resource}."
                    send_email(emp.email, subject, body)
        return jsonify({'status': 'success', 'id': perm.id})
    perms = Permission.query.all()
    return jsonify([{'id': p.id, 'role_id': p.role_id, 'resource': p.resource, 'action': p.action} for p in perms])

# GET /admin/oversight-reports
@admin_bp.route('/oversight-reports', methods=['GET'])
def oversight_reports():
    # Example: count of roles, reporting lines, approval levels, permissions
    report = {
        'role_count': Role.query.count(),
        'reporting_line_count': ReportingLine.query.count(),
        'approval_hierarchy_count': ApprovalHierarchy.query.count(),
        'permission_count': Permission.query.count()
    }
    return jsonify({'status': 'success', 'report': report})

# ==================== PROJECT MANAGEMENT ENDPOINTS ====================

@admin_bp.route('/projects')
@role_required([Roles.SUPER_HQ])
def projects():
    """Display all projects with comprehensive project management dashboard"""
    try:
        projects = Project.query.order_by(Project.created_at.desc()).all()
        
        # Calculate project statistics
        total_projects = len(projects)
        active_projects = len([p for p in projects if p.status in ['Active', 'In Progress']])
        completed_projects = len([p for p in projects if p.status == 'Completed'])
        total_budget = sum([p.budget or 0 for p in projects])
        
        project_stats = {
            'total_projects': total_projects,
            'active_projects': active_projects,
            'completed_projects': completed_projects,
            'total_budget': total_budget
        }
        
        # Pass current date for template calculations
        current_date_obj = date.today()
        
        return render_template('admin/projects.html', 
                             projects=projects, 
                             project_stats=project_stats,
                             current_date_obj=current_date_obj)
    except Exception as e:
        flash(f'Error loading projects: {str(e)}', 'error')
        return render_template('error.html'), 500

@admin_bp.route('/add-project', methods=['GET', 'POST'])
@role_required([Roles.SUPER_HQ])
def add_project():
    """Add new construction project"""
    form_data = {}  # Initialize empty form data
    
    if request.method == 'POST':
        try:
            data = request.form
            form_data = data.to_dict()  # Store form data for repopulation
            
            # Validate required fields
            if not data.get('name'):
                flash('Project name is required', 'error')
                employees = Employee.query.filter_by(status='Active').order_by(Employee.name).all()
                return render_template('admin/create_project.html', employees=employees, form_data=form_data)
            
            # Handle date parsing with validation
            start_date = None
            end_date = None
            
            if data.get('start_date'):
                try:
                    start_date = datetime.strptime(data.get('start_date'), '%Y-%m-%d').date()
                except ValueError:
                    flash('Invalid start date format', 'error')
                    employees = Employee.query.filter_by(status='Active').order_by(Employee.name).all()
                    return render_template('admin/create_project.html', employees=employees, form_data=form_data)
            
            if data.get('end_date'):
                try:
                    end_date = datetime.strptime(data.get('end_date'), '%Y-%m-%d').date()
                except ValueError:
                    flash('Invalid end date format', 'error')
                    employees = Employee.query.filter_by(status='Active').order_by(Employee.name).all()
                    return render_template('admin/create_project.html', employees=employees, form_data=form_data)
            
            # Validate date logic
            if start_date and end_date and end_date < start_date:
                flash('End date cannot be before start date', 'error')
                employees = Employee.query.filter_by(status='Active').order_by(Employee.name).all()
                return render_template('admin/create_project.html', employees=employees, form_data=form_data)
            
            # Handle budget parsing
            budget = 0.0
            if data.get('budget'):
                try:
                    budget = float(data.get('budget'))
                    if budget < 0:
                        flash('Budget cannot be negative', 'error')
                        employees = Employee.query.filter_by(status='Active').order_by(Employee.name).all()
                        return render_template('admin/create_project.html', employees=employees, form_data=form_data)
                except ValueError:
                    flash('Invalid budget amount', 'error')
                    employees = Employee.query.filter_by(status='Active').order_by(Employee.name).all()
                    return render_template('admin/create_project.html', employees=employees, form_data=form_data)
            
            # Handle contingency budget
            contingency_budget = 0.0
            if data.get('contingency_budget'):
                try:
                    contingency_budget = float(data.get('contingency_budget'))
                except ValueError:
                    contingency_budget = 0.0
            
            # Create new project with enhanced fields
            project = Project(
                name=data.get('name').strip(),
                description=data.get('description', '').strip(),
                start_date=start_date,
                end_date=end_date,
                status=data.get('status', 'Planning'),
                project_manager=data.get('project_manager', '').strip(),
                budget=budget,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                # Enhanced fields
                project_type=data.get('project_type', '').strip(),
                priority=data.get('priority', 'Medium'),
                client_name=data.get('client_name', '').strip(),
                site_location=data.get('site_location', '').strip(),
                funding_source=data.get('funding_source', '').strip(),
                risk_level=data.get('risk_level', 'Low'),
                safety_requirements=data.get('safety_requirements', 'Standard'),
                regulatory_requirements=data.get('regulatory_requirements', '').strip()
            )
            
            db.session.add(project)
            db.session.commit()
            
            # Create initial budget entries
            if budget > 0:
                # Main project budget
                budget_entry = Budget(
                    project_id=project.id,
                    category='Total Project Budget',
                    allocated_amount=budget,
                    spent_amount=0.0,
                    created_at=datetime.utcnow()
                )
                db.session.add(budget_entry)
                
                # Contingency budget if specified
                if contingency_budget > 0:
                    contingency_entry = Budget(
                        project_id=project.id,
                        category='Contingency Fund',
                        allocated_amount=contingency_budget,
                        spent_amount=0.0,
                        created_at=datetime.utcnow()
                    )
                    db.session.add(contingency_entry)
                
                db.session.commit()
            
            flash(f'Project "{project.name}" created successfully!', 'success')
            return redirect(url_for('admin.projects'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error creating project: {str(e)}')
            flash(f'Error creating project: {str(e)}', 'error')
            employees = Employee.query.filter_by(status='Active').order_by(Employee.name).all()
            return render_template('admin/create_project.html', employees=employees, form_data=form_data)
    
    # GET request - show form
    try:
        employees = Employee.query.filter_by(status='Active').order_by(Employee.name).all()
        return render_template('admin/create_project.html', employees=employees, form_data=form_data)
    except Exception as e:
        current_app.logger.error(f'Error loading project form: {str(e)}')
        flash(f'Error loading form: {str(e)}', 'error')
        return redirect(url_for('admin.projects'))


@admin_bp.route('/milestones/<int:project_id>')
@role_required([Roles.SUPER_HQ])
def milestones(project_id):
    """Display milestones for a specific project"""
    try:
        project = Project.query.get_or_404(project_id)
        milestones = Milestone.query.filter_by(project_id=project_id).order_by(Milestone.due_date).all()
        
        # Calculate milestone statistics
        total_milestones = len(milestones)
        completed_milestones = len([m for m in milestones if m.status == 'Completed'])
        overdue_milestones = len([m for m in milestones if m.due_date < datetime.now().date() and m.status != 'Completed'])
        
        milestone_stats = {
            'total_milestones': total_milestones,
            'completed_milestones': completed_milestones,
            'overdue_milestones': overdue_milestones,
            'completion_rate': (completed_milestones / total_milestones * 100) if total_milestones > 0 else 0
        }
        
        # Pass current date for template calculations
        from datetime import date
        current_date_obj = date.today()
        
        return render_template('admin/projects/milestones.html', 
                             project=project, 
                             milestones=milestones, 
                             milestone_stats=milestone_stats,
                             current_date_obj=current_date_obj)
    except Exception as e:
        flash(f'Error loading milestones: {str(e)}', 'error')
        return render_template('error.html'), 500

@admin_bp.route('/add-milestone/<int:project_id>', methods=['GET', 'POST'])
@role_required([Roles.SUPER_HQ])
def add_milestone(project_id):
    """Add milestone to specific project"""
    project = Project.query.get_or_404(project_id)
    
    if request.method == 'POST':
        try:
            data = request.form
            
            milestone = Milestone(
                project_id=project_id,
                title=data.get('title'),
                due_date=datetime.strptime(data.get('due_date'), '%Y-%m-%d').date(),
                status=data.get('status', 'Pending')
            )
            
            db.session.add(milestone)
            db.session.commit()
            
            flash(f'Milestone "{milestone.title}" added successfully!', 'success')
            return redirect(url_for('admin.milestones', project_id=project_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating milestone: {str(e)}', 'error')
    
    return render_template('admin/add_milestone.html', project=project)

@admin_bp.route('/all-milestones')
@role_required([Roles.SUPER_HQ])
def all_milestones():
    """Display all milestones across all projects"""
    try:
        # Get all milestones with their associated projects
        milestones = Milestone.query.join(Project).order_by(Milestone.due_date.asc()).all()
        
        # Calculate comprehensive milestone statistics
        total_milestones = len(milestones)
        completed_milestones = len([m for m in milestones if m.status == 'Completed'])
        pending_milestones = len([m for m in milestones if m.status == 'Pending' or m.status is None])
        overdue_milestones = len([m for m in milestones if m.due_date and m.due_date < datetime.now().date() and m.status != 'Completed'])
        
        # Calculate milestones by project
        project_milestones = {}
        for milestone in milestones:
            project_name = milestone.project.name if milestone.project else 'Unknown Project'
            if project_name not in project_milestones:
                project_milestones[project_name] = {
                    'total': 0,
                    'completed': 0,
                    'pending': 0,
                    'overdue': 0,
                    'project_id': milestone.project.id if milestone.project else None
                }
            
            project_milestones[project_name]['total'] += 1
            
            if milestone.status == 'Completed':
                project_milestones[project_name]['completed'] += 1
            elif milestone.due_date and milestone.due_date < datetime.now().date() and milestone.status != 'Completed':
                project_milestones[project_name]['overdue'] += 1
            else:
                project_milestones[project_name]['pending'] += 1
        
        # Calculate upcoming milestones (next 30 days)
        next_month = datetime.now().date() + timedelta(days=30)
        upcoming_milestones = [m for m in milestones if m.due_date and m.due_date <= next_month and m.status != 'Completed']
        
        milestone_stats = {
            'total_milestones': total_milestones,
            'completed_milestones': completed_milestones,
            'pending_milestones': pending_milestones,
            'overdue_milestones': overdue_milestones,
            'completion_rate': (completed_milestones / total_milestones * 100) if total_milestones > 0 else 0,
            'upcoming_count': len(upcoming_milestones),
            'project_count': len(project_milestones)
        }
        
        return render_template('admin/all_milestones.html', 
                             milestones=milestones,
                             milestone_stats=milestone_stats,
                             project_milestones=project_milestones,
                             upcoming_milestones=upcoming_milestones,
                             today=datetime.now().date())
    except Exception as e:
        flash(f'Error loading milestones: {str(e)}', 'error')
        return render_template('error.html'), 500

@admin_bp.route('/edit-milestone/<int:milestone_id>', methods=['GET', 'POST'])
@role_required([Roles.SUPER_HQ])
def edit_milestone(milestone_id):
    """Edit milestone details"""
    milestone = Milestone.query.get_or_404(milestone_id)
    project = milestone.project
    
    if request.method == 'POST':
        try:
            data = request.form
            
            milestone.title = data.get('title')
            milestone.due_date = datetime.strptime(data.get('due_date'), '%Y-%m-%d').date()
            milestone.status = data.get('status', 'Pending')
            
            db.session.commit()
            
            flash(f'Milestone "{milestone.title}" updated successfully!', 'success')
            return redirect(url_for('admin.milestones', project_id=project.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating milestone: {str(e)}', 'error')
    
    return render_template('admin/edit_milestone.html', milestone=milestone, project=project)

@admin_bp.route('/delete-milestone/<int:milestone_id>', methods=['POST'])
@role_required([Roles.SUPER_HQ])
def delete_milestone(milestone_id):
    """Delete milestone"""
    try:
        milestone = Milestone.query.get_or_404(milestone_id)
        project_id = milestone.project_id
        title = milestone.title
        
        db.session.delete(milestone)
        db.session.commit()
        
        flash(f'Milestone "{title}" deleted successfully!', 'success')
        return redirect(url_for('admin.milestones', project_id=project_id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting milestone: {str(e)}', 'error')
        return redirect(url_for('admin.projects'))

# ==================== ASSET AND INVENTORY MANAGEMENT ====================

@admin_bp.route('/assets')
@role_required([Roles.SUPER_HQ])
def assets():
    """Display all construction assets"""
    try:
        assets = Asset.query.order_by(Asset.created_at.desc()).all()
        
        # Calculate asset statistics
        total_assets = len(assets)
        active_assets = len([a for a in assets if a.status == 'Active'])
        retired_assets = len([a for a in assets if a.status == 'Retired'])
        
        asset_stats = {
            'total_assets': total_assets,
            'active_assets': active_assets,
            'retired_assets': retired_assets,
            'asset_types': {}
        }
        
        # Group by asset type
        for asset in assets:
            asset_type = asset.type or 'Unknown'
            if asset_type not in asset_stats['asset_types']:
                asset_stats['asset_types'][asset_type] = 0
            asset_stats['asset_types'][asset_type] += 1
        
        return render_template('admin/assets.html', 
                             assets=assets, 
                             asset_stats=asset_stats)
    except Exception as e:
        flash(f'Error loading assets: {str(e)}', 'error')
        return render_template('error.html'), 500

@admin_bp.route('/add-asset', methods=['GET', 'POST'])
@role_required([Roles.SUPER_HQ])
def add_asset():
    """Add new construction asset"""
    if request.method == 'POST':
        try:
            data = request.form
            
            asset = Asset(
                name=data.get('name'),
                type=data.get('type'),
                status=data.get('status', 'Active'),
                location=data.get('location'),
                purchase_date=datetime.strptime(data.get('purchase_date'), '%Y-%m-%d').date() if data.get('purchase_date') else None
            )
            
            db.session.add(asset)
            db.session.commit()
            
            flash(f'Asset "{asset.name}" added successfully!', 'success')
            return redirect(url_for('admin.assets'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating asset: {str(e)}', 'error')
    
    return render_template('admin/add_asset.html')

@admin_bp.route('/asset/<int:asset_id>')
@role_required([Roles.SUPER_HQ])
def view_asset(asset_id):
    """API endpoint to fetch individual asset data"""
    try:
        asset = Asset.query.get_or_404(asset_id)
        
        asset_data = {
            'id': asset.id,
            'name': asset.name,
            'type': asset.type,
            'status': asset.status,
            'location': asset.location,
            'purchase_date': asset.purchase_date.strftime('%Y-%m-%d') if asset.purchase_date else None,
            'retired_date': asset.retired_date.strftime('%Y-%m-%d') if asset.retired_date else None,
            'created_at': asset.created_at.strftime('%Y-%m-%d %H:%M') if asset.created_at else None
        }
        
        return jsonify({
            'success': True,
            'asset': asset_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@admin_bp.route('/edit-asset/<int:asset_id>', methods=['GET', 'POST'])
@role_required([Roles.SUPER_HQ])
def edit_asset(asset_id):
    """Edit existing asset"""
    asset = Asset.query.get_or_404(asset_id)
    
    if request.method == 'POST':
        try:
            data = request.form
            
            # Update asset fields
            asset.name = data.get('name')
            asset.type = data.get('type')
            asset.status = data.get('status', 'Active')
            asset.location = data.get('location')
            
            # Handle purchase date
            purchase_date = data.get('purchase_date')
            if purchase_date:
                asset.purchase_date = datetime.strptime(purchase_date, '%Y-%m-%d').date()
            else:
                asset.purchase_date = None
            
            db.session.commit()
            
            flash(f'Asset "{asset.name}" updated successfully!', 'success')
            return redirect(url_for('admin.assets'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating asset: {str(e)}', 'error')
    
    return render_template('admin/edit_asset.html', asset=asset)

@admin_bp.route('/retire-asset/<int:asset_id>', methods=['POST'])
@role_required([Roles.SUPER_HQ])
def retire_asset(asset_id):
    """Retire an asset"""
    try:
        asset = Asset.query.get_or_404(asset_id)
        asset_name = asset.name
        
        asset.status = 'Retired'
        asset.retired_date = datetime.utcnow().date()
        
        db.session.commit()
        
        flash(f'Asset "{asset_name}" retired successfully!', 'success')
        return redirect(url_for('admin.assets'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error retiring asset: {str(e)}', 'error')
        return redirect(url_for('admin.assets'))

@admin_bp.route('/delete-asset/<int:asset_id>', methods=['POST'])
@role_required([Roles.SUPER_HQ])
def delete_asset(asset_id):
    """Delete asset"""
    try:
        asset = Asset.query.get_or_404(asset_id)
        asset_name = asset.name
        
        db.session.delete(asset)
        db.session.commit()
        
        flash(f'Asset "{asset_name}" deleted successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting asset: {str(e)}', 'error')
    
    return redirect(url_for('admin.assets'))

@admin_bp.route('/stock')
@role_required([Roles.SUPER_HQ])
def stock():
    """Display stock/inventory management"""
    try:
        stock_items = Stock.query.order_by(Stock.created_at.desc()).all()
        
        # Calculate stock statistics
        total_items = len(stock_items)
        low_stock_items = len([s for s in stock_items if s.quantity <= s.low_stock_threshold])
        out_of_stock = len([s for s in stock_items if s.quantity == 0])
        available_items = len([s for s in stock_items if s.status == 'Available'])
        
        stock_stats = {
            'total_items': total_items,
            'low_stock_items': low_stock_items,
            'out_of_stock': out_of_stock,
            'available_items': available_items
        }
        
        return render_template('admin/stock.html', 
                             stock_items=stock_items, 
                             stock_stats=stock_stats)
    except Exception as e:
        flash(f'Error loading stock: {str(e)}', 'error')
        return render_template('error.html'), 500

@admin_bp.route('/add-stock', methods=['GET', 'POST'])
@role_required([Roles.SUPER_HQ])
def add_stock():
    """Add new stock item"""
    if request.method == 'POST':
        try:
            data = request.form
            
            stock_item = Stock(
                name=data.get('name'),
                quantity=int(data.get('quantity', 0)),
                unit=data.get('unit'),
                status=data.get('status', 'Available'),
                low_stock_threshold=int(data.get('low_stock_threshold', 10))
            )
            
            db.session.add(stock_item)
            db.session.commit()
            
            flash(f'Stock item "{stock_item.name}" added successfully!', 'success')
            return redirect(url_for('admin.stock'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating stock item: {str(e)}', 'error')
    
    return render_template('admin/add_stock.html')

@admin_bp.route('/stock/<int:stock_id>')
@role_required([Roles.SUPER_HQ])
def view_stock_item(stock_id):
    """API endpoint to fetch individual stock item data"""
    try:
        stock_item = Stock.query.get_or_404(stock_id)
        
        stock_data = {
            'id': stock_item.id,
            'name': stock_item.name,
            'quantity': stock_item.quantity,
            'unit': stock_item.unit,
            'status': stock_item.status,
            'low_stock_threshold': stock_item.low_stock_threshold,
            'created_at': stock_item.created_at.strftime('%Y-%m-%d %H:%M') if stock_item.created_at else None
        }
        
        return jsonify({
            'success': True,
            'stock_item': stock_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@admin_bp.route('/edit-stock/<int:stock_id>', methods=['GET', 'POST'])
@role_required([Roles.SUPER_HQ])
def edit_stock_item(stock_id):
    """Edit existing stock item"""
    stock_item = Stock.query.get_or_404(stock_id)
    
    if request.method == 'POST':
        try:
            data = request.form
            
            # Update stock item fields
            stock_item.name = data.get('name')
            stock_item.quantity = int(data.get('quantity', 0))
            stock_item.unit = data.get('unit')
            stock_item.status = data.get('status', 'Available')
            stock_item.low_stock_threshold = int(data.get('low_stock_threshold', 10))
            
            db.session.commit()
            
            flash(f'Stock item "{stock_item.name}" updated successfully!', 'success')
            return redirect(url_for('admin.stock'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating stock item: {str(e)}', 'error')
    
    return render_template('admin/edit_stock.html', stock_item=stock_item)

@admin_bp.route('/adjust-stock/<int:stock_id>', methods=['POST'])
@role_required([Roles.SUPER_HQ])
def adjust_stock_quantity(stock_id):
    """Adjust stock quantity"""
    try:
        stock_item = Stock.query.get_or_404(stock_id)
        
        # Try JSON first, then form data
        data = request.get_json() or request.form
        
        adjustment_type = data.get('adjustment_type')
        quantity = int(data.get('quantity', 0))
        reason = data.get('reason', '')
        
        old_quantity = stock_item.quantity
        
        if adjustment_type == 'add':
            stock_item.quantity += quantity
        elif adjustment_type == 'remove':
            stock_item.quantity = max(0, stock_item.quantity - quantity)
        elif adjustment_type == 'set':
            stock_item.quantity = quantity
        
        db.session.commit()
        
        # Log the adjustment (you could create an audit table for this)
        flash_message = f'Stock adjusted from {old_quantity} to {stock_item.quantity}'
        if reason:
            flash_message += f' (Reason: {reason})'
        
        flash(flash_message, 'success')
        return redirect(url_for('admin.stock'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error adjusting stock: {str(e)}', 'error')
        return redirect(url_for('admin.stock'))

@admin_bp.route('/delete-stock/<int:stock_id>', methods=['POST'])
@role_required([Roles.SUPER_HQ])
def delete_stock_item(stock_id):
    """Delete stock item"""
    try:
        stock_item = Stock.query.get_or_404(stock_id)
        stock_name = stock_item.name
        
        db.session.delete(stock_item)
        db.session.commit()
        
        flash(f'Stock item "{stock_name}" deleted successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting stock item: {str(e)}', 'error')
    
    return redirect(url_for('admin.stock'))

# ==================== EQUIPMENT MANAGEMENT ====================

@admin_bp.route('/equipment')
@role_required([Roles.SUPER_HQ])
def equipment():
    """Display all construction equipment"""
    try:
        equipment = Equipment.query.order_by(Equipment.id.desc()).all()
        
        # Calculate equipment statistics
        total_equipment = len(equipment)
        active_equipment = len([e for e in equipment if e.status == 'Active'])
        maintenance_equipment = len([e for e in equipment if e.status in ['Maintenance', 'Under Maintenance']])
        inactive_equipment = len([e for e in equipment if e.status in ['Retired', 'Inactive', 'Out of Service']])
        
        equipment_stats = {
            'total_equipment': total_equipment,
            'active_equipment': active_equipment,
            'maintenance_equipment': maintenance_equipment,
            'inactive_equipment': inactive_equipment,
            'utilization_rate': (active_equipment / total_equipment * 100) if total_equipment > 0 else 0,
            'equipment_by_status': {}
        }
        
        # Group by equipment status
        for equip in equipment:
            equipment_status = equip.status or 'Unknown'
            if equipment_status not in equipment_stats['equipment_by_status']:
                equipment_stats['equipment_by_status'][equipment_status] = 0
            equipment_stats['equipment_by_status'][equipment_status] += 1
        
        return render_template('admin/equipment.html', 
                             equipment=equipment, 
                             equipment_stats=equipment_stats)
    except Exception as e:
        flash(f'Error loading equipment: {str(e)}', 'error')
        return render_template('error.html'), 500

@admin_bp.route('/equipment/<int:equipment_id>')
@role_required([Roles.SUPER_HQ])
def view_equipment(equipment_id):
    """API endpoint to fetch individual equipment data"""
    try:
        equipment = Equipment.query.get_or_404(equipment_id)
        
        equipment_data = {
            'id': equipment.id,
            'name': equipment.name,
            'status': equipment.status,
            'machine_hours': equipment.machine_hours,
            'diesel_consumption': equipment.diesel_consumption,
            'maintenance_due': equipment.maintenance_due.strftime('%Y-%m-%d') if equipment.maintenance_due else None,
            'remarks': equipment.remarks,
            'created_at': equipment.id  # Using id as a placeholder since there's no created_at field
        }
        
        return jsonify({
            'success': True,
            'equipment': equipment_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@admin_bp.route('/add-equipment', methods=['GET', 'POST'])
@role_required([Roles.SUPER_HQ])
def add_equipment():
    """Add new construction equipment"""
    if request.method == 'POST':
        try:
            data = request.form
            
            equipment = Equipment(
                name=data.get('name'),
                status=data.get('status', 'Active'),
                remarks=data.get('description'),  # Map description to remarks
                machine_hours=float(data.get('machine_hours', 0)) if data.get('machine_hours') else 0,
                diesel_consumption=float(data.get('diesel_consumption', 0)) if data.get('diesel_consumption') else 0,
                maintenance_due=datetime.strptime(data.get('last_maintenance_date'), '%Y-%m-%d').date() if data.get('last_maintenance_date') else None
            )
            
            db.session.add(equipment)
            db.session.commit()
            
            flash(f'Equipment "{equipment.name}" added successfully!', 'success')
            return redirect(url_for('admin.equipment'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating equipment: {str(e)}', 'error')
    
    return render_template('admin/add_equipment.html')

@admin_bp.route('/edit-equipment/<int:equipment_id>', methods=['GET', 'POST'])
@role_required([Roles.SUPER_HQ])
def edit_equipment(equipment_id):
    """Edit existing equipment"""
    equipment = Equipment.query.get_or_404(equipment_id)
    
    if request.method == 'POST':
        try:
            data = request.form
            
            # Update equipment fields
            equipment.name = data.get('name')
            equipment.status = data.get('status', 'Active')
            equipment.remarks = data.get('remarks')
            equipment.machine_hours = float(data.get('machine_hours', 0)) if data.get('machine_hours') else 0
            equipment.diesel_consumption = float(data.get('diesel_consumption', 0)) if data.get('diesel_consumption') else 0
            
            # Handle maintenance due date
            maintenance_due = data.get('maintenance_due')
            if maintenance_due:
                equipment.maintenance_due = datetime.strptime(maintenance_due, '%Y-%m-%d').date()
            else:
                equipment.maintenance_due = None
            
            db.session.commit()
            
            flash(f'Equipment "{equipment.name}" updated successfully!', 'success')
            return redirect(url_for('admin.equipment'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating equipment: {str(e)}', 'error')
    
    return render_template('admin/edit_equipment.html', equipment=equipment)

@admin_bp.route('/delete-equipment/<int:equipment_id>', methods=['POST'])
@role_required([Roles.SUPER_HQ])
def delete_equipment(equipment_id):
    """Delete equipment"""
    try:
        equipment = Equipment.query.get_or_404(equipment_id)
        equipment_name = equipment.name
        
        db.session.delete(equipment)
        db.session.commit()
        
        flash(f'Equipment "{equipment_name}" deleted successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting equipment: {str(e)}', 'error')
    
    return redirect(url_for('admin.equipment'))

# ==================== MONITORING ENDPOINTS ====================

@admin_bp.route('/incidents')
@role_required([Roles.SUPER_HQ])
def incidents():
    """Display all site incidents"""
    try:
        incidents = Incident.query.order_by(Incident.date_reported.desc()).all()
        
        # Calculate incident statistics
        total_incidents = len(incidents)
        open_incidents = len([i for i in incidents if i.status == 'Open'])
        resolved_incidents = len([i for i in incidents if i.status == 'Resolved'])
        critical_incidents = len([i for i in incidents if i.severity == 'Critical'])
        
        incident_stats = {
            'total_incidents': total_incidents,
            'open_incidents': open_incidents,
            'resolved_incidents': resolved_incidents,
            'critical_incidents': critical_incidents
        }
        
        return render_template('admin/incidents.html', 
                             incidents=incidents, 
                             incident_stats=incident_stats)
    except Exception as e:
        flash(f'Error loading incidents: {str(e)}', 'error')
        return render_template('error.html'), 500

@admin_bp.route('/add-incident', methods=['GET', 'POST'])
@role_required([Roles.SUPER_HQ])
def add_incident():
    """Report new safety incident"""
    if request.method == 'POST':
        try:
            data = request.form
            
            incident = Incident(
                title=data.get('title'),
                description=data.get('description'),
                status=data.get('status', 'Open'),
                reported_by=data.get('reported_by'),
                severity=data.get('severity', 'Medium')
            )
            
            db.session.add(incident)
            db.session.commit()
            
            flash(f'Incident "{incident.title}" reported successfully!', 'success')
            return redirect(url_for('admin.incidents'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error reporting incident: {str(e)}', 'error')
    
    employees = Employee.query.all()
    return render_template('admin/add_incident.html', employees=employees)

@admin_bp.route('/alerts')
@role_required([Roles.SUPER_HQ])
def alerts():
    """Display all system alerts"""
    try:
        alerts = Alert.query.order_by(Alert.created_at.desc()).all()
        
        # Calculate alert statistics
        total_alerts = len(alerts)
        active_alerts = len([a for a in alerts if a.status == 'Active'])
        critical_alerts = len([a for a in alerts if a.severity == 'Critical'])
        
        alert_stats = {
            'total_alerts': total_alerts,
            'active_alerts': active_alerts,
            'critical_alerts': critical_alerts
        }
        
        return render_template('admin/alerts.html', 
                             alerts=alerts, 
                             alert_stats=alert_stats)
    except Exception as e:
        flash(f'Error loading alerts: {str(e)}', 'error')
        return render_template('error.html'), 500

@admin_bp.route('/add-alert', methods=['GET', 'POST'])
@role_required([Roles.SUPER_HQ])
def add_alert():
    """Create new system alert"""
    if request.method == 'POST':
        try:
            data = request.form
            
            alert = Alert(
                title=data.get('title'),
                type=data.get('type'),
                description=data.get('description'),
                status=data.get('status', 'Active'),
                severity=data.get('severity', 'Medium')
            )
            
            db.session.add(alert)
            db.session.commit()
            
            flash(f'Alert "{alert.title}" created successfully!', 'success')
            return redirect(url_for('admin.alerts'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating alert: {str(e)}', 'error')
    
    return render_template('admin/add_alert.html')

# ==================== SCHEDULING ENDPOINTS ====================

@admin_bp.route('/schedules')
@role_required([Roles.SUPER_HQ])
def schedules():
    """Display all project schedules with filtering and enhanced business logic"""
    try:
        # Get filter parameters
        project_filter = request.args.get('project', '')
        status_filter = request.args.get('status', '')
        type_filter = request.args.get('type', '')
        view_schedule_id = request.args.get('view_schedule', '')
        
        # Base query with project relationship
        schedules_query = Schedule.query.join(Project)
        
        # Apply filters
        if project_filter:
            schedules_query = schedules_query.filter(Schedule.project_id == project_filter)
        if status_filter:
            schedules_query = schedules_query.filter(Schedule.status == status_filter)
        if type_filter:
            schedules_query = schedules_query.filter(Schedule.type == type_filter)
        
        # Get schedules ordered by start time
        schedules = schedules_query.order_by(Schedule.start_time.asc()).all()
        
        # Get all projects for filters
        projects = Project.query.filter_by(status='Active').order_by(Project.name).all()
        
        # Get specific schedule for viewing if requested
        view_schedule = None
        if view_schedule_id:
            try:
                view_schedule = Schedule.query.get(int(view_schedule_id))
            except (ValueError, TypeError):
                pass
        
        # Enhanced schedule statistics with business logic
        from datetime import datetime, timedelta
        now = datetime.now()
        today = now.date()
        
        # Categorize schedules
        upcoming_schedules = [s for s in schedules if s.start_time.date() > today]
        ongoing_schedules = [s for s in schedules if s.start_time.date() <= today <= s.end_time.date() and s.status not in ['Completed', 'Cancelled']]
        overdue_schedules = [s for s in schedules if s.end_time.date() < today and s.status not in ['Completed', 'Cancelled']]
        completed_schedules = [s for s in schedules if s.status == 'Completed']
        
        # This week's schedules
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        this_week_schedules = [s for s in schedules if week_start <= s.start_time.date() <= week_end]
        
        # Calculate project schedule health
        project_schedule_health = {}
        for project in projects:
            project_schedules = [s for s in schedules if s.project_id == project.id]
            if project_schedules:
                total = len(project_schedules)
                completed = len([s for s in project_schedules if s.status == 'Completed'])
                overdue = len([s for s in project_schedules if s.end_time.date() < today and s.status not in ['Completed', 'Cancelled']])
                
                health_score = 100
                if total > 0:
                    completion_rate = (completed / total) * 100
                    overdue_penalty = (overdue / total) * 50  # 50% penalty for overdue
                    health_score = max(0, completion_rate - overdue_penalty)
                
                project_schedule_health[project.id] = {
                    'health_score': round(health_score, 1),
                    'total': total,
                    'completed': completed,
                    'overdue': overdue
                }
        
        schedule_stats = {
            'total_schedules': len(schedules),
            'upcoming_schedules': len(upcoming_schedules),
            'ongoing_schedules': len(ongoing_schedules),
            'overdue_schedules': len(overdue_schedules),
            'completed_schedules': len(completed_schedules),
            'this_week_schedules': len(this_week_schedules),
            'project_health': project_schedule_health
        }
        
        # Schedule types for filtering
        schedule_types = ['Planning', 'Construction', 'Inspection', 'Meeting', 'Delivery', 'Maintenance', 'Other']
        schedule_statuses = ['Scheduled', 'In Progress', 'Completed', 'Cancelled', 'Postponed']
        
        return render_template('admin/schedules.html', 
                             schedules=schedules, 
                             projects=projects,
                             schedule_stats=schedule_stats,
                             project_health=project_schedule_health,
                             schedule_types=schedule_types,
                             schedule_statuses=schedule_statuses,
                             project_filter=project_filter,
                             status_filter=status_filter,
                             type_filter=type_filter,
                             view_schedule=view_schedule,
                             upcoming_schedules=upcoming_schedules,
                             ongoing_schedules=ongoing_schedules,
                             overdue_schedules=overdue_schedules,
                             this_week_schedules=this_week_schedules)
    except Exception as e:
        flash(f'Error loading schedules: {str(e)}', 'error')
        return render_template('error.html'), 500

@admin_bp.route('/add-general-schedule', methods=['GET', 'POST'])
@role_required([Roles.SUPER_HQ])
def add_general_schedule():
    """Create new project schedule"""
    if request.method == 'POST':
        try:
            data = request.form
            
            schedule = Schedule(
                project_id=int(data.get('project_id')),
                title=data.get('title'),
                type=data.get('type'),
                description=data.get('description'),
                start_time=datetime.strptime(data.get('start_time'), '%Y-%m-%dT%H:%M'),
                end_time=datetime.strptime(data.get('end_time'), '%Y-%m-%dT%H:%M'),
                status=data.get('status', 'Scheduled')
            )
            
            db.session.add(schedule)
            db.session.commit()
            
            flash(f'Schedule "{schedule.title}" created successfully!', 'success')
            return redirect(url_for('admin.schedules'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating schedule: {str(e)}', 'error')
    
    projects = Project.query.all()
    return render_template('admin/add_schedule.html', projects=projects)

@admin_bp.route('/edit-schedule/<int:schedule_id>', methods=['GET', 'POST'])
@role_required([Roles.SUPER_HQ])
def edit_schedule(schedule_id):
    """Edit existing schedule"""
    try:
        schedule = Schedule.query.get_or_404(schedule_id)
        
        if request.method == 'POST':
            try:
                data = request.form
                
                # Update schedule fields
                schedule.project_id = int(data.get('project_id'))
                schedule.title = data.get('title')
                schedule.type = data.get('type')
                schedule.description = data.get('description')
                schedule.start_time = datetime.strptime(data.get('start_time'), '%Y-%m-%dT%H:%M')
                schedule.end_time = datetime.strptime(data.get('end_time'), '%Y-%m-%dT%H:%M')
                schedule.status = data.get('status', 'Scheduled')
                
                db.session.commit()
                
                flash(f'Schedule "{schedule.title}" updated successfully!', 'success')
                return redirect(url_for('admin.schedules'))
                
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating schedule: {str(e)}', 'error')
        
        projects = Project.query.all()
        schedule_types = ['Planning', 'Construction', 'Inspection', 'Meeting', 'Delivery', 'Maintenance', 'Other']
        schedule_statuses = ['Scheduled', 'In Progress', 'Completed', 'Cancelled', 'Postponed']
        
        return render_template('admin/edit_schedule.html', 
                             schedule=schedule, 
                             projects=projects,
                             schedule_types=schedule_types,
                             schedule_statuses=schedule_statuses)
        
    except Exception as e:
        flash(f'Error loading schedule: {str(e)}', 'error')
        return redirect(url_for('admin.schedules'))

@admin_bp.route('/delete-schedule/<int:schedule_id>', methods=['POST'])
@role_required([Roles.SUPER_HQ])
def delete_schedule(schedule_id):
    """Delete a schedule"""
    try:
        schedule = Schedule.query.get_or_404(schedule_id)
        schedule_title = schedule.title
        
        db.session.delete(schedule)
        db.session.commit()
        
        flash(f'Schedule "{schedule_title}" deleted successfully!', 'success')
        return redirect(url_for('admin.schedules'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting schedule: {str(e)}', 'error')
        return redirect(url_for('admin.schedules'))

# ==================== ANALYTICS ENDPOINTS ====================

@admin_bp.route('/analytics')
@role_required([Roles.SUPER_HQ])
def analytics():
    """Analytics dashboard - redirect to comprehensive analytics"""
    return redirect(url_for('admin.analytics_custom'))


@admin_bp.route('/analytics-custom')
@role_required([Roles.SUPER_HQ])
def analytics_custom():
    """Comprehensive analytics dashboard for all modules"""
    try:
        from datetime import datetime, timedelta
        from sqlalchemy import func, extract
        
        current_date = datetime.now()
        current_month = current_date.replace(day=1)
        last_month = (current_month - timedelta(days=1)).replace(day=1)
        current_year = current_date.year
        
        # Comprehensive analytics data from all modules
        analytics_data = {
            # PROJECT ANALYTICS
            'project_analytics': {
                'total_projects': Project.query.count(),
                'active_projects': Project.query.filter_by(status='Active').count(),
                'completed_projects': Project.query.filter_by(status='Completed').count(),
                'planning_projects': Project.query.filter_by(status='Planning').count(),
                'on_hold_projects': Project.query.filter_by(status='On Hold').count(),
                'total_budget': db.session.query(func.sum(Project.budget)).scalar() or 0,
                'avg_budget': db.session.query(func.avg(Project.budget)).scalar() or 0,
                'projects_this_month': Project.query.filter(Project.created_at >= current_month).count(),
                'projects_last_month': Project.query.filter(
                    Project.created_at >= last_month,
                    Project.created_at < current_month
                ).count()
            },
            
            # FINANCIAL ANALYTICS
            'financial_analytics': {
                'total_orders': PurchaseOrder.query.count(),
                'pending_orders': PurchaseOrder.query.filter_by(status='Pending').count(),
                'approved_orders': PurchaseOrder.query.filter_by(status='Approved').count(),
                'rejected_orders': PurchaseOrder.query.filter_by(status='Rejected').count(),
                'total_order_value': db.session.query(func.sum(PurchaseOrder.total_amount)).scalar() or 0,
                'pending_order_value': db.session.query(func.sum(PurchaseOrder.total_amount)).filter(
                    PurchaseOrder.status == 'Pending'
                ).scalar() or 0,
                'approved_order_value': db.session.query(func.sum(PurchaseOrder.total_amount)).filter(
                    PurchaseOrder.status == 'Approved'
                ).scalar() or 0,
                'orders_this_month': PurchaseOrder.query.filter(PurchaseOrder.created_at >= current_month).count(),
                'total_expenses': db.session.query(func.sum(Expense.amount)).scalar() or 0,
                'expenses_this_month': db.session.query(func.sum(Expense.amount)).filter(
                    Expense.date >= current_month.date()
                ).scalar() or 0,
                'avg_order_value': db.session.query(func.avg(PurchaseOrder.total_amount)).scalar() or 0
            },
            
            # PROCUREMENT ANALYTICS
            'procurement_analytics': {
                'total_suppliers': Supplier.query.count(),
                'active_suppliers': Supplier.query.filter_by(status='Active').count(),
                'inactive_suppliers': Supplier.query.filter_by(status='Inactive').count(),
                'total_stock_items': Stock.query.count(),
                'low_stock_items': Stock.query.filter(Stock.quantity <= 10).count(),
                'out_of_stock_items': Stock.query.filter(Stock.quantity <= 0).count(),
                'total_stock_quantity': db.session.query(func.sum(Stock.quantity)).scalar() or 0,
                'suppliers_this_month': Supplier.query.filter(Supplier.created_at >= current_month).count()
            },
            
            # HR ANALYTICS
            'hr_analytics': {
                'total_employees': Employee.query.count(),
                'active_employees': Employee.query.filter_by(status='Active').count(),
                'inactive_employees': Employee.query.filter_by(status='Inactive').count(),
                'departments': db.session.query(func.count(func.distinct(Employee.department))).scalar() or 0,
                'positions': db.session.query(func.count(func.distinct(Employee.position))).scalar() or 0,
                'new_hires_this_month': Employee.query.filter(Employee.date_of_employment >= current_month.date()).count(),
                'avg_salary': db.session.query(func.avg(Payroll.amount)).scalar() or 0,
                'total_payroll': db.session.query(func.sum(Payroll.amount)).scalar() or 0
            },
            
            # ASSET ANALYTICS
            'asset_analytics': {
                'total_assets': Asset.query.count(),
                'active_assets': Asset.query.filter_by(status='Active').count(),
                'retired_assets': Asset.query.filter_by(status='Retired').count(),
                'maintenance_assets': Asset.query.filter_by(status='Under Maintenance').count(),
                'assets_this_month': Asset.query.filter(Asset.created_at >= current_month).count()
            },
            
            # EQUIPMENT ANALYTICS
            'equipment_analytics': {
                'total_equipment': Equipment.query.count(),
                'active_equipment': Equipment.query.filter_by(status='Active').count(),
                'maintenance_equipment': Equipment.query.filter_by(status='Under Maintenance').count(),
                'retired_equipment': Equipment.query.filter_by(status='Retired').count(),
                'avg_machine_hours': db.session.query(func.avg(Equipment.machine_hours)).scalar() or 0,
                'total_diesel_consumption': db.session.query(func.sum(Equipment.diesel_consumption)).scalar() or 0
            },
            
            # INCIDENT ANALYTICS
            'incident_analytics': {
                'total_incidents': Incident.query.count(),
                'open_incidents': Incident.query.filter_by(status='Open').count(),
                'closed_incidents': Incident.query.filter_by(status='Closed').count(),
                'critical_incidents': Incident.query.filter_by(severity='Critical').count(),
                'high_incidents': Incident.query.filter_by(severity='High').count(),
                'medium_incidents': Incident.query.filter_by(severity='Medium').count(),
                'low_incidents': Incident.query.filter_by(severity='Low').count(),
                'incidents_this_month': Incident.query.filter(Incident.date_reported >= current_month.date()).count()
            },
            
            # SCHEDULE ANALYTICS
            'schedule_analytics': {
                'total_schedules': Schedule.query.count(),
                'active_schedules': Schedule.query.filter_by(status='active').count(),
                'pending_schedules': Schedule.query.filter_by(status='pending').count(),
                'completed_schedules': Schedule.query.filter_by(status='completed').count(),
                'schedules_this_month': Schedule.query.filter(Schedule.created_at >= current_month).count(),
                'overdue_schedules': Schedule.query.filter(
                    Schedule.end_time < current_date,
                    Schedule.status.notin_(['completed', 'cancelled'])
                ).count()
            },
            
            # DOCUMENT ANALYTICS
            'document_analytics': {
                'total_documents': Document.query.count(),
                'documents_this_month': Document.query.filter(Document.uploaded_at >= current_month).count(),
                'total_file_size': db.session.query(func.sum(Document.size)).scalar() or 0,
                'avg_file_size': db.session.query(func.avg(Document.size)).scalar() or 0
            }
        }
        
        # Monthly trend data for charts (last 12 months)
        monthly_data = []
        for i in range(12):
            month_start = datetime.now().replace(day=1) - timedelta(days=30*i)
            month_end = month_start + timedelta(days=30)
            
            monthly_stats = {
                'month': month_start.strftime('%Y-%m'),
                'month_name': month_start.strftime('%B %Y'),
                'projects': Project.query.filter(
                    Project.created_at >= month_start,
                    Project.created_at < month_end
                ).count(),
                'orders': PurchaseOrder.query.filter(
                    PurchaseOrder.created_at >= month_start,
                    PurchaseOrder.created_at < month_end
                ).count(),
                'order_value': db.session.query(func.sum(PurchaseOrder.total_amount)).filter(
                    PurchaseOrder.created_at >= month_start,
                    PurchaseOrder.created_at < month_end
                ).scalar() or 0,
                'expenses': db.session.query(func.sum(Expense.amount)).filter(
                    Expense.date >= month_start.date(),
                    Expense.date < month_end.date()
                ).scalar() or 0,
                'incidents': Incident.query.filter(
                    Incident.date_reported >= month_start.date(),
                    Incident.date_reported < month_end.date()
                ).count(),
                'new_employees': Employee.query.filter(
                    Employee.date_of_employment >= month_start.date(),
                    Employee.date_of_employment < month_end.date()
                ).count(),
                'schedules': Schedule.query.filter(
                    Schedule.created_at >= month_start,
                    Schedule.created_at < month_end
                ).count()
            }
            monthly_data.append(monthly_stats)
        
        analytics_data['monthly_trends'] = list(reversed(monthly_data))
        
        # Calculate growth rates
        analytics_data['growth_rates'] = {
            'projects': calculate_growth_rate(
                analytics_data['project_analytics']['projects_this_month'],
                analytics_data['project_analytics']['projects_last_month']
            ),
            'orders': calculate_growth_rate(
                analytics_data['financial_analytics']['orders_this_month'],
                PurchaseOrder.query.filter(
                    PurchaseOrder.created_at >= last_month,
                    PurchaseOrder.created_at < current_month
                ).count()
            ),
            'employees': calculate_growth_rate(
                analytics_data['hr_analytics']['new_hires_this_month'],
                Employee.query.filter(
                    Employee.date_of_employment >= last_month.date(),
                    Employee.date_of_employment < current_month.date()
                ).count()
            )
        }
        
        return render_template('admin/analytics.html', analytics=analytics_data)
    except Exception as e:
        flash(f'Error loading analytics: {str(e)}', 'error')
        return render_template('error.html'), 500


def calculate_growth_rate(current, previous):
    """Calculate growth rate percentage"""
    if previous == 0:
        return 100 if current > 0 else 0
    return round(((current - previous) / previous) * 100, 1)

@admin_bp.route('/analytics-export-csv')
@role_required([Roles.SUPER_HQ])
def analytics_export_csv():
    """Export analytics data as CSV"""
    try:
        # Create CSV data
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow(['Report Type', 'Metric', 'Value', 'Generated At'])
        
        # Project metrics
        writer.writerow(['Projects', 'Total Projects', Project.query.count(), datetime.now()])
        writer.writerow(['Projects', 'Active Projects', Project.query.filter_by(status='Active').count(), datetime.now()])
        writer.writerow(['Projects', 'Completed Projects', Project.query.filter_by(status='Completed').count(), datetime.now()])
        
        # Asset metrics
        writer.writerow(['Assets', 'Total Assets', Asset.query.count(), datetime.now()])
        writer.writerow(['Assets', 'Active Assets', Asset.query.filter_by(status='Active').count(), datetime.now()])
        
        # Employee metrics
        writer.writerow(['Employees', 'Total Employees', Employee.query.count(), datetime.now()])
        writer.writerow(['Employees', 'Active Employees', Employee.query.filter_by(status='Active').count(), datetime.now()])
        
        # Incident metrics
        writer.writerow(['Incidents', 'Total Incidents', Incident.query.count(), datetime.now()])
        writer.writerow(['Incidents', 'Open Incidents', Incident.query.filter_by(status='Open').count(), datetime.now()])
        
        # Create response
        output.seek(0)
        
        # Create a bytes buffer
        mem = io.BytesIO()
        mem.write(output.getvalue().encode('utf-8'))
        mem.seek(0)
        
        filename = f"construction_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return send_file(
            mem,
            as_attachment=True,
            download_name=filename,
            mimetype='text/csv'
        )
        
    except Exception as e:
        flash(f'Error exporting analytics: {str(e)}', 'error')
        return redirect(url_for('admin.analytics_custom'))

# ==================== USER MANAGEMENT ENDPOINTS ====================

@admin_bp.route('/profile')
@role_required([Roles.SUPER_HQ])
def profile():
    """Admin user profile management"""
    try:
        # Use Flask-Login current_user
        from flask_login import current_user
        
        if not current_user.is_authenticated:
            flash('Please log in to view profile', 'error')
            return redirect(url_for('login'))
        
        user = current_user
        
        # Get user activity statistics
        user_stats = {
            'projects_managed': Project.query.filter_by(project_manager=user.name or user.username).count(),
            'incidents_reported': Incident.query.filter_by(reported_by=user.name or user.username).count(),
            'last_login': user.updated_at if hasattr(user, 'updated_at') else None,
            'account_created': user.created_at if hasattr(user, 'created_at') else None
        }
        
        return render_template('admin/profile.html', user=user, user_stats=user_stats)
    except Exception as e:
        flash(f'Error loading profile: {str(e)}', 'error')
        return render_template('error.html'), 500

@admin_bp.route('/logout')
def logout():
    """Admin logout functionality"""
    try:
        # Clear session
        session.clear()
        flash('You have been logged out successfully', 'success')
        return redirect(url_for('login'))
    except Exception as e:
        flash(f'Error during logout: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))

# Purchase Order Management Routes

@admin_bp.route('/orders')
@role_required([Roles.SUPER_HQ])
def orders():
    """Display purchase orders management"""
    try:
        # Get filter parameters
        status_filter = request.args.get('status', '')
        priority_filter = request.args.get('priority', '')
        supplier_filter = request.args.get('supplier', '')
        project_filter = request.args.get('project', '')
        view_order_id = request.args.get('view_order', '')
        
        # Base query
        orders_query = PurchaseOrder.query
        
        # Apply filters
        if status_filter:
            orders_query = orders_query.filter(PurchaseOrder.status == status_filter)
        if priority_filter:
            orders_query = orders_query.filter(PurchaseOrder.priority == priority_filter)
        if supplier_filter:
            orders_query = orders_query.filter(PurchaseOrder.supplier_name.ilike(f'%{supplier_filter}%'))
        if project_filter:
            orders_query = orders_query.filter(PurchaseOrder.project_id == project_filter)
        
        # Get orders with relationships
        purchase_orders = orders_query.order_by(PurchaseOrder.created_at.desc()).all()
        
        # Get filter data
        projects = Project.query.all()
        suppliers = Supplier.query.filter_by(status='Active').all()
        
        # Calculate statistics
        total_orders = PurchaseOrder.query.count()
        pending_orders = PurchaseOrder.query.filter_by(status='Pending').count()
        approved_orders = PurchaseOrder.query.filter_by(status='Approved').count()
        total_value = db.session.query(func.sum(PurchaseOrder.total_amount)).filter_by(status='Approved').scalar() or 0
        
        order_stats = {
            'total_orders': total_orders,
            'pending_orders': pending_orders,
            'approved_orders': approved_orders,
            'total_value': total_value
        }
        
        # Get specific order for viewing if requested
        view_order = None
        if view_order_id:
            try:
                view_order = PurchaseOrder.query.get(int(view_order_id))
            except (ValueError, TypeError):
                pass
        
        return render_template('admin/orders.html', 
                             purchase_orders=purchase_orders,
                             order_stats=order_stats,
                             projects=projects,
                             suppliers=suppliers,
                             status_filter=status_filter,
                             priority_filter=priority_filter,
                             supplier_filter=supplier_filter,
                             project_filter=project_filter,
                             view_order=view_order)
    except Exception as e:
        flash(f'Error loading purchase orders: {str(e)}', 'error')
        return render_template('error.html'), 500

@admin_bp.route('/add-order', methods=['GET', 'POST'])
@role_required([Roles.SUPER_HQ])
def add_order():
    """Add new purchase order"""
    if request.method == 'POST':
        try:
            data = request.form
            
            # Generate order number
            from datetime import datetime
            import random
            order_number = f"PO-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
            
            # Create purchase order
            purchase_order = PurchaseOrder(
                order_number=order_number,
                supplier_name=data.get('supplier_name'),
                supplier_contact=data.get('supplier_contact'),
                supplier_email=data.get('supplier_email'),
                supplier_phone=data.get('supplier_phone'),
                project_id=int(data.get('project_id')) if data.get('project_id') else None,
                priority=data.get('priority', 'Normal'),
                description=data.get('description'),
                expected_delivery=datetime.strptime(data.get('expected_delivery'), '%Y-%m-%d').date() if data.get('expected_delivery') else None,
                delivery_address=data.get('delivery_address'),
                notes=data.get('notes'),
                status=data.get('status', 'Pending'),  # Handle status from form
                requested_by=current_user.id  # Use current_user instead of session
            )
            
            db.session.add(purchase_order)
            db.session.flush()  # Get the ID
            
            # Process line items
            item_names = request.form.getlist('item_name[]')
            item_descriptions = request.form.getlist('item_description[]')
            item_quantities = request.form.getlist('item_quantity[]')
            item_units = request.form.getlist('item_unit[]')
            item_prices = request.form.getlist('item_price[]')
            
            subtotal = 0
            has_items = False
            
            for i in range(len(item_names)):
                if item_names[i] and item_names[i].strip():  # Check for non-empty item name
                    try:
                        quantity = float(item_quantities[i]) if item_quantities[i] else 0
                        unit_price = float(item_prices[i]) if item_prices[i] else 0
                        
                        if quantity > 0 and unit_price > 0:  # Only add items with valid quantity and price
                            line_total = quantity * unit_price
                            
                            line_item = PurchaseOrderLineItem(
                                purchase_order_id=purchase_order.id,
                                item_name=item_names[i].strip(),
                                description=item_descriptions[i].strip() if item_descriptions[i] else '',
                                quantity=quantity,
                                unit=item_units[i].strip() if item_units[i] else '',
                                unit_price=unit_price,
                                line_total=line_total
                            )
                            db.session.add(line_item)
                            subtotal += line_total
                            has_items = True
                    except (ValueError, TypeError):
                        # Skip invalid items
                        continue
            
            if not has_items:
                raise ValueError("At least one valid item with quantity and price is required")
            
            # Calculate totals
            tax_rate = float(data.get('tax_rate', 0)) / 100
            tax_amount = subtotal * tax_rate
            total_amount = subtotal + tax_amount
            
            # Update purchase order totals
            purchase_order.subtotal = subtotal
            purchase_order.tax_rate = tax_rate * 100
            purchase_order.tax_amount = tax_amount
            purchase_order.total_amount = total_amount
            
            db.session.commit()
            
            flash(f'Purchase order {order_number} created successfully!', 'success')
            return redirect(url_for('admin.orders'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating purchase order: {str(e)}', 'error')
    
    # GET request - show form
    try:
        projects = Project.query.all()
        suppliers = Supplier.query.filter_by(status='Active').all()
        stock_items = Stock.query.all()
        
        return render_template('admin/add_order_simple.html', 
                             projects=projects,
                             suppliers=suppliers,
                             stock_items=stock_items)
    except Exception as e:
        flash(f'Error loading form data: {str(e)}', 'error')
        return render_template('error.html'), 500

@admin_bp.route('/order/<int:order_id>')
@role_required([Roles.SUPER_HQ])
def view_order(order_id):
    """View purchase order details"""
    try:
        purchase_order = PurchaseOrder.query.get_or_404(order_id)
        
        order_data = {
            'id': purchase_order.id,
            'order_number': purchase_order.order_number,
            'supplier_name': purchase_order.supplier_name,
            'supplier_contact': purchase_order.supplier_contact,
            'supplier_email': purchase_order.supplier_email,
            'supplier_phone': purchase_order.supplier_phone,
            'project_name': purchase_order.project.name if purchase_order.project else None,
            'status': purchase_order.status,
            'priority': purchase_order.priority,
            'description': purchase_order.description,
            'subtotal': purchase_order.subtotal,
            'tax_rate': purchase_order.tax_rate,
            'tax_amount': purchase_order.tax_amount,
            'total_amount': purchase_order.total_amount,
            'expected_delivery': purchase_order.expected_delivery.strftime('%Y-%m-%d') if purchase_order.expected_delivery else None,
            'delivery_address': purchase_order.delivery_address,
            'notes': purchase_order.notes,
            'requested_by': purchase_order.requested_by_employee.name if purchase_order.requested_by_employee else None,
            'approved_by': purchase_order.approved_by_employee.name if purchase_order.approved_by_employee else None,
            'approval_date': purchase_order.approval_date.strftime('%Y-%m-%d %H:%M') if purchase_order.approval_date else None,
            'created_at': purchase_order.created_at.strftime('%Y-%m-%d %H:%M'),
            'line_items': [{
                'item_name': item.item_name,
                'description': item.description,
                'quantity': item.quantity,
                'unit': item.unit,
                'unit_price': item.unit_price,
                'line_total': item.line_total
            } for item in purchase_order.line_items]
        }
        
        return jsonify({
            'success': True,
            'order': order_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@admin_bp.route('/order/<int:order_id>/approve', methods=['POST'])
@role_required([Roles.SUPER_HQ])
def approve_order(order_id):
    """Approve purchase order"""
    try:
        purchase_order = PurchaseOrder.query.get_or_404(order_id)
        
        if purchase_order.status not in ['Draft', 'Pending']:
            flash('Order cannot be approved in current status', 'error')
            return redirect(url_for('admin.orders'))
        
        purchase_order.status = 'Approved'
        purchase_order.approved_by = session.get('user_id')
        purchase_order.approval_date = datetime.utcnow()
        
        db.session.commit()
        
        # Send notification to the user who requested the order
        if purchase_order.requested_by:
            # Try to get user email from User model first
            user = User.query.filter_by(id=purchase_order.requested_by).first()
            if user and user.email:
                send_order_notification(user.email, purchase_order.order_number, 'Approved')
            else:
                # Fallback to Employee model
                employee = Employee.query.filter_by(id=purchase_order.requested_by).first()
                if employee and employee.email:
                    send_order_notification(employee.email, purchase_order.order_number, 'Approved')
        
        flash(f'Purchase order {purchase_order.order_number} approved successfully!', 'success')
        return redirect(url_for('admin.orders'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error approving purchase order: {str(e)}', 'error')
        return redirect(url_for('admin.orders'))

@admin_bp.route('/order/<int:order_id>/reject', methods=['POST'])
@role_required([Roles.SUPER_HQ])
def reject_order(order_id):
    """Reject purchase order"""
    try:
        purchase_order = PurchaseOrder.query.get_or_404(order_id)
        # Try JSON first, then form data
        data = request.get_json() or request.form
        rejection_reason = data.get('reason', 'No reason provided')
        
        if purchase_order.status not in ['Draft', 'Pending']:
            flash('Order cannot be rejected in current status', 'error')
            return redirect(url_for('admin.orders'))
        
        purchase_order.status = 'Rejected'
        purchase_order.notes = f"{purchase_order.notes or ''}\n\nRejection reason: {rejection_reason}"
        
        db.session.commit()
        
        # Send notification to the user who requested the order
        if purchase_order.requested_by:
            # Try to get user email from User model first
            user = User.query.filter_by(id=purchase_order.requested_by).first()
            if user and user.email:
                send_order_notification(user.email, purchase_order.order_number, 'Rejected', rejection_reason)
            else:
                # Fallback to Employee model
                employee = Employee.query.filter_by(id=purchase_order.requested_by).first()
                if employee and employee.email:
                    send_order_notification(employee.email, purchase_order.order_number, 'Rejected', rejection_reason)
        
        flash(f'Purchase order {purchase_order.order_number} rejected.', 'warning')
        return redirect(url_for('admin.orders'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error rejecting purchase order: {str(e)}', 'error')
        return redirect(url_for('admin.orders'))

@admin_bp.route('/order/<int:order_id>/reject-form', methods=['GET', 'POST'])
@role_required([Roles.SUPER_HQ])
def reject_order_form(order_id):
    """Handle reject order form submission"""
    purchase_order = PurchaseOrder.query.get_or_404(order_id)
    
    if request.method == 'GET':
        # Show reject form
        return render_template('admin/reject_order.html', order=purchase_order)
    
    try:
        if purchase_order.status not in ['Draft', 'Pending']:
            flash('Order cannot be rejected in current status', 'error')
            return redirect(url_for('admin.orders'))
        
        rejection_reason = request.form.get('reason', 'No reason provided')
        
        purchase_order.status = 'Rejected'
        purchase_order.notes = f"{purchase_order.notes or ''}\n\nRejection reason: {rejection_reason}"
        
        db.session.commit()
        
        # Send notification to the user who requested the order
        if purchase_order.requested_by:
            # Try to get user email from User model first
            user = User.query.filter_by(id=purchase_order.requested_by).first()
            if user and user.email:
                send_order_notification(user.email, purchase_order.order_number, 'Rejected', rejection_reason)
            else:
                # Fallback to Employee model
                employee = Employee.query.filter_by(id=purchase_order.requested_by).first()
                if employee and employee.email:
                    send_order_notification(employee.email, purchase_order.order_number, 'Rejected', rejection_reason)
        
        flash(f'Purchase order {purchase_order.order_number} rejected successfully. Notification sent to requestor.', 'success')
        return redirect(url_for('admin.orders'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error rejecting order: {str(e)}', 'error')
        return redirect(url_for('admin.orders'))

@admin_bp.route('/order/<int:order_id>/delete-form', methods=['POST'])
@role_required([Roles.SUPER_HQ])
def delete_order_form(order_id):
    """Handle delete order form submission"""
    try:
        purchase_order = PurchaseOrder.query.get_or_404(order_id)
        
        if purchase_order.status in ['Approved', 'Ordered', 'Delivered']:
            flash('Cannot delete order in current status', 'error')
            return redirect(url_for('admin.orders'))
        
        order_number = purchase_order.order_number
        db.session.delete(purchase_order)
        db.session.commit()
        
        flash(f'Purchase order {order_number} deleted successfully.', 'success')
        return redirect(url_for('admin.orders'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting order: {str(e)}', 'error')
        return redirect(url_for('admin.orders'))

@admin_bp.route('/order/<int:order_id>/delete', methods=['POST', 'DELETE'])
@role_required([Roles.SUPER_HQ])
def delete_order(order_id):
    """Delete purchase order"""
    try:
        purchase_order = PurchaseOrder.query.get_or_404(order_id)
        
        if purchase_order.status in ['Approved', 'Ordered', 'Delivered']:
            flash('Cannot delete order in current status', 'error')
            return redirect(url_for('admin.orders'))
        
        order_number = purchase_order.order_number
        db.session.delete(purchase_order)
        db.session.commit()
        
        flash(f'Purchase order {order_number} deleted successfully.', 'success')
        return redirect(url_for('admin.orders'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting purchase order: {str(e)}', 'error')
        return redirect(url_for('admin.orders'))

# Supplier Management Routes

@admin_bp.route('/suppliers')
@role_required([Roles.SUPER_HQ])
def suppliers():
    """Display suppliers management"""
    try:
        view_supplier_id = request.args.get('view_supplier', '')
        
        suppliers = Supplier.query.order_by(Supplier.name).all()
        
        # Get specific supplier for viewing if requested
        view_supplier = None
        if view_supplier_id:
            try:
                view_supplier = Supplier.query.get(int(view_supplier_id))
            except (ValueError, TypeError):
                pass
        
        return render_template('admin/suppliers.html', 
                             suppliers=suppliers, 
                             view_supplier=view_supplier)
    except Exception as e:
        flash(f'Error loading suppliers: {str(e)}', 'error')
        return render_template('error.html'), 500

@admin_bp.route('/add-supplier', methods=['GET', 'POST'])
@role_required([Roles.SUPER_HQ])
def add_supplier():
    """Add new supplier"""
    if request.method == 'POST':
        try:
            data = request.form
            
            supplier = Supplier(
                name=data.get('name'),
                contact_person=data.get('contact_person'),
                email=data.get('email'),
                phone=data.get('phone'),
                address=data.get('address'),
                tax_id=data.get('tax_id'),
                payment_terms=data.get('payment_terms'),
                rating=float(data.get('rating', 0)) if data.get('rating') else None,
                notes=data.get('notes')
            )
            
            db.session.add(supplier)
            db.session.commit()
            
            flash(f'Supplier "{supplier.name}" added successfully!', 'success')
            return redirect(url_for('admin.suppliers'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating supplier: {str(e)}', 'error')
    
    return render_template('admin/add_supplier.html')

@admin_bp.route('/edit-supplier/<int:supplier_id>', methods=['GET', 'POST'])
@role_required([Roles.SUPER_HQ])
def edit_supplier(supplier_id):
    """Edit existing supplier"""
    try:
        supplier = Supplier.query.get_or_404(supplier_id)
        
        if request.method == 'POST':
            try:
                data = request.form
                
                # Update supplier fields
                supplier.name = data.get('name')
                supplier.contact_person = data.get('contact_person')
                supplier.email = data.get('email')
                supplier.phone = data.get('phone')
                supplier.address = data.get('address')
                supplier.tax_id = data.get('tax_id')
                supplier.payment_terms = data.get('payment_terms')
                supplier.rating = float(data.get('rating', 0)) if data.get('rating') else None
                supplier.notes = data.get('notes')
                supplier.status = data.get('status', 'Active')
                supplier.website = data.get('website')
                supplier.description = data.get('description')
                supplier.products_services = data.get('products_services')
                
                db.session.commit()
                
                flash(f'Supplier "{supplier.name}" updated successfully!', 'success')
                return redirect(url_for('admin.suppliers'))
                
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating supplier: {str(e)}', 'error')
        
        return render_template('admin/edit_supplier.html', supplier=supplier)
        
    except Exception as e:
        flash(f'Error loading supplier: {str(e)}', 'error')
        return redirect(url_for('admin.suppliers'))

# Context processor to provide global variables to all admin templates
@admin_bp.context_processor
def inject_monitoring_counts():
    """Inject monitoring counts for sidebar badges"""
    try:
        incident_count = Incident.query.filter_by(status='Open').count()
        alert_count = Alert.query.filter_by(status='Active').count()
        
        return {
            'incident_count': incident_count,
            'alert_count': alert_count
        }
    except Exception as e:
        # Return default values if database query fails
        return {
            'incident_count': 0,
            'alert_count': 0
        }

# --- Payroll Approval Routes ---
@admin_bp.route('/payroll/pending')
@role_required([Roles.SUPER_HQ])
def pending_payrolls():
    """View pending payroll approvals for admin"""
    try:
        from models import PayrollApproval, User
        
        # Get payrolls pending admin approval
        pending_approvals = db.session.query(PayrollApproval, User).join(
            User, PayrollApproval.submitted_by == User.id
        ).filter(
            PayrollApproval.status == 'pending_admin'
        ).order_by(PayrollApproval.submitted_at.desc()).all()
        
        return render_template('admin/payroll/pending.html', 
                             pending_approvals=pending_approvals)
        
    except Exception as e:
        current_app.logger.error(f"Error loading pending payrolls: {str(e)}")
        flash("Error loading pending payrolls", "error")
        return redirect(url_for('admin.index'))

@admin_bp.route('/payroll/<int:approval_id>/review', methods=['GET', 'POST'])
@role_required([Roles.SUPER_HQ])
def review_payroll(approval_id):
    """Review and approve/reject payroll"""
    try:
        from models import PayrollApproval, StaffPayroll, Employee
        
        approval = db.session.get(PayrollApproval, approval_id)
        if not approval:
            flash("Payroll approval not found", "error")
            return redirect(url_for('admin.pending_payrolls'))
        
        if approval.status != 'pending_admin':
            flash("This payroll is no longer pending admin approval", "warning")
            return redirect(url_for('admin.pending_payrolls'))
        
        if request.method == 'POST':
            action = request.form.get('action')
            comments = request.form.get('comments', '')
            
            if action == 'approve':
                approval.status = 'pending_finance'
                approval.admin_reviewer = session.get('user_id')
                approval.admin_reviewed_at = datetime.now()
                approval.admin_comments = comments
                
                # Update all related staff payrolls
                year, month = map(int, approval.payroll_period.split('-'))
                staff_payrolls = StaffPayroll.query.filter(
                    StaffPayroll.period_year == year,
                    StaffPayroll.period_month == month
                ).all()
                
                for payroll in staff_payrolls:
                    payroll.approval_status = 'pending_finance'
                    payroll.approved_by_admin = session.get('user_id')
                    payroll.admin_approved_at = datetime.now()
                
                flash(f"Payroll for {approval.payroll_period} approved and sent to Finance", "success")
                
            elif action == 'reject':
                approval.status = 'rejected'
                approval.admin_reviewer = session.get('user_id')
                approval.admin_reviewed_at = datetime.now()
                approval.admin_comments = comments
                
                # Update all related staff payrolls
                year, month = map(int, approval.payroll_period.split('-'))
                staff_payrolls = StaffPayroll.query.filter(
                    StaffPayroll.period_year == year,
                    StaffPayroll.period_month == month
                ).all()
                
                for payroll in staff_payrolls:
                    payroll.approval_status = 'rejected'
                
                flash(f"Payroll for {approval.payroll_period} rejected", "warning")
            
            db.session.commit()
            return redirect(url_for('admin.pending_payrolls'))
        
        # Get payroll details for review
        year, month = map(int, approval.payroll_period.split('-'))
        staff_payrolls = db.session.query(StaffPayroll, Employee).join(
            Employee, StaffPayroll.employee_id == Employee.id
        ).filter(
            StaffPayroll.period_year == year,
            StaffPayroll.period_month == month
        ).all()
        
        return render_template('admin/payroll/review.html',
                             approval=approval,
                             staff_payrolls=staff_payrolls)
        
    except Exception as e:
        current_app.logger.error(f"Error reviewing payroll: {str(e)}")
        flash("Error reviewing payroll", "error")
        return redirect(url_for('admin.pending_payrolls'))

@admin_bp.route('/<int:project_id>/assign-staff', methods=['POST'])
@login_required
@role_required([Roles.SUPER_HQ])
def assign_staff(project_id):
    try:
        # Get data from form
        staff_role = request.form.get('role')
        staff_id = request.form.get('staff_id')
        
        if not staff_role or not staff_id:
            flash('Role and staff member are required', 'error')
            return redirect(url_for('admin.project_details', project_id=project_id))
        
        # Validate project exists
        project = Project.query.get_or_404(project_id)
        
        # Validate staff member exists
        staff_member = User.query.get(staff_id)
        if not staff_member:
            flash('Staff member not found', 'error')
            return redirect(url_for('admin.project_details', project_id=project_id))
        
        # Check if staff is already assigned to this project
        existing_assignment = StaffAssignment.query.filter_by(
            project_id=project_id, 
            staff_id=staff_id
        ).first()
        
        if existing_assignment:
            flash(f'{staff_member.name} is already assigned to this project', 'error')
            return redirect(url_for('admin.project_details', project_id=project_id))
        
        # Create new assignment
        assignment = StaffAssignment(
            project_id=project_id, 
            staff_id=staff_id, 
            role=staff_role,
            assigned_at=datetime.now()
        )
        
        db.session.add(assignment)
        db.session.commit()
        
        current_app.logger.info(f"Staff {staff_member.name} (ID: {staff_id}) assigned as {staff_role} to project {project_id}")
        
        flash(f'{staff_member.name} assigned as {staff_role} to {project.name}', 'success')
        return redirect(url_for('admin.project_details', project_id=project_id))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Assign staff error: {str(e)}", exc_info=True)
        flash(f'Error assigning staff: {str(e)}', 'error')
        return redirect(url_for('admin.project_details', project_id=project_id))


# Remove staff from project
@admin_bp.route('/<int:project_id>/remove-staff', methods=['POST'])
@login_required
@role_required([Roles.SUPER_HQ])
def remove_staff(project_id):
    try:
        staff_id = request.form.get('staff_id')
        
        if not staff_id:
            flash('Staff ID is required', 'error')
            return redirect(url_for('admin.project_details', project_id=project_id))
        
        assignment = StaffAssignment.query.filter_by(
            project_id=project_id, 
            staff_id=staff_id
        ).first()
        
        if not assignment:
            flash('Staff assignment not found', 'error')
            return redirect(url_for('admin.project_details', project_id=project_id))
        
        staff_member = User.query.get(staff_id)
        staff_name = staff_member.name if staff_member else f'Staff {staff_id}'
        
        db.session.delete(assignment)
        db.session.commit()
        
        current_app.logger.info(f"Staff {staff_name} (ID: {staff_id}) removed from project {project_id}")
        
        flash(f'{staff_name} removed from project', 'success')
        return redirect(url_for('admin.project_details', project_id=project_id))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Remove staff error: {str(e)}", exc_info=True)
        flash(f'Error removing staff: {str(e)}', 'error')
        return redirect(url_for('admin.project_details', project_id=project_id))


# Delete project endpoint
@admin_bp.route('/<int:project_id>/delete', methods=['POST'])
@login_required
@role_required([Roles.SUPER_HQ])
def delete_project(project_id):
    try:
        project = Project.query.get_or_404(project_id)
        project_name = project.name
        
        # Remove all staff assignments first
        StaffAssignment.query.filter_by(project_id=project_id).delete()
        
        # Remove related milestones
        Milestone.query.filter_by(project_id=project_id).delete()
        
        # Remove related tasks
        Task.query.filter_by(project_id=project_id).delete()
        
        # Remove related schedules if they exist
        if hasattr(Schedule, 'project_id'):
            Schedule.query.filter_by(project_id=project_id).delete()
        
        # Delete the project
        db.session.delete(project)
        db.session.commit()
        
        current_app.logger.info(f"Project {project_name} (ID: {project_id}) deleted by {current_user.name}")
        
        flash(f'Project "{project_name}" deleted successfully', 'success')
        return redirect(url_for('admin.projects'))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Delete project error: {str(e)}", exc_info=True)
        flash(f'Error deleting project: {str(e)}', 'error')
        return redirect(url_for('admin.projects'))


# Update project status endpoint
@admin_bp.route('/<int:project_id>/update-status', methods=['POST'])
@login_required
@role_required([Roles.SUPER_HQ])
def update_project_status(project_id):
    try:
        new_status = request.form.get('status')
        
        if not new_status:
            flash('Status is required', 'error')
            return redirect(url_for('admin.project_details', project_id=project_id))
        
        project = Project.query.get_or_404(project_id)
        old_status = project.status
        project.status = new_status
        project.updated_at = datetime.now()
        
        # Auto-update progress based on status
        if new_status == 'Completed':
            project.progress = 100.0
        elif new_status == 'Active' and not project.progress:
            project.progress = 10.0  # Start with 10% if active
        
        db.session.commit()
        
        current_app.logger.info(f"Project {project_id} status updated from {old_status} to {new_status}")
        
        flash(f'Project status updated to {new_status}', 'success')
        return redirect(url_for('admin.project_details', project_id=project_id))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update project status error: {str(e)}", exc_info=True)
        flash(f'Error updating status: {str(e)}', 'error')
        return redirect(url_for('admin.project_details', project_id=project_id))


# Update project progress endpoint
@admin_bp.route('/<int:project_id>/update-progress', methods=['POST'])
@login_required
@role_required([Roles.SUPER_HQ])
def update_project_progress(project_id):
    try:
        progress = float(request.form.get('progress', 0))
        
        if progress < 0 or progress > 100:
            flash('Progress must be between 0 and 100', 'error')
            return redirect(url_for('admin.project_details', project_id=project_id))
        
        project = Project.query.get_or_404(project_id)
        old_progress = project.progress
        project.progress = progress
        project.updated_at = datetime.now()
        
        # Auto-update status based on progress
        if progress == 100:
            project.status = 'Completed'
        elif progress > 0 and project.status == 'Planning':
            project.status = 'Active'
        
        db.session.commit()
        
        current_app.logger.info(f"Project {project_id} progress updated from {old_progress}% to {progress}%")
        
        flash(f'Project progress updated to {progress}%', 'success')
        return redirect(url_for('admin.project_details', project_id=project_id))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update project progress error: {str(e)}", exc_info=True)
        flash(f'Error updating progress: {str(e)}', 'error')
        return redirect(url_for('admin.project_details', project_id=project_id))


# Get project progress for admin dashboard
@admin_bp.route('/<int:project_id>/progress', methods=['GET'])
@login_required  
@role_required([Roles.SUPER_HQ])
def get_project_progress(project_id):
    try:
        project = Project.query.get_or_404(project_id)
        
        # Get updated milestone counts
        milestones = Milestone.query.filter_by(project_id=project_id).all()
        completed_milestones = [m for m in milestones if hasattr(m, 'status') and m.status == 'Completed']
        
        # Get updated task counts
        tasks = Task.query.filter_by(project_id=project_id).all()
        completed_tasks = [t for t in tasks if hasattr(t, 'status') and t.status == 'completed']
        
        return jsonify({
            'status': 'success',
            'progress': project.progress or 0,
            'milestone_count': len(milestones),
            'milestones_completed': len(completed_milestones),
            'task_count': len(tasks),
            'tasks_completed': len(completed_tasks),
            'project_status': project.status,
            'last_updated': project.updated_at.isoformat() if project.updated_at else None
        })
        
    except Exception as e:
        current_app.logger.error(f"Get admin project progress error: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error fetching project progress'}), 500


@admin_bp.route('/projects/<int:project_id>')
@login_required
def project_details(project_id):
    try:
        current_app.logger.info(f"User {current_user.id} accessing project {project_id}")
        project = Project.query.get_or_404(project_id)
        
        # Check if user has access to this project
        user_assignment = StaffAssignment.query.filter_by(
            project_id=project_id, 
            staff_id=current_user.id
        ).first()
        
        is_manager = project.project_manager == current_user.name
        is_super_hq = current_user.has_role(Roles.SUPER_HQ)
        
        current_app.logger.info(f"Access check - assignment: {bool(user_assignment)}, manager: {is_manager}, super_hq: {is_super_hq}")
        
        # Allow access if user is assigned, is the manager, or is SUPER_HQ
        if not (user_assignment or is_manager or is_super_hq):
            current_app.logger.warning(f"Access denied for user {current_user.id} to project {project_id}")
            flash("You don't have access to this project.", "error")
            return redirect(url_for('admin.projects'))
        
        # Get staff assignments with user details
        staff_assignments = db.session.query(StaffAssignment, User.name).join(
            User, StaffAssignment.staff_id == User.id
        ).filter(StaffAssignment.project_id == project_id).all()
        
        # Get employee assignments with employee details
        employee_assignments = db.session.query(EmployeeAssignment, Employee.name).join(
            Employee, EmployeeAssignment.employee_id == Employee.id
        ).filter(EmployeeAssignment.project_id == project_id).all()
        
        # Combine both types of assignments for display
        all_assignments = []
        
        # Add staff assignments
        for assignment, staff_name in staff_assignments:
            all_assignments.append({
                'assignment': assignment,
                'staff_name': staff_name,
                'type': 'user',
                'role': assignment.role,
                'assigned_at': assignment.assigned_at,
                'id': assignment.staff_id
            })
        
        # Add employee assignments
        for assignment, employee_name in employee_assignments:
            all_assignments.append({
                'assignment': assignment,
                'staff_name': employee_name,
                'type': 'employee',
                'role': assignment.role,
                'assigned_at': assignment.assigned_at,
                'id': f"emp_{assignment.employee_id}"
            })
        
        # Get ALL available staff and employees for assignment
        # Get all Users (Staff)
        all_users = User.query.all()
        
        # Get all Employees
        all_employees = Employee.query.all()
        
        # Create a combined list with type identification
        available_staff = []
        
        # Add all users (existing logic - show as available even if assigned)
        for user in all_users:
            is_assigned = any(assignment['id'] == user.id for assignment in all_assignments)
            
            available_staff.append({
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'role': user.role,
                'type': 'user',
                'display_info': f"{user.role} | {user.email}",
                'is_assigned': is_assigned
            })
        
        # Add all employees with unique negative IDs to avoid conflicts
        for employee in all_employees:
            employee_id = f"emp_{employee.id}"
            is_assigned = any(assignment['id'] == employee_id for assignment in all_assignments)
            
            available_staff.append({
                'id': employee_id,  # Prefix to distinguish from users
                'name': employee.name,
                'email': employee.email or 'No email',
                'role': employee.role or employee.position or 'Employee',
                'type': 'employee',
                'display_info': f"{employee.department or 'No Dept'} | {employee.role or employee.position or 'Employee'}",
                'is_assigned': is_assigned,
                'staff_code': employee.staff_code,
                'department': employee.department
            })
        
        # Get milestones with status counts
        milestones = Milestone.query.filter_by(project_id=project_id).all()
        completed_milestones = [m for m in milestones if hasattr(m, 'status') and m.status == 'Completed']
        pending_milestones = [m for m in milestones if hasattr(m, 'status') and m.status == 'Pending']
        overdue_milestones = [m for m in milestones if hasattr(m, 'status') and m.status == 'Pending' and hasattr(m, 'due_date') and m.due_date and m.due_date < datetime.now().date()]
        
        # Get schedules if they exist
        schedules = Schedule.query.filter_by(project_id=project_id).all() if hasattr(Schedule, 'project_id') else []
        
        # Get tasks for the project
        tasks = Task.query.filter_by(project_id=project_id).all()
        completed_tasks = [t for t in tasks if hasattr(t, 'status') and t.status == 'completed']
        
        # Calculate project metrics
        progress = project.progress or 0
        if milestones:
            milestone_progress = (len(completed_milestones) / len(milestones)) * 100
            # Use milestone progress if it differs significantly from stored progress
            if abs(milestone_progress - progress) > 5:
                progress = milestone_progress
        
        # Budget calculations
        total_budget = project.budget or 0
        # Get total expenses for this project (if expense model has project_id)
        project_expenses = []
        if hasattr(Expense, 'project_id'):
            project_expenses = Expense.query.filter_by(project_id=project_id).all()
        elif hasattr(Expense, 'user_id'):
            # Fallback: if expenses are linked to users instead of projects
            assigned_user_ids = [assignment.staff_id for assignment, _ in staff_assignments]
            if assigned_user_ids:
                project_expenses = Expense.query.filter(Expense.user_id.in_(assigned_user_ids)).all()
        
        spent_amount = sum(expense.amount for expense in project_expenses if hasattr(expense, 'amount'))
        remaining_budget = total_budget - spent_amount
        budget_utilization = (spent_amount / total_budget * 100) if total_budget > 0 else 0
        
        # Timeline calculations
        is_overdue = False
        days_remaining = None
        if project.end_date:
            today = datetime.now().date()
            if project.end_date < today:
                is_overdue = True
                days_remaining = (today - project.end_date).days
            else:
                days_remaining = (project.end_date - today).days
        
        # Team statistics (combine both user and employee assignments)
        team_size = len(all_assignments)
        team_roles = {}
        for assignment_data in all_assignments:
            role = assignment_data['role'] or 'Unknown'
            if role in team_roles:
                team_roles[role] += 1
            else:
                team_roles[role] = 1
        
        # Project health calculation
        health_status = "Good"
        if is_overdue or budget_utilization > 90:
            health_status = "Critical"
        elif progress < 50 and days_remaining and days_remaining < 30:
            health_status = "Warning"
        elif len(overdue_milestones) > 0:
            health_status = "Warning"
        
        # Recent activity (last 3 milestones or tasks)
        recent_milestones = []
        if milestones:
            recent_milestones = sorted([m for m in milestones if hasattr(m, 'due_date') and m.due_date], 
                                     key=lambda x: x.due_date, reverse=True)[:3]
        
        recent_tasks = []
        if tasks:
            recent_tasks = sorted([t for t in tasks if hasattr(t, 'updated_at') and t.updated_at], 
                                key=lambda x: x.updated_at, reverse=True)[:3]
        
        # BOQ calculations
        boq_items = []
        total_boq_cost = 0
        try:
            boq_items = BOQItem.query.filter_by(project_id=project_id).all()
            total_boq_cost = sum(item.total_cost for item in boq_items if hasattr(item, 'total_cost') and item.total_cost)
        except Exception as boq_error:
            current_app.logger.warning(f"BOQ query error: {str(boq_error)}")

        # Get documents and activity log safely
        documents = []
        activity_log = []
        try:
            documents = ProjectDocument.query.filter_by(project_id=project_id).all()
        except Exception as doc_error:
            current_app.logger.warning(f"Document query error: {str(doc_error)}")
        
        try:
            activity_log = ProjectActivity.query.filter_by(project_id=project_id).order_by(ProjectActivity.created_at.desc()).limit(10).all()
        except Exception as activity_error:
            current_app.logger.warning(f"Activity query error: {str(activity_error)}")

        return render_template('admin/view_project.html',
                             project=project,
                             staff_assignments=all_assignments,
                             available_staff=available_staff,
                             milestones=milestones,
                             schedules=schedules,
                             tasks=tasks,
                             # Metrics
                             progress=round(progress, 1),
                             milestone_count=len(milestones),
                             completed_milestones=len(completed_milestones),
                             pending_milestones=len(pending_milestones),
                             overdue_milestones=len(overdue_milestones),
                             task_count=len(tasks),
                             completed_tasks=len(completed_tasks),
                             # Budget
                             total_budget=total_budget,
                             spent_amount=spent_amount,
                             remaining_budget=remaining_budget,
                             budget_utilization=round(budget_utilization, 1),
                             # Timeline
                             is_overdue=is_overdue,
                             days_remaining=days_remaining,
                             # Team
                             team_size=team_size,
                             team_roles=team_roles,
                             # Health
                             health_status=health_status,
                             # Recent activity
                             recent_milestones=recent_milestones,
                             recent_tasks=recent_tasks,
                             # Additional data for enhanced template
                             boq_items=boq_items,
                             total_boq_cost=total_boq_cost,
                             documents=documents,
                             activity_log=activity_log)
    except Exception as e:
        current_app.logger.error(f"Admin project details error: {str(e)}", exc_info=True)
        current_app.logger.error(f"Error type: {type(e).__name__}")
        current_app.logger.error(f"Error args: {e.args}")
        flash(f"Error loading project details: {str(e)}", "error")
        return redirect(url_for('admin.projects'))


# ===== ENHANCED PROJECT MANAGEMENT ROUTES =====

@admin_bp.route('/projects/<int:project_id>/assign_staff', methods=['POST'])
@login_required
@role_required([Roles.SUPER_HQ])
def assign_staff_new(project_id):
    """Enhanced staff assignment endpoint"""
    try:
        project = Project.query.get_or_404(project_id)
        
        staff_id = request.form.get('staff_id')
        role = request.form.get('role')
        
        if not staff_id or not role:
            flash('Staff ID and role are required', 'error')
            return redirect(url_for('admin.project_details', project_id=project_id))
        
        # Handle employee IDs (prefixed with 'emp_')
        if str(staff_id).startswith('emp_'):
            # This is an employee from HR database
            employee_id = str(staff_id).replace('emp_', '')
            employee = Employee.query.get(employee_id)
            
            if not employee:
                flash('Employee not found', 'error')
                return redirect(url_for('admin.project_details', project_id=project_id))
            
            # Check if employee is already assigned
            existing_assignment = EmployeeAssignment.query.filter_by(
                project_id=project_id, 
                employee_id=employee_id
            ).first()
            
            if existing_assignment:
                flash('Employee is already assigned to this project', 'warning')
                return redirect(url_for('admin.project_details', project_id=project_id))
            
            # Create new employee assignment
            assignment = EmployeeAssignment(
                project_id=project_id,
                employee_id=employee_id,
                role=role,
                assigned_at=datetime.utcnow(),
                assigned_by=current_user.id,
                status='Active'
            )
            
            db.session.add(assignment)
            
            # Log activity
            activity = ProjectActivity(
                project_id=project_id,
                user_id=current_user.id,
                action_type='employee_assigned',
                description=f'{employee.name} was assigned as {role}',
                user_name=current_user.name
            )
            db.session.add(activity)
            
            db.session.commit()
            
            flash(f'{employee.name} has been assigned as {role}', 'success')
            return redirect(url_for('admin.project_details', project_id=project_id))
            
        else:
            # This is a regular user
            # Check if staff is already assigned
            existing_assignment = StaffAssignment.query.filter_by(
                project_id=project_id, 
                staff_id=staff_id
            ).first()
            
            if existing_assignment:
                flash('Staff member is already assigned to this project', 'warning')
                return redirect(url_for('admin.project_details', project_id=project_id))
            
            # Get staff member details
            staff_member = User.query.get(staff_id)
            if not staff_member:
                flash('Staff member not found', 'error')
                return redirect(url_for('admin.project_details', project_id=project_id))
            
            # Create new assignment for user
            assignment = StaffAssignment(
                project_id=project_id,
                staff_id=staff_id,
                role=role,
                assigned_at=datetime.utcnow()
            )
            
            db.session.add(assignment)
            
            # Log activity
            activity = ProjectActivity(
                project_id=project_id,
                user_id=current_user.id,
                action_type='staff_assigned',
                description=f'{staff_member.name} was assigned as {role}',
                user_name=current_user.name
            )
            db.session.add(activity)
            
            db.session.commit()
            
            flash(f'{staff_member.name} has been assigned as {role}', 'success')
            
        return redirect(url_for('admin.project_details', project_id=project_id))
        
    except Exception as e:
        current_app.logger.error(f"Error assigning staff: {str(e)}", exc_info=True)
        db.session.rollback()
        flash('An error occurred while assigning staff', 'error')
        return redirect(url_for('admin.project_details', project_id=project_id))


@admin_bp.route('/projects/<int:project_id>/remove_staff', methods=['POST'])
@login_required
@role_required([Roles.SUPER_HQ])
def remove_staff_new(project_id):
    """Enhanced staff removal endpoint"""
    try:
        project = Project.query.get_or_404(project_id)
        
        # Try JSON first, then form data
        data = request.get_json() or request.form
        staff_id = data.get('staff_id')
        
        if not staff_id:
            flash('Staff ID is required', 'error')
            return redirect(url_for('admin.project_details', project_id=project_id))
        
        # Find and remove assignment
        assignment = StaffAssignment.query.filter_by(
            project_id=project_id,
            staff_id=staff_id
        ).first()
        
        if not assignment:
            flash('Staff assignment not found', 'error')
            return redirect(url_for('admin.project_details', project_id=project_id))
        
        # Get staff member details for logging
        staff_member = User.query.get(staff_id)
        staff_name = staff_member.name if staff_member else 'Unknown'
        role = assignment.role
        
        db.session.delete(assignment)
        
        # Log activity
        activity = ProjectActivity(
            project_id=project_id,
            user_id=current_user.id,
            action_type='staff_removed',
            description=f'{staff_name} was removed from {role} role',
            user_name=current_user.name
        )
        db.session.add(activity)
        
        db.session.commit()
        
        flash(f'{staff_name} has been removed from the project', 'success')
        return redirect(url_for('admin.project_details', project_id=project_id))
        
    except Exception as e:
        current_app.logger.error(f"Error removing staff: {str(e)}", exc_info=True)
        db.session.rollback()
        flash('An error occurred while removing staff', 'error')
        return redirect(url_for('admin.project_details', project_id=project_id))


@admin_bp.route('/projects/<int:project_id>/add_milestone', methods=['POST'])
@login_required
@role_required([Roles.SUPER_HQ])
def add_milestone_new(project_id):
    """Enhanced milestone creation endpoint"""
    try:
        project = Project.query.get_or_404(project_id)
        
        milestone_name = request.form.get('milestone_name')
        milestone_description = request.form.get('milestone_description', '')
        due_date_str = request.form.get('due_date')
        
        if not milestone_name or not due_date_str:
            flash('Milestone name and due date are required', 'error')
            return redirect(url_for('admin.project_details', project_id=project_id))
        
        # Parse due date
        try:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format', 'error')
            return redirect(url_for('admin.project_details', project_id=project_id))
        
        # Create new milestone
        milestone = Milestone(
            project_id=project_id,
            title=milestone_name,
            due_date=due_date,
            status='Pending'
        )
        
        # Add description if Milestone model supports it
        if hasattr(milestone, 'description'):
            milestone.description = milestone_description
        
        db.session.add(milestone)
        
        # Log activity
        activity = ProjectActivity(
            project_id=project_id,
            user_id=current_user.id,
            action_type='milestone_added',
            description=f'Milestone "{milestone_name}" was created with due date {due_date.strftime("%B %d, %Y")}',
            user_name=current_user.name
        )
        db.session.add(activity)
        
        db.session.commit()
        
        flash(f'Milestone "{milestone_name}" has been created', 'success')
        return redirect(url_for('admin.project_details', project_id=project_id))
        
    except Exception as e:
        current_app.logger.error(f"Error adding milestone: {str(e)}", exc_info=True)
        db.session.rollback()
        flash('An error occurred while adding milestone', 'error')
        return redirect(url_for('admin.project_details', project_id=project_id))


@admin_bp.route('/projects/<int:project_id>/milestones/<int:milestone_id>', methods=['POST', 'DELETE'])
@login_required
@role_required([Roles.SUPER_HQ])
def delete_milestone_new(project_id, milestone_id):
    """Enhanced milestone deletion endpoint"""
    try:
        project = Project.query.get_or_404(project_id)
        milestone = Milestone.query.filter_by(id=milestone_id, project_id=project_id).first()
        
        if not milestone:
            flash('Milestone not found', 'error')
            return redirect(url_for('admin.project_details', project_id=project_id))
        
        milestone_title = milestone.title
        db.session.delete(milestone)
        
        # Log activity
        activity = ProjectActivity(
            project_id=project_id,
            user_id=current_user.id,
            action_type='milestone_deleted',
            description=f'Milestone "{milestone_title}" was deleted',
            user_name=current_user.name
        )
        db.session.add(activity)
        
        db.session.commit()
        
        flash(f'Milestone "{milestone_title}" has been deleted', 'success')
        return redirect(url_for('admin.project_details', project_id=project_id))
        
    except Exception as e:
        current_app.logger.error(f"Error deleting milestone: {str(e)}", exc_info=True)
        db.session.rollback()
        flash('An error occurred while deleting milestone', 'error')
        return redirect(url_for('admin.project_details', project_id=project_id))


@admin_bp.route('/projects/<int:project_id>/add_boq_item', methods=['POST'])
@login_required
@role_required([Roles.SUPER_HQ])
def add_boq_item(project_id):
    """Add BOQ (Bill of Quantities) item endpoint"""
    try:
        project = Project.query.get_or_404(project_id)
        
        item_description = request.form.get('item_description')
        quantity = request.form.get('quantity')
        unit = request.form.get('unit')
        unit_price = request.form.get('unit_price')
        
        if not all([item_description, quantity, unit, unit_price]):
            return jsonify({'success': False, 'message': 'All fields are required'}), 400
        
        try:
            quantity = float(quantity)
            unit_price = float(unit_price)
            total_cost = quantity * unit_price
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid numeric values'}), 400
        
        # Create new BOQ item
        boq_item = BOQItem(
            project_id=project_id,
            item_description=item_description,
            quantity=quantity,
            unit=unit,
            unit_price=unit_price,
            total_cost=total_cost
        )
        
        db.session.add(boq_item)
        
        # Log activity
        activity = ProjectActivity(
            project_id=project_id,
            user_id=current_user.id,
            action_type='boq_item_added',
            description=f'BOQ item "{item_description}" was added (₦{total_cost:,.2f})',
            user_name=current_user.name
        )
        db.session.add(activity)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'BOQ item "{item_description}" has been added'
        })
        
    except Exception as e:
        current_app.logger.error(f"Error adding BOQ item: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({'success': False, 'message': 'An error occurred while adding BOQ item'}), 500


@admin_bp.route('/projects/<int:project_id>/boq_items/<int:item_id>', methods=['DELETE'])
@login_required
@role_required([Roles.SUPER_HQ])
def delete_boq_item(project_id, item_id):
    """Delete BOQ item endpoint"""
    try:
        project = Project.query.get_or_404(project_id)
        boq_item = BOQItem.query.filter_by(id=item_id, project_id=project_id).first()
        
        if not boq_item:
            return jsonify({'success': False, 'message': 'BOQ item not found'}), 404
        
        item_description = boq_item.item_description
        db.session.delete(boq_item)
        
        # Log activity
        activity = ProjectActivity(
            project_id=project_id,
            user_id=current_user.id,
            action_type='boq_item_deleted',
            description=f'BOQ item "{item_description}" was deleted',
            user_name=current_user.name
        )
        db.session.add(activity)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'BOQ item "{item_description}" has been deleted'
        })
        
    except Exception as e:
        current_app.logger.error(f"Error deleting BOQ item: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({'success': False, 'message': 'An error occurred while deleting BOQ item'}), 500


@admin_bp.route('/projects/<int:project_id>/upload_document', methods=['POST'])
@login_required
@role_required([Roles.SUPER_HQ])
def upload_document(project_id):
    """Enhanced document upload endpoint"""
    try:
        project = Project.query.get_or_404(project_id)
        
        if 'document_file' not in request.files:
            flash('No file selected', 'error')
            return redirect(url_for('admin.project_details', project_id=project_id))
        
        file = request.files['document_file']
        document_type = request.form.get('document_type')
        description = request.form.get('document_description', '')
        
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('admin.project_details', project_id=project_id))
        
        if not document_type:
            flash('Document type is required', 'error')
            return redirect(url_for('admin.project_details', project_id=project_id))
        
        # Validate file type
        allowed_extensions = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'png', 'jpg', 'jpeg'}
        if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
            flash('File type not allowed', 'error')
            return redirect(url_for('admin.project_details', project_id=project_id))
        
        # Create uploads directory if it doesn't exist
        upload_folder = os.path.join(current_app.root_path, 'uploads', 'projects', str(project_id))
        os.makedirs(upload_folder, exist_ok=True)
        
        # Generate secure filename
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        unique_filename = timestamp + filename
        file_path = os.path.join(upload_folder, unique_filename)
        
        # Save file
        file.save(file_path)
        file_size = os.path.getsize(file_path)
        
        # Create document record
        document = ProjectDocument(
            project_id=project_id,
            filename=unique_filename,
            original_filename=filename,
            document_type=document_type,
            description=description,
            file_size=file_size,
            file_path=file_path,
            uploader_id=current_user.id,
            uploader_name=current_user.name
        )
        
        db.session.add(document)
        
        # Log activity
        activity = ProjectActivity(
            project_id=project_id,
            user_id=current_user.id,
            action_type='document_uploaded',
            description=f'Document "{filename}" was uploaded ({document_type})',
            user_name=current_user.name
        )
        db.session.add(activity)
        
        db.session.commit()
        
        flash(f'Document "{filename}" has been uploaded successfully', 'success')
        return redirect(url_for('admin.project_details', project_id=project_id))
        
    except Exception as e:
        current_app.logger.error(f"Error uploading document: {str(e)}", exc_info=True)
        db.session.rollback()
        flash('An error occurred while uploading document', 'error')
        return redirect(url_for('admin.project_details', project_id=project_id))


@admin_bp.route('/projects/<int:project_id>/documents/<int:document_id>/download')
@login_required
@role_required([Roles.SUPER_HQ])
def download_document(project_id, document_id):
    """Enhanced document download endpoint"""
    try:
        project = Project.query.get_or_404(project_id)
        document = ProjectDocument.query.filter_by(id=document_id, project_id=project_id).first()
        
        if not document:
            flash('Document not found', 'error')
            return redirect(url_for('admin.project_details', project_id=project_id))
        
        if not os.path.exists(document.file_path):
            flash('File not found on disk', 'error')
            return redirect(url_for('admin.project_details', project_id=project_id))
        
        return send_file(
            document.file_path,
            as_attachment=True,
            download_name=document.original_filename,
            mimetype='application/octet-stream'
        )
        
    except Exception as e:
        current_app.logger.error(f"Error downloading document: {str(e)}", exc_info=True)
        flash('An error occurred while downloading the document', 'error')
        return redirect(url_for('admin.project_details', project_id=project_id))


@admin_bp.route('/projects/<int:project_id>/documents/<int:document_id>', methods=['POST', 'DELETE'])
@login_required
@role_required([Roles.SUPER_HQ])
def delete_document(project_id, document_id):
    """Enhanced document deletion endpoint"""
    try:
        project = Project.query.get_or_404(project_id)
        document = ProjectDocument.query.filter_by(id=document_id, project_id=project_id).first()
        
        if not document:
            flash('Document not found', 'error')
            return redirect(url_for('admin.project_details', project_id=project_id))
        
        # Delete file from disk
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
        
        document_name = document.original_filename
        db.session.delete(document)
        
        # Log activity
        activity = ProjectActivity(
            project_id=project_id,
            user_id=current_user.id,
            action_type='document_deleted',
            description=f'Document "{document_name}" was deleted',
            user_name=current_user.name
        )
        db.session.add(activity)
        
        db.session.commit()
        
        flash(f'Document "{document_name}" has been deleted', 'success')
        return redirect(url_for('admin.project_details', project_id=project_id))
        
    except Exception as e:
        current_app.logger.error(f"Error deleting document: {str(e)}", exc_info=True)
        db.session.rollback()
        flash('An error occurred while deleting document', 'error')
        return redirect(url_for('admin.project_details', project_id=project_id))


@admin_bp.route('/projects/<int:project_id>/update_progress', methods=['POST'])
@login_required
@role_required([Roles.SUPER_HQ])
def update_progress_new(project_id):
    """Enhanced progress update endpoint"""
    try:
        project = Project.query.get_or_404(project_id)
        
        data = request.get_json()
        progress = data.get('progress')
        
        if progress is None:
            return jsonify({'success': False, 'message': 'Progress value is required'}), 400
        
        try:
            progress = float(progress)
            if progress < 0 or progress > 100:
                return jsonify({'success': False, 'message': 'Progress must be between 0 and 100'}), 400
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid progress value'}), 400
        
        old_progress = project.progress or 0
        project.progress = progress
        
        # Log activity
        activity = ProjectActivity(
            project_id=project_id,
            user_id=current_user.id,
            action_type='progress_updated',
            description=f'Project progress updated from {old_progress}% to {progress}%',
            user_name=current_user.name
        )
        db.session.add(activity)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Project progress updated to {progress}%'
        })
        
    except Exception as e:
        current_app.logger.error(f"Error updating progress: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({'success': False, 'message': 'An error occurred while updating progress'}), 500


@admin_bp.route('/projects/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required([Roles.SUPER_HQ])
def edit_project(project_id):
    """Edit project information endpoint"""
    try:
        project = Project.query.get_or_404(project_id)
        
        if request.method == 'GET':
            # Return project data for modal/form population
            project_data = {
                'id': project.id,
                'name': project.name,
                'description': project.description,
                'start_date': project.start_date.isoformat() if project.start_date else None,
                'end_date': project.end_date.isoformat() if project.end_date else None,
                'status': project.status,
                'project_manager': project.project_manager,
                'budget': project.budget,
                'project_type': project.project_type,
                'priority': project.priority,
                'client_name': project.client_name,
                'site_location': project.site_location,
                'funding_source': project.funding_source,
                'risk_level': project.risk_level,
                'safety_requirements': project.safety_requirements,
                'regulatory_requirements': project.regulatory_requirements
            }
            return jsonify({'success': True, 'project': project_data})
        
        elif request.method == 'POST':
            # Handle project update
            data = request.get_json() or request.form
            
            # Store old values for activity log
            changes = []
            
            # Update fields if provided
            if 'name' in data and data['name'] != project.name:
                changes.append(f"Name changed from '{project.name}' to '{data['name']}'")
                project.name = data['name']
            
            if 'description' in data and data['description'] != project.description:
                changes.append(f"Description updated")
                project.description = data['description']
            
            if 'start_date' in data:
                new_start = datetime.strptime(data['start_date'], '%Y-%m-%d').date() if data['start_date'] else None
                if new_start != project.start_date:
                    changes.append(f"Start date changed to {new_start.strftime('%B %d, %Y') if new_start else 'None'}")
                    project.start_date = new_start
            
            if 'end_date' in data:
                new_end = datetime.strptime(data['end_date'], '%Y-%m-%d').date() if data['end_date'] else None
                if new_end != project.end_date:
                    changes.append(f"End date changed to {new_end.strftime('%B %d, %Y') if new_end else 'None'}")
                    project.end_date = new_end
            
            if 'status' in data and data['status'] != project.status:
                changes.append(f"Status changed from '{project.status}' to '{data['status']}'")
                project.status = data['status']
            
            if 'project_manager' in data and data['project_manager'] != project.project_manager:
                changes.append(f"Project manager changed to '{data['project_manager']}'")
                project.project_manager = data['project_manager']
            
            if 'budget' in data:
                try:
                    new_budget = float(data['budget'])
                    if new_budget != project.budget:
                        changes.append(f"Budget changed from ₦{project.budget:,.2f} to ₦{new_budget:,.2f}")
                        project.budget = new_budget
                except ValueError:
                    return jsonify({'success': False, 'message': 'Invalid budget value'}), 400
            
            if 'project_type' in data and data['project_type'] != project.project_type:
                changes.append(f"Project type changed to '{data['project_type']}'")
                project.project_type = data['project_type']
            
            if 'priority' in data and data['priority'] != project.priority:
                changes.append(f"Priority changed to '{data['priority']}'")
                project.priority = data['priority']
            
            if 'client_name' in data and data['client_name'] != project.client_name:
                changes.append(f"Client name changed to '{data['client_name']}'")
                project.client_name = data['client_name']
            
            if 'site_location' in data and data['site_location'] != project.site_location:
                changes.append(f"Site location updated")
                project.site_location = data['site_location']
            
            if 'funding_source' in data and data['funding_source'] != project.funding_source:
                changes.append(f"Funding source changed to '{data['funding_source']}'")
                project.funding_source = data['funding_source']
            
            if 'risk_level' in data and data['risk_level'] != project.risk_level:
                changes.append(f"Risk level changed to '{data['risk_level']}'")
                project.risk_level = data['risk_level']
            
            if 'safety_requirements' in data and data['safety_requirements'] != project.safety_requirements:
                changes.append(f"Safety requirements changed to '{data['safety_requirements']}'")
                project.safety_requirements = data['safety_requirements']
            
            if 'regulatory_requirements' in data and data['regulatory_requirements'] != project.regulatory_requirements:
                changes.append(f"Regulatory requirements updated")
                project.regulatory_requirements = data['regulatory_requirements']
            
            # Update the updated_at timestamp
            project.updated_at = datetime.utcnow()
            
            # Log activities for changes
            if changes:
                activity = ProjectActivity(
                    project_id=project_id,
                    user_id=current_user.id,
                    action_type='project_updated',
                    description=f'Project updated: {"; ".join(changes)}',
                    user_name=current_user.name
                )
                db.session.add(activity)
                
                db.session.commit()
                
                return jsonify({
                    'success': True, 
                    'message': 'Project updated successfully',
                    'changes': len(changes)
                })
            else:
                return jsonify({'success': True, 'message': 'No changes made'})
        
    except Exception as e:
        current_app.logger.error(f"Error editing project: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500


@admin_bp.route('/projects/<int:project_id>/activity_log')
@login_required
def get_activity_log(project_id):
    """Get detailed activity log for a project"""
    try:
        project = Project.query.get_or_404(project_id)
        
        # Check user access
        user_assignment = StaffAssignment.query.filter_by(
            project_id=project_id, 
            staff_id=current_user.id
        ).first()
        
        is_manager = project.project_manager == current_user.name
        is_super_hq = current_user.has_role(Roles.SUPER_HQ)
        
        if not (user_assignment or is_manager or is_super_hq):
            return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        # Get activity log with pagination
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        activities_query = ProjectActivity.query.filter_by(project_id=project_id)\
                                                .order_by(ProjectActivity.created_at.desc())
        
        activities_paginated = activities_query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        activities_data = []
        for activity in activities_paginated.items:
            activity_data = {
                'id': activity.id,
                'action_type': activity.action_type,
                'description': activity.description,
                'user_name': activity.user_name or 'System',
                'created_at': activity.created_at.strftime('%B %d, %Y at %I:%M %p'),
                'created_at_iso': activity.created_at.isoformat(),
                'user_id': activity.user_id
            }
            activities_data.append(activity_data)
        
        # Get activity statistics
        total_activities = activities_query.count()
        
        # Activity type breakdown
        activity_types = db.session.query(
            ProjectActivity.action_type,
            func.count(ProjectActivity.id).label('count')
        ).filter_by(project_id=project_id)\
         .group_by(ProjectActivity.action_type)\
         .all()
        
        activity_stats = {action_type: count for action_type, count in activity_types}
        
        # Recent activity summary (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_count = ProjectActivity.query.filter(
            ProjectActivity.project_id == project_id,
            ProjectActivity.created_at >= week_ago
        ).count()
        
        return jsonify({
            'success': True,
            'activities': activities_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total_activities,
                'pages': activities_paginated.pages,
                'has_prev': activities_paginated.has_prev,
                'has_next': activities_paginated.has_next
            },
            'statistics': {
                'total_activities': total_activities,
                'recent_activities_week': recent_count,
                'activity_types': activity_stats
            },
            'project': {
                'id': project.id,
                'name': project.name,
                'created_at': project.created_at.strftime('%B %d, %Y')
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting activity log: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500


@admin_bp.route('/projects/<int:project_id>/reports')
@role_required([Roles.SUPER_HQ])
def project_reports(project_id):
    """Project analytics and reports page"""
    try:
        current_app.logger.info(f"Accessing project reports for project_id: {project_id}")
        
        # Get project
        project = Project.query.get_or_404(project_id)
        current_app.logger.info(f"Project found: {project.name}")
        
        # Calculate analytics data using correct relationships with safe access
        try:
            total_employees = len(project.staff_assignments) if hasattr(project, 'staff_assignments') and project.staff_assignments else 0
        except Exception:
            total_employees = 0
            
        try:
            total_milestones = len(project.milestones) if hasattr(project, 'milestones') and project.milestones else 0
        except Exception:
            total_milestones = 0
            
        try:
            completed_milestones = len([m for m in project.milestones if m.status and m.status.lower() == 'completed']) if hasattr(project, 'milestones') and project.milestones else 0
        except Exception:
            completed_milestones = 0
            
        try:
            total_documents = len(project.project_documents) if hasattr(project, 'project_documents') and project.project_documents else 0
        except Exception:
            total_documents = 0
        
        # Equipment statistics - using general Equipment model since no project relation exists
        all_equipment = Equipment.query.all()
        equipment_stats = {}
        if all_equipment:
            equipment_stats['total'] = len(all_equipment)
            equipment_stats['operational'] = len([e for e in all_equipment if e.status and e.status.lower() in ['operational', 'active']])
            equipment_stats['maintenance'] = len([e for e in all_equipment if e.status and e.status.lower() in ['maintenance', 'under maintenance']])
        else:
            equipment_stats['total'] = 0
            equipment_stats['operational'] = 0
            equipment_stats['maintenance'] = 0
        
        # Financial data - using budget and purchase orders since no direct expenses relation
        total_expenses = 0
        try:
            if hasattr(project, 'purchase_orders') and project.purchase_orders:
                total_expenses = sum(order.total_amount or 0 for order in project.purchase_orders)
            elif hasattr(project, 'budgets') and project.budgets:
                total_expenses = sum(budget.allocated_amount or 0 for budget in project.budgets)
        except Exception:
            total_expenses = 0
        
        # Progress statistics
        milestone_completion_rate = (completed_milestones / total_milestones * 100) if total_milestones > 0 else 0
        
        # Get recent milestones for the template
        recent_milestones = []
        try:
            if hasattr(project, 'milestones') and project.milestones:
                recent_milestones = sorted([m for m in project.milestones if hasattr(m, 'created_at')], 
                                         key=lambda x: x.created_at if x.created_at else datetime.min, 
                                         reverse=True)[:5]
        except Exception:
            recent_milestones = []

        # Get equipment data
        total_equipment = 0
        active_equipment = 0
        try:
            if hasattr(project, 'equipment') and project.equipment:
                total_equipment = len(project.equipment)
                active_equipment = len([e for e in project.equipment if hasattr(e, 'status') and e.status and e.status.lower() in ['active', 'operational']])
        except Exception:
            total_equipment = 0
            active_equipment = 0

        # Calculate budget utilization
        budget_utilized = total_expenses / 1000 if total_expenses > 0 else 0  # Convert to thousands

        # Get recent tasks and alerts (mock data for now)
        recent_tasks = []
        recent_alerts = []

        analytics_data = {
            'project': project,
            'total_employees': total_employees or 0,
            'total_milestones': total_milestones or 0,
            'completed_milestones': completed_milestones or 0,
            'milestone_completion_rate': round(milestone_completion_rate, 1) if milestone_completion_rate is not None else 0,
            'total_documents': total_documents or 0,
            'equipment_stats': equipment_stats or {'total': 0, 'operational': 0, 'maintenance': 0},
            'total_expenses': total_expenses or 0,
            'total_equipment': total_equipment or 0,
            'active_equipment': active_equipment or 0,
            'budget_utilized': budget_utilized or 0,
            'recent_milestones': recent_milestones or [],
            'recent_tasks': recent_tasks or [],
            'recent_alerts': recent_alerts or [],
            'recent_activities': project.milestones[-5:] if hasattr(project, 'milestones') and project.milestones else []
        }
        
        return render_template('admin/project_reports.html', **analytics_data)
        
    except Exception as e:
        current_app.logger.error(f"Error loading project reports for project {project_id}: {str(e)}", exc_info=True)
        current_app.logger.error(f"Exception type: {type(e).__name__}")
        current_app.logger.error(f"Exception args: {e.args}")
        flash(f'Error loading project reports: {str(e)}. Please try again.', 'error')
        return redirect(url_for('admin.project_details', project_id=project_id))


@admin_bp.route('/projects/<int:project_id>/budget-analysis')
@role_required([Roles.SUPER_HQ])
def budget_analysis(project_id):
    """Comprehensive budget analysis with real business logic"""
    try:
        current_app.logger.info(f"Accessing budget analysis for project_id: {project_id}")
        
        # Get project with all related data
        project = Project.query.get_or_404(project_id)
        
        # Get all budgets for this project
        budgets = Budget.query.filter_by(project_id=project_id).all()
        
        # Get all expenses related to this project (assuming expenses have project_id or can be linked)
        # For now, we'll get all expenses and categorize them
        expenses = Expense.query.all()  # In real scenario, filter by project
        
        # Get procurement requests for this project
        procurement_requests = ProcurementRequest.query.filter_by(project_id=project_id).all()
        
        # Get purchase orders for this project
        purchase_orders = PurchaseOrder.query.filter_by(project_id=project_id).all()
        
        # Calculate budget totals
        total_allocated = sum([b.allocated_amount for b in budgets])
        total_spent = sum([b.spent_amount for b in budgets])
        total_remaining = total_allocated - total_spent
        
        # Calculate budget utilization percentage
        utilization_percentage = (total_spent / total_allocated * 100) if total_allocated > 0 else 0
        
        # Budget breakdown by category
        budget_breakdown = {}
        for budget in budgets:
            budget_breakdown[budget.category] = {
                'allocated': budget.allocated_amount,
                'spent': budget.spent_amount,
                'remaining': budget.remaining_amount,
                'usage_percentage': budget.usage_percentage
            }
        
        # Calculate expense trends (last 6 months)
        from datetime import datetime, timedelta
        from sqlalchemy import extract, func
        
        current_date = datetime.now()
        six_months_ago = current_date - timedelta(days=180)
        
        # Monthly expense trends
        monthly_expenses = db.session.query(
            extract('month', Expense.date).label('month'),
            extract('year', Expense.date).label('year'),
            func.sum(Expense.amount).label('total_amount'),
            func.count(Expense.id).label('expense_count')
        ).filter(
            Expense.date >= six_months_ago
        ).group_by(
            extract('year', Expense.date),
            extract('month', Expense.date)
        ).order_by(
            extract('year', Expense.date),
            extract('month', Expense.date)
        ).all()
        
        # Category-wise spending analysis
        category_spending = db.session.query(
            Expense.category,
            func.sum(Expense.amount).label('total_amount'),
            func.count(Expense.id).label('expense_count')
        ).group_by(Expense.category).all()
        
        # Cost variance analysis
        cost_variances = []
        for budget in budgets:
            variance = budget.spent_amount - budget.allocated_amount
            variance_percentage = (variance / budget.allocated_amount * 100) if budget.allocated_amount > 0 else 0
            cost_variances.append({
                'category': budget.category,
                'planned': budget.allocated_amount,
                'actual': budget.spent_amount,
                'variance': variance,
                'variance_percentage': variance_percentage,
                'status': 'over_budget' if variance > 0 else 'under_budget' if variance < 0 else 'on_budget'
            })
        
        # Procurement analysis
        total_procurement_value = sum([pr.price * pr.qty for pr in procurement_requests])
        pending_procurement = sum([pr.price * pr.qty for pr in procurement_requests if pr.status == 'pending'])
        approved_procurement = sum([pr.price * pr.qty for pr in procurement_requests if pr.status == 'approved'])
        
        # Purchase order analysis
        total_po_value = sum([po.total_amount for po in purchase_orders])
        pending_po_value = sum([po.total_amount for po in purchase_orders if po.status == 'Pending'])
        approved_po_value = sum([po.total_amount for po in purchase_orders if po.status == 'Approved'])
        
        # ROI and profitability analysis
        project_revenue = project.budget  # Assuming project budget represents revenue/contract value
        project_costs = total_spent
        gross_profit = project_revenue - project_costs
        profit_margin = (gross_profit / project_revenue * 100) if project_revenue > 0 else 0
        
        # Budget forecasting (simple linear projection)
        if monthly_expenses:
            # Calculate average monthly burn rate
            recent_months = monthly_expenses[-3:] if len(monthly_expenses) >= 3 else monthly_expenses
            avg_monthly_burn = sum([exp.total_amount for exp in recent_months]) / len(recent_months) if recent_months else 0
            
            # Forecast remaining budget duration
            months_remaining = (total_remaining / avg_monthly_burn) if avg_monthly_burn > 0 and total_remaining > 0 else 0
            
            # Forecast project completion cost
            if project.end_date:
                remaining_months = max(0, (project.end_date - current_date.date()).days / 30)
                forecasted_total_cost = total_spent + (avg_monthly_burn * remaining_months)
                cost_overrun_risk = max(0, forecasted_total_cost - total_allocated)
            else:
                forecasted_total_cost = 0
                cost_overrun_risk = 0
        else:
            avg_monthly_burn = 0
            months_remaining = 0
            forecasted_total_cost = 0
            cost_overrun_risk = 0
        
        # Risk indicators
        risk_indicators = {
            'budget_utilization_risk': 'high' if utilization_percentage > 80 else 'medium' if utilization_percentage > 60 else 'low',
            'cost_overrun_risk': 'high' if cost_overrun_risk > total_allocated * 0.1 else 'medium' if cost_overrun_risk > 0 else 'low',
            'cash_flow_risk': 'high' if months_remaining < 2 else 'medium' if months_remaining < 6 else 'low',
            'procurement_risk': 'high' if pending_procurement > total_allocated * 0.2 else 'medium' if pending_procurement > total_allocated * 0.1 else 'low'
        }
        
        # Key performance indicators
        kpis = {
            'budget_efficiency': min(100, max(0, 100 - abs(utilization_percentage - 80))),  # Optimal around 80%
            'cost_control_score': max(0, 100 - (abs(sum([cv['variance_percentage'] for cv in cost_variances]) / len(cost_variances)) if cost_variances else 0)),
            'procurement_efficiency': (approved_procurement / total_procurement_value * 100) if total_procurement_value > 0 else 100,
            'financial_health': max(0, min(100, profit_margin + 50))  # Normalized score
        }
        
        # Recent financial activities (last 30 days)
        thirty_days_ago = current_date - timedelta(days=30)
        recent_expenses = Expense.query.filter(Expense.date >= thirty_days_ago).order_by(Expense.date.desc()).limit(10).all()
        recent_procurement = ProcurementRequest.query.filter(
            ProcurementRequest.project_id == project_id,
            ProcurementRequest.created_at >= thirty_days_ago
        ).order_by(ProcurementRequest.created_at.desc()).limit(5).all()
        
        # Budget alerts
        budget_alerts = []
        for budget in budgets:
            if budget.usage_percentage > 90:
                budget_alerts.append({
                    'type': 'critical',
                    'category': budget.category,
                    'message': f'{budget.category} budget is {budget.usage_percentage:.1f}% utilized',
                    'severity': 'high'
                })
            elif budget.usage_percentage > 75:
                budget_alerts.append({
                    'type': 'warning',
                    'category': budget.category,
                    'message': f'{budget.category} budget is {budget.usage_percentage:.1f}% utilized',
                    'severity': 'medium'
                })
        
        if cost_overrun_risk > 0:
            budget_alerts.append({
                'type': 'forecast',
                'category': 'overall',
                'message': f'Potential cost overrun of ₦{cost_overrun_risk:,.2f} forecasted',
                'severity': 'high' if cost_overrun_risk > total_allocated * 0.1 else 'medium'
            })
        
        # Prepare chart data for JavaScript
        chart_categories = list(budget_breakdown.keys())
        chart_allocated = [budget_breakdown[cat]['allocated'] for cat in chart_categories]
        chart_spent = [budget_breakdown[cat]['spent'] for cat in chart_categories]
        
        # Compile all data for template
        budget_data = {
            'project': project,
            'budgets': budgets,
            'budget_breakdown': budget_breakdown,
            'total_allocated': total_allocated,
            'total_spent': total_spent,
            'total_remaining': total_remaining,
            'utilization_percentage': round(utilization_percentage, 1),
            'monthly_expenses': monthly_expenses,
            'category_spending': category_spending,
            'cost_variances': cost_variances,
            'total_procurement_value': total_procurement_value,
            'pending_procurement': pending_procurement,
            'approved_procurement': approved_procurement,
            'total_po_value': total_po_value,
            'pending_po_value': pending_po_value,
            'approved_po_value': approved_po_value,
            'project_revenue': project_revenue,
            'project_costs': project_costs,
            'gross_profit': gross_profit,
            'profit_margin': round(profit_margin, 1),
            'avg_monthly_burn': avg_monthly_burn,
            'months_remaining': round(months_remaining, 1),
            'forecasted_total_cost': forecasted_total_cost,
            'cost_overrun_risk': cost_overrun_risk,
            'risk_indicators': risk_indicators,
            'kpis': kpis,
            'recent_expenses': recent_expenses,
            'recent_procurement': recent_procurement,
            'budget_alerts': budget_alerts,
            'chart_categories': chart_categories,
            'chart_allocated': chart_allocated,
            'chart_spent': chart_spent
        }
        
        return render_template('admin/budget_analysis.html', **budget_data)
        
    except Exception as e:
        current_app.logger.error(f"Error loading budget analysis for project {project_id}: {str(e)}", exc_info=True)
        flash(f'Error loading budget analysis: {str(e)}. Please try again.', 'error')
        return redirect(url_for('admin.project_details', project_id=project_id))

# =====================================
# HR MANAGEMENT ROUTES (Admin Access)
# =====================================

@admin_bp.route("/hr")
@role_required([Roles.SUPER_HQ])
def hr_dashboard():
    """Admin HR Dashboard - Overview of HR operations"""
    try:
        from models import Employee, StaffPayroll, PayrollApproval
        
        # Get HR statistics
        total_employees = Employee.query.count()
        active_employees = Employee.query.filter_by(status='Active').count()
        
        # Get pending payroll approvals
        pending_payrolls = PayrollApproval.query.filter_by(status='pending_admin').all()
        total_pending_amount = sum(approval.total_amount for approval in pending_payrolls)
        
        # Get current month payroll status
        current_date = datetime.now()
        current_month_payroll = PayrollApproval.query.filter(
            PayrollApproval.period_year == current_date.year,
            PayrollApproval.period_month == current_date.month
        ).first()
        
        # Recent HR activities
        recent_employees = Employee.query.order_by(Employee.date_of_employment.desc()).limit(5).all()
        
        hr_summary = {
            'total_employees': total_employees,
            'active_employees': active_employees,
            'pending_payrolls': len(pending_payrolls),
            'total_pending_amount': total_pending_amount,
            'current_month_status': current_month_payroll.status if current_month_payroll else 'Not Submitted',
            'recent_employees': recent_employees
        }
        
        return render_template('admin/hr/dashboard.html', summary=hr_summary)
        
    except Exception as e:
        current_app.logger.error(f"Error loading HR dashboard: {str(e)}")
        flash('Error loading HR dashboard', 'error')
        return render_template('error.html')

@admin_bp.route("/hr/payroll-approvals")
@role_required([Roles.SUPER_HQ])
def payroll_approvals():
    """View pending payroll submissions for approval"""
    try:
        from models import PayrollApproval, StaffPayroll, Employee
        
        # Get all pending payroll approvals
        pending_approvals = PayrollApproval.query.filter_by(status='pending_admin').order_by(
            PayrollApproval.submitted_at.desc()
        ).all()
        
        # Format approval data with employee details
        approval_data = []
        for approval in pending_approvals:
            # Get payroll details for this approval
            payroll_items = StaffPayroll.query.filter(
                StaffPayroll.period_year == approval.period_year,
                StaffPayroll.period_month == approval.period_month,
                StaffPayroll.approval_status == 'pending_admin'
            ).all()
            
            # Get employee count and total
            employee_count = len(payroll_items)
            total_amount = sum(item.gross or 0 for item in payroll_items)
            
            approval_data.append({
                'id': approval.id,
                'period': f"{approval.period_month}/{approval.period_year}",
                'submitted_by': approval.submitted_by,
                'submitted_at': approval.submitted_at,
                'employee_count': employee_count,
                'total_amount': total_amount,
                'status': approval.status,
                'comments': approval.comments
            })
        
        return render_template('admin/hr/payroll_approvals.html', approvals=approval_data)
        
    except Exception as e:
        current_app.logger.error(f"Error loading payroll approvals: {str(e)}")
        flash('Error loading payroll approvals', 'error')
        return redirect(url_for('admin.hr_dashboard'))

@admin_bp.route("/hr/payroll-approval/<int:approval_id>")
@role_required([Roles.SUPER_HQ])
def view_payroll_details(approval_id):
    """View detailed payroll submission for approval"""
    try:
        from models import PayrollApproval, StaffPayroll, Employee
        
        # Get the approval record
        approval = PayrollApproval.query.get_or_404(approval_id)
        
        # Get all payroll items for this period
        payroll_items = StaffPayroll.query.filter(
            StaffPayroll.period_year == approval.period_year,
            StaffPayroll.period_month == approval.period_month,
            StaffPayroll.approval_status == 'pending_admin'
        ).order_by(StaffPayroll.id).all()
        
        # Format payroll data with employee details
        payroll_data = []
        total_gross = 0
        total_deductions = 0
        total_net = 0
        
        for item in payroll_items:
            employee = Employee.query.get(item.employee_id)
            gross = item.gross or 0
            deductions = (item.tax or 0) + (item.pension or 0) + (item.nhf or 0) + (item.nhis or 0) + (item.other_deductions or 0)
            net = gross - deductions
            
            total_gross += gross
            total_deductions += deductions
            total_net += net
            
            payroll_data.append({
                'employee_id': item.employee_id,
                'employee_name': employee.name if employee else 'Unknown',
                'designation': item.designation,
                'site': item.site,
                'work_days': item.work_days,
                'gross': gross,
                'tax': item.tax or 0,
                'pension': item.pension or 0,
                'nhf': item.nhf or 0,
                'nhis': item.nhis or 0,
                'other_deductions': item.other_deductions or 0,
                'total_deductions': deductions,
                'net_pay': net,
                'bank_name': item.bank_name,
                'account_number': item.account_number
            })
        
        summary = {
            'period': f"{approval.period_month}/{approval.period_year}",
            'submitted_by': approval.submitted_by,
            'submitted_at': approval.submitted_at,
            'employee_count': len(payroll_items),
            'total_gross': total_gross,
            'total_deductions': total_deductions,
            'total_net': total_net,
            'status': approval.status,
            'comments': approval.comments
        }
        
        return render_template('admin/hr/payroll_details.html', 
                             approval=approval, 
                             payroll_data=payroll_data, 
                             summary=summary)
        
    except Exception as e:
        current_app.logger.error(f"Error loading payroll details: {str(e)}")
        flash('Error loading payroll details', 'error')
        return redirect(url_for('admin.payroll_approvals'))

@admin_bp.route("/hr/approve-payroll/<int:approval_id>", methods=['POST'])
@role_required([Roles.SUPER_HQ])
def approve_payroll(approval_id):
    """Approve payroll submission and send to finance"""
    try:
        from models import PayrollApproval, StaffPayroll
        
        # Get the approval record
        approval = PayrollApproval.query.get_or_404(approval_id)
        
        if approval.status != 'pending_admin':
            flash('This payroll has already been processed', 'warning')
            return redirect(url_for('admin.payroll_approvals'))
        
        # Get admin comments
        admin_comments = request.form.get('comments', '').strip()
        
        # Update approval status
        approval.status = 'approved'
        approval.approved_by = session.get('username', 'Admin')
        approval.approved_at = datetime.now()
        approval.admin_comments = admin_comments
        
        # Update all related payroll items
        payroll_items = StaffPayroll.query.filter(
            StaffPayroll.period_year == approval.period_year,
            StaffPayroll.period_month == approval.period_month,
            StaffPayroll.approval_status == 'pending_admin'
        ).all()
        
        for item in payroll_items:
            item.approval_status = 'approved'
            item.approved_at = datetime.now()
            item.approved_by = session.get('username', 'Admin')
        
        db.session.commit()
        
        flash(f'Payroll for {approval.period_month}/{approval.period_year} approved successfully. '
              f'Finance team has been notified.', 'success')
        
        current_app.logger.info(f"Payroll approved: Period {approval.period_month}/{approval.period_year}, "
                               f"Approved by: {session.get('username', 'Admin')}")
        
    except Exception as e:
        current_app.logger.error(f"Error approving payroll: {str(e)}")
        flash('Error approving payroll', 'error')
        db.session.rollback()
    
    return redirect(url_for('admin.payroll_approvals'))

@admin_bp.route("/hr/reject-payroll/<int:approval_id>", methods=['POST'])
@role_required([Roles.SUPER_HQ])
def reject_payroll(approval_id):
    """Reject payroll submission and send back to HR"""
    try:
        from models import PayrollApproval, StaffPayroll
        
        # Get the approval record
        approval = PayrollApproval.query.get_or_404(approval_id)
        
        if approval.status != 'pending_admin':
            flash('This payroll has already been processed', 'warning')
            return redirect(url_for('admin.payroll_approvals'))
        
        # Get rejection reason
        rejection_reason = request.form.get('rejection_reason', '').strip()
        if not rejection_reason:
            flash('Please provide a reason for rejection', 'error')
            return redirect(url_for('admin.view_payroll_details', approval_id=approval_id))
        
        # Update approval status
        approval.status = 'rejected'
        approval.approved_by = session.get('username', 'Admin')
        approval.approved_at = datetime.now()
        approval.admin_comments = rejection_reason
        
        # Update all related payroll items back to draft
        payroll_items = StaffPayroll.query.filter(
            StaffPayroll.period_year == approval.period_year,
            StaffPayroll.period_month == approval.period_month,
            StaffPayroll.approval_status == 'pending_admin'
        ).all()
        
        for item in payroll_items:
            item.approval_status = 'draft'
            item.approved_at = None
            item.approved_by = None
        
        db.session.commit()
        
        flash(f'Payroll for {approval.period_month}/{approval.period_year} rejected. '
              f'HR team has been notified to make corrections.', 'success')
        
        current_app.logger.info(f"Payroll rejected: Period {approval.period_month}/{approval.period_year}, "
                               f"Rejected by: {session.get('username', 'Admin')}, Reason: {rejection_reason}")
        
    except Exception as e:
        current_app.logger.error(f"Error rejecting payroll: {str(e)}")
        flash('Error rejecting payroll', 'error')
        db.session.rollback()
    
    return redirect(url_for('admin.payroll_approvals'))

@admin_bp.route("/hr/employees")
@role_required([Roles.SUPER_HQ])
def view_employees():
    """View all employees (admin access to HR data)"""
    try:
        from models import Employee
        
        # Get search and filter parameters
        search = request.args.get('search', '').strip()
        status_filter = request.args.get('status', '')
        department_filter = request.args.get('department', '')
        
        # Build query
        query = Employee.query
        
        if search:
            query = query.filter(
                Employee.name.ilike(f'%{search}%') | 
                Employee.email.ilike(f'%{search}%') |
                Employee.staff_code.ilike(f'%{search}%')
            )
        
        if status_filter:
            query = query.filter(Employee.status == status_filter)
            
        if department_filter:
            query = query.filter(Employee.department == department_filter)
        
        employees = query.order_by(Employee.date_of_employment.desc()).all()
        
        # Get unique departments for filter
        departments = db.session.query(Employee.department).filter(
            Employee.department.isnot(None)
        ).distinct().all()
        departments = [dept[0] for dept in departments if dept[0]]
        
        return render_template('admin/hr/employees.html', 
                             employees=employees,
                             departments=departments,
                             current_search=search,
                             current_status=status_filter,
                             current_department=department_filter)
        
    except Exception as e:
        current_app.logger.error(f"Error loading employees: {str(e)}")
        flash('Error loading employees', 'error')
        return redirect(url_for('admin.hr_dashboard'))

@admin_bp.route('/user-management')
@login_required
@role_required(['super_hq', 'hq_hr'])
def user_management():
    """Comprehensive user management view - shows all users, employees, and their roles"""
    try:
        # Get all users with role information
        users = db.session.query(User).order_by(User.created_at.desc()).all()
        
        # Get all employees with their information
        employees = db.session.query(Employee).order_by(Employee.date_of_employment.desc()).all()
        
        # Get all projects for assignment
        projects = db.session.query(Project).filter(Project.status.in_(['active', 'planning'])).all()
        
        # Get staff assignments for project mapping
        staff_assignments = db.session.query(StaffAssignment).all()
        
        # Create a mapping of employee to assigned projects
        employee_projects = {}
        for assignment in staff_assignments:
            if assignment.employee_id not in employee_projects:
                employee_projects[assignment.employee_id] = []
            employee_projects[assignment.employee_id].append(assignment.project)
        
        # Available roles for assignment
        available_roles = [
            {'value': 'super_hq', 'name': 'Super HQ Admin'},
            {'value': 'hq_finance', 'name': 'HQ Finance Manager'},
            {'value': 'hr', 'name': 'HQ Manager'},
            {'value': 'hq_hr', 'name': 'HQ HR Manager'},
            {'value': 'hq_procurement', 'name': 'HQ Procurement Manager'},
            {'value': 'hq_quarry', 'name': 'Quarry Manager'},
            {'value': 'hq_project', 'name': 'Project Manager'},
            {'value': 'hq_cost_control', 'name': 'HQ Cost Control Manager'},
            {'value': 'finance_staff', 'name': 'Finance Staff'},
            {'value': 'hr_staff', 'name': 'HR Staff'},
            {'value': 'procurement_staff', 'name': 'Procurement Staff'},
            {'value': 'procurement_officer', 'name': 'Procurement Officer'},
            {'value': 'quarry_staff', 'name': 'Quarry Staff'},
            {'value': 'project_staff', 'name': 'Project Staff'},
        ]
        
        # Statistics
        stats = {
            'total_users': len(users),
            'total_employees': len(employees),
            'active_employees': len([e for e in employees if e.status == 'Active']),
            'total_projects': len(projects),
            'users_with_roles': len([u for u in users if u.role]),
            'employees_assigned': len(set([a.employee_id for a in staff_assignments]))
        }
        
        return render_template('admin/user_management.html',
                             users=users,
                             employees=employees,
                             projects=projects,
                             employee_projects=employee_projects,
                             available_roles=available_roles,
                             stats=stats)
                             
    except Exception as e:
        current_app.logger.error(f"Error in user management: {str(e)}")
        flash('Error loading user management data', 'error')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/assign-user-role', methods=['POST'])
@login_required
@role_required(['super_hq', 'hq_hr'])
def assign_user_role():
    """Assign or update user role"""
    try:
        user_id = request.form.get('user_id')
        new_role = request.form.get('role')
        
        if not user_id or not new_role:
            flash('User ID and role are required', 'error')
            return redirect(url_for('admin.user_management'))
        
        user = User.query.get_or_404(user_id)
        old_role = user.role
        user.role = new_role
        
        db.session.commit()
        
        current_app.logger.info(f"User {user.name} (ID: {user.id}) role updated from '{old_role}' to '{new_role}' by {current_user.name}")
        flash(f'Successfully updated {user.name}\'s role to {new_role}', 'success')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error assigning user role: {str(e)}")
        flash('Error updating user role', 'error')
    
    return redirect(url_for('admin.user_management'))

@admin_bp.route('/assign-employee-project', methods=['POST'])
@login_required
@role_required(['super_hq', 'hq_hr', 'hq_project'])
def assign_employee_project():
    """Assign employee to project"""
    try:
        employee_id = request.form.get('employee_id')
        project_id = request.form.get('project_id')
        role = request.form.get('assignment_role', 'Team Member')
        
        if not employee_id or not project_id:
            flash('Employee and project are required', 'error')
            return redirect(url_for('admin.user_management'))
        
        # Check if assignment already exists
        existing = StaffAssignment.query.filter_by(
            employee_id=employee_id,
            project_id=project_id
        ).first()
        
        if existing:
            flash('Employee is already assigned to this project', 'warning')
            return redirect(url_for('admin.user_management'))
        
        # Create new assignment
        assignment = StaffAssignment(
            employee_id=employee_id,
            project_id=project_id,
            role=role,
            assigned_at=datetime.utcnow(),
            assigned_by=current_user.id
        )
        
        db.session.add(assignment)
        db.session.commit()
        
        employee = Employee.query.get(employee_id)
        project = Project.query.get(project_id)
        
        current_app.logger.info(f"Employee {employee.name} assigned to project {project.name} by {current_user.name}")
        flash(f'Successfully assigned {employee.name} to {project.name}', 'success')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error assigning employee to project: {str(e)}")
        flash('Error assigning employee to project', 'error')
    
    return redirect(url_for('admin.user_management'))

@admin_bp.route('/remove-employee-assignment/<int:assignment_id>', methods=['POST'])
@login_required
@role_required(['super_hq', 'hq_hr', 'hq_project'])
def remove_employee_assignment(assignment_id):
    """Remove employee from project assignment"""
    try:
        assignment = StaffAssignment.query.get_or_404(assignment_id)
        employee_name = assignment.employee.name
        project_name = assignment.project.name
        
        db.session.delete(assignment)
        db.session.commit()
        
        current_app.logger.info(f"Employee {employee_name} removed from project {project_name} by {current_user.name}")
        flash(f'Successfully removed {employee_name} from {project_name}', 'success')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error removing employee assignment: {str(e)}")
        flash('Error removing employee assignment', 'error')
    
    return redirect(url_for('admin.user_management'))

@admin_bp.route('/comprehensive-user-management')
@login_required
@role_required(['super_hq', 'hq_hr', 'hq_project'])
def comprehensive_user_management():
    """Comprehensive user management page - display all users and employees"""
    try:
        # Get all users from User table (staff)
        users = User.query.all()
        
        # Get all employees from Employee table
        employees = Employee.query.all()
        
        # Get all projects for assignment options
        projects = Project.query.filter_by(status='Active').all()
        
        # Get available roles
        available_roles = ['admin', 'manager', 'supervisor', 'staff', 'viewer', 'project_manager', 
                          'site_engineer', 'foreman', 'safety_officer', 'quality_control']
        
        # Get staff assignments with project details
        staff_assignments = db.session.query(StaffAssignment, Project.name.label('project_name')).join(Project).all()
        
        # Create assignment lookup for easy access
        user_assignments = {}
        for assignment, project_name in staff_assignments:
            if assignment.staff_id not in user_assignments:
                user_assignments[assignment.staff_id] = []
            user_assignments[assignment.staff_id].append({
                'project_id': assignment.project_id,
                'project_name': project_name,
                'role': assignment.role,
                'assigned_at': assignment.assigned_at
            })
        
        # Statistics
        total_users = len(users)
        total_employees = len(employees)
        active_users = len([u for u in users if u.role != 'inactive'])
        users_with_projects = len(user_assignments)
        
        current_app.logger.info(f"Comprehensive user management accessed by {current_user.name}")
        
        return render_template('admin/comprehensive_user_management.html',
                             users=users,
                             employees=employees,
                             projects=projects,
                             available_roles=available_roles,
                             user_assignments=user_assignments,
                             total_users=total_users,
                             total_employees=total_employees,
                             active_users=active_users,
                             users_with_projects=users_with_projects)
                             
    except Exception as e:
        current_app.logger.error(f"Error loading comprehensive user management: {str(e)}")
        flash('Error loading user management page', 'error')
        return redirect(url_for('admin.index'))

@admin_bp.route('/assign-user-role-new', methods=['POST'])
@login_required
@role_required(['super_hq', 'hq_hr'])
def assign_user_role_new():
    """Assign or update user role"""
    try:
        user_id = request.form.get('user_id')
        new_role = request.form.get('role')
        
        if not user_id or not new_role:
            flash('User and role are required', 'error')
            return redirect(url_for('admin.comprehensive_user_management'))
        
        user = User.query.get_or_404(user_id)
        old_role = user.role
        user.role = new_role
        user.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        current_app.logger.info(f"User {user.name} role changed from {old_role} to {new_role} by {current_user.name}")
        flash(f'Successfully updated {user.name}\'s role from {old_role} to {new_role}', 'success')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating user role: {str(e)}")
        flash('Error updating user role', 'error')
    
    return redirect(url_for('admin.comprehensive_user_management'))

@admin_bp.route('/assign-user-project-new', methods=['POST'])
@login_required
@role_required(['super_hq', 'hq_project'])
def assign_user_project_new():
    """Assign user to project"""
    try:
        user_id = request.form.get('user_id')
        project_id = request.form.get('project_id')
        role = request.form.get('project_role', 'Staff')
        
        if not user_id or not project_id:
            flash('User and project are required', 'error')
            return redirect(url_for('admin.comprehensive_user_management'))
        
        # Check if assignment already exists
        existing = StaffAssignment.query.filter_by(staff_id=user_id, project_id=project_id).first()
        if existing:
            flash('User is already assigned to this project', 'warning')
            return redirect(url_for('admin.comprehensive_user_management'))
        
        assignment = StaffAssignment(
            staff_id=user_id,
            project_id=project_id,
            role=role,
            assigned_at=datetime.utcnow()
        )
        
        db.session.add(assignment)
        db.session.commit()
        
        user = User.query.get(user_id)
        project = Project.query.get(project_id)
        
        current_app.logger.info(f"User {user.name} assigned to project {project.name} as {role} by {current_user.name}")
        flash(f'Successfully assigned {user.name} to {project.name} as {role}', 'success')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error assigning user to project: {str(e)}")
        flash('Error assigning user to project', 'error')
    
    return redirect(url_for('admin.comprehensive_user_management'))

@admin_bp.route('/remove-user-project/<int:user_id>/<int:project_id>', methods=['POST'])
@login_required
@role_required(['super_hq', 'hq_project'])
def remove_user_project(user_id, project_id):
    """Remove user from project"""
    try:
        assignment = StaffAssignment.query.filter_by(staff_id=user_id, project_id=project_id).first()
        if not assignment:
            flash('Assignment not found', 'error')
            return redirect(url_for('admin.comprehensive_user_management'))
        
        user = User.query.get(user_id)
        project = Project.query.get(project_id)
        
        db.session.delete(assignment)
        db.session.commit()
        
        current_app.logger.info(f"User {user.name} removed from project {project.name} by {current_user.name}")
        flash(f'Successfully removed {user.name} from {project.name}', 'success')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error removing user from project: {str(e)}")
        flash('Error removing user from project', 'error')
    
    return redirect(url_for('admin.comprehensive_user_management'))
