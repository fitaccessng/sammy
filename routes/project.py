from datetime import datetime
from flask import Blueprint, render_template, current_app, flash, request, jsonify, url_for, redirect, session, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from extensions import db
from models import Project, StaffAssignment, Task, Equipment, Material, Report, Document, User, Milestone, Schedule, Expense
from utils.decorators import role_required
from utils.constants import Roles
from sqlalchemy import func
import os

project_bp = Blueprint('project', __name__, url_prefix='/projects')

# Dashboard
@project_bp.route('/')
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER,Roles.HQ_FINANCE, Roles.HQ_PROCUREMENT])
def project_home():
    try:
        # Get only projects assigned to the current user
        # Join StaffAssignment with Project to get projects where current user is assigned
        user_projects_query = db.session.query(Project).join(
            StaffAssignment, Project.id == StaffAssignment.project_id
        ).filter(StaffAssignment.staff_id == current_user.id)
        
        # For SUPER_HQ role, also include projects they manage
        if current_user.has_role(Roles.SUPER_HQ):
            # Get projects managed by the current user or assigned to them
            managed_projects_query = Project.query.filter(
                Project.project_manager == current_user.name
            )
            # Combine both queries
            projects = user_projects_query.union(managed_projects_query).order_by(Project.created_at.desc()).all()
        else:
            # For other roles, only show assigned projects
            projects = user_projects_query.order_by(Project.created_at.desc()).all()
        
        # Get project statistics for user's projects only
        total_projects = len(projects)
        active_projects = len([p for p in projects if p.status in ['Active', 'In Progress']])
        completed_projects = len([p for p in projects if p.status == 'Completed'])
        planning_projects = len([p for p in projects if p.status == 'Planning'])
        
        # Calculate total budget and spent amounts for user's projects
        total_budget = sum([p.budget or 0 for p in projects])
        total_spent = 0  # This would come from expenses table in real system
        
        # Get recent activities for user's projects only
        recent_activities = []
        for project in projects[:5]:  # Last 5 projects
            recent_activities.append({
                'project_name': project.name,
                'activity': 'Project created' if project.status == 'Planning' else f'Status updated to {project.status}',
                'timestamp': project.updated_at or project.created_at,
                'user': project.project_manager or 'System'
            })
        
        # Enhanced project data with staff assignments and progress for user's projects
        enhanced_projects = []
        for project in projects:
            try:
                # Get user's role in this project
                user_assignment = StaffAssignment.query.filter_by(
                    project_id=project.id, 
                    staff_id=current_user.id
                ).first()
                user_role_in_project = user_assignment.role if user_assignment else "Manager"
                
                # Get milestones for progress calculation
                milestones = project.milestones.all() if hasattr(project, 'milestones') else []
                completed_milestones = [m for m in milestones if hasattr(m, 'status') and m.status == 'Completed']
                progress = (len(completed_milestones) / len(milestones) * 100) if milestones else 0
                
                # Get all staff assignments for the project (for display)
                all_staff_assignments = StaffAssignment.query.filter_by(project_id=project.id).all()
                
                enhanced_project = {
                    'id': project.id,
                    'name': project.name,
                    'description': project.description or 'No description provided',
                    'status': project.status or 'Planning',
                    'progress': progress,
                    'manager': project.project_manager or 'Not assigned',
                    'created_at': project.created_at.strftime('%Y-%m-%d') if project.created_at else 'Unknown',
                    'start_date': project.start_date.strftime('%Y-%m-%d') if project.start_date else 'Not set',
                    'end_date': project.end_date.strftime('%Y-%m-%d') if project.end_date else 'Not set',
                    'budget': project.budget or 0,
                    'spent': project.budget * 0.6 if project.budget else 0,  # Simulated spent amount
                    'milestone_count': len(milestones),
                    'completed_milestones': len(completed_milestones),
                    'staff_count': len(all_staff_assignments),
                    'days_remaining': (project.end_date - datetime.now().date()).days if project.end_date else None,
                    'is_overdue': project.end_date and project.end_date < datetime.now().date() and project.status != 'Completed',
                    'priority': 'High' if project.budget and project.budget > 10000000 else 'Medium' if project.budget and project.budget > 5000000 else 'Normal',
                    'user_role': user_role_in_project,  # Current user's role in this project
                    'is_manager': project.project_manager == current_user.name,
                    'staff': {
                        'Project Manager': project.project_manager or 'Not assigned',
                        'Team Size': len(all_staff_assignments),
                        'User Role': user_role_in_project
                    }
                }
                enhanced_projects.append(enhanced_project)
                
            except Exception as e:
                current_app.logger.error(f"Error processing project {project.id}: {str(e)}")
                # Fallback basic project data
                enhanced_projects.append({
                    'id': project.id,
                    'name': project.name,
                    'description': project.description or 'No description provided',
                    'status': project.status or 'Planning',
                    'progress': project.progress or 0,
                    'manager': project.project_manager or 'Not assigned',
                    'created_at': project.created_at.strftime('%Y-%m-%d') if project.created_at else 'Unknown',
                    'start_date': project.start_date.strftime('%Y-%m-%d') if project.start_date else 'Not set',
                    'end_date': project.end_date.strftime('%Y-%m-%d') if project.end_date else 'Not set',
                    'budget': project.budget or 0,
                    'spent': 0,
                    'milestone_count': 0,
                    'completed_milestones': 0,
                    'staff_count': 0,
                    'days_remaining': None,
                    'is_overdue': False,
                    'priority': 'Normal',
                    'user_role': 'Member',
                    'is_manager': False,
                    'staff': {
                        'Project Manager': project.project_manager or 'Not assigned',
                        'Team Size': 0,
                        'User Role': 'Member'
                    }
                })
        
        project_stats = {
            'total_projects': total_projects,
            'active_projects': active_projects,
            'completed_projects': completed_projects,
            'planning_projects': planning_projects,
            'total_budget': total_budget,
            'total_spent': total_spent,
            'completion_rate': (completed_projects / total_projects * 100) if total_projects > 0 else 0,
            'user_name': current_user.name,
            'user_role': current_user.role
        }
        
        return render_template('projects/index.html', 
                             projects=enhanced_projects,
                             project_stats=project_stats,
                             recent_activities=recent_activities,
                             current_user=current_user)
                             
    except Exception as e:
        current_app.logger.error(f"Project dashboard error: {str(e)}", exc_info=True)
        # Fallback with empty data
        return render_template('projects/index.html', 
                             projects=[],
                             project_stats={
                                 'total_projects': 0,
                                 'active_projects': 0,
                                 'completed_projects': 0,
                                 'planning_projects': 0,
                                 'total_budget': 0,
                                 'total_spent': 0,
                                 'completion_rate': 0,
                                 'user_name': current_user.name if current_user.is_authenticated else 'Unknown',
                                 'user_role': current_user.role if current_user.is_authenticated else 'Unknown'
                             },
                             recent_activities=[],
                             current_user=current_user)


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
        
        # Check if user has access to this project
        user_assignment = StaffAssignment.query.filter_by(
            project_id=project_id, 
            staff_id=current_user.id
        ).first()
        
        is_manager = project.project_manager == current_user.name
        is_super_hq = current_user.has_role(Roles.SUPER_HQ)
        
        # Allow access if user is assigned, is the manager, or is SUPER_HQ
        if not (user_assignment or is_manager or is_super_hq):
            flash("You don't have access to this project.", "error")
            return redirect(url_for('project.project_home'))
        
        # Get staff assignments with user details
        staff_assignments = db.session.query(StaffAssignment, User.name).join(
            User, StaffAssignment.staff_id == User.id
        ).filter(StaffAssignment.project_id == project_id).all()
        
        # Get available staff for assignment (exclude already assigned staff)
        assigned_staff_ids = [assignment.staff_id for assignment, _ in staff_assignments]
        available_staff = User.query.filter(
            User.id.notin_(assigned_staff_ids) if assigned_staff_ids else True
        ).all()
        
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
        
        # Team statistics
        team_size = len(staff_assignments)
        team_roles = {}
        for assignment, staff_name in staff_assignments:
            role = assignment.role if hasattr(assignment, 'role') else 'Unknown'
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
        
        # Import the new models
        from models import BOQItem, ProjectActivity, ProjectDocument
        
        return render_template('admin/view_project.html',
                             project=project,
                             staff_assignments=[{'assignment': assignment, 'staff_name': staff_name}
                                              for assignment, staff_name in staff_assignments],
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
                             boq_items=BOQItem.query.filter_by(project_id=project_id).all(),
                             project_documents=ProjectDocument.query.filter_by(project_id=project_id).all(),
                             activity_log=ProjectActivity.query.filter_by(project_id=project_id).order_by(ProjectActivity.created_at.desc()).limit(10).all())
    except Exception as e:
        current_app.logger.error(f"Project details error: {str(e)}", exc_info=True)
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


# ==================== API ENDPOINTS FOR PROJECT MANAGEMENT ====================

@project_bp.route('/api/projects/<int:project_id>/status', methods=['POST'])
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def update_project_status(project_id):
    """Update project status"""
    try:
        data = request.get_json() if request.is_json else request.form
        new_status = data.get('status')
        
        if not new_status:
            return jsonify({'error': 'Status is required'}), 400
            
        project = Project.query.get_or_404(project_id)
        old_status = project.status
        project.status = new_status
        project.updated_at = datetime.utcnow()
        
        # Auto-update progress based on status
        if new_status == 'Completed':
            project.progress = 100.0
        elif new_status == 'Active':
            if not project.progress:
                project.progress = 10.0  # Start with 10% if active
        
        db.session.commit()
        
        current_app.logger.info(f"Project {project_id} status updated from {old_status} to {new_status}")
        
        return jsonify({
            'status': 'success',
            'message': f'Project status updated to {new_status}',
            'project': {
                'id': project.id,
                'name': project.name,
                'status': project.status,
                'progress': project.progress
            }
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update project status error: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error updating project status'}), 500

@project_bp.route('/api/projects/<int:project_id>/progress', methods=['POST'])
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def update_project_progress(project_id):
    """Update project progress"""
    try:
        data = request.get_json() if request.is_json else request.form
        progress = float(data.get('progress', 0))
        
        if progress < 0 or progress > 100:
            return jsonify({'error': 'Progress must be between 0 and 100'}), 400
            
        project = Project.query.get_or_404(project_id)
        old_progress = project.progress
        project.progress = progress
        project.updated_at = datetime.utcnow()
        
        # Auto-update status based on progress
        if progress == 100:
            project.status = 'Completed'
        elif progress > 0 and project.status == 'Planning':
            project.status = 'Active'
        
        db.session.commit()
        
        current_app.logger.info(f"Project {project_id} progress updated from {old_progress}% to {progress}%")
        
        return jsonify({
            'status': 'success',
            'message': f'Project progress updated to {progress}%',
            'project': {
                'id': project.id,
                'name': project.name,
                'status': project.status,
                'progress': project.progress
            }
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update project progress error: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error updating project progress'}), 500

@project_bp.route('/api/projects/<int:project_id>/progress', methods=['GET'])
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def get_project_progress(project_id):
    """Get current project progress and metrics"""
    try:
        project = Project.query.get_or_404(project_id)
        
        # Get updated milestone counts
        milestones = Milestone.query.filter_by(project_id=project_id).all()
        completed_milestones = [m for m in milestones if m.status == 'Completed']
        
        # Get updated task counts
        tasks = Task.query.filter_by(project_id=project_id).all()
        completed_tasks = [t for t in tasks if t.status == 'completed']
        
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
        current_app.logger.error(f"Get project progress error: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error fetching project progress'}), 500

@project_bp.route('/api/projects/filter')
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def filter_projects():
    """Filter projects by various criteria"""
    try:
        status = request.args.get('status')
        search = request.args.get('search', '')
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        query = Project.query
        
        # Apply status filter
        if status and status != 'all':
            query = query.filter(Project.status == status)
        
        # Apply search filter
        if search:
            query = query.filter(
                db.or_(
                    Project.name.ilike(f'%{search}%'),
                    Project.description.ilike(f'%{search}%'),
                    Project.project_manager.ilike(f'%{search}%')
                )
            )
        
        # Apply sorting
        if hasattr(Project, sort_by):
            if sort_order == 'desc':
                query = query.order_by(getattr(Project, sort_by).desc())
            else:
                query = query.order_by(getattr(Project, sort_by))
        
        projects = query.all()
        
        # Format projects for response
        formatted_projects = []
        for project in projects:
            milestones = project.milestones.all() if hasattr(project, 'milestones') else []
            completed_milestones = [m for m in milestones if hasattr(m, 'status') and m.status == 'Completed']
            
            formatted_projects.append({
                'id': project.id,
                'name': project.name,
                'description': project.description or 'No description',
                'status': project.status or 'Planning',
                'progress': project.progress or 0,
                'manager': project.project_manager or 'Not assigned',
                'created_at': project.created_at.strftime('%Y-%m-%d') if project.created_at else None,
                'start_date': project.start_date.strftime('%Y-%m-%d') if project.start_date else None,
                'end_date': project.end_date.strftime('%Y-%m-%d') if project.end_date else None,
                'budget': project.budget or 0,
                'milestone_count': len(milestones),
                'completed_milestones': len(completed_milestones)
            })
        
        return jsonify({
            'status': 'success',
            'projects': formatted_projects,
            'count': len(formatted_projects)
        })
        
    except Exception as e:
        current_app.logger.error(f"Filter projects error: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error filtering projects'}), 500

@project_bp.route('/api/projects/<int:project_id>/details')
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def get_project_details(project_id):
    """Get comprehensive project details"""
    try:
        project = Project.query.get_or_404(project_id)
        
        # Get milestones
        milestones = project.milestones.all() if hasattr(project, 'milestones') else []
        milestone_data = []
        for milestone in milestones:
            milestone_data.append({
                'id': milestone.id,
                'title': milestone.title,
                'description': milestone.description,
                'due_date': milestone.due_date.strftime('%Y-%m-%d') if milestone.due_date else None,
                'status': getattr(milestone, 'status', 'Pending'),
                'progress': getattr(milestone, 'progress', 0)
            })
        
        # Get schedules/assignments
        schedules = project.schedules.all() if hasattr(project, 'schedules') else []
        schedule_data = []
        for schedule in schedules:
            schedule_data.append({
                'id': schedule.id,
                'task': getattr(schedule, 'task', 'No task specified'),
                'assigned_to': getattr(schedule, 'assigned_to', 'Not assigned'),
                'start_date': schedule.start_date.strftime('%Y-%m-%d') if hasattr(schedule, 'start_date') and schedule.start_date else None,
                'end_date': schedule.end_date.strftime('%Y-%m-%d') if hasattr(schedule, 'end_date') and schedule.end_date else None,
                'status': getattr(schedule, 'status', 'Pending')
            })
        
        # Calculate project health
        days_remaining = None
        is_overdue = False
        if project.end_date:
            days_remaining = (project.end_date - datetime.now().date()).days
            is_overdue = days_remaining < 0 and project.status != 'Completed'
        
        project_details = {
            'id': project.id,
            'name': project.name,
            'description': project.description or 'No description provided',
            'status': project.status or 'Planning',
            'progress': project.progress or 0,
            'manager': project.project_manager or 'Not assigned',
            'created_at': project.created_at.strftime('%Y-%m-%d %H:%M:%S') if project.created_at else None,
            'updated_at': project.updated_at.strftime('%Y-%m-%d %H:%M:%S') if project.updated_at else None,
            'start_date': project.start_date.strftime('%Y-%m-%d') if project.start_date else None,
            'end_date': project.end_date.strftime('%Y-%m-%d') if project.end_date else None,
            'budget': project.budget or 0,
            'spent': (project.budget * 0.6) if project.budget else 0,  # Simulated
            'milestones': milestone_data,
            'schedules': schedule_data,
            'milestone_count': len(milestone_data),
            'completed_milestones': len([m for m in milestone_data if m['status'] == 'Completed']),
            'team_size': len(schedule_data),
            'days_remaining': days_remaining,
            'is_overdue': is_overdue,
            'health_status': 'Critical' if is_overdue else 'Good' if days_remaining and days_remaining > 30 else 'Warning'
        }
        
        return jsonify({
            'status': 'success',
            'project': project_details
        })
        
    except Exception as e:
        current_app.logger.error(f"Get project details error: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error fetching project details'}), 500

@project_bp.route('/api/projects/statistics')
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def get_project_statistics():
    """Get comprehensive project statistics"""
    try:
        # Basic counts
        total_projects = Project.query.count()
        active_projects = Project.query.filter(Project.status.in_(['Active', 'In Progress'])).count()
        completed_projects = Project.query.filter_by(status='Completed').count()
        planning_projects = Project.query.filter_by(status='Planning').count()
        overdue_projects = Project.query.filter(
            Project.end_date < datetime.now().date(),
            Project.status != 'Completed'
        ).count()
        
        # Budget calculations
        total_budget = db.session.query(func.sum(Project.budget)).scalar() or 0
        avg_project_value = total_budget / total_projects if total_projects > 0 else 0
        
        # Progress calculations
        avg_progress = db.session.query(func.avg(Project.progress)).scalar() or 0
        
        # Monthly project creation trend (last 6 months)
        monthly_stats = []
        for i in range(6):
            month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if i > 0:
                if month_start.month > i:
                    month_start = month_start.replace(month=month_start.month - i)
                else:
                    month_start = month_start.replace(year=month_start.year - 1, month=12 - (i - month_start.month))
            
            month_end = month_start.replace(day=28) + datetime.timedelta(days=4)
            month_end = month_end - datetime.timedelta(days=month_end.day)
            
            count = Project.query.filter(
                Project.created_at >= month_start,
                Project.created_at <= month_end
            ).count()
            
            monthly_stats.append({
                'month': month_start.strftime('%B %Y'),
                'count': count
            })
        
        # Status distribution
        status_distribution = {
            'Planning': planning_projects,
            'Active': active_projects,
            'Completed': completed_projects,
            'Overdue': overdue_projects
        }
        
        statistics = {
            'overview': {
                'total_projects': total_projects,
                'active_projects': active_projects,
                'completed_projects': completed_projects,
                'planning_projects': planning_projects,
                'overdue_projects': overdue_projects,
                'completion_rate': (completed_projects / total_projects * 100) if total_projects > 0 else 0
            },
            'financial': {
                'total_budget': total_budget,
                'average_project_value': avg_project_value,
                'total_spent': total_budget * 0.6  # Simulated
            },
            'progress': {
                'average_progress': round(avg_progress, 1),
                'projects_on_track': active_projects - overdue_projects,
                'projects_at_risk': overdue_projects
            },
            'trends': {
                'monthly_creation': monthly_stats,
                'status_distribution': status_distribution
            }
        }
        
        return jsonify({
            'status': 'success',
            'statistics': statistics
        })
        
    except Exception as e:
        current_app.logger.error(f"Get project statistics error: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error fetching project statistics'}), 500


# ===== ENHANCED PROJECT MANAGEMENT ROUTES =====

@project_bp.route('/<int:project_id>/assign_staff', methods=['POST'])
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def assign_staff_enhanced(project_id):
    """Enhanced staff assignment endpoint"""
    try:
        project = Project.query.get_or_404(project_id)
        
        staff_id = request.form.get('staff_id')
        role = request.form.get('role')
        
        if not staff_id or not role:
            return jsonify({'success': False, 'message': 'Staff ID and role are required'}), 400
        
        # Check if staff is already assigned
        existing_assignment = StaffAssignment.query.filter_by(
            project_id=project_id, 
            staff_id=staff_id
        ).first()
        
        if existing_assignment:
            return jsonify({'success': False, 'message': 'Staff member is already assigned to this project'}), 400
        
        # Get staff member details
        staff_member = User.query.get(staff_id)
        if not staff_member:
            return jsonify({'success': False, 'message': 'Staff member not found'}), 404
        
        # Create new assignment
        assignment = StaffAssignment(
            project_id=project_id,
            staff_id=staff_id,
            role=role,
            assigned_at=datetime.utcnow()
        )
        
        db.session.add(assignment)
        
        # Log activity
        from models import ProjectActivity
        activity = ProjectActivity(
            project_id=project_id,
            user_id=current_user.id,
            action_type='staff_assigned',
            description=f'{staff_member.name} was assigned as {role}',
            user_name=current_user.name
        )
        db.session.add(activity)
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'{staff_member.name} has been assigned as {role}'
        })
        
    except Exception as e:
        current_app.logger.error(f"Error assigning staff: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({'success': False, 'message': 'An error occurred while assigning staff'}), 500


@project_bp.route('/<int:project_id>/remove_staff', methods=['POST'])
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def remove_staff_new(project_id):
    """Enhanced staff removal endpoint"""
    try:
        project = Project.query.get_or_404(project_id)
        
        data = request.get_json()
        staff_id = data.get('staff_id')
        
        if not staff_id:
            return jsonify({'success': False, 'message': 'Staff ID is required'}), 400
        
        # Find and remove assignment
        assignment = StaffAssignment.query.filter_by(
            project_id=project_id,
            staff_id=staff_id
        ).first()
        
        if not assignment:
            return jsonify({'success': False, 'message': 'Staff assignment not found'}), 404
        
        # Get staff member details for logging
        staff_member = User.query.get(staff_id)
        staff_name = staff_member.name if staff_member else 'Unknown'
        role = assignment.role
        
        db.session.delete(assignment)
        
        # Log activity
        from models import ProjectActivity
        activity = ProjectActivity(
            project_id=project_id,
            user_id=current_user.id,
            action_type='staff_removed',
            description=f'{staff_name} was removed from {role} role',
            user_name=current_user.name
        )
        db.session.add(activity)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{staff_name} has been removed from the project'
        })
        
    except Exception as e:
        current_app.logger.error(f"Error removing staff: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({'success': False, 'message': 'An error occurred while removing staff'}), 500


@project_bp.route('/<int:project_id>/add_milestone', methods=['POST'])
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def add_milestone_enhanced(project_id):
    """Enhanced milestone creation endpoint"""
    try:
        project = Project.query.get_or_404(project_id)
        
        milestone_name = request.form.get('milestone_name')
        milestone_description = request.form.get('milestone_description', '')
        due_date_str = request.form.get('due_date')
        
        if not milestone_name or not due_date_str:
            return jsonify({'success': False, 'message': 'Milestone name and due date are required'}), 400
        
        # Parse due date
        try:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid date format'}), 400
        
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
        from models import ProjectActivity
        activity = ProjectActivity(
            project_id=project_id,
            user_id=current_user.id,
            action_type='milestone_added',
            description=f'Milestone "{milestone_name}" was created with due date {due_date.strftime("%B %d, %Y")}',
            user_name=current_user.name
        )
        db.session.add(activity)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Milestone "{milestone_name}" has been created'
        })
        
    except Exception as e:
        current_app.logger.error(f"Error adding milestone: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({'success': False, 'message': 'An error occurred while adding milestone'}), 500


@project_bp.route('/<int:project_id>/milestones/<int:milestone_id>', methods=['DELETE'])
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def delete_milestone_new(project_id, milestone_id):
    """Enhanced milestone deletion endpoint"""
    try:
        project = Project.query.get_or_404(project_id)
        milestone = Milestone.query.filter_by(id=milestone_id, project_id=project_id).first()
        
        if not milestone:
            return jsonify({'success': False, 'message': 'Milestone not found'}), 404
        
        milestone_title = milestone.title
        db.session.delete(milestone)
        
        # Log activity
        from models import ProjectActivity
        activity = ProjectActivity(
            project_id=project_id,
            user_id=current_user.id,
            action_type='milestone_deleted',
            description=f'Milestone "{milestone_title}" was deleted',
            user_name=current_user.name
        )
        db.session.add(activity)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Milestone "{milestone_title}" has been deleted'
        })
        
    except Exception as e:
        current_app.logger.error(f"Error deleting milestone: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({'success': False, 'message': 'An error occurred while deleting milestone'}), 500


@project_bp.route('/<int:project_id>/add_boq_item', methods=['POST'])
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def add_boq_item_enhanced(project_id):
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
        from models import BOQItem
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
        from models import ProjectActivity
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


@project_bp.route('/<int:project_id>/boq_items/<int:item_id>', methods=['DELETE'])
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def delete_boq_item(project_id, item_id):
    """Delete BOQ item endpoint"""
    try:
        project = Project.query.get_or_404(project_id)
        from models import BOQItem
        boq_item = BOQItem.query.filter_by(id=item_id, project_id=project_id).first()
        
        if not boq_item:
            return jsonify({'success': False, 'message': 'BOQ item not found'}), 404
        
        item_description = boq_item.item_description
        db.session.delete(boq_item)
        
        # Log activity
        from models import ProjectActivity
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


@project_bp.route('/<int:project_id>/upload_document', methods=['POST'])
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def upload_document_enhanced(project_id):
    """Enhanced document upload endpoint"""
    try:
        project = Project.query.get_or_404(project_id)
        
        if 'document_file' not in request.files:
            return jsonify({'success': False, 'message': 'No file selected'}), 400
        
        file = request.files['document_file']
        document_type = request.form.get('document_type')
        description = request.form.get('document_description', '')
        
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'}), 400
        
        if not document_type:
            return jsonify({'success': False, 'message': 'Document type is required'}), 400
        
        # Validate file type
        allowed_extensions = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'png', 'jpg', 'jpeg'}
        if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
            return jsonify({'success': False, 'message': 'File type not allowed'}), 400
        
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
        from models import ProjectDocument
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
        from models import ProjectActivity
        activity = ProjectActivity(
            project_id=project_id,
            user_id=current_user.id,
            action_type='document_uploaded',
            description=f'Document "{filename}" was uploaded ({document_type})',
            user_name=current_user.name
        )
        db.session.add(activity)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Document "{filename}" has been uploaded successfully'
        })
        
    except Exception as e:
        current_app.logger.error(f"Error uploading document: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({'success': False, 'message': 'An error occurred while uploading document'}), 500


@project_bp.route('/<int:project_id>/documents/<int:document_id>/download')
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def download_project_document(project_id, document_id):
    """Enhanced document download endpoint"""
    try:
        project = Project.query.get_or_404(project_id)
        from models import ProjectDocument
        document = ProjectDocument.query.filter_by(id=document_id, project_id=project_id).first()
        
        if not document:
            flash('Document not found', 'error')
            return redirect(url_for('project.project_details', project_id=project_id))
        
        if not os.path.exists(document.file_path):
            flash('File not found on disk', 'error')
            return redirect(url_for('project.project_details', project_id=project_id))
        
        return send_file(
            document.file_path,
            as_attachment=True,
            download_name=document.original_filename,
            mimetype='application/octet-stream'
        )
        
    except Exception as e:
        current_app.logger.error(f"Error downloading document: {str(e)}", exc_info=True)
        flash('An error occurred while downloading the document', 'error')
        return redirect(url_for('project.project_details', project_id=project_id))


@project_bp.route('/<int:project_id>/documents/<int:document_id>', methods=['DELETE'])
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def delete_document_enhanced(project_id, document_id):
    """Enhanced document deletion endpoint"""
    try:
        project = Project.query.get_or_404(project_id)
        from models import ProjectDocument
        document = ProjectDocument.query.filter_by(id=document_id, project_id=project_id).first()
        
        if not document:
            return jsonify({'success': False, 'message': 'Document not found'}), 404
        
        # Delete file from disk
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
        
        document_name = document.original_filename
        db.session.delete(document)
        
        # Log activity
        from models import ProjectActivity
        activity = ProjectActivity(
            project_id=project_id,
            user_id=current_user.id,
            action_type='document_deleted',
            description=f'Document "{document_name}" was deleted',
            user_name=current_user.name
        )
        db.session.add(activity)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Document "{document_name}" has been deleted'
        })
        
    except Exception as e:
        current_app.logger.error(f"Error deleting document: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({'success': False, 'message': 'An error occurred while deleting document'}), 500


@project_bp.route('/<int:project_id>/update_progress', methods=['POST'])
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def update_progress_enhanced(project_id):
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
        from models import ProjectActivity
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
