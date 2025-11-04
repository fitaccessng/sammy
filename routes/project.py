import os
from datetime import datetime
from flask import Blueprint, render_template, current_app, flash, request, jsonify, url_for, redirect, session, send_file
from flask_login import login_required, current_user, logout_user
from werkzeug.utils import secure_filename
from extensions import db
from models import Project, StaffAssignment, EmployeeAssignment, Employee, Task, Equipment, Material, Report, Document, User, Milestone, Schedule, Expense, DailyProductionReport, DPRProductionItem, DPRMaterialUsage, Budget
from utils.decorators import role_required
from utils.constants import Roles
from utils.email import send_email_notification
from sqlalchemy import func
import os

project_bp = Blueprint('project', __name__)

def get_user_accessible_projects(user):
    """Get projects that the user has access to based on their role"""
    current_app.logger.info(f"Getting accessible projects for user {user.id} ({user.role})")
    
    if user.has_role(Roles.SUPER_HQ):
        # SUPER_HQ sees all projects
        projects = Project.query.all()
        current_app.logger.info(f"SUPER_HQ user - returning all {len(projects)} projects")
        return projects
    elif user.has_role(Roles.PROJECT_MANAGER):
        # Project managers see projects they manage AND projects they're assigned to
        managed_projects = Project.query.filter(Project.project_manager == user.name).all()
        
        # Also get projects assigned to them as staff
        assigned_projects_query = db.session.query(Project).join(
            StaffAssignment, Project.id == StaffAssignment.project_id
        ).filter(StaffAssignment.staff_id == user.id)
        assigned_projects = assigned_projects_query.all()
        
        # Combine and remove duplicates
        all_projects = managed_projects + assigned_projects
        unique_projects = list({project.id: project for project in all_projects}.values())
        
        current_app.logger.info(f"PROJECT_MANAGER user - {len(managed_projects)} managed, {len(assigned_projects)} assigned, {len(unique_projects)} total")
        return unique_projects
    else:
        # Staff see only assigned projects - check both User assignments and Employee assignments
        current_app.logger.info(f"Staff user - checking assignments for user {user.id}")
        
        # Get projects assigned to user directly
        user_projects_query = db.session.query(Project).join(
            StaffAssignment, Project.id == StaffAssignment.project_id
        ).filter(StaffAssignment.staff_id == user.id)
        user_projects = user_projects_query.all()
        current_app.logger.info(f"Found {len(user_projects)} direct user assignments")
        
        # Get projects assigned to user as employee (match by email or name)
        employee_projects = []
        try:
            # Find employee record that matches this user (by email first, then by name)
            employee = None
            if user.email:
                employee = Employee.query.filter_by(email=user.email).first()
                if employee:
                    current_app.logger.info(f"Found matching employee by email: {employee.name} (ID: {employee.id})")
            if not employee and user.name:
                employee = Employee.query.filter_by(name=user.name).first()
                if employee:
                    current_app.logger.info(f"Found matching employee by name: {employee.name} (ID: {employee.id})")
            
            if employee:
                # Get projects assigned to this employee
                employee_projects_query = db.session.query(Project).join(
                    EmployeeAssignment, Project.id == EmployeeAssignment.project_id
                ).filter(EmployeeAssignment.employee_id == employee.id)
                employee_projects = employee_projects_query.all()
                current_app.logger.info(f"Found {len(employee_projects)} employee assignments")
            else:
                current_app.logger.info("No matching employee record found")
                
        except Exception as e:
            current_app.logger.error(f"Error getting employee projects for user {user.id}: {str(e)}")
            employee_projects = []
        
        # Combine both lists and remove duplicates
        all_projects = user_projects + employee_projects
        unique_projects = list({project.id: project for project in all_projects}.values())
        
        current_app.logger.info(f"Staff user - {len(user_projects)} user assignments + {len(employee_projects)} employee assignments = {len(unique_projects)} total projects")
        
        return unique_projects

def get_user_accessible_project_ids(user):
    """Get project IDs that the user has access to"""
    projects = get_user_accessible_projects(user)
    return [p.id for p in projects]

# Dashboard
@project_bp.route('/')
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER, Roles.PROJECT_STAFF, Roles.HQ_FINANCE, Roles.HQ_PROCUREMENT])
def project_home():
    try:
        current_app.logger.info(f"User {current_user.id} ({current_user.role}) accessing project dashboard")
        
        # Filter projects based on user role and assignments using centralized function
        projects = get_user_accessible_projects(current_user)
        current_app.logger.info(f"User {current_user.id} ({current_user.role}) accessing {len(projects)} projects")
        
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
                milestones = project.milestones if hasattr(project, 'milestones') else []
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
                    'created_at': project.created_at,  # Keep as datetime object
                    'updated_at': project.updated_at,  # Keep as datetime object
                    'start_date': project.start_date,  # Keep as datetime object
                    'end_date': project.end_date,  # Keep as datetime object
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
                             current_user=current_user,
                             current_date_obj=datetime.now().date())
                             
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
                             current_user=current_user,
                             current_date_obj=datetime.now().date())


# Create Project - Only SUPER_HQ can create projects
@project_bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required([Roles.SUPER_HQ])
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


# Assign Staff to Project - Only SUPER_HQ and Project Managers can assign staff
@project_bp.route('/<int:project_id>/assign-staff', methods=['POST'])
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def assign_staff(project_id):
    try:
        project = Project.query.get_or_404(project_id)
        
        # Check if user has permission to assign staff to this project
        is_manager = project.project_manager == current_user.name
        is_super_hq = current_user.has_role(Roles.SUPER_HQ)
        
        if not (is_manager or is_super_hq):
            current_app.logger.warning(f"User {current_user.id} denied staff assignment access to project {project_id}")
            flash("You don't have permission to assign staff to this project.", "error")
            return redirect(url_for('project.project_details', project_id=project_id))
        
        staff_role = request.form.get('role')
        staff_id = request.form.get('staff_id')
        assignment = StaffAssignment(project_id=project_id, staff_id=staff_id, role=staff_role)
        db.session.add(assignment)
        db.session.commit()
        current_app.logger.info(f"Staff {staff_id} assigned to project {project_id} by user {current_user.id}")
        flash(f"{staff_role} assigned to project {project_id} successfully!", "success")
        return redirect(url_for('project.project_details', project_id=project_id))
    except Exception as e:
        db.session.rollback()
        flash(f"Error assigning staff: {str(e)}", "error")
        return redirect(url_for('project.project_details', project_id=project_id))


# View Project Details
@project_bp.route('/<int:project_id>')
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER, Roles.PROJECT_STAFF, Roles.HQ_FINANCE, Roles.HQ_PROCUREMENT])
def project_details(project_id):
    try:
        current_app.logger.info(f"Project route: User {current_user.id} ({current_user.role}) accessing project {project_id}")
        project = Project.query.get_or_404(project_id)
        
        # Check if user has access to this project
        user_assignment = StaffAssignment.query.filter_by(
            project_id=project_id, 
            staff_id=current_user.id
        ).first()
        
        # Also check if user has access as an employee
        employee_assignment = None
        try:
            # Find employee record that matches this user
            employee = None
            if current_user.email:
                employee = Employee.query.filter_by(email=current_user.email).first()
            if not employee and current_user.name:
                employee = Employee.query.filter_by(name=current_user.name).first()
            
            if employee:
                employee_assignment = EmployeeAssignment.query.filter_by(
                    project_id=project_id,
                    employee_id=employee.id
                ).first()
        except Exception as e:
            current_app.logger.error(f"Error checking employee assignment for user {current_user.id}: {str(e)}")
            employee_assignment = None
        
        is_manager = project.project_manager == current_user.name
        is_super_hq = current_user.has_role(Roles.SUPER_HQ)
        
        # Allow access if user is assigned (as user or employee), is the manager, or is SUPER_HQ
        if not (user_assignment or employee_assignment or is_manager or is_super_hq):
            current_app.logger.warning(f"User {current_user.id} denied access to project {project_id}")
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
        try:
            from models import BOQItem, ProjectActivity, ProjectDocument
        except ImportError as import_error:
            current_app.logger.error(f"Model import error: {import_error}")
            raise
        
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
                             boq_items=BOQItem.query.filter_by(project_id=project_id).all() if BOQItem else [],
                             project_documents=ProjectDocument.query.filter_by(project_id=project_id).all() if ProjectDocument else [],
                             activity_log=ProjectActivity.query.filter_by(project_id=project_id).order_by(ProjectActivity.created_at.desc()).limit(10).all() if ProjectActivity else [])
    except Exception as e:
        current_app.logger.error(f"Project details error: {str(e)}", exc_info=True)
        flash("Error loading project details", "error")
        return redirect(url_for('project.project_home'))


# API: List Projects (for AJAX)
@project_bp.route('/api/list')
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def list_projects():
    try:
        projects = Project.query.order_by(Project.created_at.desc()).all()
        # Instead of returning JSON, redirect to project home which displays the list
        return redirect(url_for('project.project_home'))
    except Exception as e:
        flash(f"Error loading projects: {str(e)}", "error")
        return redirect(url_for('project.project_home'))
    
# Update Project - Only SUPER_HQ and Project Managers can edit their projects
@project_bp.route('/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def edit_project(project_id):
    try:
        project = Project.query.get_or_404(project_id)
        
        # Check if user has permission to edit this project
        is_manager = project.project_manager == current_user.name
        is_super_hq = current_user.has_role(Roles.SUPER_HQ)
        
        if not (is_manager or is_super_hq):
            current_app.logger.warning(f"User {current_user.id} denied edit access to project {project_id}")
            flash("You don't have permission to edit this project.", "error")
            return redirect(url_for('project.project_details', project_id=project_id))
        
        if request.method == 'POST':
            project.name = request.form.get('name', project.name)
            project.status = request.form.get('status', project.status)
            project.description = request.form.get('description', project.description)
            project.updated_at = datetime.utcnow()
            db.session.commit()
            current_app.logger.info(f"Project {project_id} updated by user {current_user.id}")
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
        flash(f"Error deleting project: {str(e)}", "error")
        return redirect(url_for('project.project_home'))


# Project Timeline / Milestones - Allow project managers to manage their project milestones
@project_bp.route('/<int:project_id>/timeline', methods=['GET', 'POST'])
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def project_timeline(project_id):
    try:
        project = Project.query.get_or_404(project_id)
        
        # Check if user has permission to manage milestones for this project
        is_manager = project.project_manager == current_user.name
        is_super_hq = current_user.has_role(Roles.SUPER_HQ)
        
        if not (is_manager or is_super_hq):
            current_app.logger.warning(f"User {current_user.id} denied milestone access to project {project_id}")
            flash("You don't have permission to manage milestones for this project.", "error")
            return redirect(url_for('project.project_details', project_id=project_id))
        
        if request.method == 'POST':
            title = request.form.get('title')
            due_date = request.form.get('due_date')
            status = request.form.get('status', 'Pending')
            milestone = Milestone(project_id=project_id, title=title, due_date=due_date, status=status)
            db.session.add(milestone)
            db.session.commit()
            current_app.logger.info(f"Milestone added to project {project_id} by user {current_user.id}")
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
        # Instead of returning JSON, redirect to project details which shows staff
        return redirect(url_for('project.project_details', project_id=project_id))
    except Exception as e:
        flash(f"Error loading project staff: {str(e)}", "error")
        return redirect(url_for('project.project_details', project_id=project_id))


# Tasks Page
@project_bp.route('/tasks')
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER, Roles.PROJECT_STAFF])
def tasks():
    try:
        # Get user's accessible projects
        accessible_projects = get_user_accessible_projects(current_user)
        
        current_app.logger.info(f"User {current_user.id} ({current_user.role}) accessing tasks for {len(accessible_projects)} projects")
        
        # Pass accessible projects to template for project selection
        return render_template('projects/tasks.html', 
                             accessible_projects=accessible_projects,
                             user_role=current_user.role)
    except Exception as e:
        current_app.logger.error(f"Tasks page error: {str(e)}")
        return render_template('error.html', error="Failed to load tasks"), 500


# Get milestones for a specific project (API endpoint)
@project_bp.route('/milestones/project/<int:project_id>')
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER, Roles.PROJECT_STAFF])
def get_project_milestones(project_id):
    try:
        # Get user's accessible projects
        accessible_projects = get_user_accessible_projects(current_user)
        accessible_project_ids = [p.id for p in accessible_projects]
        
        # Validate project access
        if project_id not in accessible_project_ids:
            return jsonify({'error': 'Access denied to this project'}), 403
        
        # Get milestones for the project
        milestones = Milestone.query.filter_by(project_id=project_id).order_by(Milestone.due_date).all()
        
        # Convert to JSON
        milestones_data = []
        for milestone in milestones:
            milestones_data.append({
                'id': milestone.id,
                'title': milestone.title,
                'due_date': milestone.due_date.isoformat(),
                'status': milestone.status,
                'description': getattr(milestone, 'description', ''),  # Handle case where description might not exist
                'project_id': milestone.project_id
            })
        
        return jsonify({'milestones': milestones_data})
        
    except Exception as e:
        current_app.logger.error(f"Error loading project milestones: {str(e)}")
        return jsonify({'error': 'Failed to load milestones'}), 500


# Create milestone (API endpoint)
@project_bp.route('/milestones', methods=['POST'])
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def create_milestone():
    try:
        # Get user's accessible projects
        accessible_projects = get_user_accessible_projects(current_user)
        accessible_project_ids = [p.id for p in accessible_projects]
        
        project_id = request.form.get('project_id')
        title = request.form.get('title')
        due_date = request.form.get('due_date')
        status = request.form.get('status', 'Pending')
        description = request.form.get('description', '')
        
        # Validate required fields
        if not all([project_id, title, due_date]):
            return jsonify({'error': 'Project, title, and due date are required'}), 400
        
        # Validate project access
        if int(project_id) not in accessible_project_ids:
            return jsonify({'error': 'Access denied to this project'}), 403
        
        # Create milestone
        milestone = Milestone(
            project_id=int(project_id),
            title=title,
            due_date=datetime.strptime(due_date, '%Y-%m-%d').date(),
            status=status
        )
        
        # Add description if the model supports it
        if hasattr(milestone, 'description'):
            milestone.description = description
        
        db.session.add(milestone)
        db.session.commit()
        
        current_app.logger.info(f"Milestone '{title}' created for project {project_id} by user {current_user.id}")
        
        return jsonify({'status': 'success', 'message': 'Milestone created successfully'})
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating milestone: {str(e)}")
        return jsonify({'error': 'Failed to create milestone'}), 500


# Delete milestone (API endpoint)
@project_bp.route('/milestones/<int:milestone_id>/delete', methods=['POST'])
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def delete_milestone(milestone_id):
    try:
        milestone = Milestone.query.get_or_404(milestone_id)
        
        # Check project access
        accessible_projects = get_user_accessible_projects(current_user)
        accessible_project_ids = [p.id for p in accessible_projects]
        
        if milestone.project_id not in accessible_project_ids:
            return jsonify({'error': 'Access denied to this project'}), 403
        
        # Delete milestone
        db.session.delete(milestone)
        db.session.commit()
        
        current_app.logger.info(f"Milestone {milestone_id} deleted by user {current_user.id}")
        
        return jsonify({'status': 'success', 'message': 'Milestone deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting milestone: {str(e)}")
        return jsonify({'error': 'Failed to delete milestone'}), 500


# Equipment Page - Filter by user's accessible projects
@project_bp.route('/equipment', methods=['GET', 'POST'])
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER, Roles.PROJECT_STAFF, Roles.HQ_FINANCE, Roles.HQ_PROCUREMENT])
def equipment():
    try:
        # Get user's accessible projects
        accessible_projects = get_user_accessible_projects(current_user)
        accessible_project_ids = [p.id for p in accessible_projects]
        
        # Only SUPER_HQ and PROJECT_MANAGER can add/edit equipment
        can_manage = current_user.has_role(Roles.SUPER_HQ) or current_user.has_role(Roles.PROJECT_MANAGER)
        
        current_app.logger.info(f"User {current_user.id} ({current_user.role}) accessing equipment for {len(accessible_projects)} projects")
        
        # Get selected project from request
        selected_project_id = request.args.get('project_id') or request.form.get('project_id')
        selected_project = None
        equipment_list = []
        
        if selected_project_id:
            try:
                selected_project_id = int(selected_project_id)
                if selected_project_id in accessible_project_ids:
                    selected_project = Project.query.get(selected_project_id)
            except (ValueError, TypeError):
                selected_project_id = None
        
        # Handle POST request (add new equipment)
        if request.method == 'POST' and 'add_equipment' in request.form:
            if not can_manage:
                flash('You do not have permission to add equipment', 'error')
                return redirect(url_for('project.equipment', project_id=selected_project_id))
            
            name = request.form.get('name')
            project_id = request.form.get('project_id')
            maintenance_due = request.form.get('maintenance_due')
            machine_hours = request.form.get('machine_hours', 0)
            diesel_consumption = request.form.get('diesel_consumption', 0)
            remarks = request.form.get('remarks', '')
            status = request.form.get('status', 'Active')
            
            # Validate required fields
            if not name or not project_id:
                flash('Equipment name and project are required', 'error')
                return redirect(url_for('project.equipment', project_id=project_id))
            
            # Validate project access
            if int(project_id) not in accessible_project_ids:
                flash('You do not have access to the selected project', 'error')
                return redirect(url_for('project.equipment'))
            
            # Create equipment record
            equipment = Equipment(
                name=name,
                project_id=int(project_id),
                maintenance_due=datetime.strptime(maintenance_due, '%Y-%m-%d').date() if maintenance_due else None,
                machine_hours=float(machine_hours) if machine_hours else 0,
                diesel_consumption=float(diesel_consumption) if diesel_consumption else 0,
                remarks=remarks,
                status=status
            )
            
            try:
                db.session.add(equipment)
                db.session.commit()
                
                current_app.logger.info(f"Equipment '{name}' added by user {current_user.id} for project {project_id}")
                flash(f'Equipment "{name}" added successfully!', 'success')
                return redirect(url_for('project.equipment', project_id=project_id))
                
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Database error during equipment creation: {str(e)}")
                flash('Failed to add equipment', 'error')
                return redirect(url_for('project.equipment', project_id=project_id))
        
        # GET request - load equipment for selected project
        if selected_project:
            equipment_list = Equipment.query.filter_by(project_id=selected_project.id).order_by(Equipment.maintenance_due).all()
        
        return render_template('projects/equipment.html', 
                             equipment_list=equipment_list,
                             accessible_projects=accessible_projects,
                             selected_project=selected_project,
                             can_manage=can_manage,
                             user_role=current_user.role)
    except Exception as e:
        current_app.logger.error(f"Equipment page error: {str(e)}", exc_info=True)
        flash(f'Failed to load equipment page: {str(e)}', 'error')
        return redirect(url_for('project.project_home'))


# Edit Equipment
@project_bp.route('/equipment/<int:equipment_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def edit_equipment(equipment_id):
    try:
        equipment = Equipment.query.get_or_404(equipment_id)
        
        # Check project access
        accessible_projects = get_user_accessible_projects(current_user)
        accessible_project_ids = [p.id for p in accessible_projects]
        
        if equipment.project_id not in accessible_project_ids:
            flash('You do not have access to this equipment', 'error')
            return redirect(url_for('project.equipment', project_id=equipment.project_id))
        
        if request.method == 'POST':
            equipment.name = request.form.get('name')
            equipment.maintenance_due = datetime.strptime(request.form.get('maintenance_due'), '%Y-%m-%d').date() if request.form.get('maintenance_due') else None
            equipment.machine_hours = float(request.form.get('machine_hours', 0))
            equipment.diesel_consumption = float(request.form.get('diesel_consumption', 0))
            equipment.remarks = request.form.get('remarks', '')
            equipment.status = request.form.get('status', 'Active')
            
            try:
                db.session.commit()
                flash('Equipment updated successfully!', 'success')
                return redirect(url_for('project.equipment', project_id=equipment.project_id))
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error updating equipment: {str(e)}")
                flash('Failed to update equipment', 'error')
                return redirect(url_for('project.equipment', project_id=equipment.project_id))
        
        # GET request - show edit form
        accessible_projects_list = get_user_accessible_projects(current_user)
        return render_template('projects/edit_equipment.html',
                             equipment=equipment,
                             accessible_projects=accessible_projects_list,
                             user_role=current_user.role)
                             
    except Exception as e:
        current_app.logger.error(f"Error editing equipment: {str(e)}")
        flash('Failed to edit equipment', 'error')
        return redirect(url_for('project.equipment'))


# Delete Equipment
@project_bp.route('/equipment/<int:equipment_id>/delete', methods=['POST'])
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def delete_equipment(equipment_id):
    try:
        equipment = Equipment.query.get_or_404(equipment_id)
        project_id = equipment.project_id
        
        # Check project access
        accessible_projects = get_user_accessible_projects(current_user)
        accessible_project_ids = [p.id for p in accessible_projects]
        
        if equipment.project_id not in accessible_project_ids:
            flash('You do not have access to this equipment', 'error')
            return redirect(url_for('project.equipment', project_id=equipment.project_id))
        
        db.session.delete(equipment)
        db.session.commit()
        
        flash('Equipment deleted successfully!', 'success')
        return redirect(url_for('project.equipment', project_id=project_id))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting equipment: {str(e)}")
        flash('Failed to delete equipment', 'error')
        return redirect(url_for('project.equipment'))


# Materials Page - Filter by user's accessible projects
@project_bp.route('/materials')
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER, Roles.PROJECT_STAFF, Roles.HQ_FINANCE, Roles.HQ_PROCUREMENT])
def materials():
    try:
        # Get user's accessible projects
        accessible_projects = get_user_accessible_projects(current_user)
        accessible_project_ids = [p.id for p in accessible_projects]
        
        current_app.logger.info(f"User {current_user.id} ({current_user.role}) accessing materials for {len(accessible_projects)} projects")
        
        # For now, since Material model doesn't have project_id, we'll show all materials
        # but with context of accessible projects for future filtering
        materials_data = Material.query.order_by(Material.name).all()
        
        # In a real scenario, you might want to add project_id to Material model
        # For now, we'll pass accessible projects to the template for context
        return render_template('projects/materials.html', 
                             materials=materials_data,
                             accessible_projects=accessible_projects,
                             user_role=current_user.role)
    except Exception as e:
        current_app.logger.error(f"Materials page error: {str(e)}")
        return render_template('error.html', error="Failed to load materials"), 500


# Analytics Page
@project_bp.route('/analytics')
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def analytics():
    from datetime import datetime, timedelta
    from sqlalchemy import func
    import calendar
    
    try:
        # Get user's accessible projects
        accessible_projects = get_user_accessible_projects(current_user)
        
        # Get actual data from database
        current_date = datetime.now()
        current_year = current_date.year
        
        # Calculate real portfolio metrics
        total_projects = len(accessible_projects)
        active_projects = len([p for p in accessible_projects if p.status == 'Active'])
        completed_projects = len([p for p in accessible_projects if p.status == 'Completed'])
        
        # Calculate actual budget data from Budget and Expense models
        total_planned_value = 0
        total_actual_cost = 0
        total_earned_value = 0
        
        for project in accessible_projects:
            # Get project's actual budget allocations
            project_budgets = Budget.query.filter_by(project_id=project.id).all()
            project_allocated = sum(b.allocated_amount for b in project_budgets)
            project_spent = sum(b.spent_amount for b in project_budgets)
            
            # If no budget entries, use project.budget field
            if not project_budgets and project.budget:
                project_allocated = project.budget
                # Estimate spent based on progress
                if project.progress:
                    project_spent = project.budget * (project.progress / 100.0)
                else:
                    project_spent = 0
            
            total_planned_value += project_allocated
            total_actual_cost += project_spent
            
            # Calculate earned value based on actual progress
            if project.progress and project_allocated:
                total_earned_value += project_allocated * (project.progress / 100.0)
            elif project.status == 'Completed' and project_allocated:
                total_earned_value += project_allocated
        
        # EVM Performance Indicators
        spi = total_earned_value / total_planned_value if total_planned_value > 0 else 0  # Schedule Performance Index
        cpi = total_earned_value / total_actual_cost if total_actual_cost > 0 else 0     # Cost Performance Index
        
        # Forecast calculations
        budget_at_completion = total_planned_value
        estimate_at_completion = budget_at_completion / cpi if cpi > 0 else budget_at_completion
        estimate_to_complete = estimate_at_completion - total_actual_cost
        variance_at_completion = budget_at_completion - estimate_at_completion
        
        # Get actual report data
        total_reports = Report.query.join(User).filter(User.id.in_([p.id for p in accessible_projects])).count() if accessible_projects else 0
        total_dprs = DailyProductionReport.query.filter(
            DailyProductionReport.project_id.in_([p.id for p in accessible_projects])
        ).count() if accessible_projects else 0
        
        # Get reports this month
        month_start = current_date.replace(day=1)
        reports_this_month = Report.query.filter(
            Report.date >= month_start,
            Report.uploader_id.in_([p.project_manager for p in accessible_projects if p.project_manager])
        ).count() if accessible_projects else 0
        
        dprs_this_month = DailyProductionReport.query.filter(
            DailyProductionReport.created_at >= month_start,
            DailyProductionReport.project_id.in_([p.id for p in accessible_projects])
        ).count() if accessible_projects else 0
        
        # Calculate monthly trending data based on actual progress
        pv_monthly = []
        ev_monthly = []
        ac_monthly = []
        
        for month in range(1, 13):
            month_factor = month / 12.0
            pv_monthly.append(int(total_planned_value * month_factor))
            ev_monthly.append(int(total_earned_value * month_factor))
            ac_monthly.append(int(total_actual_cost * month_factor))
        
        # Real quality metrics based on project data
        quality_index = calculate_real_quality_index(accessible_projects)
        safety_score = calculate_real_safety_score(accessible_projects)
        
        # Real resource utilization based on project assignments
        resource_data = calculate_real_resource_utilization(accessible_projects)
        
        # Material and equipment efficiency based on actual data
        material_efficiency = calculate_real_material_efficiency(accessible_projects)
        equipment_utilization = calculate_real_equipment_utilization(accessible_projects)
        
        # Risk assessment based on project characteristics
        portfolio_risk_score = calculate_real_portfolio_risk_score(accessible_projects)
        
        # Weather impact from DPR data
        weather_delays = calculate_real_weather_impact(accessible_projects)
        
        # Days without incident from DPR data
        days_without_incident = calculate_days_without_incident(accessible_projects)
        
        # Project status counts
        status_counts = {}
        for project in accessible_projects:
            status = project.status or 'Unknown'
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Compile real data
        data = {
            # Portfolio KPIs
            'portfolio_value': total_planned_value,
            'active_projects': active_projects,
            'completed_projects': completed_projects,
            'total_projects': total_projects,
            
            # EVM Metrics (actual calculations)
            'spi': round(spi, 3),
            'cpi': round(cpi, 3),
            'planned_value': total_planned_value,
            'earned_value': total_earned_value,
            'actual_cost': total_actual_cost,
            'eac': estimate_at_completion,
            'etc': estimate_to_complete,
            'vac': variance_at_completion,
            
            # Monthly trending data
            'pv_monthly': pv_monthly,
            'ev_monthly': ev_monthly,
            'ac_monthly': ac_monthly,
            
            # Real metrics
            'quality_index': quality_index,
            'safety_score': safety_score,
            'weather_delays': weather_delays,
            'days_without_incident': days_without_incident,
            'material_efficiency': material_efficiency,
            'equipment_utilization': equipment_utilization,
            'risk_score': portfolio_risk_score,
            
            # Report metrics
            'total_reports': total_reports,
            'total_dprs': total_dprs,
            'reports_this_month': reports_this_month,
            'dprs_this_month': dprs_this_month,
            
            # Resource data
            'resource_allocation': resource_data['allocation'],
            'resource_utilization': resource_data['utilization'],
            
            # Performance matrix data for table
            'performance_matrix': generate_real_performance_matrix(accessible_projects),
            
            # Legacy compatibility
            'project_status': status_counts,
            'budget_overview': {
                'allocated': total_planned_value,
                'spent': total_actual_cost,
                'remaining': total_planned_value - total_actual_cost
            }
        }
        
        return render_template('projects/analytics.html', data=data, total_projects=total_projects)
        
    except Exception as e:
        current_app.logger.error(f"Analytics page error: {str(e)}")
        return render_template('error.html', error="Failed to load analytics"), 500


# Real Data Calculation Functions
def calculate_real_quality_index(projects):
    """Calculate quality index based on actual project data"""
    if not projects:
        return 0
    
    total_quality = 0
    for project in projects:
        # Base quality score
        quality = 85
        
        # Adjust based on project completion and status
        if project.status == 'Completed':
            quality += 10  # Completed projects assumed higher quality
        elif project.status == 'Active' and project.progress:
            # Higher progress generally indicates better quality control
            if project.progress >= 80:
                quality += 5
            elif project.progress >= 60:
                quality += 3
        
        # Adjust based on budget performance (CPI)
        project_budgets = Budget.query.filter_by(project_id=project.id).all()
        if project_budgets:
            allocated = sum(b.allocated_amount for b in project_budgets)
            spent = sum(b.spent_amount for b in project_budgets)
            if allocated > 0 and spent > 0:
                cpi = (project.progress or 0) / 100.0 * allocated / spent
                if cpi >= 1.0:
                    quality += 3  # Good cost performance
                elif cpi < 0.8:
                    quality -= 5  # Poor cost performance
        
        total_quality += min(100, max(60, quality))
    
    return round(total_quality / len(projects), 1)


def calculate_real_safety_score(projects):
    """Calculate safety score based on project data and risk levels"""
    if not projects:
        return 0
    
    total_safety = 0
    for project in projects:
        # Base safety score
        safety = 88
        
        # Adjust based on risk level
        if project.risk_level == 'Low':
            safety += 5
        elif project.risk_level == 'High':
            safety -= 8
        elif project.risk_level == 'Critical':
            safety -= 15
        
        # Adjust based on safety requirements
        if project.safety_requirements == 'Enhanced':
            safety += 3
        elif project.safety_requirements == 'High Security':
            safety += 5
        elif project.safety_requirements == 'Specialized':
            safety += 7
        
        # Active projects with issues might have lower safety scores
        if project.status == 'Active':
            # Check for issues in DPRs
            recent_dprs = DailyProductionReport.query.filter(
                DailyProductionReport.project_id == project.id,
                DailyProductionReport.issues.isnot(None)
            ).limit(5).all()
            
            if len(recent_dprs) > 2:  # Multiple recent issues
                safety -= 5
        
        total_safety += min(100, max(70, safety))
    
    return round(total_safety / len(projects), 1)


def calculate_real_resource_utilization(projects):
    """Calculate resource allocation and utilization based on actual assignments"""
    if not projects:
        return {'allocation': {}, 'utilization': {}}
    
    # Get actual staff and employee assignments
    from models import EmployeeAssignment
    
    # Get staff assignments (no status field)
    staff_assignments = StaffAssignment.query.filter(
        StaffAssignment.project_id.in_([p.id for p in projects])
    ).all()
    
    # Get employee assignments (has status field)
    employee_assignments = EmployeeAssignment.query.filter(
        EmployeeAssignment.project_id.in_([p.id for p in projects])
    ).all()
    
    # Categorize by role
    allocation = {
        'engineers': 0,
        'supervisors': 0,
        'skilled_workers': 0,
        'general_labor': 0,
        'equipment_operators': 0
    }
    
    utilization = allocation.copy()
    
    # Process staff assignments (assume all active since no status field)
    for assignment in staff_assignments:
        if assignment.role:
            role_lower = assignment.role.lower()
            if 'engineer' in role_lower:
                allocation['engineers'] += 1
                utilization['engineers'] += 1  # Assume active
            elif 'supervisor' in role_lower or 'manager' in role_lower:
                allocation['supervisors'] += 1
                utilization['supervisors'] += 1
            elif 'skilled' in role_lower or 'technician' in role_lower:
                allocation['skilled_workers'] += 1
                utilization['skilled_workers'] += 1
            elif 'operator' in role_lower:
                allocation['equipment_operators'] += 1
                utilization['equipment_operators'] += 1
            else:
                allocation['general_labor'] += 1
                utilization['general_labor'] += 1
    
    # Process employee assignments (with status field)
    for assignment in employee_assignments:
        if assignment.role:
            role_lower = assignment.role.lower()
            if 'engineer' in role_lower:
                allocation['engineers'] += 1
                if assignment.status == 'Active':
                    utilization['engineers'] += 1
            elif 'supervisor' in role_lower or 'manager' in role_lower:
                allocation['supervisors'] += 1
                if assignment.status == 'Active':
                    utilization['supervisors'] += 1
            elif 'skilled' in role_lower or 'technician' in role_lower:
                allocation['skilled_workers'] += 1
                if assignment.status == 'Active':
                    utilization['skilled_workers'] += 1
            elif 'operator' in role_lower:
                allocation['equipment_operators'] += 1
                if assignment.status == 'Active':
                    utilization['equipment_operators'] += 1
            else:
                allocation['general_labor'] += 1
                if assignment.status == 'Active':
                    utilization['general_labor'] += 1
    
    # If no assignments found, return default values
    if sum(allocation.values()) == 0:
        allocation = {'engineers': 15, 'supervisors': 8, 'skilled_workers': 45, 'general_labor': 120, 'equipment_operators': 25}
        utilization = {'engineers': 13, 'supervisors': 7, 'skilled_workers': 35, 'general_labor': 106, 'equipment_operators': 24}
    
    return {'allocation': allocation, 'utilization': utilization}


def calculate_real_material_efficiency(projects):
    """Calculate material efficiency based on budget performance"""
    if not projects:
        return 92
    
    total_efficiency = 0
    project_count = 0
    
    for project in projects:
        if project.status in ['Active', 'Completed']:
            # Check budget efficiency for material categories
            material_budgets = Budget.query.filter(
                Budget.project_id == project.id,
                Budget.category.in_(['materials', 'procurement', 'supplies'])
            ).all()
            
            if material_budgets:
                for budget in material_budgets:
                    if budget.allocated_amount > 0:
                        usage_efficiency = (budget.allocated_amount - budget.spent_amount) / budget.allocated_amount
                        efficiency = 85 + (usage_efficiency * 15)  # Convert to percentage
                        total_efficiency += min(98, max(75, efficiency))
                        project_count += 1
            else:
                # Use project-level budget if no material budgets
                if project.budget and project.progress:
                    efficiency = 90 + (project.progress / 100 * 8)  # Higher progress = better efficiency
                    total_efficiency += min(98, max(80, efficiency))
                    project_count += 1
    
    if project_count == 0:
        return 92  # Default value
    
    return round(total_efficiency / project_count, 1)


def calculate_real_equipment_utilization(projects):
    """Calculate equipment utilization based on project data"""
    if not projects:
        return 87
    
    # Base calculation on active projects
    active_projects = [p for p in projects if p.status == 'Active']
    
    if not active_projects:
        return 87
    
    # Higher utilization for projects with good progress
    total_utilization = 0
    for project in active_projects:
        if project.progress:
            if project.progress >= 80:
                utilization = 92
            elif project.progress >= 60:
                utilization = 88
            elif project.progress >= 40:
                utilization = 85
            else:
                utilization = 80
        else:
            utilization = 87
        
        # Adjust based on budget performance
        project_budgets = Budget.query.filter_by(project_id=project.id).all()
        if project_budgets:
            total_allocated = sum(b.allocated_amount for b in project_budgets)
            total_spent = sum(b.spent_amount for b in project_budgets)
            if total_allocated > 0:
                budget_efficiency = total_spent / total_allocated
                if budget_efficiency < 0.8:  # Under budget = efficient equipment use
                    utilization += 3
                elif budget_efficiency > 1.2:  # Over budget = inefficient
                    utilization -= 5
        
        total_utilization += min(95, max(70, utilization))
    
    return round(total_utilization / len(active_projects), 1)


def calculate_real_portfolio_risk_score(projects):
    """Calculate portfolio risk based on actual project risk levels"""
    if not projects:
        return 4
    
    risk_mapping = {
        'Low': 2,
        'Medium': 4,
        'High': 7,
        'Critical': 9
    }
    
    total_risk = 0
    for project in projects:
        project_risk = risk_mapping.get(project.risk_level, 4)
        
        # Adjust based on budget overruns
        project_budgets = Budget.query.filter_by(project_id=project.id).all()
        if project_budgets:
            for budget in project_budgets:
                if budget.usage_percentage > 90:
                    project_risk += 1
        
        # Adjust based on project status
        if project.status == 'Active' and project.progress and project.progress < 50:
            project_risk += 0.5  # Behind schedule increases risk
        
        total_risk += min(10, project_risk)
    
    return round(total_risk / len(projects), 1)


def calculate_real_weather_impact(projects):
    """Calculate weather delays from actual DPR data"""
    if not projects:
        return 0
    
    from datetime import datetime, timedelta
    
    # Get current month's DPRs
    month_start = datetime.now().replace(day=1)
    
    dprs_with_weather_issues = DailyProductionReport.query.filter(
        DailyProductionReport.project_id.in_([p.id for p in projects]),
        DailyProductionReport.created_at >= month_start,
        DailyProductionReport.issues.like('%weather%')
    ).count()
    
    return dprs_with_weather_issues


def calculate_days_without_incident(projects):
    """Calculate days without safety incidents from DPR data"""
    if not projects:
        return 0
    
    from datetime import datetime, timedelta
    
    # Check last 90 days for incidents
    ninety_days_ago = datetime.now() - timedelta(days=90)
    
    # Look for DPRs with safety-related issues
    last_incident = DailyProductionReport.query.filter(
        DailyProductionReport.project_id.in_([p.id for p in projects]),
        DailyProductionReport.created_at >= ninety_days_ago,
        DailyProductionReport.issues.like('%incident%') | 
        DailyProductionReport.issues.like('%accident%') |
        DailyProductionReport.issues.like('%injury%') |
        DailyProductionReport.issues.like('%safety%')
    ).order_by(DailyProductionReport.created_at.desc()).first()
    
    if last_incident:
        days_since = (datetime.now() - last_incident.created_at).days
        return max(0, days_since)
    else:
        # No incidents found in last 90 days
        return 90


def generate_real_performance_matrix(projects):
    """Generate performance matrix using real project data"""
    matrix_data = []
    
    for project in projects[:10]:  # Limit display
        # Get real budget data
        project_budgets = Budget.query.filter_by(project_id=project.id).all()
        planned_value = sum(b.allocated_amount for b in project_budgets) or project.budget or 0
        actual_cost = sum(b.spent_amount for b in project_budgets) or 0
        
        # Calculate earned value
        if project.progress and planned_value:
            earned_value = planned_value * (project.progress / 100.0)
        elif project.status == 'Completed':
            earned_value = planned_value
        else:
            earned_value = 0
        
        # Calculate performance indices
        spi = earned_value / planned_value if planned_value > 0 else 0
        cpi = earned_value / actual_cost if actual_cost > 0 else 0
        
        matrix_data.append({
            'project_name': project.name,
            'budget': planned_value,
            'spi': round(spi, 3),
            'cpi': round(cpi, 3),
            'quality': calculate_real_quality_index([project]),
            'safety': calculate_real_safety_score([project]),
            'status': project.status,
            'progress': project.progress or 0,
            'risk_level': project.risk_level or 'Medium'
        })
    
    return matrix_data


@project_bp.route('/analytics/data')
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def analytics_data():
    """API endpoint for real-time dashboard updates"""
    from datetime import datetime
    
    try:
        # Get user's accessible projects
        accessible_projects = get_user_accessible_projects(current_user)
        
        # Calculate current metrics
        total_pv = sum(p.budget or 0 for p in accessible_projects)
        total_ev = sum(calculate_earned_value(p) for p in accessible_projects)
        total_ac = sum(calculate_actual_cost(p) for p in accessible_projects)
        
        data = {
            'timestamp': datetime.now().isoformat(),
            'spi': round(total_ev / total_pv if total_pv > 0 else 0, 3),
            'cpi': round(total_ev / total_ac if total_ac > 0 else 0, 3),
            'portfolio_value': total_pv,
            'active_projects': len([p for p in accessible_projects if p.status == 'Active']),
            'quality_index': calculate_portfolio_quality_index(accessible_projects),
            'safety_score': calculate_portfolio_safety_score(accessible_projects),
            'weather_delays': sum(calculate_weather_impact(p) for p in accessible_projects),
            'evm_data': {
                'pv': [int(total_pv * i / 12) for i in range(1, 13)],
                'ev': [int(total_ev * i / 12) for i in range(1, 13)],
                'ac': [int(total_ac * i / 12) for i in range(1, 13)]
            }
        }
        
        return jsonify(data)
        
    except Exception as e:
        current_app.logger.error(f"Analytics data API error: {str(e)}")
        return jsonify({'error': 'Failed to fetch analytics data'}), 500


# Construction PMO Calculation Functions
def calculate_earned_value(project):
    """Calculate Earned Value based on project completion percentage"""
    if not project.budget:
        return 0
    
    if project.status == 'Completed':
        return project.budget
    elif project.status == 'Active':
        # Use project progress if available, otherwise simulate based on timeline
        if hasattr(project, 'progress') and project.progress:
            return int(project.budget * (project.progress / 100.0))
        
        # Simulate progress based on project timeline
        from datetime import datetime
        if hasattr(project, 'start_date') and project.start_date:
            days_elapsed = (datetime.now().date() - project.start_date).days
            if hasattr(project, 'end_date') and project.end_date:
                total_days = (project.end_date - project.start_date).days
                if total_days > 0:
                    progress = min(days_elapsed / total_days, 0.9)  # Cap at 90% for active projects
                    return int(project.budget * progress)
        
        # Default to 60% for active projects without dates
        return int(project.budget * 0.6)
    else:
        return 0


def calculate_actual_cost(project):
    """Calculate Actual Cost incurred"""
    if not project.budget:
        return 0
    
    if project.status == 'Completed':
        # Completed projects typically have slight cost overrun
        return int(project.budget * 1.05)
    elif project.status == 'Active':
        # Active projects have spent proportional to earned value with some variance
        earned_value = calculate_earned_value(project)
        cost_efficiency = 0.95  # Assuming 5% cost efficiency
        return int(earned_value / cost_efficiency)
    else:
        return 0


def calculate_quality_index(project):
    """Construction Quality Index (0-100)"""
    base_quality = 85  # Base quality score
    
    # Adjust based on project characteristics
    if project.status == 'Completed':
        return base_quality + 10  # Completed projects typically have higher quality scores
    elif project.status == 'Active':
        return base_quality + (hash(str(project.id)) % 10)  # Simulate variance
    else:
        return base_quality


def calculate_safety_score(project):
    """Construction Safety Score (0-100)"""
    base_safety = 88  # Base safety score
    
    # Simulate variance based on project characteristics
    if project.status == 'Active':
        variance = (hash(str(project.id) + 'safety') % 8) - 4  # +/- 4 points variance
        return max(75, min(100, base_safety + variance))
    
    return base_safety


def calculate_weather_impact(project):
    """Weather delay days this month"""
    if project.status == 'Active':
        return (hash(str(project.id) + 'weather') % 6)  # 0-5 delay days
    return 0


def calculate_material_efficiency(project):
    """Material utilization efficiency percentage"""
    base_efficiency = 92
    if project.status == 'Active':
        variance = (hash(str(project.id) + 'material') % 6) - 3  # +/- 3% variance
        return max(85, min(98, base_efficiency + variance))
    return base_efficiency


def calculate_equipment_utilization(project):
    """Equipment utilization percentage"""
    base_utilization = 87
    if project.status == 'Active':
        variance = (hash(str(project.id) + 'equipment') % 8) - 4  # +/- 4% variance
        return max(75, min(95, base_utilization + variance))
    return base_utilization


def calculate_project_risk_score(project):
    """Project risk score (1-10, where 10 is highest risk)"""
    base_risk = 4  # Medium risk
    
    # Adjust based on project budget (larger projects = higher risk)
    if project.budget:
        if project.budget > 10000000:  # $10M+
            base_risk += 2
        elif project.budget > 5000000:  # $5M+
            base_risk += 1
    
    # Active projects have higher current risk
    if project.status == 'Active':
        base_risk += 1
    
    return min(10, base_risk)


def get_critical_path_tasks(project):
    """Get critical path tasks for the project"""
    # In a real system, this would analyze the project schedule
    # For simulation, return sample critical tasks
    critical_tasks = [
        {'name': 'Foundation Work', 'duration': 14, 'status': 'completed'},
        {'name': 'Structural Steel', 'duration': 21, 'status': 'in_progress'},
        {'name': 'Electrical Rough-in', 'duration': 10, 'status': 'pending'},
        {'name': 'Final Inspection', 'duration': 3, 'status': 'pending'}
    ]
    
    return critical_tasks


def generate_performance_matrix(projects):
    """Generate performance matrix data for all projects"""
    matrix_data = []
    
    for project in projects[:10]:  # Limit to first 10 projects for display
        earned_value = calculate_earned_value(project)
        actual_cost = calculate_actual_cost(project)
        planned_value = project.budget or 0
        
        spi = earned_value / planned_value if planned_value > 0 else 0
        cpi = earned_value / actual_cost if actual_cost > 0 else 0
        
        matrix_data.append({
            'project_name': project.name,
            'budget': planned_value,
            'spi': round(spi, 3),
            'cpi': round(cpi, 3),
            'quality': calculate_quality_index(project),
            'safety': calculate_safety_score(project),
            'status': project.status,
            'risk_level': 'High' if calculate_project_risk_score(project) > 7 else 
                        'Medium' if calculate_project_risk_score(project) > 4 else 'Low'
        })
    
    return matrix_data


def calculate_portfolio_quality_index(projects):
    """Calculate overall portfolio quality index"""
    if not projects:
        return 0
    
    total_quality = sum(calculate_quality_index(p) for p in projects)
    return round(total_quality / len(projects), 1)


def calculate_portfolio_safety_score(projects):
    """Calculate overall portfolio safety score"""
    if not projects:
        return 0
    
    total_safety = sum(calculate_safety_score(p) for p in projects)
    return round(total_safety / len(projects), 1)


def calculate_portfolio_material_efficiency(projects):
    """Calculate overall portfolio material efficiency"""
    if not projects:
        return 0
    
    total_efficiency = sum(calculate_material_efficiency(p) for p in projects)
    return round(total_efficiency / len(projects), 1)


def calculate_portfolio_equipment_utilization(projects):
    """Calculate overall portfolio equipment utilization"""
    if not projects:
        return 0
    
    total_utilization = sum(calculate_equipment_utilization(p) for p in projects)
    return round(total_utilization / len(projects), 1)


def calculate_portfolio_risk_score(projects):
    """Calculate overall portfolio risk score"""
    if not projects:
        return 0
    
    total_risk = sum(calculate_project_risk_score(p) for p in projects)
    return round(total_risk / len(projects), 1)


# Calendar Page
@project_bp.route('/calendar')
@login_required
def calendar():
    try:
        # Get user's accessible projects
        accessible_projects = get_user_accessible_projects(current_user)
        
        # Get selected project from query parameter
        selected_project_id = request.args.get('project_id', type=int)
        if selected_project_id and selected_project_id in [p['id'] for p in accessible_projects]:
            # Load events for selected project
            events = get_project_calendar_events(selected_project_id)
            selected_project = Project.query.get(selected_project_id)
        else:
            events = []
            selected_project = None
            
        return render_template('projects/calendar.html', 
                             accessible_projects=accessible_projects,
                             selected_project=selected_project,
                             calendar={'events': events})
    except Exception as e:
        current_app.logger.error(f"Calendar page error: {str(e)}")
        return render_template('error.html', error="Failed to load calendar"), 500

@project_bp.route('/calendar/events/<int:project_id>')
@login_required
def get_calendar_events(project_id):
    """API endpoint to get calendar events for a specific project"""
    try:
        # Verify user has access to this project
        accessible_projects = get_user_accessible_projects(current_user)
        if project_id not in [p['id'] for p in accessible_projects]:
            return jsonify({'error': 'Access denied'}), 403
            
        events = get_project_calendar_events(project_id)
        return jsonify({'status': 'success', 'events': events})
    except Exception as e:
        current_app.logger.error(f"Error loading calendar events: {str(e)}")
        return jsonify({'error': 'Failed to load events'}), 500

def get_project_calendar_events(project_id):
    """Helper function to get all calendar events for a project"""
    events = []
    
    # Get the project
    project = Project.query.get(project_id)
    if not project:
        return events
    
    # Project start and end dates
    if project.start_date:
        events.append({
            'id': f"project-start-{project.id}",
            'title': f"🏗️ {project.name} - Start",
            'start': project.start_date.strftime('%Y-%m-%d'),
            'type': 'project-start',
            'backgroundColor': '#10B981',
            'borderColor': '#059669',
            'description': f"Project start date"
        })
    
    if project.end_date:
        events.append({
            'id': f"project-end-{project.id}",
            'title': f"🏁 {project.name} - End",
            'start': project.end_date.strftime('%Y-%m-%d'),
            'type': 'project-end',
            'backgroundColor': '#EF4444',
            'borderColor': '#DC2626',
            'description': f"Project end date"
        })
    
    # Milestones
    milestones = Milestone.query.filter_by(project_id=project_id).all()
    for milestone in milestones:
        if milestone.due_date:
            color = '#8B5CF6' if milestone.status == 'Pending' else '#10B981' if milestone.status == 'Completed' else '#F59E0B'
            events.append({
                'id': f"milestone-{milestone.id}",
                'title': f"🎯 {milestone.title}",
                'start': milestone.due_date.strftime('%Y-%m-%d'),
                'type': 'milestone',
                'backgroundColor': color,
                'borderColor': color,
                'description': f"Milestone: {milestone.title} - Status: {milestone.status}"
            })
    
    # Tasks with due dates
    tasks = Task.query.filter_by(project_id=project_id).filter(Task.due_date.isnot(None)).all()
    for task in tasks:
        color = '#6B7280' if task.status == 'pending' else '#10B981' if task.status == 'completed' else '#F59E0B'
        events.append({
            'id': f"task-{task.id}",
            'title': f"📋 {task.title}",
            'start': task.due_date.strftime('%Y-%m-%d'),
            'type': 'task',
            'backgroundColor': color,
            'borderColor': color,
            'description': f"Task: {task.title} - Status: {task.status}"
        })
    
    # Schedules
    schedules = Schedule.query.filter_by(project_id=project_id).all()
    for schedule in schedules:
        events.append({
            'id': f"schedule-{schedule.id}",
            'title': f"📅 {schedule.title}",
            'start': schedule.start_time.strftime('%Y-%m-%dT%H:%M:%S'),
            'end': schedule.end_time.strftime('%Y-%m-%dT%H:%M:%S'),
            'type': 'schedule',
            'backgroundColor': '#3B82F6',
            'borderColor': '#2563EB',
            'description': f"Schedule: {schedule.title} - Type: {schedule.type}"
        })
    
    # DPR submissions for the project
    dprs = DailyProductionReport.query.filter_by(project_id=project_id).all()
    for dpr in dprs:
        if dpr.completed_at:  # Use completed_at instead of submitted_at
            events.append({
                'id': f"dpr-{dpr.id}",
                'title': f"🏗️ DPR Submitted",
                'start': dpr.completed_at.strftime('%Y-%m-%d'),
                'type': 'dpr',
                'backgroundColor': '#059669',
                'borderColor': '#047857',
                'description': f"Daily Production Report submitted for {dpr.completed_at.strftime('%B %d, %Y')}"
            })
    
    # Project expenses (based on staff assignments)
    project_staff = StaffAssignment.query.filter_by(project_id=project_id).all()
    staff_ids = [assignment.user_id for assignment in project_staff]
    
    if staff_ids:
        project_expenses = Expense.query.filter(Expense.user_id.in_(staff_ids)).order_by(
            Expense.date.desc()
        ).limit(20).all()  # Recent 20 expenses
        
        for expense in project_expenses:
            events.append({
                'id': f"expense-{expense.id}",
                'title': f"💰 Expense: ${expense.amount:.2f}",
                'start': expense.date.strftime('%Y-%m-%d'),
                'type': 'expense',
                'backgroundColor': '#DC2626',
                'borderColor': '#B91C1C',
                'description': f"Expense: {expense.description} - Amount: ${expense.amount:.2f} - Category: {expense.category}"
            })
    
    return events


# Staff Management - Filter by user's accessible projects
@project_bp.route('/staff')
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER, Roles.PROJECT_STAFF, Roles.HQ_FINANCE, Roles.HQ_PROCUREMENT])
def staff():
    try:
        # Get user's accessible projects
        accessible_projects = get_user_accessible_projects(current_user)
        accessible_project_ids = [p.id for p in accessible_projects]
        
        current_app.logger.info(f"User {current_user.id} ({current_user.role}) accessing staff for {len(accessible_projects)} projects")
        
        # Filter project managers and team members based on accessible projects
        managers_data = []
        members_data = []
        
        if accessible_projects:
            # Get project managers for accessible projects only
            accessible_project_managers = set()
            for project in accessible_projects:
                if project.project_manager:
                    accessible_project_managers.add(project.project_manager)
            
            # Query managers who manage accessible projects
            if accessible_project_managers:
                project_managers = User.query.filter(
                    User.name.in_(accessible_project_managers)
                ).all()
                
                for manager in project_managers:
                    # Only show projects that the current user has access to
                    manager_projects = [p for p in accessible_projects if p.project_manager == manager.name]
                    if manager_projects:
                        managers_data.append({
                            'id': manager.id,
                            'name': manager.name,
                            'role': manager.role,
                            'projects': [{'id': p.id, 'name': p.name} for p in manager_projects]
                        })
            
            # Get team members assigned to accessible projects
            staff_assignments = StaffAssignment.query.filter(
                StaffAssignment.project_id.in_(accessible_project_ids)
            ).all()
            
            # Group assignments by staff member
            staff_projects = {}
            for assignment in staff_assignments:
                if assignment.staff_id not in staff_projects:
                    staff_projects[assignment.staff_id] = []
                project = Project.query.get(assignment.project_id)
                if project:
                    staff_projects[assignment.staff_id].append({'id': project.id, 'name': project.name})
            
            # Get user details for staff members
            if staff_projects:
                team_members = User.query.filter(
                    User.id.in_(staff_projects.keys())
                ).all()
                
                for member in team_members:
                    if member.id in staff_projects:
                        members_data.append({
                            'id': member.id,
                            'name': member.name,
                            'role': member.role,
                            'projects': staff_projects[member.id]
                        })
        
        return render_template('projects/staff.html', 
                               project_managers=managers_data,
                               team_members=members_data,
                               accessible_projects=accessible_projects,
                               user_role=current_user.role)
    except Exception as e:
        current_app.logger.error(f"Staff page error: {str(e)}")
        return render_template('error.html', error="Failed to load staff page"), 500


# Documents Page (File upload/download) - Filter by accessible projects
@project_bp.route('/documents', methods=['GET', 'POST'])
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER, Roles.PROJECT_STAFF, Roles.HQ_FINANCE, Roles.HQ_PROCUREMENT])
def documents():
    try:
        # Get user's accessible projects
        accessible_projects = get_user_accessible_projects(current_user)
        accessible_project_ids = [p.id for p in accessible_projects]
        
        # Only SUPER_HQ and PROJECT_MANAGER can upload documents
        can_upload = current_user.has_role(Roles.SUPER_HQ) or current_user.has_role(Roles.PROJECT_MANAGER)
        
        # Get selected project from request
        selected_project_id = request.args.get('project_id') or request.form.get('project_id')
        selected_project = None
        project_documents = []
        document_stats = {'total': 0, 'approved': 0, 'pending': 0, 'rejected': 0}
        
        if selected_project_id:
            try:
                selected_project_id = int(selected_project_id)
                if selected_project_id in accessible_project_ids:
                    selected_project = Project.query.get(selected_project_id)
            except (ValueError, TypeError):
                selected_project_id = None
        
        # Handle POST request (file upload)
        if request.method == 'POST':
            if not can_upload:
                flash('You do not have permission to upload documents', 'error')
                return redirect(url_for('project.documents', project_id=selected_project_id))
                
            file = request.files.get('file')
            title = request.form.get('title')
            category = request.form.get('category')
            project_id = request.form.get('project_id')
            
            # Validate required fields
            if not file or not title or not category or not project_id:
                flash('File, title, category, and project are required', 'error')
                return redirect(url_for('project.documents', project_id=project_id))
                
            # Validate file
            if file.filename == '':
                flash('No file selected', 'error')
                return redirect(url_for('project.documents', project_id=project_id))
                
            # Validate file size (limit to 50MB)
            file.seek(0, 2)  # Seek to end of file
            file_size = file.tell()  # Get current position (file size)
            file.seek(0)  # Reset file pointer to beginning
            
            if file_size > 50 * 1024 * 1024:  # 50MB limit
                flash('File size must be less than 50MB', 'error')
                return redirect(url_for('project.documents', project_id=project_id))
            
            # Validate project access
            if int(project_id) not in accessible_project_ids:
                flash('You do not have access to the selected project', 'error')
                return redirect(url_for('project.documents'))
                
            # Get project details
            project = Project.query.get(project_id)
            if not project:
                flash('Project not found', 'error')
                return redirect(url_for('project.documents'))
            
            # Validate file type (basic validation)
            allowed_extensions = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'jpg', 'jpeg', 'png', 'gif', 'zip', 'rar', 'txt', 'csv'}
            file_ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
            if file_ext not in allowed_extensions:
                flash(f'File type .{file_ext} not allowed. Allowed types: {", ".join(allowed_extensions)}', 'error')
                return redirect(url_for('project.documents', project_id=project_id))
            
            # Create secure filename with timestamp to avoid conflicts
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_filename = secure_filename(file.filename)
            if not safe_filename:
                safe_filename = f'document.{file_ext}'
            filename_parts = safe_filename.rsplit('.', 1)
            if len(filename_parts) == 2:
                secure_name = f"{filename_parts[0]}_{timestamp}.{filename_parts[1]}"
            else:
                secure_name = f"{safe_filename}_{timestamp}"
            
            # Create project-specific directory
            project_upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'projects', str(project_id))
            os.makedirs(project_upload_dir, exist_ok=True)
            
            # Save file
            filepath = os.path.join(project_upload_dir, secure_name)
            try:
                file.save(filepath)
            except Exception as e:
                current_app.logger.error(f"Failed to save file: {str(e)}")
                flash('Failed to save file', 'error')
                return redirect(url_for('project.documents', project_id=project_id))
            
            # Create document record
            document = Document(
                filename=secure_name,
                category=category,
                project_id=int(project_id),
                uploaded_at=datetime.now(),
                uploader_id=current_user.id,
                status='pending',
                size=file_size
            )
            
            try:
                db.session.add(document)
                db.session.commit()
                
                current_app.logger.info(f"Document '{title}' uploaded by user {current_user.id} for project {project_id}")
                flash(f'Document "{title}" uploaded successfully!', 'success')
                return redirect(url_for('project.documents', project_id=project_id))
                
            except Exception as e:
                db.session.rollback()
                # Remove file if database operation failed
                try:
                    os.remove(filepath)
                except:
                    pass
                current_app.logger.error(f"Database error during document upload: {str(e)}")
                flash('Failed to save document information', 'error')
                return redirect(url_for('project.documents', project_id=project_id))
        
        # GET request - load project documents
        if selected_project:
            # Get filter parameters
            category_filter = request.args.get('category_filter', '')
            status_filter = request.args.get('status_filter', '')
            
            # Base query for project documents
            docs_query = Document.query.filter_by(project_id=selected_project.id)
            
            # Apply filters
            if category_filter:
                docs_query = docs_query.filter_by(category=category_filter)
            if status_filter:
                docs_query = docs_query.filter_by(status=status_filter)
            
            # Get filtered documents
            project_documents = docs_query.order_by(Document.uploaded_at.desc()).all()
            
            # Calculate statistics for all documents in project (not filtered)
            all_project_docs = Document.query.filter_by(project_id=selected_project.id).all()
            document_stats = {
                'total': len(all_project_docs),
                'approved': len([d for d in all_project_docs if d.status == 'approved']),
                'pending': len([d for d in all_project_docs if d.status == 'pending']),
                'rejected': len([d for d in all_project_docs if d.status == 'rejected'])
            }
        
        # Get available categories from all documents
        all_categories = db.session.query(Document.category).distinct().all()
        available_categories = [c[0] for c in all_categories] if all_categories else [
            'Contract', 'Technical Drawing', 'Report', 'Certificate', 'Specification', 'BOQ', 'Other'
        ]
        
        # Get filter values for template
        category_filter = request.args.get('category_filter', '')
        status_filter = request.args.get('status_filter', '')
        
        return render_template('projects/documents.html',
                             accessible_projects=accessible_projects,
                             selected_project=selected_project,
                             project_documents=project_documents,
                             document_stats=document_stats,
                             available_categories=available_categories,
                             category_filter=category_filter,
                             status_filter=status_filter,
                             can_upload=can_upload,
                             user_role=current_user.role)
                             
    except Exception as e:
        current_app.logger.error(f"Documents page error: {str(e)}")
        flash('Failed to load documents page', 'error')
        return redirect(url_for('project.list_projects'))


# Get documents for a specific project (API endpoint)
@project_bp.route('/documents/project/<int:project_id>')
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER, Roles.PROJECT_STAFF, Roles.HQ_FINANCE, Roles.HQ_PROCUREMENT])
def get_project_documents(project_id):
    try:
        # Get user's accessible projects
        accessible_projects = get_user_accessible_projects(current_user)
        accessible_project_ids = [p.id for p in accessible_projects]
        
        # Validate project access
        if project_id not in accessible_project_ids:
            return jsonify({'error': 'Access denied to this project'}), 403
        
        # Get documents for the project
        documents = Document.query.filter_by(project_id=project_id).order_by(Document.uploaded_at.desc()).all()
        
        # Convert to JSON with proper metadata
        documents_data = []
        for doc in documents:
            # Get uploader name safely
            uploader_name = 'Unknown'
            try:
                if doc.uploader_id:
                    uploader = User.query.get(doc.uploader_id)
                    if uploader:
                        uploader_name = f"{uploader.first_name} {uploader.last_name}".strip() or uploader.username or uploader.email
            except:
                pass
                
            documents_data.append({
                'id': doc.id,
                'filename': doc.filename,
                'category': doc.category,
                'uploaded_at': doc.uploaded_at.isoformat() if doc.uploaded_at else None,
                'uploader_name': uploader_name,
                'status': doc.status or 'pending',
                'size': doc.size or 0
            })
        
        return jsonify({'documents': documents_data})
        
    except Exception as e:
        current_app.logger.error(f"Error loading project documents: {str(e)}")
        return jsonify({'error': 'Failed to load documents'}), 500


# Download document
@project_bp.route('/documents/<int:doc_id>/download')
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER, Roles.PROJECT_STAFF, Roles.HQ_FINANCE, Roles.HQ_PROCUREMENT])
def download_document(doc_id):
    try:
        document = Document.query.get_or_404(doc_id)
        
        # Check project access
        if document.project_id:
            accessible_projects = get_user_accessible_projects(current_user)
            accessible_project_ids = [p.id for p in accessible_projects]
            
            if document.project_id not in accessible_project_ids:
                flash("You do not have access to this document", "error")
                return redirect(url_for('project.documents'))
        
        # Try project-specific path first, then fallback to general uploads
        project_file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'projects', str(document.project_id), document.filename)
        general_file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], document.filename)
        
        file_path = None
        if os.path.exists(project_file_path):
            file_path = project_file_path
        elif os.path.exists(general_file_path):
            file_path = general_file_path
        
        if file_path and os.path.exists(file_path):
            # Use original filename for download (without timestamp)
            original_filename = document.filename
            # Try to extract original name by removing timestamp pattern
            parts = document.filename.rsplit('_', 1)
            if len(parts) == 2:
                timestamp_part = parts[1]
                # Check if timestamp part matches our pattern (YYYYMMDD_HHMMSS.ext)
                if len(timestamp_part) >= 15 and timestamp_part[:8].isdigit():
                    original_filename = f"{parts[0]}.{timestamp_part.split('.', 1)[-1]}" if '.' in timestamp_part else parts[0]
            
            return send_file(file_path, as_attachment=True, download_name=original_filename)
        else:
            flash("File not found", "error")
            return redirect(url_for('project.documents'))
            
    except Exception as e:
        current_app.logger.error(f"Error downloading document: {str(e)}")
        flash("Error downloading document", "error")
        return redirect(url_for('project.documents'))


# Delete document
@project_bp.route('/documents/<int:doc_id>/delete', methods=['POST'])
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def delete_document(doc_id):
    try:
        document = Document.query.get_or_404(doc_id)
        project_id = document.project_id
        
        # Check project access
        if document.project_id:
            accessible_projects = get_user_accessible_projects(current_user)
            accessible_project_ids = [p.id for p in accessible_projects]
            
            if document.project_id not in accessible_project_ids:
                flash('Access denied to this document', 'error')
                return redirect(url_for('project.documents', project_id=document.project_id))
        
        # Delete file from filesystem (try both locations)
        try:
            project_file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'projects', str(document.project_id), document.filename)
            general_file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], document.filename)
            
            # Remove from project-specific directory if exists
            if os.path.exists(project_file_path):
                os.remove(project_file_path)
                current_app.logger.info(f"Deleted file from project directory: {project_file_path}")
            
            # Remove from general directory if exists
            if os.path.exists(general_file_path):
                os.remove(general_file_path)
                current_app.logger.info(f"Deleted file from general directory: {general_file_path}")
                
        except Exception as e:
            current_app.logger.warning(f"Failed to delete file from filesystem: {str(e)}")
        
        # Delete from database
        db.session.delete(document)
        db.session.commit()
        
        flash('Document deleted successfully!', 'success')
        return redirect(url_for('project.documents', project_id=project_id))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting document: {str(e)}")
        flash('Failed to delete document', 'error')
        return redirect(url_for('project.documents'))





# Document Approval/Rejection
@project_bp.route('/documents/<int:doc_id>/approve', methods=['POST'])
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def approve_document(doc_id):
    try:
        document = Document.query.get_or_404(doc_id)
        
        # Check project access
        if document.project_id:
            accessible_projects = get_user_accessible_projects(current_user)
            accessible_project_ids = [p.id for p in accessible_projects]
            
            if document.project_id not in accessible_project_ids:
                flash('Access denied to this document', 'error')
                return redirect(url_for('project.documents', project_id=document.project_id))
        
        document.status = 'approved'
        document.approved_by = current_user.id
        document.approved_at = datetime.now()
        db.session.commit()
        
        flash('Document approved successfully!', 'success')
        return redirect(url_for('project.documents', project_id=document.project_id))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error approving document: {str(e)}")
        flash('Failed to approve document', 'error')
        return redirect(url_for('project.documents'))

@project_bp.route('/documents/<int:doc_id>/reject', methods=['POST'])
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def reject_document(doc_id):
    try:
        document = Document.query.get_or_404(doc_id)
        
        # Check project access
        if document.project_id:
            accessible_projects = get_user_accessible_projects(current_user)
            accessible_project_ids = [p.id for p in accessible_projects]
            
            if document.project_id not in accessible_project_ids:
                flash('Access denied to this document', 'error')
                return redirect(url_for('project.documents', project_id=document.project_id))
        
        document.status = 'rejected'
        document.approved_by = current_user.id
        document.approved_at = datetime.now()
        db.session.commit()
        
        flash('Document rejected successfully!', 'warning')
        return redirect(url_for('project.documents', project_id=document.project_id))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error rejecting document: {str(e)}")
        flash('Failed to reject document', 'error')
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

# Upload/View/Download Reports as PDF/Excel - Filter by accessible projects
@project_bp.route('/reports/upload', methods=['GET', 'POST'])
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER, Roles.PROJECT_STAFF, Roles.HQ_FINANCE, Roles.HQ_PROCUREMENT])
def upload_report():
    try:
        # Get user's accessible projects
        accessible_projects = get_user_accessible_projects(current_user)
        
        # Only SUPER_HQ and PROJECT_MANAGER can upload reports
        can_upload = current_user.has_role(Roles.SUPER_HQ) or current_user.has_role(Roles.PROJECT_MANAGER)
        
        if request.method == 'POST':
            if not can_upload:
                flash('You do not have permission to upload reports', 'error')
                return redirect(url_for('project.reports_index'))
                
            file = request.files.get('report_file')
            report_type = request.form.get('type')
            project_id = request.form.get('project_id')  # Optional project association
            
            if not file or not report_type:
                flash('File and report type required', 'error')
                return redirect(url_for('project.upload_report'))
                
            # Validate project access if project_id is provided
            if project_id:
                accessible_project_ids = [p.id for p in accessible_projects]
                if int(project_id) not in accessible_project_ids:
                    flash('You do not have access to the selected project', 'error')
                    return redirect(url_for('project.upload_report'))
            
            filename = secure_filename(file.filename)
            filepath = os.path.join(current_app.config['REPORTS_UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            report = Report(
                filename=filename, 
                type=report_type, 
                uploaded_at=datetime.now(), 
                uploader_id=current_user.id
            )
            
            # If Report model has project_id field, uncomment:
            # if project_id:
            #     report.project_id = int(project_id)
            
            db.session.add(report)
            db.session.commit()
            
            current_app.logger.info(f"Report uploaded by user {current_user.id} for project {project_id or 'general'}")
            flash('Report uploaded successfully!', 'success')
            return redirect(url_for('project.reports_index'))
            
        return render_template('projects/upload_report.html', 
                             accessible_projects=accessible_projects,
                             can_upload=can_upload,
                             user_role=current_user.role)
    except Exception as e:
        current_app.logger.error(f"Report upload error: {str(e)}")
        flash('Failed to upload report', 'error')
        return redirect(url_for('project.reports_index'))

@project_bp.route('/reports/download/<int:report_id>')
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER, Roles.PROJECT_STAFF, Roles.HQ_FINANCE, Roles.HQ_PROCUREMENT])
def download_report(report_id):
    try:
        report = Report.query.get_or_404(report_id)
        
        # Check if user has access to this report's project (if report has project_id)
        # For now, we'll allow download if user has any project access
        accessible_projects = get_user_accessible_projects(current_user)
        
        # If Report model has project_id field, add this check:
        # if hasattr(report, 'project_id') and report.project_id:
        #     accessible_project_ids = [p.id for p in accessible_projects]
        #     if report.project_id not in accessible_project_ids:
        #         flash('You do not have access to this report', 'error')
        #         return redirect(url_for('project.reports'))
        
        filepath = os.path.join(current_app.config['REPORTS_UPLOAD_FOLDER'], report.filename)
        current_app.logger.info(f"Report {report_id} downloaded by user {current_user.id}")
        return send_file(filepath, as_attachment=True)
    except Exception as e:
        current_app.logger.error(f"Report download error: {str(e)}")
        flash('Failed to download report', 'error')
        return redirect(url_for('project.reports_index'))


# Logout
@project_bp.route('/logout')
@login_required
def logout():
    try:
        # Log out the current user
        logout_user()
        # Clear the session
        session.clear()
        flash("You have been successfully logged out", "success")
        return redirect(url_for('login'))
    except Exception as e:
        current_app.logger.error(f"Logout error: {str(e)}")
        flash("Error during logout", "error")
        return redirect(url_for('login'))

# Settings
@project_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    try:
        if request.method == 'POST':
            form_type = request.args.get('form')
            
            if form_type == 'profile':
                name = request.form.get('name')
                email = request.form.get('email')
                department = request.form.get('department')
                
                user = User.query.get(current_user.id)
                if not user:
                    flash("User not found", "error")
                    return redirect(url_for('project.settings'))
                
                # Validate email uniqueness (excluding current user)
                existing_user = User.query.filter(User.email == email, User.id != current_user.id).first()
                if existing_user:
                    flash("Email address is already in use by another account", "error")
                    return redirect(url_for('project.settings'))
                
                user.name = name
                user.email = email
                if hasattr(user, 'department'):
                    user.department = department
                
                db.session.commit()
                flash("Profile updated successfully!", "success")
                
            elif form_type == 'security':
                current_password = request.form.get('current_password')
                new_password = request.form.get('new_password')
                confirm_password = request.form.get('confirm_password')
                
                user = User.query.get(current_user.id)
                if not user:
                    flash("User not found", "error")
                    return redirect(url_for('project.settings'))
                
                # Validate current password
                if not user.check_password(current_password):
                    flash("Current password is incorrect", "error")
                    return redirect(url_for('project.settings'))
                
                # Validate new password match
                if new_password != confirm_password:
                    flash("New passwords do not match", "error")
                    return redirect(url_for('project.settings'))
                
                # Validate password strength
                if len(new_password) < 8:
                    flash("Password must be at least 8 characters long", "error")
                    return redirect(url_for('project.settings'))
                
                user.set_password(new_password)
                db.session.commit()
                flash("Password updated successfully!", "success")
                
            elif form_type == 'notifications':
                email_notifications = request.form.get('email_notifications') == 'on'
                task_reminders = request.form.get('task_reminders') == 'on'
                project_updates = request.form.get('project_updates') == 'on'
                
                user = User.query.get(current_user.id)
                if not user:
                    flash("User not found", "error")
                    return redirect(url_for('project.settings'))
                
                # Store notification preferences (assuming these fields exist or we create them)
                if hasattr(user, 'email_notifications'):
                    user.email_notifications = email_notifications
                if hasattr(user, 'task_reminders'):
                    user.task_reminders = task_reminders
                if hasattr(user, 'project_updates'):
                    user.project_updates = project_updates
                
                db.session.commit()
                flash("Notification preferences updated successfully!", "success")
            
            return redirect(url_for('project.settings'))
        
        # GET request - render settings page
        user = User.query.get(current_user.id)
        if not user:
            flash("User not found", "error")
            return redirect(url_for('project.project_home'))
        
        # Get user's accessible projects for display
        accessible_projects = get_user_accessible_projects(current_user)
        
        user_data = {
            'name': user.name or '',
            'email': user.email or '',
            'role': user.role or 'Staff',
            'department': getattr(user, 'department', ''),
            'notification_preferences': {
                'email_notifications': getattr(user, 'email_notifications', True),
                'task_reminders': getattr(user, 'task_reminders', True),
                'project_updates': getattr(user, 'project_updates', True)
            }
        }
        
        return render_template('projects/settings.html', 
                             user=user_data, 
                             accessible_projects=accessible_projects)
                             
    except Exception as e:
        current_app.logger.error(f"Settings page error: {str(e)}")
        flash("Error processing settings request", "error")
        return render_template('error.html', error="Settings page error"), 500


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


# Staff Removal from Project - Only SUPER_HQ and Project Managers can remove staff
@project_bp.route('/<int:project_id>/remove-staff', methods=['POST'])
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def remove_staff(project_id):
    try:
        project = Project.query.get_or_404(project_id)
        
        # Check if user has permission to remove staff from this project
        is_manager = project.project_manager == current_user.name
        is_super_hq = current_user.has_role(Roles.SUPER_HQ)
        
        if not (is_manager or is_super_hq):
            current_app.logger.warning(f"User {current_user.id} denied staff removal access to project {project_id}")
            flash("You don't have permission to remove staff from this project.", "error")
            return redirect(url_for('project.project_details', project_id=project_id))
        
        staff_id = request.form.get('staff_id')
        assignment = StaffAssignment.query.filter_by(project_id=project_id, staff_id=staff_id).first()
        if assignment:
            db.session.delete(assignment)
            db.session.commit()
            current_app.logger.info(f"Staff {staff_id} removed from project {project_id} by user {current_user.id}")
            flash(f"Staff {staff_id} removed from project {project_id} successfully!", "success")
        else:
            flash("Staff assignment not found", "error")
        return redirect(url_for('project.project_details', project_id=project_id))
    except Exception as e:
        db.session.rollback()
        flash(f"Error removing staff: {str(e)}", "error")
        return redirect(url_for('project.project_details', project_id=project_id))


# ==================== API ENDPOINTS FOR PROJECT MANAGEMENT ====================

@project_bp.route('/api/projects/<int:project_id>/status', methods=['POST'])
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def update_project_status(project_id):
    """Update project status - Only SUPER_HQ and project managers can update their projects"""
    try:
        project = Project.query.get_or_404(project_id)
        
        # Check if user has permission to update this project
        is_manager = project.project_manager == current_user.name
        is_super_hq = current_user.has_role(Roles.SUPER_HQ)
        
        if not (is_manager or is_super_hq):
            current_app.logger.warning(f"User {current_user.id} denied status update access to project {project_id}")
            flash("You don't have permission to update this project's status.", "error")
            return redirect(url_for('project.project_details', project_id=project_id))
        
        data = request.get_json() if request.is_json else request.form
        new_status = data.get('status')
        
        if not new_status:
            flash("Status is required", "error")
            return redirect(url_for('project.project_details', project_id=project_id))
            
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
        
        current_app.logger.info(f"Project {project_id} status updated from {old_status} to {new_status} by user {current_user.id}")
        
        flash(f"Project status updated to {new_status} successfully!", "success")
        return redirect(url_for('project.project_details', project_id=project_id))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update project status error: {str(e)}", exc_info=True)
        flash("Error updating project status", "error")
        return redirect(url_for('project.project_details', project_id=project_id))

@project_bp.route('/api/projects/<int:project_id>/progress', methods=['POST'])
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def update_project_progress(project_id):
    """Update project progress - Only SUPER_HQ and project managers can update their projects"""
    try:
        project = Project.query.get_or_404(project_id)
        
        # Check if user has permission to update this project
        is_manager = project.project_manager == current_user.name
        is_super_hq = current_user.has_role(Roles.SUPER_HQ)
        
        if not (is_manager or is_super_hq):
            current_app.logger.warning(f"User {current_user.id} denied progress update access to project {project_id}")
            flash("You don't have permission to update this project's progress.", "error")
            return redirect(url_for('project.project_details', project_id=project_id))
        
        data = request.get_json() if request.is_json else request.form
        progress = float(data.get('progress', 0))
        
        if progress < 0 or progress > 100:
            flash("Progress must be between 0 and 100", "error")
            return redirect(url_for('project.project_details', project_id=project_id))
            
        old_progress = project.progress
        project.progress = progress
        project.updated_at = datetime.utcnow()
        
        # Auto-update status based on progress
        if progress == 100:
            project.status = 'Completed'
        elif progress > 0 and project.status == 'Planning':
            project.status = 'Active'
        
        db.session.commit()
        
        current_app.logger.info(f"Project {project_id} progress updated from {old_progress}% to {progress}% by user {current_user.id}")
        
        flash(f"Project progress updated to {progress}% successfully!", "success")
        return redirect(url_for('project.project_details', project_id=project_id))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update project progress error: {str(e)}", exc_info=True)
        flash("Error updating project progress", "error")
        return redirect(url_for('project.project_details', project_id=project_id))

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
        
        # Instead of returning JSON, redirect to project details which shows progress
        return redirect(url_for('project.project_details', project_id=project_id))
        
    except Exception as e:
        current_app.logger.error(f"Get project progress error: {str(e)}", exc_info=True)
        flash("Error fetching project progress", "error")
        return redirect(url_for('project.project_details', project_id=project_id))

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
        
        # Instead of returning JSON, redirect to project home with filtered results
        # You could store filter criteria in session if needed
        if search:
            flash(f"Found {len(projects)} projects matching '{search}'", "info")
        return redirect(url_for('project.project_home'))
        
    except Exception as e:
        current_app.logger.error(f"Filter projects error: {str(e)}", exc_info=True)
        flash("Error filtering projects", "error")
        return redirect(url_for('project.project_home'))

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
        
        # Instead of returning detailed JSON, redirect to project details page
        # which already shows all this information
        return redirect(url_for('project.project_details', project_id=project_id))
        
    except Exception as e:
        current_app.logger.error(f"Get project details error: {str(e)}", exc_info=True)
        flash("Error fetching project details", "error")
        return redirect(url_for('project.project_details', project_id=project_id))

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
        
        flash('Project statistics retrieved successfully', 'success')
        return redirect(url_for('project.project_home'))
        
    except Exception as e:
        current_app.logger.error(f"Get project statistics error: {str(e)}", exc_info=True)
        flash('Error fetching project statistics', 'error')
        return redirect(url_for('project.project_home'))


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
            flash('Staff ID and role are required', 'error')
            return redirect(url_for('project.project_details', project_id=project_id))
        
        # Check if staff is already assigned
        existing_assignment = StaffAssignment.query.filter_by(
            project_id=project_id, 
            staff_id=staff_id
        ).first()
        
        if existing_assignment:
            flash('Staff member is already assigned to this project', 'error')
            return redirect(url_for('project.project_details', project_id=project_id))
        
        # Get staff member details
        staff_member = User.query.get(staff_id)
        if not staff_member:
            flash('Staff member not found', 'error')
            return redirect(url_for('project.project_details', project_id=project_id))
        
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
        
        flash(f'{staff_member.name} has been assigned as {role}', 'success')
        return redirect(url_for('project.project_details', project_id=project_id))
        
    except Exception as e:
        current_app.logger.error(f"Error assigning staff: {str(e)}", exc_info=True)
        db.session.rollback()
        flash('An error occurred while assigning staff', 'error')
        return redirect(url_for('project.project_details', project_id=project_id))


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
            flash('Staff ID is required', 'error')
            return redirect(url_for('project.project_details', project_id=project_id))
        
        # Find and remove assignment
        assignment = StaffAssignment.query.filter_by(
            project_id=project_id,
            staff_id=staff_id
        ).first()
        
        if not assignment:
            flash('Staff assignment not found', 'error')
            return redirect(url_for('project.project_details', project_id=project_id))
        
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
        
        flash(f'{staff_name} has been removed from the project', 'success')
        return redirect(url_for('project.project_details', project_id=project_id))
        
    except Exception as e:
        current_app.logger.error(f"Error removing staff: {str(e)}", exc_info=True)
        db.session.rollback()
        flash('An error occurred while removing staff', 'error')
        return redirect(url_for('project.project_details', project_id=project_id))


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
            flash('Milestone name and due date are required', 'error')
            return redirect(url_for('project.project_details', project_id=project_id))
        
        # Parse due date
        try:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format', 'error')
            return redirect(url_for('project.project_details', project_id=project_id))
        
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
        
        flash(f'Milestone "{milestone_name}" has been created', 'success')
        return redirect(url_for('project.project_details', project_id=project_id))
        
    except Exception as e:
        current_app.logger.error(f"Error adding milestone: {str(e)}", exc_info=True)
        db.session.rollback()
        flash('An error occurred while adding milestone', 'error')
        return redirect(url_for('project.project_details', project_id=project_id))


@project_bp.route('/<int:project_id>/milestones/<int:milestone_id>', methods=['DELETE'])
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def delete_milestone_new(project_id, milestone_id):
    """Enhanced milestone deletion endpoint"""
    try:
        project = Project.query.get_or_404(project_id)
        milestone = Milestone.query.filter_by(id=milestone_id, project_id=project_id).first()
        
        if not milestone:
            flash('Milestone not found', 'error')
            return redirect(url_for('project.project_details', project_id=project_id))
        
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
        
        flash(f'Milestone "{milestone_title}" has been deleted', 'success')
        return redirect(url_for('project.project_details', project_id=project_id))
        
    except Exception as e:
        current_app.logger.error(f"Error deleting milestone: {str(e)}", exc_info=True)
        db.session.rollback()
        flash('An error occurred while deleting milestone', 'error')
        return redirect(url_for('project.project_details', project_id=project_id))


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
            flash('All fields are required', 'error')
            return redirect(url_for('project.project_details', project_id=project_id))
        
        try:
            quantity = float(quantity)
            unit_price = float(unit_price)
            total_cost = quantity * unit_price
        except ValueError:
            flash('Invalid numeric values', 'error')
            return redirect(url_for('project.project_details', project_id=project_id))
        
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
        
        flash(f'BOQ item "{item_description}" has been added', 'success')
        return redirect(url_for('project.project_details', project_id=project_id))
        
    except Exception as e:
        current_app.logger.error(f"Error adding BOQ item: {str(e)}", exc_info=True)
        db.session.rollback()
        flash('An error occurred while adding BOQ item', 'error')
        return redirect(url_for('project.project_details', project_id=project_id))


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
            flash('BOQ item not found', 'error')
            return redirect(url_for('project.project_details', project_id=project_id))
        
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
        
        flash(f'BOQ item "{item_description}" has been deleted', 'success')
        return redirect(url_for('project.project_details', project_id=project_id))
        
    except Exception as e:
        current_app.logger.error(f"Error deleting BOQ item: {str(e)}", exc_info=True)
        db.session.rollback()
        flash('An error occurred while deleting BOQ item', 'error')
        return redirect(url_for('project.project_details', project_id=project_id))


@project_bp.route('/<int:project_id>/upload_document', methods=['POST'])
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def upload_document_enhanced(project_id):
    """Enhanced document upload endpoint"""
    try:
        project = Project.query.get_or_404(project_id)
        
        if 'document_file' not in request.files:
            flash('No file selected', 'error')
            return redirect(url_for('project.project_details', project_id=project_id))
        
        file = request.files['document_file']
        document_type = request.form.get('document_type')
        description = request.form.get('document_description', '')
        
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('project.project_details', project_id=project_id))
        
        if not document_type:
            flash('Document type is required', 'error')
            return redirect(url_for('project.project_details', project_id=project_id))
        
        # Validate file type
        allowed_extensions = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'png', 'jpg', 'jpeg'}
        if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
            flash('File type not allowed', 'error')
            return redirect(url_for('project.project_details', project_id=project_id))
        
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
        
        flash(f'Document "{filename}" has been uploaded successfully', 'success')
        return redirect(url_for('project.project_details', project_id=project_id))
        
    except Exception as e:
        current_app.logger.error(f"Error uploading document: {str(e)}", exc_info=True)
        db.session.rollback()
        flash('An error occurred while uploading document', 'error')
        return redirect(url_for('project.project_details', project_id=project_id))


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
            flash('Document not found', 'error')
            return redirect(url_for('project.project_details', project_id=project_id))
        
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
        
        flash(f'Document "{document_name}" has been deleted', 'success')
        return redirect(url_for('project.project_details', project_id=project_id))
        
    except Exception as e:
        current_app.logger.error(f"Error deleting document: {str(e)}", exc_info=True)
        db.session.rollback()
        flash('An error occurred while deleting document', 'error')
        return redirect(url_for('project.project_details', project_id=project_id))


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
            flash('Progress value is required', 'error')
            return redirect(url_for('project.project_details', project_id=project_id))
        
        try:
            progress = float(progress)
            if progress < 0 or progress > 100:
                flash('Progress must be between 0 and 100', 'error')
                return redirect(url_for('project.project_details', project_id=project_id))
        except ValueError:
            flash('Invalid progress value', 'error')
            return redirect(url_for('project.project_details', project_id=project_id))
        
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
        
        flash(f'Project progress updated to {progress}%', 'success')
        return redirect(url_for('project.project_details', project_id=project_id))
        
    except Exception as e:
        current_app.logger.error(f"Error updating progress: {str(e)}", exc_info=True)
        db.session.rollback()
        flash('An error occurred while updating progress', 'error')
        return redirect(url_for('project.project_details', project_id=project_id))


# API Endpoints for Adding Resources (Role-based restrictions)

@project_bp.route('/equipment/add', methods=['POST'])
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def add_equipment():
    """Add equipment - restricted to SUPER_HQ and PROJECT_MANAGER, REQUIRES project context"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name') or not data.get('status'):
            return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
        
        # Project ID is REQUIRED - no global equipment allowed
        project_id = data.get('project_id')
        if not project_id:
            return jsonify({'status': 'error', 'message': 'Project selection is required. Equipment must be assigned to a specific project.'}), 400
        
        # Check if user has access to the specified project
        accessible_project_ids = get_user_accessible_project_ids(current_user)
        if int(project_id) not in accessible_project_ids:
            return jsonify({'status': 'error', 'message': 'You do not have access to the specified project'}), 403
        
        # Verify project exists
        project = Project.query.get(project_id)
        if not project:
            return jsonify({'status': 'error', 'message': 'Project not found'}), 404
        
        # Create new equipment
        equipment = Equipment(
            name=data['name'],
            status=data['status'],
            maintenance_due=datetime.strptime(data['maintenance_due'], '%Y-%m-%d').date() if data.get('maintenance_due') else None,
            assigned_to=data.get('assigned_to'),
            project_id=project_id
        )
        
        db.session.add(equipment)
        db.session.commit()
        
        current_app.logger.info(f"User {current_user.id} added equipment '{data['name']}' to project {project_id}")
        return jsonify({'status': 'success', 'message': f'Equipment added to project "{project.name}" successfully'})
        
    except Exception as e:
        current_app.logger.error(f"Error adding equipment: {str(e)}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': 'Failed to add equipment'}), 500


@project_bp.route('/materials/add', methods=['POST'])
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def add_material():
    """Add material - restricted to SUPER_HQ and PROJECT_MANAGER, REQUIRES project context"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name') or not data.get('quantity') or not data.get('unit'):
            return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
        
        # Project ID is REQUIRED - no global materials allowed
        project_id = data.get('project_id')
        if not project_id:
            return jsonify({'status': 'error', 'message': 'Project selection is required. Materials must be assigned to a specific project.'}), 400
        
        # Check if user has access to the specified project
        accessible_project_ids = get_user_accessible_project_ids(current_user)
        if int(project_id) not in accessible_project_ids:
            return jsonify({'status': 'error', 'message': 'You do not have access to the specified project'}), 403
        
        # Verify project exists
        project = Project.query.get(project_id)
        if not project:
            return jsonify({'status': 'error', 'message': 'Project not found'}), 404
        
        # Create new material
        material = Material(
            name=data['name'],
            quantity=int(data['quantity']),
            unit=data['unit'],
            delivered=int(data['quantity']),  # Initially, delivered = quantity
            status='In Stock',  # Default status
            last_updated=datetime.now().strftime('%Y-%m-%d'),
            project_id=project_id
        )
        
        db.session.add(material)
        db.session.commit()
        
        current_app.logger.info(f"User {current_user.id} added material '{data['name']}' to project {project_id}")
        return jsonify({'status': 'success', 'message': f'Material added to project "{project.name}" successfully'})
        
    except Exception as e:
        current_app.logger.error(f"Error adding material: {str(e)}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': 'Failed to add material'}), 500


@project_bp.route('/staff/add', methods=['POST'])
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def add_staff():
    """Add staff member - restricted to SUPER_HQ and PROJECT_MANAGER, REQUIRES project context"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name') or not data.get('role'):
            return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
        
        # Project ID is REQUIRED - no global staff assignment allowed
        project_id = data.get('project_id')
        if not project_id:
            return jsonify({'status': 'error', 'message': 'Project selection is required. Staff must be assigned to a specific project.'}), 400
        
        # Check if user has access to the specified project
        accessible_project_ids = get_user_accessible_project_ids(current_user)
        if int(project_id) not in accessible_project_ids:
            return jsonify({'status': 'error', 'message': 'You do not have access to the specified project'}), 403
        
        # Verify project exists
        project = Project.query.get(project_id)
        if not project:
            return jsonify({'status': 'error', 'message': 'Project not found'}), 404
        
        # For now, this is a placeholder since we need user registration logic
        # In a real system, you'd create a User and then assign to projects via StaffAssignment
        current_app.logger.info(f"User {current_user.id} initiated staff addition to project {project_id}")
        
        return jsonify({
            'status': 'success', 
            'message': f'Staff member addition to project "{project.name}" initiated (requires full user registration and assignment process)'
        })
        
    except Exception as e:
        current_app.logger.error(f"Error adding staff: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to add staff member'}), 500
        
    except Exception as e:
        current_app.logger.error(f"Error adding staff: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to add staff member'}), 500


# Generate Reports Endpoints (Project-based)

@project_bp.route('/equipment/report', methods=['POST'])
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def generate_equipment_report():
    """Generate equipment report for accessible projects"""
    try:
        data = request.get_json() or {}
        project_id = data.get('project_id')
        
        # Get user's accessible projects
        accessible_projects = get_user_accessible_projects(current_user)
        accessible_project_ids = [p.id for p in accessible_projects]
        
        # Filter equipment by project if specified
        if project_id:
            if int(project_id) not in accessible_project_ids:
                return jsonify({'status': 'error', 'message': 'No access to specified project'}), 403
            equipment_query = Equipment.query.filter_by(project_id=project_id)
            project_name = Project.query.get(project_id).name
        else:
            # For now, show all equipment (in future, filter by accessible projects)
            equipment_query = Equipment.query
            project_name = "All Accessible Projects"
        
        equipment_list = equipment_query.all()
        
        # This would generate actual report in real system
        return jsonify({
            'status': 'success', 
            'message': f'Equipment report generated for {project_name}',
            'report_data': {
                'project': project_name,
                'equipment_count': len(equipment_list),
                'available_count': len([e for e in equipment_list if e.status == 'Available']),
                'in_use_count': len([e for e in equipment_list if e.status == 'In Use']),
                'maintenance_count': len([e for e in equipment_list if e.status == 'Maintenance'])
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error generating equipment report: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to generate report'}), 500


@project_bp.route('/materials/export', methods=['POST'])
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def export_materials():
    """Export materials inventory for accessible projects"""
    try:
        data = request.get_json() or {}
        project_id = data.get('project_id')
        
        # Get user's accessible projects
        accessible_projects = get_user_accessible_projects(current_user)
        accessible_project_ids = [p.id for p in accessible_projects]
        
        # Filter materials by project if specified
        if project_id:
            if int(project_id) not in accessible_project_ids:
                return jsonify({'status': 'error', 'message': 'No access to specified project'}), 403
            materials_query = Material.query.filter_by(project_id=project_id)
            project_name = Project.query.get(project_id).name
        else:
            # For now, show all materials (in future, filter by accessible projects)
            materials_query = Material.query
            project_name = "All Accessible Projects"
        
        materials_list = materials_query.all()
        
        # This would generate actual export in real system
        return jsonify({
            'status': 'success', 
            'message': f'Materials inventory exported for {project_name}',
            'export_data': {
                'project': project_name,
                'materials_count': len(materials_list),
                'in_stock_count': len([m for m in materials_list if m.status == 'In Stock']),
                'low_stock_count': len([m for m in materials_list if m.status == 'Low Stock']),
                'out_of_stock_count': len([m for m in materials_list if m.status == 'Out of Stock'])
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error exporting materials: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to export materials'}), 500


# --- Daily Production Report (DPR) Routes ---

@project_bp.route('/dpr')
@project_bp.route('/dpr/<int:selected_project_id>')
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER, Roles.PROJECT_STAFF])
def dpr_list(selected_project_id=None):
    """List DPRs - Project Managers can create, Staff can fill, Admins can view all"""
    try:
        # Get user's accessible projects
        accessible_projects = get_user_accessible_projects(current_user)
        
        # Initialize data variables
        project_staff = []
        project_dprs = []
        selected_project = None
        
        # Check for project ID in query parameters if not in URL path
        if not selected_project_id:
            selected_project_id = request.args.get('selected_project_id')
        
        # If a project is selected, load its staff and DPRs
        if selected_project_id:
            try:
                selected_project_id = int(selected_project_id)
                accessible_project_ids = get_user_accessible_project_ids(current_user)
                
                if selected_project_id in accessible_project_ids:
                    selected_project = Project.query.get(selected_project_id)
                    current_app.logger.info(f"Loading staff for project {selected_project_id}: {selected_project.name if selected_project else 'Not found'}")
                    
                    # Get staff assigned to this project (both users and employees)
                    staff_assignments = StaffAssignment.query.filter_by(project_id=selected_project_id).all()
                    employee_assignments = EmployeeAssignment.query.filter_by(project_id=selected_project_id).all()
                    
                    current_app.logger.info(f"Found {len(staff_assignments)} staff assignments and {len(employee_assignments)} employee assignments")
                    
                    # Collect staff members with their details
                    for assignment in staff_assignments:
                        user = User.query.get(assignment.staff_id)
                        if user:
                            project_staff.append({
                                'id': user.id,
                                'name': user.name,
                                'email': user.email,
                                'role': assignment.role,
                                'type': 'user'
                            })
                    
                    for assignment in employee_assignments:
                        employee = Employee.query.get(assignment.employee_id)
                        if employee:
                            project_staff.append({
                                'id': employee.id,
                                'name': employee.name,
                                'email': employee.email,
                                'role': assignment.role,
                                'type': 'employee'
                            })
                    
                    current_app.logger.info(f"Final project_staff list has {len(project_staff)} members")
                    
                    # Get DPRs for this project
                    dprs = DailyProductionReport.query.filter_by(project_id=selected_project_id).order_by(
                        DailyProductionReport.report_date.desc()
                    ).all()
                    
                    for dpr in dprs:
                        project_dprs.append({
                            'id': dpr.id,
                            'report_date': dpr.report_date,
                            'status': dpr.status,
                            'created_by': dpr.created_by.name if dpr.created_by else 'Unknown',
                            'assigned_to': dpr.assigned_to.name if dpr.assigned_to else 'Unassigned',
                            'completed_by': dpr.completed_by.name if dpr.completed_by else None,
                            'created_at': dpr.created_at,
                            'completed_at': dpr.completed_at,
                            'project_name': selected_project.name if selected_project else 'Unknown'
                        })
                else:
                    current_app.logger.warning(f"User {current_user.id} does not have access to project {selected_project_id}")
            except ValueError:
                current_app.logger.error(f"Invalid project ID: {selected_project_id}")
                selected_project_id = None
        
        return render_template('projects/dpr.html', 
                             accessible_projects=accessible_projects,
                             selected_project=selected_project,
                             project_staff=project_staff,
                             project_dprs=project_dprs,
                             user_role=current_user.role)
    except Exception as e:
        current_app.logger.error(f"DPR list error: {str(e)}")
        return render_template('error.html', error="Failed to load DPR page"), 500


@project_bp.route('/dpr/create', methods=['POST'])
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def create_dpr():
    """Create new DPR - Project Managers only"""
    try:
        # Get form data instead of JSON
        project_id = request.form.get('project_id')
        report_date_str = request.form.get('report_date')
        assigned_to_id = request.form.get('assigned_to_id')
        action = request.form.get('action', 'save_draft')
        
        # Validate required fields
        if not project_id or not report_date_str:
            flash('Missing required fields: project and report date', 'error')
            return redirect(url_for('project.dpr_list'))
        
        # Check project access
        accessible_project_ids = get_user_accessible_project_ids(current_user)
        if int(project_id) not in accessible_project_ids:
            flash('You do not have access to the specified project', 'error')
            return redirect(url_for('project.dpr_list'))
        
        # Verify project exists
        project = Project.query.get(project_id)
        if not project:
            flash('Project not found', 'error')
            return redirect(url_for('project.dpr_list'))
        
        # Parse report date
        report_date = datetime.strptime(report_date_str, '%Y-%m-%d').date()
        
        # Check if DPR already exists for this date
        existing_dpr = DailyProductionReport.query.filter_by(
            project_id=project_id,
            report_date=report_date
        ).first()
        
        if existing_dpr:
            flash('DPR already exists for this date', 'error')
            return redirect(url_for('project.dpr_list', selected_project_id=project_id))
        
        # Create DPR
        dpr = DailyProductionReport(
            project_id=project_id,
            report_date=report_date,
            created_by_id=current_user.id,
            assigned_to_id=assigned_to_id if assigned_to_id else None,
            status='sent_to_staff' if action == 'send_to_staff' else 'draft',
            sent_at=datetime.utcnow() if action == 'send_to_staff' else None
        )
        
        db.session.add(dpr)
        db.session.flush()  # Get the DPR ID
        
        # Process production items from form data
        production_items_data = [
            {'code': '1.01', 'description': 'Soft Cut Works', 'unit': 'M3'},
            {'code': '1.02', 'description': 'Fill works', 'unit': 'M3'},
            {'code': '1.03', 'description': 'Scarification', 'unit': 'M2'},
            {'code': '2.01', 'description': 'Blinding', 'unit': 'M3'},
            {'code': '2.02', 'description': 'Base/Top Slab concrete', 'unit': 'M3'},
        ]
        
        for item_data in production_items_data:
            code = item_data['code']
            location = request.form.get(f'location_{code}', '')
            target_qty = request.form.get(f'target_qty_{code}', '0')
            daily_qty = request.form.get(f'daily_qty_{code}', '0')
            
            # Only create production item if any data is provided
            if location or float(target_qty or 0) > 0 or float(daily_qty or 0) > 0:
                production_item = DPRProductionItem(
                    dpr_id=dpr.id,
                    item_code=code,
                    description=item_data['description'],
                    location=location,
                    unit=item_data['unit'],
                    target_qty=float(target_qty or 0),
                    day_production=float(daily_qty or 0)
                )
                db.session.add(production_item)
        
        # Process material usage from form data
        material_items_data = [
            {'number': 1, 'description': 'Cement', 'unit': 'bag'},
            {'number': 2, 'description': 'Earthfill works', 'unit': 'trucks'},
            {'number': 3, 'description': 'Cut work', 'unit': 'trucks'},
            {'number': 4, 'description': 'Diesel', 'unit': 'ltr'},
            {'number': 5, 'description': 'Concrete Mixer small truck', 'unit': 'trucks'},
        ]
        
        for material_data in material_items_data:
            number = material_data['number']
            quantity = request.form.get(f'material_qty_{number}', '0')
            
            # Only create material item if quantity is provided
            if float(quantity or 0) > 0:
                material_item = DPRMaterialUsage(
                    dpr_id=dpr.id,
                    item_number=number,
                    description=material_data['description'],
                    unit=material_data['unit'],
                    quantity_used=float(quantity or 0)
                )
                db.session.add(material_item)
        
        db.session.commit()
        
        current_app.logger.info(f"User {current_user.id} created DPR for project {project_id} on {report_date}")
        
        # Send email notification if DPR is assigned to staff
        if action == 'send_to_staff' and dpr.assigned_to_id:
            assigned_staff = User.query.get(dpr.assigned_to_id)
            if assigned_staff and assigned_staff.email:
                try:
                    email_subject = f"Daily Production Report Assignment - {project.name}"
                    email_body = f"""
Dear {assigned_staff.name},

You have been assigned a Daily Production Report to fill out for the project: {project.name}

Report Date: {report_date.strftime('%B %d, %Y')}
Created By: {current_user.name}
Project: {project.name}

Please log in to your dashboard to fill out the DPR:
{url_for('project.fill_dpr', dpr_id=dpr.id, _external=True)}

This DPR includes production items and material usage that need to be completed.

Best regards,
SammyA Project Management System
                    """
                    
                    send_email_notification(
                        to_email=assigned_staff.email,
                        subject=email_subject,
                        body=email_body
                    )
                    
                    current_app.logger.info(f"Email notification sent to {assigned_staff.email} for DPR {dpr.id}")
                    
                except Exception as email_error:
                    current_app.logger.error(f"Failed to send email notification: {str(email_error)}")
                    # Don't fail the DPR creation if email fails
        
        message = f"DPR created successfully for {project.name}"
        if action == 'send_to_staff':
            if dpr.assigned_to_id:
                assigned_staff = User.query.get(dpr.assigned_to_id)
                message += f" and sent to {assigned_staff.name if assigned_staff else 'staff'}"
                if assigned_staff and assigned_staff.email:
                    message += f" (email notification sent to {assigned_staff.email})"
            else:
                message += " (no staff member assigned)"
        
        flash(message, 'success')
        return redirect(url_for('project.dpr_list', selected_project_id=project_id))
        
    except Exception as e:
        current_app.logger.error(f"Error creating DPR: {str(e)}")
        db.session.rollback()
        flash('Failed to create DPR. Please try again.', 'error')
        return redirect(url_for('project.dpr_list'))


@project_bp.route('/dpr/<int:dpr_id>/fill', methods=['GET', 'POST'])
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER, Roles.PROJECT_STAFF])
def fill_dpr(dpr_id):
    """Fill/Complete DPR - Staff fills, Managers can view"""
    try:
        dpr = DailyProductionReport.query.get_or_404(dpr_id)
        
        # Check access - must be assigned to DPR or have manager access
        has_access = (
            dpr.assigned_to_id == current_user.id or  # Assigned staff
            dpr.created_by_id == current_user.id or   # Creating manager
            current_user.has_role(Roles.SUPER_HQ) or  # Admin
            (current_user.has_role(Roles.PROJECT_MANAGER) and dpr.project.project_manager == current_user.name)
        )
        
        if not has_access:
            return render_template('error.html', error="No access to this DPR"), 403
        
        if request.method == 'GET':
            return render_template('projects/dpr_fill.html', dpr=dpr)
        
        # POST - Save DPR data
        action = request.form.get('action')
        
        # Update production items
        for item in dpr.production_items:
            location = request.form.get(f'location_{item.id}')
            previous_qty = request.form.get(f'previous_qty_{item.id}')
            day_production = request.form.get(f'day_production_{item.id}')
            total_qty = request.form.get(f'total_qty_{item.id}')
            
            if location is not None:
                item.location = location
            if previous_qty is not None:
                item.previous_qty_done = float(previous_qty) if previous_qty else 0
            if day_production is not None:
                item.day_production = float(day_production) if day_production else 0
            if total_qty is not None:
                item.total_qty_done = float(total_qty) if total_qty else 0
        
        # Update material usage
        for material in dpr.material_usage:
            previous_qty = request.form.get(f'material_previous_{material.id}')
            day_usage = request.form.get(f'material_day_{material.id}')
            total_qty = request.form.get(f'material_total_{material.id}')
            
            if previous_qty is not None:
                material.previous_qty_used = float(previous_qty) if previous_qty else 0
            if day_usage is not None:
                material.day_usage = float(day_usage) if day_usage else 0
            if total_qty is not None:
                material.total_qty_used = float(total_qty) if total_qty else 0
        
        # Update DPR metadata
        dpr.issues = request.form.get('issues', '')
        dpr.prepared_by = request.form.get('prepared_by', '')
        dpr.checked_by = request.form.get('checked_by', '')
        
        if action == 'submit_completed':
            dpr.status = 'completed'
            dpr.completed_at = datetime.utcnow()
            dpr.completed_by_id = current_user.id
        
        db.session.commit()
        
        current_app.logger.info(f"User {current_user.id} updated DPR {dpr_id} - action: {action}")
        
        message = "DPR saved successfully"
        if action == 'submit_completed':
            message = "DPR submitted successfully"
        
        return jsonify({'status': 'success', 'message': message})
        
    except Exception as e:
        current_app.logger.error(f"Error filling DPR: {str(e)}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': 'Failed to save DPR'}), 500


@project_bp.route('/dpr/project/<int:project_id>')
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER, Roles.PROJECT_STAFF])
def get_project_dprs(project_id):
    """Get DPRs for a specific project"""
    try:
        # Check project access
        accessible_project_ids = get_user_accessible_project_ids(current_user)
        if project_id not in accessible_project_ids:
            return jsonify({'status': 'error', 'message': 'No access to project'}), 403
        
        dprs = DailyProductionReport.query.filter_by(project_id=project_id).order_by(
            DailyProductionReport.report_date.desc()
        ).all()
        
        dpr_data = []
        for dpr in dprs:
            dpr_data.append({
                'id': dpr.id,
                'report_date': dpr.report_date.strftime('%Y-%m-%d'),
                'status': dpr.status,
                'created_by': dpr.created_by.name if dpr.created_by else 'Unknown',
                'assigned_to': dpr.assigned_to.name if dpr.assigned_to else 'Unassigned',
                'completed_by': dpr.completed_by.name if dpr.completed_by else None,
                'created_at': dpr.created_at.strftime('%Y-%m-%d %H:%M'),
                'completed_at': dpr.completed_at.strftime('%Y-%m-%d %H:%M') if dpr.completed_at else None
            })
        
        return jsonify({'status': 'success', 'dprs': dpr_data})
        
    except Exception as e:
        current_app.logger.error(f"Error getting project DPRs: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to load DPRs'}), 500


@project_bp.route('/reports')
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER, Roles.PROJECT_STAFF])
def reports_index():
    """Project Reports page with server-side data loading"""
    # Handle project selection from form
    selected_project_id = request.args.get('selected_project_id', type=int)
    return reports_view(selected_project_id)

@project_bp.route('/reports/<int:selected_project_id>')
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER, Roles.PROJECT_STAFF])
def reports_project(selected_project_id):
    """Project Reports page for a specific project"""
    return reports_view(selected_project_id)

def reports_view(selected_project_id=None):
    """Project Reports page with server-side data loading"""
    try:
        # Get user's accessible projects
        accessible_projects = get_user_accessible_projects(current_user)
        
        # Get report types for form dropdown
        report_types = ['Progress Report', 'Financial Report', 'Material Report', 'Equipment Report']
        
        # Initialize data variables
        project_reports = []
        project_dprs = []
        dpr_summary = {'total': 0, 'pending': 0, 'completed': 0, 'monthly': 0}
        selected_project = None
        
        # If a project is selected, load its data
        if selected_project_id:
            accessible_project_ids = get_user_accessible_project_ids(current_user)
            
            if selected_project_id in accessible_project_ids:
                selected_project = Project.query.get(selected_project_id)
                
                # Load reports (all reports since Report model doesn't have project_id)
                reports = Report.query.order_by(Report.date.desc()).limit(20).all()
                
                for report in reports:
                    uploader = User.query.get(report.uploader_id) if report.uploader_id else None
                    project_reports.append({
                        'id': report.id,
                        'title': getattr(report, 'title', None) or f"{report.type} Report",
                        'type': report.type,
                        'date': report.date,
                        'author': uploader.name if uploader else 'Unknown',
                        'status': getattr(report, 'status', 'Draft'),
                        'description': getattr(report, 'description', f'Report file: {report.filename}'),
                        'filename': report.filename
                    })
                
                # Load DPRs for the selected project
                try:
                    dprs = DailyProductionReport.query.filter_by(project_id=selected_project_id).order_by(
                        DailyProductionReport.report_date.desc()
                    ).all()
                    
                    from datetime import date
                    current_month = date.today().month
                    current_year = date.today().year
                    
                    for dpr in dprs:
                        try:
                            project_dprs.append({
                                'id': dpr.id,
                                'report_date': dpr.report_date,
                                'status': dpr.status,
                                'created_by': dpr.created_by.name if dpr.created_by else 'Unknown',
                                'assigned_to': dpr.assigned_to.name if dpr.assigned_to else 'Unassigned',
                                'completed_by': dpr.completed_by.name if dpr.completed_by else None,
                                'created_at': dpr.created_at,
                                'completed_at': dpr.completed_at,
                                'issues': dpr.issues,
                                'prepared_by': dpr.prepared_by,
                                'checked_by': dpr.checked_by
                            })
                        except Exception as dpr_error:
                            current_app.logger.error(f"Error processing DPR {dpr.id}: {str(dpr_error)}")
                            # Add a basic entry for this DPR with safe data
                            project_dprs.append({
                                'id': dpr.id,
                                'report_date': dpr.report_date,
                                'status': dpr.status,
                                'created_by': 'Unknown',
                                'assigned_to': 'Unassigned',
                                'completed_by': None,
                                'created_at': dpr.created_at,
                                'completed_at': dpr.completed_at,
                                'issues': getattr(dpr, 'issues', ''),
                                'prepared_by': getattr(dpr, 'prepared_by', ''),
                                'checked_by': getattr(dpr, 'checked_by', '')
                            })
                    
                    # Calculate DPR summary
                    dpr_summary = {
                        'total': len(dprs),
                        'pending': len([d for d in dprs if d.status == 'sent_to_staff']),
                        'completed': len([d for d in dprs if d.status == 'completed']),
                        'monthly': len([d for d in dprs if d.report_date.month == current_month and d.report_date.year == current_year])
                    }
                except Exception as dpr_loading_error:
                    current_app.logger.error(f"Error loading DPRs for project {selected_project_id}: {str(dpr_loading_error)}")
                    # Set empty DPR data if there's an error
                    project_dprs = []
                    dpr_summary = {'total': 0, 'pending': 0, 'completed': 0, 'monthly': 0}
        
        return render_template('projects/reports.html', 
                             accessible_projects=accessible_projects,
                             user_role=current_user.role,
                             selected_project=selected_project,
                             project_reports=project_reports,
                             project_dprs=project_dprs,
                             dpr_summary=dpr_summary,
                             data={'report_types': report_types})
    except Exception as e:
        current_app.logger.error(f"Reports page error: {str(e)}")
        return render_template('error.html', error="Failed to load reports page"), 500



@project_bp.route('/reports/project/<int:project_id>')
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER, Roles.PROJECT_STAFF])
def get_project_reports(project_id):
    """Get general reports for a specific project"""
    try:
        current_app.logger.info(f"Fetching reports for project {project_id}")
        
        # Check project access
        accessible_project_ids = get_user_accessible_project_ids(current_user)
        if project_id not in accessible_project_ids:
            return jsonify({'status': 'error', 'message': 'No access to project'}), 403
        
        # Since the Report model doesn't have project_id, we'll create sample reports for now
        # In a real implementation, you'd either add project_id to Report model or link through another table
        current_app.logger.info(f"Report model structure: {Report.__table__.columns.keys()}")
        
        # For now, return all reports (could be filtered by uploader if they're project staff)
        reports = Report.query.order_by(Report.date.desc()).limit(10).all()
        
        report_data = []
        for report in reports:
            # Get uploader info for the report
            uploader = User.query.get(report.uploader_id) if report.uploader_id else None
            
            report_data.append({
                'id': report.id,
                'title': getattr(report, 'title', None) or f"{report.type} Report",
                'type': report.type,
                'date': report.date.strftime('%Y-%m-%d') if report.date else 'Unknown',
                'author': uploader.name if uploader else 'Unknown',
                'status': getattr(report, 'status', 'Draft'),
                'description': getattr(report, 'description', f'Report file: {report.filename}')
            })
        
        current_app.logger.info(f"Found {len(report_data)} reports")
        return jsonify({'status': 'success', 'reports': report_data})
        
    except Exception as e:
        current_app.logger.error(f"Error getting project reports: {str(e)}")
        import traceback
        current_app.logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'status': 'error', 'message': f'Failed to load reports: {str(e)}'}), 500


@project_bp.route('/reports/create', methods=['POST'])
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER, Roles.PROJECT_STAFF])
def create_report():
    """Create a new report"""
    try:
        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        # Validate required fields
        if not data.get('title') or not data.get('type'):
            if request.is_json:
                return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
            else:
                flash('Missing required fields', 'error')
                return redirect(url_for('project.reports_index'))
        
        project_id = data.get('project_id')
        if project_id:
            # Check project access if project_id is provided
            accessible_project_ids = get_user_accessible_project_ids(current_user)
            if int(project_id) not in accessible_project_ids:
                if request.is_json:
                    return jsonify({'status': 'error', 'message': 'No access to specified project'}), 403
                else:
                    flash('No access to specified project', 'error')
                    return redirect(url_for('project.reports_index'))
        
        # Create filename based on title and type
        title = data['title'].replace(' ', '_').lower()
        report_type = data['type'].replace(' ', '_').lower()
        filename = f"{report_type}_{title}_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        # Create report record
        report = Report(
            filename=filename,
            type=data['type'],
            date=datetime.now(),
            uploader_id=current_user.id,
            uploaded_at=datetime.now()
        )
        
        db.session.add(report)
        db.session.commit()
        
        current_app.logger.info(f"User {current_user.id} created report: {data['title']}")
        
        if request.is_json:
            return jsonify({
                'status': 'success', 
                'message': f"Report '{data['title']}' created successfully",
                'report_id': report.id
            })
        else:
            flash(f"Report '{data['title']}' created successfully", 'success')
            if project_id:
                return redirect(url_for('project.reports_index', selected_project_id=project_id))
            else:
                return redirect(url_for('project.reports_index'))
        
    except Exception as e:
        current_app.logger.error(f"Error creating report: {str(e)}")
        db.session.rollback()
        if request.is_json:
            return jsonify({'status': 'error', 'message': 'Failed to create report'}), 500
        else:
            flash('Failed to create report', 'error')
            return redirect(url_for('project.reports_index'))


@project_bp.route('/dpr/<int:dpr_id>/details')
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER, Roles.PROJECT_STAFF])
def get_dpr_details(dpr_id):
    """Get detailed DPR information including production items and material usage"""
    try:
        dpr = DailyProductionReport.query.get_or_404(dpr_id)
        
        # Check access - must be assigned to DPR or have manager access
        has_access = (
            dpr.assigned_to_id == current_user.id or  # Assigned staff
            dpr.created_by_id == current_user.id or   # Creating manager
            current_user.has_role(Roles.SUPER_HQ) or  # Admin
            (current_user.has_role(Roles.PROJECT_MANAGER) and dpr.project.project_manager == current_user.name)
        )
        
        if not has_access:
            return jsonify({'status': 'error', 'message': 'No access to this DPR'}), 403
        
        # Build production items data
        production_items = []
        for item in dpr.production_items:
            production_items.append({
                'id': item.id,
                'item_code': item.item_code,
                'description': item.description,
                'location': item.location,
                'unit': item.unit,
                'target_qty': float(item.target_qty),
                'previous_qty_done': float(item.previous_qty_done),
                'day_production': float(item.day_production),
                'total_qty_done': float(item.total_qty_done)
            })
        
        # Build material usage data
        material_usage = []
        for material in dpr.material_usage:
            material_usage.append({
                'id': material.id,
                'item_number': material.item_number,
                'description': material.description,
                'unit': material.unit,
                'previous_qty_used': float(material.previous_qty_used),
                'day_usage': float(material.day_usage),
                'total_qty_used': float(material.total_qty_used)
            })
        
        dpr_data = {
            'id': dpr.id,
            'report_date': dpr.report_date.strftime('%Y-%m-%d'),
            'status': dpr.status,
            'created_by': dpr.created_by.name if dpr.created_by else 'Unknown',
            'assigned_to': dpr.assigned_to.name if dpr.assigned_to else 'Unassigned',
            'completed_by': dpr.completed_by.name if dpr.completed_by else None,
            'created_at': dpr.created_at.strftime('%Y-%m-%d %H:%M'),
            'completed_at': dpr.completed_at.strftime('%Y-%m-%d %H:%M') if dpr.completed_at else None,
            'issues': dpr.issues,
            'prepared_by': dpr.prepared_by,
            'checked_by': dpr.checked_by,
            'production_items': production_items,
            'material_usage': material_usage
        }
        
        return jsonify({'status': 'success', 'dpr': dpr_data})
        
    except Exception as e:
        current_app.logger.error(f"Error getting DPR details: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to load DPR details'}), 500


@project_bp.route('/dpr/<int:dpr_id>/view')
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER, Roles.PROJECT_STAFF])
def view_dpr(dpr_id):
    """View DPR details in web interface"""
    try:
        dpr = DailyProductionReport.query.get_or_404(dpr_id)
        
        # Check access - must be assigned to DPR or have manager access
        has_access = (
            dpr.assigned_to_id == current_user.id or  # Assigned staff
            dpr.created_by_id == current_user.id or   # Creating manager
            current_user.has_role(Roles.SUPER_HQ) or  # Admin
            (current_user.has_role(Roles.PROJECT_MANAGER) and 
             dpr.project_id in get_user_accessible_project_ids(current_user))
        )
        
        if not has_access:
            flash('You do not have access to view this DPR.', 'error')
            return redirect(url_for('project.dpr_list'))
        
        # Get production items and material usage
        production_items = dpr.production_items
        material_usage = dpr.material_usage
        
        return render_template('projects/dpr_view.html',
                             dpr=dpr,
                             production_items=production_items,
                             material_usage=material_usage,
                             user_role=current_user.role)
        
    except Exception as e:
        current_app.logger.error(f"Error viewing DPR: {str(e)}")
        flash('Failed to load DPR details.', 'error')
        return redirect(url_for('project.dpr_list'))


@project_bp.route('/dpr/<int:dpr_id>/approve', methods=['POST'])
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def approve_dpr(dpr_id):
    """Approve a completed DPR"""
    try:
        dpr = DailyProductionReport.query.get_or_404(dpr_id)
        
        # Check access - must be manager or admin
        has_access = (
            current_user.has_role(Roles.SUPER_HQ) or
            (current_user.has_role(Roles.PROJECT_MANAGER) and 
             dpr.project_id in get_user_accessible_project_ids(current_user))
        )
        
        if not has_access:
            return jsonify({'success': False, 'message': 'No access to approve this DPR'}), 403
        
        if dpr.status not in ['completed', 'sent_to_staff']:
            return jsonify({'success': False, 'message': 'DPR must be completed before approval'}), 400
        
        # Update DPR status
        dpr.status = 'approved'
        dpr.reviewed_at = datetime.utcnow()
        db.session.commit()
        
        current_app.logger.info(f"User {current_user.id} approved DPR {dpr_id}")
        
        return jsonify({'success': True, 'message': 'DPR approved successfully'})
        
    except Exception as e:
        current_app.logger.error(f"Error approving DPR: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to approve DPR'}), 500


@project_bp.route('/dpr/<int:dpr_id>/reject', methods=['POST'])
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def reject_dpr(dpr_id):
    """Reject a completed DPR"""
    try:
        data = request.get_json()
        reason = data.get('reason', '').strip()
        
        if not reason:
            return jsonify({'success': False, 'message': 'Rejection reason is required'}), 400
        
        dpr = DailyProductionReport.query.get_or_404(dpr_id)
        
        # Check access - must be manager or admin
        has_access = (
            current_user.has_role(Roles.SUPER_HQ) or
            (current_user.has_role(Roles.PROJECT_MANAGER) and 
             dpr.project_id in get_user_accessible_project_ids(current_user))
        )
        
        if not has_access:
            return jsonify({'success': False, 'message': 'No access to reject this DPR'}), 403
        
        if dpr.status not in ['completed', 'sent_to_staff']:
            return jsonify({'success': False, 'message': 'DPR must be completed before rejection'}), 400
        
        # Update DPR status and add rejection reason
        dpr.status = 'rejected'
        dpr.issues = f"REJECTED: {reason}\n\n{dpr.issues or ''}"
        dpr.reviewed_at = datetime.utcnow()
        db.session.commit()
        
        current_app.logger.info(f"User {current_user.id} rejected DPR {dpr_id}: {reason}")
        
        return jsonify({'success': True, 'message': 'DPR rejected successfully'})
        
    except Exception as e:
        current_app.logger.error(f"Error rejecting DPR: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to reject DPR'}), 500


# ============================================================================
# COMPREHENSIVE REPORTS CRUD OPERATIONS
# ============================================================================

@project_bp.route('/reports/list')
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER, Roles.PROJECT_STAFF])
def reports_list():
    """List reports with project selection - supports both HTML and JSON"""
    try:
        project_id = request.args.get('project_id', type=int)
        current_app.logger.info(f"User {current_user.id} requesting reports list for project {project_id}")
        
        # Check if this is an AJAX request expecting JSON
        if request.headers.get('Content-Type') == 'application/json' or request.args.get('format') == 'json':
            # Return JSON data for AJAX calls
            if project_id:
                accessible_project_ids = get_user_accessible_project_ids(current_user)
                
                if project_id not in accessible_project_ids:
                    return jsonify({'success': False, 'message': 'No access to project'}), 403
                
                # Get reports (simplified since Report model doesn't have project_id)
                reports = Report.query.order_by(Report.date.desc()).limit(20).all()
                
                reports_data = []
                for report in reports:
                    uploader = User.query.get(report.uploader_id) if report.uploader_id else None
                    reports_data.append({
                        'id': report.id,
                        'title': getattr(report, 'title', None) or f"{report.type} Report",
                        'type': report.type,
                        'date': report.date.strftime('%Y-%m-%d') if report.date else 'Unknown',
                        'author': uploader.name if uploader else 'Unknown',
                        'status': getattr(report, 'status', 'Draft'),
                        'description': getattr(report, 'description', f'Report file: {report.filename}'),
                        'filename': report.filename
                    })
                
                return jsonify({'success': True, 'reports': reports_data})
            else:
                return jsonify({'success': False, 'message': 'No project selected'})
        else:
            # Return HTML page for regular requests
            return reports_view(project_id)
            
    except Exception as e:
        current_app.logger.error(f"Error in reports_list: {str(e)}")
        import traceback
        current_app.logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Return appropriate error response based on request type
        if request.headers.get('Content-Type') == 'application/json' or request.args.get('format') == 'json':
            return jsonify({'success': False, 'message': 'Failed to load reports'}), 500
        else:
            return render_template('error.html', error="Failed to load reports"), 500


@project_bp.route('/reports/<int:report_id>/view')
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER, Roles.PROJECT_STAFF])
def view_report(report_id):
    """View a specific report"""
    try:
        report = Report.query.get_or_404(report_id)
        
        # Check access permissions
        uploader = User.query.get(report.uploader_id) if report.uploader_id else None
        
        return render_template('projects/report_view.html',
                             report=report,
                             uploader=uploader,
                             user_role=current_user.role)
        
    except Exception as e:
        current_app.logger.error(f"Error viewing report: {str(e)}")
        flash('Failed to load report details.', 'error')
        return redirect(url_for('project.reports_index'))


@project_bp.route('/reports/<int:report_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER, Roles.PROJECT_STAFF])
def edit_report(report_id):
    """Edit a specific report"""
    try:
        report = Report.query.get_or_404(report_id)
        
        # Check if user can edit this report
        can_edit = (
            current_user.has_role(Roles.SUPER_HQ) or
            (current_user.has_role(Roles.PROJECT_MANAGER)) or
            (report.uploader_id == current_user.id)
        )
        
        if not can_edit:
            flash('You do not have permission to edit this report.', 'error')
            return redirect(url_for('project.view_report', report_id=report_id))
        
        if request.method == 'POST':
            # Update report details
            if hasattr(report, 'title'):
                report.title = request.form.get('title', report.filename)
            if hasattr(report, 'description'):
                report.description = request.form.get('description', '')
            
            report.type = request.form.get('type', report.type)
            
            db.session.commit()
            
            current_app.logger.info(f"User {current_user.id} updated report {report_id}")
            flash('Report updated successfully.', 'success')
            return redirect(url_for('project.view_report', report_id=report_id))
        
        return render_template('projects/report_edit.html',
                             report=report,
                             user_role=current_user.role)
        
    except Exception as e:
        current_app.logger.error(f"Error editing report: {str(e)}")
        flash('Failed to edit report.', 'error')
        return redirect(url_for('project.reports_index'))


@project_bp.route('/reports/<int:report_id>/delete', methods=['DELETE'])
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def delete_report(report_id):
    """Delete a specific report"""
    try:
        report = Report.query.get_or_404(report_id)
        
        # Check if user can delete this report
        can_delete = (
            current_user.has_role(Roles.SUPER_HQ) or
            (current_user.has_role(Roles.PROJECT_MANAGER))
        )
        
        if not can_delete:
            return jsonify({'success': False, 'message': 'No permission to delete this report'}), 403
        
        # Delete the report file if it exists
        if report.filename:
            try:
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'reports', report.filename)
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as file_error:
                current_app.logger.warning(f"Could not delete report file: {file_error}")
        
        # Delete the database record
        db.session.delete(report)
        db.session.commit()
        
        current_app.logger.info(f"User {current_user.id} deleted report {report_id}")
        
        return jsonify({'success': True, 'message': 'Report deleted successfully'})
        
    except Exception as e:
        current_app.logger.error(f"Error deleting report: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to delete report'}), 500


@project_bp.route('/reports/<int:report_id>/approve', methods=['POST'])
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def approve_report(report_id):
    """Approve a report"""
    try:
        report = Report.query.get_or_404(report_id)
        
        # Add status field if it doesn't exist
        if not hasattr(report, 'status'):
            # For existing reports without status, we'll use a different approach
            current_app.logger.info(f"Report {report_id} approved by user {current_user.id}")
            return jsonify({'success': True, 'message': 'Report approved successfully'})
        
        report.status = 'approved'
        
        # Add approved_at field if it exists
        if hasattr(report, 'approved_at'):
            report.approved_at = datetime.utcnow()
        
        db.session.commit()
        
        current_app.logger.info(f"User {current_user.id} approved report {report_id}")
        
        return jsonify({'success': True, 'message': 'Report approved successfully'})
        
    except Exception as e:
        current_app.logger.error(f"Error approving report: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to approve report'}), 500


@project_bp.route('/reports/<int:report_id>/reject', methods=['POST'])
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def reject_report(report_id):
    """Reject a report"""
    try:
        data = request.get_json()
        reason = data.get('reason', '').strip()
        
        if not reason:
            return jsonify({'success': False, 'message': 'Rejection reason is required'}), 400
        
        report = Report.query.get_or_404(report_id)
        
        # Add status field if it doesn't exist
        if not hasattr(report, 'status'):
            current_app.logger.info(f"Report {report_id} rejected by user {current_user.id}: {reason}")
            return jsonify({'success': True, 'message': 'Report rejected successfully'})
        
        report.status = 'rejected'
        
        # Add rejection reason to description or comments
        if hasattr(report, 'rejection_reason'):
            report.rejection_reason = reason
        elif hasattr(report, 'description'):
            report.description = f"REJECTED: {reason}\n\n{report.description or ''}"
        
        # Add rejected_at field if it exists
        if hasattr(report, 'rejected_at'):
            report.rejected_at = datetime.utcnow()
        
        db.session.commit()
        
        current_app.logger.info(f"User {current_user.id} rejected report {report_id}: {reason}")
        
        return jsonify({'success': True, 'message': 'Report rejected successfully'})
        
    except Exception as e:
        current_app.logger.error(f"Error rejecting report: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to reject report'}), 500


@project_bp.route('/reports/<int:report_id>/export')
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER, Roles.PROJECT_STAFF])
def export_report(report_id):
    """Export a specific report"""
    try:
        report = Report.query.get_or_404(report_id)
        
        # If the report has a file, serve it
        if report.filename:
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'reports', report.filename)
            if os.path.exists(file_path):
                return send_file(file_path, as_attachment=True, download_name=report.filename)
        
        # Otherwise, generate a PDF export
        from flask import make_response
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        import io
        
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        
        # Add report content to PDF
        p.drawString(100, 750, f"Report: {getattr(report, 'title', report.filename)}")
        p.drawString(100, 730, f"Type: {report.type}")
        p.drawString(100, 710, f"Date: {report.date.strftime('%Y-%m-%d') if report.date else 'Unknown'}")
        
        if hasattr(report, 'description') and report.description:
            p.drawString(100, 690, "Description:")
            # Split long text into lines
            lines = report.description.split('\n')
            y = 670
            for line in lines:
                if len(line) > 80:
                    # Split long lines
                    words = line.split(' ')
                    current_line = ''
                    for word in words:
                        if len(current_line + word) < 80:
                            current_line += word + ' '
                        else:
                            p.drawString(100, y, current_line.strip())
                            y -= 20
                            current_line = word + ' '
                    if current_line:
                        p.drawString(100, y, current_line.strip())
                        y -= 20
                else:
                    p.drawString(100, y, line)
                    y -= 20
        
        p.showPage()
        p.save()
        
        buffer.seek(0)
        
        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=report_{report_id}.pdf'
        
        return response
        
    except Exception as e:
        current_app.logger.error(f"Error exporting report: {str(e)}")
        flash('Failed to export report.', 'error')
        return redirect(url_for('project.view_report', report_id=report_id))


# ============================================================================
# DPR CRUD OPERATIONS ADDITIONS
# ============================================================================

@project_bp.route('/dpr/<int:dpr_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER, Roles.PROJECT_STAFF])
def edit_dpr(dpr_id):
    """Edit an existing DPR"""
    try:
        dpr = DailyProductionReport.query.get_or_404(dpr_id)
        
        # Check access permissions
        has_access = (
            dpr.assigned_to_id == current_user.id or
            dpr.created_by_id == current_user.id or
            current_user.has_role(Roles.SUPER_HQ) or
            (current_user.has_role(Roles.PROJECT_MANAGER) and 
             dpr.project_id in get_user_accessible_project_ids(current_user))
        )
        
        if not has_access:
            flash('You do not have access to edit this DPR.', 'error')
            return redirect(url_for('project.view_dpr', dpr_id=dpr_id))
        
        if request.method == 'POST':
            # Update DPR fields
            dpr.issues = request.form.get('issues', dpr.issues)
            dpr.prepared_by = request.form.get('prepared_by', dpr.prepared_by)
            dpr.checked_by = request.form.get('checked_by', dpr.checked_by)
            
            # Update production items and material usage would go here
            # This would require more complex form handling
            
            db.session.commit()
            
            current_app.logger.info(f"User {current_user.id} updated DPR {dpr_id}")
            flash('DPR updated successfully.', 'success')
            return redirect(url_for('project.view_dpr', dpr_id=dpr_id))
        
        # Get production items and material usage
        production_items = dpr.production_items
        material_usage = dpr.material_usage
        
        return render_template('projects/dpr_edit.html',
                             dpr=dpr,
                             production_items=production_items,
                             material_usage=material_usage,
                             user_role=current_user.role)
        
    except Exception as e:
        current_app.logger.error(f"Error editing DPR: {str(e)}")
        flash('Failed to edit DPR.', 'error')
        return redirect(url_for('project.dpr_list'))


@project_bp.route('/dpr/<int:dpr_id>/delete', methods=['DELETE'])
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER])
def delete_dpr(dpr_id):
    """Delete a specific DPR"""
    try:
        dpr = DailyProductionReport.query.get_or_404(dpr_id)
        
        # Check access permissions
        has_access = (
            current_user.has_role(Roles.SUPER_HQ) or
            (current_user.has_role(Roles.PROJECT_MANAGER) and 
             dpr.project_id in get_user_accessible_project_ids(current_user))
        )
        
        if not has_access:
            return jsonify({'success': False, 'message': 'No permission to delete this DPR'}), 403
        
        # Delete related records first
        DPRProductionItem.query.filter_by(dpr_id=dpr_id).delete()
        DPRMaterialUsage.query.filter_by(dpr_id=dpr_id).delete()
        
        # Delete the DPR
        db.session.delete(dpr)
        db.session.commit()
        
        current_app.logger.info(f"User {current_user.id} deleted DPR {dpr_id}")
        
        return jsonify({'success': True, 'message': 'DPR deleted successfully'})
        
    except Exception as e:
        current_app.logger.error(f"Error deleting DPR: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to delete DPR'}), 500


@project_bp.route('/dpr/<int:dpr_id>/export')
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER, Roles.PROJECT_STAFF])
def export_dpr(dpr_id):
    """Export a specific DPR to PDF"""
    try:
        dpr = DailyProductionReport.query.get_or_404(dpr_id)
        
        # Check access permissions
        has_access = (
            dpr.assigned_to_id == current_user.id or
            dpr.created_by_id == current_user.id or
            current_user.has_role(Roles.SUPER_HQ) or
            (current_user.has_role(Roles.PROJECT_MANAGER) and 
             dpr.project_id in get_user_accessible_project_ids(current_user))
        )
        
        if not has_access:
            return jsonify({'success': False, 'message': 'No access to export this DPR'}), 403
        
        # Generate PDF export using reportlab
        from flask import make_response
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        import io
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title = f"Daily Production Report - {dpr.report_date.strftime('%B %d, %Y')}"
        story.append(Paragraph(title, styles['Title']))
        story.append(Spacer(1, 20))
        
        # Header info
        header_data = [
            ['Project:', dpr.project.name if dpr.project else 'Unknown'],
            ['Date:', dpr.report_date.strftime('%Y-%m-%d')],
            ['Status:', dpr.status.replace('_', ' ').title()],
            ['Created By:', dpr.created_by.name if dpr.created_by else 'Unknown'],
            ['Assigned To:', dpr.assigned_to.name if dpr.assigned_to else 'Unassigned']
        ]
        
        header_table = Table(header_data, colWidths=[100, 300])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.grey),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(header_table)
        story.append(Spacer(1, 20))
        
        # Production Items
        if dpr.production_items:
            story.append(Paragraph("Production Items", styles['Heading2']))
            
            prod_data = [['Item Code', 'Description', 'Location', 'Unit', 'Target Qty', 'Daily Qty', 'Total Done']]
            
            for item in dpr.production_items:
                prod_data.append([
                    item.item_code or '',
                    item.description or '',
                    item.location or '',
                    item.unit or '',
                    f"{item.target_qty:.2f}" if item.target_qty else '',
                    f"{item.day_production:.2f}" if item.day_production else '',
                    f"{item.total_qty_done:.2f}" if item.total_qty_done else ''
                ])
            
            prod_table = Table(prod_data, colWidths=[60, 120, 80, 40, 60, 60, 60])
            prod_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(prod_table)
            story.append(Spacer(1, 20))
        
        # Material Usage
        if dpr.material_usage:
            story.append(Paragraph("Material Usage", styles['Heading2']))
            
            mat_data = [['Item #', 'Description', 'Unit', 'Previous Used', 'Daily Usage', 'Total Used']]
            
            for material in dpr.material_usage:
                mat_data.append([
                    material.item_number or '',
                    material.description or '',
                    material.unit or '',
                    f"{material.previous_qty_used:.2f}" if material.previous_qty_used else '',
                    f"{material.day_usage:.2f}" if material.day_usage else '',
                    f"{material.total_qty_used:.2f}" if material.total_qty_used else ''
                ])
            
            mat_table = Table(mat_data, colWidths=[60, 140, 60, 80, 80, 80])
            mat_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(mat_table)
            story.append(Spacer(1, 20))
        
        # Issues and Comments
        if dpr.issues:
            story.append(Paragraph("Issues and Comments", styles['Heading2']))
            story.append(Paragraph(dpr.issues, styles['Normal']))
            story.append(Spacer(1, 20))
        
        # Signatures
        sig_data = [
            ['Prepared By:', dpr.prepared_by or ''],
            ['Checked By:', dpr.checked_by or '']
        ]
        
        sig_table = Table(sig_data, colWidths=[100, 200])
        sig_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12)
        ]))
        
        story.append(sig_table)
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=DPR_{dpr.project.name}_{dpr.report_date.strftime("%Y%m%d")}.pdf'
        
        current_app.logger.info(f"User {current_user.id} exported DPR {dpr_id}")
        
        return response
        
    except Exception as e:
        current_app.logger.error(f"Error exporting DPR: {str(e)}")
        import traceback
        current_app.logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'success': False, 'message': 'Failed to export DPR'}), 500


# ============================================================================
# BULK OPERATIONS AND EXPORT ROUTES
# ============================================================================

@project_bp.route('/reports/export_selected', methods=['POST'])
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER, Roles.PROJECT_STAFF])
def export_selected_reports():
    """Export selected reports"""
    try:
        report_ids = request.form.getlist('report_ids')
        if not report_ids:
            return jsonify({'success': False, 'message': 'No reports selected'}), 400
        
        # Convert to integers
        try:
            report_ids = [int(rid) for rid in report_ids]
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid report IDs'}), 400
        
        # Get the selected reports
        reports = Report.query.filter(Report.id.in_(report_ids)).all()
        
        if not reports:
            return jsonify({'success': False, 'message': 'No reports found'}), 404
        
        # Create ZIP export for multiple reports
        from flask import make_response
        import zipfile
        import io
        
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add a summary text file
            summary = f"Selected Reports Export\n"
            summary += f"Export Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}\n"
            summary += f"Total Reports: {len(reports)}\n\n"
            
            for report in reports:
                summary += f"- {report.type} Report ({report.date.strftime('%Y-%m-%d') if report.date else 'Unknown Date'})\n"
                summary += f"  ID: {report.id}\n"
                summary += f"  File: {report.filename}\n"
                if hasattr(report, 'description') and report.description:
                    summary += f"  Description: {report.description[:100]}...\n"
                summary += "\n"
            
            zip_file.writestr('selected_reports_summary.txt', summary)
            
            # Add individual report files if they exist
            for report in reports:
                if report.filename:
                    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'reports', report.filename)
                    if os.path.exists(file_path):
                        zip_file.write(file_path, f"reports/{report.filename}")
        
        zip_buffer.seek(0)
        
        response = make_response(zip_buffer.getvalue())
        response.headers['Content-Type'] = 'application/zip'
        response.headers['Content-Disposition'] = f'attachment; filename=selected_reports_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.zip'
        
        current_app.logger.info(f"User {current_user.id} exported {len(reports)} selected reports")
        
        return response
        
    except Exception as e:
        current_app.logger.error(f"Error exporting selected reports: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to export reports'}), 500


@project_bp.route('/reports/project/<int:project_id>/export')
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER, Roles.PROJECT_STAFF])
def export_project_reports(project_id):
    """Export all reports for a project"""
    try:
        # Check project access
        accessible_project_ids = get_user_accessible_project_ids(current_user)
        if project_id not in accessible_project_ids:
            return jsonify({'success': False, 'message': 'No access to project'}), 403
        
        project = Project.query.get_or_404(project_id)
        
        # For now, create a summary report
        from flask import make_response
        import zipfile
        import io
        
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add a summary text file
            summary = f"Project Reports Summary\n"
            summary += f"Project: {project.name}\n"
            summary += f"Export Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            reports = Report.query.order_by(Report.date.desc()).limit(20).all()
            summary += f"Total Reports: {len(reports)}\n\n"
            
            for report in reports:
                summary += f"- {report.type} Report ({report.date.strftime('%Y-%m-%d') if report.date else 'Unknown Date'})\n"
                summary += f"  File: {report.filename}\n\n"
            
            zip_file.writestr('reports_summary.txt', summary)
        
        zip_buffer.seek(0)
        
        response = make_response(zip_buffer.getvalue())
        response.headers['Content-Type'] = 'application/zip'
        response.headers['Content-Disposition'] = f'attachment; filename={project.name}_reports.zip'
        
        return response
        
    except Exception as e:
        current_app.logger.error(f"Error exporting project reports: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to export reports'}), 500


@project_bp.route('/dpr/export_selected', methods=['POST'])
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER, Roles.PROJECT_STAFF])
def export_selected_dprs():
    """Export selected DPRs"""
    try:
        dpr_ids = request.form.getlist('dpr_ids')
        if not dpr_ids:
            return jsonify({'success': False, 'message': 'No DPRs selected'}), 400
        
        # Convert to integers
        try:
            dpr_ids = [int(did) for did in dpr_ids]
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid DPR IDs'}), 400
        
        # Get the selected DPRs
        dprs = DailyProductionReport.query.filter(DailyProductionReport.id.in_(dpr_ids)).all()
        
        if not dprs:
            return jsonify({'success': False, 'message': 'No DPRs found'}), 404
        
        # Create Excel export for multiple DPRs
        from flask import make_response
        import pandas as pd
        import io
        
        # Prepare DPR data
        dpr_data = []
        prod_data = []
        mat_data = []
        
        for dpr in dprs:
            dpr_data.append({
                'DPR ID': dpr.id,
                'Date': dpr.report_date.strftime('%Y-%m-%d'),
                'Project': dpr.project.name if dpr.project else 'Unknown',
                'Status': dpr.status,
                'Created By': dpr.created_by.name if dpr.created_by else 'Unknown',
                'Assigned To': dpr.assigned_to.name if dpr.assigned_to else 'Unassigned',
                'Completed At': dpr.completed_at.strftime('%Y-%m-%d %H:%M') if dpr.completed_at else '',
                'Issues': dpr.issues or '',
                'Prepared By': dpr.prepared_by or '',
                'Checked By': dpr.checked_by or ''
            })
            
            # Production items
            for item in dpr.production_items:
                prod_data.append({
                    'DPR ID': dpr.id,
                    'DPR Date': dpr.report_date.strftime('%Y-%m-%d'),
                    'Item Code': item.item_code,
                    'Description': item.description,
                    'Location': item.location,
                    'Unit': item.unit,
                    'Target Qty': item.target_qty,
                    'Previous Done': item.previous_qty_done,
                    'Daily Production': item.day_production,
                    'Total Done': item.total_qty_done
                })
            
            # Material usage
            for material in dpr.material_usage:
                mat_data.append({
                    'DPR ID': dpr.id,
                    'DPR Date': dpr.report_date.strftime('%Y-%m-%d'),
                    'Item Number': material.item_number,
                    'Description': material.description,
                    'Unit': material.unit,
                    'Previous Used': material.previous_qty_used,
                    'Daily Usage': material.day_usage,
                    'Total Used': material.total_qty_used
                })
        
        # Create Excel file
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # DPR Summary sheet
            df_summary = pd.DataFrame(dpr_data)
            df_summary.to_excel(writer, sheet_name='Selected DPRs Summary', index=False)
            
            # Production Items sheet
            if prod_data:
                df_production = pd.DataFrame(prod_data)
                df_production.to_excel(writer, sheet_name='Production Items', index=False)
            
            # Material Usage sheet
            if mat_data:
                df_materials = pd.DataFrame(mat_data)
                df_materials.to_excel(writer, sheet_name='Material Usage', index=False)
        
        output.seek(0)
        
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response.headers['Content-Disposition'] = f'attachment; filename=selected_DPRs_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        current_app.logger.info(f"User {current_user.id} exported {len(dprs)} selected DPRs")
        
        return response
        
    except Exception as e:
        current_app.logger.error(f"Error exporting selected DPRs: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to export DPRs'}), 500


@project_bp.route('/dpr/project/<int:project_id>/export')
@login_required
@role_required([Roles.SUPER_HQ, Roles.PROJECT_MANAGER, Roles.PROJECT_STAFF])
def export_project_dprs(project_id):
    """Export all DPRs for a project"""
    try:
        # Check project access
        accessible_project_ids = get_user_accessible_project_ids(current_user)
        if project_id not in accessible_project_ids:
            return jsonify({'success': False, 'message': 'No access to project'}), 403
        
        project = Project.query.get_or_404(project_id)
        dprs = DailyProductionReport.query.filter_by(project_id=project_id).order_by(
            DailyProductionReport.report_date.desc()
        ).all()
        
        # Create Excel export
        from flask import make_response
        import pandas as pd
        import io
        
        # Prepare DPR data
        dpr_data = []
        for dpr in dprs:
            dpr_data.append({
                'Date': dpr.report_date.strftime('%Y-%m-%d'),
                'Status': dpr.status,
                'Created By': dpr.created_by.name if dpr.created_by else 'Unknown',
                'Assigned To': dpr.assigned_to.name if dpr.assigned_to else 'Unassigned',
                'Completed At': dpr.completed_at.strftime('%Y-%m-%d %H:%M') if dpr.completed_at else '',
                'Issues': dpr.issues or '',
                'Prepared By': dpr.prepared_by or '',
                'Checked By': dpr.checked_by or ''
            })
        
        # Create Excel file
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # DPR Summary sheet
            df_summary = pd.DataFrame(dpr_data)
            df_summary.to_excel(writer, sheet_name='DPR Summary', index=False)
            
            # Production Items sheet
            prod_data = []
            for dpr in dprs:
                for item in dpr.production_items:
                    prod_data.append({
                        'DPR Date': dpr.report_date.strftime('%Y-%m-%d'),
                        'Item Code': item.item_code,
                        'Description': item.description,
                        'Location': item.location,
                        'Unit': item.unit,
                        'Target Qty': item.target_qty,
                        'Previous Done': item.previous_qty_done,
                        'Daily Production': item.day_production,
                        'Total Done': item.total_qty_done
                    })
            
            if prod_data:
                df_production = pd.DataFrame(prod_data)
                df_production.to_excel(writer, sheet_name='Production Items', index=False)
            
            # Material Usage sheet
            mat_data = []
            for dpr in dprs:
                for material in dpr.material_usage:
                    mat_data.append({
                        'DPR Date': dpr.report_date.strftime('%Y-%m-%d'),
                        'Item Number': material.item_number,
                        'Description': material.description,
                        'Unit': material.unit,
                        'Previous Used': material.previous_qty_used,
                        'Daily Usage': material.day_usage,
                        'Total Used': material.total_qty_used
                    })
            
            if mat_data:
                df_materials = pd.DataFrame(mat_data)
                df_materials.to_excel(writer, sheet_name='Material Usage', index=False)
        
        output.seek(0)
        
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response.headers['Content-Disposition'] = f'attachment; filename={project.name}_DPRs.xlsx'
        
        current_app.logger.info(f"User {current_user.id} exported all DPRs for project {project_id}")
        
        return response
        
    except Exception as e:
        current_app.logger.error(f"Error exporting project DPRs: {str(e)}")
        import traceback
        current_app.logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'success': False, 'message': 'Failed to export DPRs'}), 500


# --- BOQ (Bill of Quantities) Management Routes ---

@project_bp.route('/projects/<int:project_id>/boq')
@login_required
def view_boq(project_id):
    """View BOQ for a project"""
    try:
        project = db.session.get(Project, project_id)
        if not project:
            flash('Project not found', 'error')
            return redirect(url_for('project.projects_dashboard'))
        
        # Check access
        if not current_user.has_role(Roles.SUPER_HQ):
            user_projects = get_user_accessible_projects(current_user)
            if project not in user_projects:
                flash('You do not have access to this project', 'error')
                return redirect(url_for('project.projects_dashboard'))
        
        # Import BOQItem here to avoid circular imports
        from models import BOQItem
        
        # Get BOQ items for this project
        boq_items = BOQItem.query.filter_by(project_id=project_id).order_by(
            BOQItem.bill_no, BOQItem.item_no
        ).all()
        
        # Calculate totals
        total_cost = sum(item.total_cost for item in boq_items)
        
        # Group by bill number
        boq_by_bill = {}
        for item in boq_items:
            if item.bill_no not in boq_by_bill:
                boq_by_bill[item.bill_no] = []
            boq_by_bill[item.bill_no].append(item)
        
        return render_template('project/view_boq.html',
                             project=project,
                             boq_items=boq_items,
                             boq_by_bill=boq_by_bill,
                             total_cost=total_cost)
    
    except Exception as e:
        current_app.logger.error(f"Error viewing BOQ: {str(e)}")
        flash('Error loading BOQ', 'error')
        return redirect(url_for('project.projects_dashboard'))


@project_bp.route('/projects/<int:project_id>/boq/load-template', methods=['POST'])
@login_required
def load_boq_template(project_id):
    """Load BOQ template items based on project type"""
    try:
        project = db.session.get(Project, project_id)
        if not project:
            return jsonify({'success': False, 'message': 'Project not found'}), 404
        
        # Check access
        if not current_user.has_role(Roles.SUPER_HQ):
            user_projects = get_user_accessible_projects(current_user)
            if project not in user_projects:
                return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        from models import BOQItem
        
        # Get template items based on project type
        project_type = project.project_type
        if not project_type:
            return jsonify({'success': False, 'message': 'Project type not set'}), 400
        
        # Map combined project types to individual templates
        item_types = []
        if 'Bridge' in project_type:
            item_types.append('Bridge')
        if 'Building' in project_type:
            item_types.append('Building')
        if 'Road' in project_type:
            item_types.append('Road')
        if 'Culvert' in project_type:
            item_types.append('Culvert')
        
        if not item_types:
            # Default to exact match
            item_types = [project_type]
        
        # Get template items
        template_items = BOQItem.query.filter(
            BOQItem.is_template == True,
            BOQItem.item_type.in_(item_types)
        ).all()
        
        if not template_items:
            return jsonify({'success': False, 'message': f'No BOQ template found for {project_type}'}), 404
        
        # Copy template items to project
        items_added = 0
        for template in template_items:
            new_item = BOQItem(
                project_id=project_id,
                bill_no=template.bill_no,
                item_no=template.item_no,
                item_description=template.item_description,
                quantity=template.quantity,
                unit=template.unit,
                unit_price=template.unit_price,
                total_cost=template.total_cost,
                item_type=template.item_type,
                category=template.category,
                is_template=False
            )
            db.session.add(new_item)
            items_added += 1
        
        db.session.commit()
        
        current_app.logger.info(f"User {current_user.id} loaded {items_added} BOQ template items for project {project_id}")
        
        return jsonify({
            'success': True,
            'message': f'Successfully loaded {items_added} BOQ items from template',
            'items_added': items_added
        })
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error loading BOQ template: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to load BOQ template'}), 500


@project_bp.route('/projects/<int:project_id>/boq/add', methods=['POST'])
@login_required
def add_boq_item(project_id):
    """Add a new BOQ item to a project"""
    try:
        project = db.session.get(Project, project_id)
        if not project:
            return jsonify({'success': False, 'message': 'Project not found'}), 404
        
        # Check access
        if not current_user.has_role(Roles.SUPER_HQ):
            user_projects = get_user_accessible_projects(current_user)
            if project not in user_projects:
                return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        from models import BOQItem
        
        data = request.get_json()
        
        # Create new BOQ item
        new_item = BOQItem(
            project_id=project_id,
            bill_no=data.get('bill_no'),
            item_no=data.get('item_no'),
            item_description=data.get('item_description'),
            quantity=float(data.get('quantity', 0)),
            unit=data.get('unit'),
            unit_price=float(data.get('unit_price', 0)),
            category=data.get('category'),
            is_template=False
        )
        new_item.calculate_total_cost()
        
        db.session.add(new_item)
        db.session.commit()
        
        current_app.logger.info(f"User {current_user.id} added BOQ item {new_item.id} to project {project_id}")
        
        return jsonify({
            'success': True,
            'message': 'BOQ item added successfully',
            'item': {
                'id': new_item.id,
                'bill_no': new_item.bill_no,
                'item_no': new_item.item_no,
                'item_description': new_item.item_description,
                'quantity': new_item.quantity,
                'unit': new_item.unit,
                'unit_price': new_item.unit_price,
                'total_cost': new_item.total_cost
            }
        })
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error adding BOQ item: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to add BOQ item'}), 500


@project_bp.route('/projects/<int:project_id>/boq/<int:item_id>/edit', methods=['POST'])
@login_required
def edit_boq_item(project_id, item_id):
    """Edit an existing BOQ item"""
    try:
        from models import BOQItem
        
        item = db.session.get(BOQItem, item_id)
        if not item or item.project_id != project_id:
            return jsonify({'success': False, 'message': 'BOQ item not found'}), 404
        
        # Check access
        project = db.session.get(Project, project_id)
        if not current_user.has_role(Roles.SUPER_HQ):
            user_projects = get_user_accessible_projects(current_user)
            if project not in user_projects:
                return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        data = request.get_json()
        
        # Update item
        item.bill_no = data.get('bill_no', item.bill_no)
        item.item_no = data.get('item_no', item.item_no)
        item.item_description = data.get('item_description', item.item_description)
        item.quantity = float(data.get('quantity', item.quantity))
        item.unit = data.get('unit', item.unit)
        item.unit_price = float(data.get('unit_price', item.unit_price))
        item.category = data.get('category', item.category)
        
        item.calculate_total_cost()
        
        db.session.commit()
        
        current_app.logger.info(f"User {current_user.id} edited BOQ item {item_id}")
        
        return jsonify({
            'success': True,
            'message': 'BOQ item updated successfully',
            'item': {
                'id': item.id,
                'bill_no': item.bill_no,
                'item_no': item.item_no,
                'item_description': item.item_description,
                'quantity': item.quantity,
                'unit': item.unit,
                'unit_price': item.unit_price,
                'total_cost': item.total_cost
            }
        })
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error editing BOQ item: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to update BOQ item'}), 500


@project_bp.route('/projects/<int:project_id>/boq/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_boq_item(project_id, item_id):
    """Delete a BOQ item"""
    try:
        from models import BOQItem
        
        item = db.session.get(BOQItem, item_id)
        if not item or item.project_id != project_id:
            return jsonify({'success': False, 'message': 'BOQ item not found'}), 404
        
        # Check access
        project = db.session.get(Project, project_id)
        if not current_user.has_role(Roles.SUPER_HQ):
            user_projects = get_user_accessible_projects(current_user)
            if project not in user_projects:
                return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        db.session.delete(item)
        db.session.commit()
        
        current_app.logger.info(f"User {current_user.id} deleted BOQ item {item_id}")
        
        return jsonify({
            'success': True,
            'message': 'BOQ item deleted successfully'
        })
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting BOQ item: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to delete BOQ item'}), 500


@project_bp.route('/projects/<int:project_id>/boq/import-excel', methods=['POST'])
@login_required
def import_boq_excel(project_id):
    """Import BOQ items from Excel file"""
    try:
        project = db.session.get(Project, project_id)
        if not project:
            return jsonify({'success': False, 'message': 'Project not found'}), 404
        
        # Check access
        if not current_user.has_role(Roles.SUPER_HQ):
            user_projects = get_user_accessible_projects(current_user)
            if project not in user_projects:
                return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'}), 400
        
        if not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify({'success': False, 'message': 'Invalid file format. Please upload an Excel file'}), 400
        
        from models import BOQItem
        import pandas as pd
        
        # Read Excel file
        df = pd.read_excel(file)
        
        # Validate required columns
        required_columns = ['bill_no', 'item_no', 'item_description', 'quantity', 'unit', 'unit_price']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return jsonify({
                'success': False,
                'message': f'Missing required columns: {", ".join(missing_columns)}'
            }), 400
        
        # Import items
        items_added = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                new_item = BOQItem(
                    project_id=project_id,
                    bill_no=str(row['bill_no']),
                    item_no=str(row['item_no']),
                    item_description=str(row['item_description']),
                    quantity=float(row['quantity']),
                    unit=str(row['unit']),
                    unit_price=float(row['unit_price']),
                    category=str(row.get('category', '')),
                    is_template=False
                )
                new_item.calculate_total_cost()
                db.session.add(new_item)
                items_added += 1
            except Exception as e:
                errors.append(f"Row {index + 2}: {str(e)}")
        
        db.session.commit()
        
        current_app.logger.info(f"User {current_user.id} imported {items_added} BOQ items to project {project_id}")
        
        message = f'Successfully imported {items_added} BOQ items'
        if errors:
            message += f'. {len(errors)} errors occurred.'
        
        return jsonify({
            'success': True,
            'message': message,
            'items_added': items_added,
            'errors': errors if errors else None
        })
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error importing BOQ from Excel: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to import BOQ'}), 500


@project_bp.route('/projects/<int:project_id>/boq/export-excel')
@login_required
def export_boq_excel(project_id):
    """Export BOQ items to Excel file"""
    try:
        project = db.session.get(Project, project_id)
        if not project:
            flash('Project not found', 'error')
            return redirect(url_for('project.projects_dashboard'))
        
        # Check access
        if not current_user.has_role(Roles.SUPER_HQ):
            user_projects = get_user_accessible_projects(current_user)
            if project not in user_projects:
                flash('Access denied', 'error')
                return redirect(url_for('project.projects_dashboard'))
        
        from models import BOQItem
        import pandas as pd
        from io import BytesIO
        from flask import make_response
        
        # Get BOQ items
        boq_items = BOQItem.query.filter_by(project_id=project_id).order_by(
            BOQItem.bill_no, BOQItem.item_no
        ).all()
        
        if not boq_items:
            flash('No BOQ items to export', 'warning')
            return redirect(url_for('project.view_boq', project_id=project_id))
        
        # Create DataFrame
        data = []
        for item in boq_items:
            data.append({
                'Bill No': item.bill_no,
                'Item No': item.item_no,
                'Description': item.item_description,
                'Quantity': item.quantity,
                'Unit': item.unit,
                'Unit Price': item.unit_price,
                'Total Cost': item.total_cost,
                'Category': item.category
            })
        
        df = pd.DataFrame(data)
        
        # Create Excel file
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='BOQ', index=False)
        
        output.seek(0)
        
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response.headers['Content-Disposition'] = f'attachment; filename={project.name}_BOQ.xlsx'
        
        current_app.logger.info(f"User {current_user.id} exported BOQ for project {project_id}")
        
        return response
    
    except Exception as e:
        current_app.logger.error(f"Error exporting BOQ to Excel: {str(e)}")
        flash('Error exporting BOQ', 'error')
        return redirect(url_for('project.view_boq', project_id=project_id))

