from datetime import datetime
from flask import Blueprint, render_template, current_app, flash, request, jsonify, url_for, redirect, session, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from extensions import db
from models import Project, StaffAssignment, Task, Equipment, Material, Report, Document, User, Milestone
from utils.decorators import role_required
from utils.constants import Roles
from sqlalchemy import func
import os

project_bp = Blueprint('project', __name__, url_prefix='/projects')

# Dashboard
@project_bp.route('/')
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def project_home():
    try:
        projects = Project.query.order_by(Project.created_at.desc()).all()
        return render_template('projects/index.html', projects=projects)
    except Exception as e:
        current_app.logger.error(f"Project dashboard error: {str(e)}")
        flash("Error loading project dashboard", "error")
        return render_template('error.html'), 500


# Create Project
@project_bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def create_project():
    try:
        if request.method == 'POST':
            name = request.form.get('name')
            manager_id = current_user.id
            status = request.form.get('status')
            description = request.form.get('description', '')
            if not all([name, manager_id, status]):
                flash("Please fill in all required fields", "error")
                return render_template('projects/create.html'), 400
            project = Project(name=name, manager_id=manager_id, status=status, description=description, created_at=datetime.now())
            db.session.add(project)
            db.session.commit()
            flash("Project created successfully!", "success")
            return redirect(url_for('project.project_home'))
        return render_template('projects/create.html')
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("Project creation error")
        flash("Failed to create project", "error")
        return render_template('error.html'), 500


# Assign Staff to Project
@project_bp.route('/<int:project_id>/assign-staff', methods=['POST'])
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def assign_staff(project_id):
    try:
        staff_role = request.form.get('role')
        staff_id = request.form.get('staff_id')
        assignment = StaffAssignment(project_id=project_id, staff_id=staff_id, role=staff_role)
        db.session.add(assignment)
        db.session.commit()
        return jsonify({'status': 'success', 'message': f"{staff_role} assigned to project {project_id}"})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)})


# View Project Details
@project_bp.route('/<int:project_id>')
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def project_details(project_id):
    try:
        project = Project.query.get_or_404(project_id)
        staff_assignments = StaffAssignment.query.filter_by(project_id=project_id).all()
        return render_template('projects/details.html', project=project, staff_assignments=staff_assignments)
    except Exception as e:
        current_app.logger.error(f"Project details error: {str(e)}")
        flash("Error loading project details", "error")
        return render_template('error.html'), 500


# API: List Projects (for AJAX)
@project_bp.route('/api/list')
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def list_projects():
    try:
        projects = Project.query.order_by(Project.created_at.desc()).all()
        return jsonify([{'id': p.id, 'name': p.name, 'status': p.status} for p in projects])
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})
    
# Update Project
@project_bp.route('/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def edit_project(project_id):
    try:
        project = Project.query.get_or_404(project_id)
        if request.method == 'POST':
            project.name = request.form.get('name', project.name)
            project.status = request.form.get('status', project.status)
            project.description = request.form.get('description', project.description)
            db.session.commit()
            flash(f"Project {project_id} updated successfully!", "success")
            return redirect(url_for('project.project_details', project_id=project_id))
        return render_template('projects/edit.html', project=project)
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Project edit error: {str(e)}")
        flash("Error updating project", "error")
        return render_template('error.html'), 500


# Delete Project
@project_bp.route('/<int:project_id>/delete', methods=['POST'])
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def delete_project(project_id):
    try:
        project = Project.query.get_or_404(project_id)
        db.session.delete(project)
        db.session.commit()
        flash(f"Project {project_id} deleted successfully!", "success")
        return redirect(url_for('project.project_home'))
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)})


# Project Reports
@project_bp.route('/reports')
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def reports():
    try:
        recent_reports = Report.query.order_by(Report.date.desc()).limit(10).all()
        report_types = db.session.query(Report.type).distinct().all()
        return render_template('projects/reports.html', data={
            'recent_reports': recent_reports,
            'report_types': [rt[0] for rt in report_types]
        })
    except Exception as e:
        current_app.logger.error(f"Reports page error: {str(e)}")
        return render_template('error.html', error="Failed to load reports"), 500


# Project Timeline / Milestones
@project_bp.route('/<int:project_id>/timeline', methods=['GET', 'POST'])
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def project_timeline(project_id):
    try:
        if request.method == 'POST':
            title = request.form.get('title')
            due_date = request.form.get('due_date')
            status = request.form.get('status', 'Pending')
            milestone = Milestone(project_id=project_id, title=title, due_date=due_date, status=status)
            db.session.add(milestone)
            db.session.commit()
            flash("Milestone added successfully!", "success")
        milestones = Milestone.query.filter_by(project_id=project_id).order_by(Milestone.due_date).all()
        return render_template('projects/timeline.html', milestones=milestones, project_id=project_id)
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Timeline error: {str(e)}")
        flash("Error loading timeline", "error")
        return render_template('error.html'), 500


# Project API: Staff Assignments
@project_bp.route('/<int:project_id>/api/staff')
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def project_staff_api(project_id):
    try:
        staff = StaffAssignment.query.filter_by(project_id=project_id).all()
        staff_data = {s.role: s.staff.name for s in staff}
        return jsonify({'project_id': project_id, 'staff': staff_data})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


# Tasks Page
@project_bp.route('/tasks')
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def tasks():
    try:
        pending = Task.query.filter_by(status='pending').order_by(Task.due_date).all()
        in_progress = Task.query.filter_by(status='in_progress').order_by(Task.due_date).all()
        completed = Task.query.filter_by(status='completed').order_by(Task.due_date.desc()).all()
        tasks_data = {
            'pending': pending,
            'in_progress': in_progress,
            'completed': completed
        }
        return render_template('projects/tasks.html', tasks=tasks_data)
    except Exception as e:
        current_app.logger.error(f"Tasks page error: {str(e)}")
        return render_template('error.html', error="Failed to load tasks"), 500


# Equipment Page
@project_bp.route('/equipment')
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def equipment():
    try:
        equipment_data = Equipment.query.order_by(Equipment.maintenance_due).all()
        return render_template('projects/equipment.html', equipment=equipment_data)
    except Exception as e:
        current_app.logger.error(f"Equipment page error: {str(e)}")
        return render_template('error.html', error="Failed to load equipment"), 500


# Materials Page
@project_bp.route('/materials')
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def materials():
    try:
        materials_data = Material.query.order_by(Material.name).all()
        return render_template('projects/materials.html', materials=materials_data)
    except Exception as e:
        current_app.logger.error(f"Materials page error: {str(e)}")
        return render_template('error.html', error="Failed to load materials"), 500


# Analytics Page
@project_bp.route('/analytics')
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def analytics():
    try:
        status_counts = db.session.query(Project.status, func.count(Project.id)).group_by(Project.status).all()
        project_status = {status: count for status, count in status_counts}
        resource_utilization = db.session.query(func.avg(Project.resource_utilization)).scalar() or 0
        budget_overview = {
            'allocated': db.session.query(func.sum(Project.budget_allocated)).scalar() or 0,
            'spent': db.session.query(func.sum(Project.budget_spent)).scalar() or 0,
            'remaining': (db.session.query(func.sum(Project.budget_allocated)).scalar() or 0) - (db.session.query(func.sum(Project.budget_spent)).scalar() or 0)
        }
        total_projects = sum(project_status.values())
        chart_data = {
            'status_labels': list(project_status.keys()),
            'status_data': list(project_status.values()),
            'resource_utilization': resource_utilization,
            'budget': budget_overview
        }
        return render_template('projects/analytics.html', data=chart_data, total_projects=total_projects)
    except Exception as e:
        current_app.logger.error(f"Analytics page error: {str(e)}")
        return render_template('error.html', error="Failed to load analytics"), 500


# Calendar Page
@project_bp.route('/calendar')
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def calendar():
    try:
        # Example: events from milestones and tasks
        milestones = Milestone.query.order_by(Milestone.due_date).all()
        tasks = Task.query.order_by(Task.due_date).all()
        events = []
        for m in milestones:
            events.append({
                'id': f"milestone-{m.id}",
                'title': m.title,
                'start': m.due_date.strftime('%Y-%m-%d'),
                'end': m.due_date.strftime('%Y-%m-%d'),
                'type': 'milestone'
            })
        for t in tasks:
            events.append({
                'id': f"task-{t.id}",
                'title': t.title,
                'start': t.due_date.strftime('%Y-%m-%d'),
                'end': t.due_date.strftime('%Y-%m-%d'),
                'type': 'task'
            })
        return render_template('projects/calendar.html', calendar={'events': events})
    except Exception as e:
        current_app.logger.error(f"Calendar page error: {str(e)}")
        return render_template('error.html', error="Failed to load calendar"), 500


# Staff Management
@project_bp.route('/staff')
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def staff():
    try:
        # Query project managers
        project_managers = User.query.filter_by(role='Project Manager').all()
        managers_data = []
        for manager in project_managers:
            projects = Project.query.filter_by(manager_id=manager.id).all()
            managers_data.append({
                'id': manager.id,
                'name': manager.name,
                'role': manager.role,
                'projects': [p.name for p in projects]
            })
        # Query team members (not project managers)
        team_members = User.query.filter(User.role != 'Project Manager').all()
        members_data = []
        for member in team_members:
            assignments = StaffAssignment.query.filter_by(staff_id=member.id).all()
            projects = [Project.query.get(a.project_id).name for a in assignments if Project.query.get(a.project_id)]
            members_data.append({
                'id': member.id,
                'name': member.name,
                'role': member.role,
                'projects': projects
            })
        staff_data = {
            'project_managers': managers_data,
            'team_members': members_data
        }
        return render_template('projects/staff.html', staff=staff_data)
    except Exception as e:
        current_app.logger.error(f"Staff page error: {str(e)}")
        return render_template('error.html', error="Failed to load staff page"), 500


# Documents Page (File upload/download)
@project_bp.route('/documents', methods=['GET', 'POST'])
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def documents():
    try:
        if request.method == 'POST':
            file = request.files.get('file')
            category = request.form.get('category')
            if not file or not category:
                flash("File and category required", "error")
                return redirect(url_for('project.documents'))
            filename = secure_filename(file.filename)
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            document = Document(filename=filename, category=category, uploaded_at=datetime.now(), uploader_id=current_user.id)
            db.session.add(document)
            db.session.commit()
            flash("File uploaded successfully", "success")
            return redirect(url_for('project.documents'))
        categories = db.session.query(Document.category).distinct().all()
        recent_documents = Document.query.order_by(Document.uploaded_at.desc()).limit(10).all()
        return render_template('projects/documents.html', categories=[c[0] for c in categories], recent_documents=recent_documents)
    except Exception as e:
        current_app.logger.error(f"Documents page error: {str(e)}")
        return render_template('error.html', error="Failed to load documents"), 500


@project_bp.route('/documents/download/<int:doc_id>')
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def download_document(doc_id):
    try:
        document = Document.query.get_or_404(doc_id)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], document.filename)
        return send_file(filepath, as_attachment=True)
    except Exception as e:
        current_app.logger.error(f"Download error: {str(e)}")
        flash("Failed to download file", "error")
        return redirect(url_for('project.documents'))


# Document Approval/Rejection
@project_bp.route('/documents/<int:doc_id>/approve', methods=['POST'])
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def approve_document(doc_id):
    try:
        document = Document.query.get_or_404(doc_id)
        document.status = 'approved'
        db.session.commit()
        flash('Document approved!', 'success')
        return redirect(url_for('project.documents'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error approving document: {str(e)}', 'error')
        return redirect(url_for('project.documents'))

@project_bp.route('/documents/<int:doc_id>/reject', methods=['POST'])
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def reject_document(doc_id):
    try:
        document = Document.query.get_or_404(doc_id)
        document.status = 'rejected'
        db.session.commit()
        flash('Document rejected!', 'success')
        return redirect(url_for('project.documents'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error rejecting document: {str(e)}', 'error')
        return redirect(url_for('project.documents'))

# Document Search
@project_bp.route('/documents/search')
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def search_documents():
    try:
        query = request.args.get('q', '').strip()
        category = request.args.get('category', '').strip()
        status = request.args.get('status', '').strip()
        documents_query = Document.query
        if query:
            documents_query = documents_query.filter(Document.filename.ilike(f'%{query}%'))
        if category:
            documents_query = documents_query.filter_by(category=category)
        if status:
            documents_query = documents_query.filter_by(status=status)
        results = documents_query.order_by(Document.uploaded_at.desc()).all()
        return render_template('projects/documents_search.html', results=results, query=query, category=category, status=status)
    except Exception as e:
        current_app.logger.error(f"Document search error: {str(e)}")
        return render_template('error.html', error="Failed to search documents"), 500

# Upload/View/Download Reports as PDF/Excel
@project_bp.route('/reports/upload', methods=['GET', 'POST'])
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def upload_report():
    try:
        if request.method == 'POST':
            file = request.files.get('report_file')
            report_type = request.form.get('type')
            if not file or not report_type:
                flash('File and report type required', 'error')
                return redirect(url_for('project.upload_report'))
            filename = secure_filename(file.filename)
            filepath = os.path.join(current_app.config['REPORTS_UPLOAD_FOLDER'], filename)
            file.save(filepath)
            report = Report(filename=filename, type=report_type, uploaded_at=datetime.now(), uploader_id=current_user.id)
            db.session.add(report)
            db.session.commit()
            flash('Report uploaded successfully!', 'success')
            return redirect(url_for('project.reports'))
        return render_template('projects/upload_report.html')
    except Exception as e:
        current_app.logger.error(f"Report upload error: {str(e)}")
        flash('Failed to upload report', 'error')
        return redirect(url_for('project.reports'))

@project_bp.route('/reports/download/<int:report_id>')
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def download_report(report_id):
    try:
        report = Report.query.get_or_404(report_id)
        filepath = os.path.join(current_app.config['REPORTS_UPLOAD_FOLDER'], report.filename)
        return send_file(filepath, as_attachment=True)
    except Exception as e:
        current_app.logger.error(f"Report download error: {str(e)}")
        flash('Failed to download report', 'error')
        return redirect(url_for('project.reports'))


# Logout
@project_bp.route('/logout')
def logout():
    try:
        # Clear the session
        session.clear()
        flash("You have been successfully logged out", "success")
        return redirect(url_for('auth.login'))
    except Exception as e:
        current_app.logger.error(f"Logout error: {str(e)}")
        flash("Error during logout", "error")
        return redirect(url_for('project.project_home'))

# Settings
@project_bp.route('/settings', methods=['GET', 'POST'])
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def settings():
    try:
        if request.method == 'POST':
            form_type = request.args.get('form')
            if form_type == 'profile':
                name = request.form.get('name')
                email = request.form.get('email')
                department = request.form.get('department')
                user = User.query.get(current_user.id)
                user.name = name
                user.email = email
                user.department = department
                db.session.commit()
                flash("Profile updated successfully", "success")
            elif form_type == 'security':
                current_password = request.form.get('current_password')
                new_password = request.form.get('new_password')
                confirm_password = request.form.get('confirm_password')
                user = User.query.get(current_user.id)
                if not user.check_password(current_password):
                    flash("Current password incorrect", "error")
                    return redirect(url_for('project.settings'))
                if new_password != confirm_password:
                    flash("New passwords do not match", "error")
                    return redirect(url_for('project.settings'))
                user.set_password(new_password)
                db.session.commit()
                flash("Password updated successfully", "success")
            elif form_type == 'notifications':
                email_notifications = request.form.get('email_notifications') == 'on'
                task_reminders = request.form.get('task_reminders') == 'on'
                user = User.query.get(current_user.id)
                user.email_notifications = email_notifications
                user.task_reminders = task_reminders
                db.session.commit()
                flash("Notification preferences updated", "success")
            return redirect(url_for('project.settings'))
        user = User.query.get(current_user.id)
        user_data = {
            'name': user.name,
            'email': user.email,
            'role': user.role,
            'department': getattr(user, 'department', ''),
            'notification_preferences': {
                'email_notifications': getattr(user, 'email_notifications', True),
                'task_reminders': getattr(user, 'task_reminders', True)
            }
        }
        return render_template('projects/settings.html', user=user_data)
    except Exception as e:
        current_app.logger.error(f"Settings page error: {str(e)}")
        flash("Error updating settings", "error")
        return render_template('error.html'), 500


# Weekly Site Report Endpoint
@project_bp.route('/weekly-site-report', methods=['GET', 'POST'])
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def weekly_site_report():
    try:
        if request.method == 'POST':
            # Handle report upload (PDF/Excel)
            file = request.files.get('report_file')
            if file:
                filename = secure_filename(file.filename)
                filepath = os.path.join(current_app.config['REPORTS_UPLOAD_FOLDER'], filename)
                file.save(filepath)
                # Save report record
                report = Report(filename=filename, type='Weekly Site', uploaded_at=datetime.now(), uploader_id=current_user.id)
                db.session.add(report)
                db.session.commit()
                flash('Weekly site report uploaded!', 'success')
                return redirect(url_for('project.weekly_site_report'))
        # Labour Check
        staff_assignments = StaffAssignment.query.all()
        staff_categories = {}
        for s in staff_assignments:
            category = s.staff.role
            staff_categories.setdefault(category, []).append(s.staff)
        # Plant Check
        plant_data = Equipment.query.with_entities(Equipment.name, Equipment.machine_hours, Equipment.diesel_consumption).all()
        # Materials Check
        materials = Material.query.with_entities(Material.name, Material.delivered, Material.used, Material.balance).all()
        # Progress Check
        progress_items = Task.query.with_entities(Task.title, Task.from_item, Task.to_item, Task.quantity, Task.percent_complete).all()
        # Remarks
        equipment_remarks = Equipment.query.with_entities(Equipment.name, Equipment.remarks).all()
        manager_comment = ''  # Could be fetched from a model or form
        # Visitors
        visitors = Report.query.filter_by(type='Visitor').order_by(Report.date.desc()).limit(10).all()
        # Sign-off
        sign_off = {
            'project_manager': current_user.name,
            'md_ceo': '',  # Could be fetched from User model
            'site_file': ''  # Could be a file or record
        }
        return render_template('projects/weekly_site_report.html',
            staff_categories=staff_categories,
            plant_data=plant_data,
            materials=materials,
            progress_items=progress_items,
            equipment_remarks=equipment_remarks,
            manager_comment=manager_comment,
            visitors=visitors,
            sign_off=sign_off
        )
    except Exception as e:
        current_app.logger.error(f"Weekly Site Report error: {str(e)}")
        return render_template('error.html', error="Failed to load weekly site report"), 500


# Staff Removal from Project
@project_bp.route('/<int:project_id>/remove-staff', methods=['POST'])
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def remove_staff(project_id):
    try:
        staff_id = request.form.get('staff_id')
        assignment = StaffAssignment.query.filter_by(project_id=project_id, staff_id=staff_id).first()
        if assignment:
            db.session.delete(assignment)
            db.session.commit()
            return jsonify({'status': 'success', 'message': f'Staff {staff_id} removed from project {project_id}'})
        else:
            return jsonify({'status': 'error', 'message': 'Staff assignment not found'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)})
