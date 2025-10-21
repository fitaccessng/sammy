from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for
from datetime import datetime
from extensions import db
from models import Role, ReportingLine, ApprovalHierarchy, Permission, Payroll
from utils.decorators import role_required
from utils.constants import Roles

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# POST/GET /admin/roles
@admin_bp.route('/roles', methods=['POST', 'GET'])
def manage_roles():
    if request.method == 'POST':
        data = request.get_json()
        role = Role(name=data.get('name'))
        db.session.add(role)
        db.session.commit()
        return jsonify({'status': 'success', 'id': role.id})
    roles = Role.query.all()
    return jsonify([{'id': r.id, 'name': r.name} for r in roles])

# POST/GET /admin/reporting-lines
@admin_bp.route('/reporting-lines', methods=['POST', 'GET'])
def manage_reporting_lines():
    if request.method == 'POST':
        data = request.get_json()
        rl = ReportingLine(manager_id=data.get('manager_id'), staff_id=data.get('staff_id'))
        db.session.add(rl)
        db.session.commit()
        # Notify manager and staff
        from models import Employee
        from utils.email import send_email
        manager = Employee.query.get(data.get('manager_id'))
        staff = Employee.query.get(data.get('staff_id'))
        if manager and hasattr(manager, 'email') and manager.email:
            subject = "Reporting Line Assigned"
            body = f"Dear {manager.name},\nYou are now the manager for {staff.name if staff else 'staff member'}."
            send_email(manager.email, subject, body)
        if staff and hasattr(staff, 'email') and staff.email:
            subject = "Reporting Line Assigned"
            body = f"Dear {staff.name},\nYou now report to {manager.name if manager else 'your manager'}."
            send_email(staff.email, subject, body)
        return jsonify({'status': 'success', 'id': rl.id})
    lines = ReportingLine.query.all()
    return jsonify([{'id': l.id, 'manager_id': l.manager_id, 'staff_id': l.staff_id} for l in lines])

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