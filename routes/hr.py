from flask import Blueprint, render_template, current_app, flash, request, jsonify, url_for, redirect, session
from datetime import datetime, timedelta
from utils.decorators import role_required
from utils.constants import Roles

hr_bp = Blueprint("hr", __name__, url_prefix="/hr")

# Dashboard Route
@hr_bp.route("/")
@role_required([Roles.SUPER_HQ, Roles.HQ_HR])
def hr_home():
    try:
        summary = {
            'total_staff': 246,
            'active_leaves': 12,
            'pending_queries': 5,
            'attendance_today': 232,
            'pending_tasks': 18,
            'pending_payroll': 3500000
        }
        return render_template('hr/index.html', summary=summary)
    except Exception as e:
        current_app.logger.error(f"HR dashboard error: {str(e)}")
        flash("Error loading HR dashboard", "error")
        return render_template('error.html'), 500

# Leave Management Routes
@hr_bp.route("/leave")
@role_required([Roles.SUPER_HQ, Roles.HQ_HR])
def leave_management():
    try:
        # Stats data
        leaves = {
            'pending': 5,
            'approved': 12,
            'rejected': 2,
            'upcoming': 8
        }
        
        # Sample leave events data
        leave_events = [
            {
                'title': 'John Doe - Annual Leave',
                'start': '2025-09-15',
                'end': '2025-09-20',
                'extendedProps': {
                    'status': 'approved',
                    'type': 'Annual Leave',
                    'staff': 'John Doe',
                    'department': 'Engineering'
                }
            },
            {
                'title': 'Jane Smith - Sick Leave',
                'start': '2025-09-10',
                'end': '2025-09-12',
                'extendedProps': {
                    'status': 'pending',
                    'type': 'Sick Leave',
                    'staff': 'Jane Smith',
                    'department': 'HR'
                }
            }
        ]
        
        return render_template('hr/leave/index.html', 
                             leaves=leaves,
                             leave_events=leave_events)
                             
    except Exception as e:
        current_app.logger.error(f"Leave management error: {str(e)}")
        flash("Error loading leave management", "error")
        return render_template('error.html'), 500

# Staff Query Routes
@hr_bp.route("/queries")
@role_required([Roles.SUPER_HQ, Roles.HQ_HR])
def staff_queries():
    try:
        # Add query statistics
        stats = {
            'total': 28,
            'pending': 5,
            'in_progress': 8,
            'resolved': 15
        }
        
        # Mock queries list
        queries_list = [
            {
                'id': 1,
                'subject': 'Leave Balance Inquiry',
                'staff': 'John Doe',
                'department': 'Engineering',
                'status': 'Pending',
                'priority': 'Medium',
                'submitted_at': '2025-09-02 14:30:00',
                'description': 'Need clarification on remaining leave days'
            },
            {
                'id': 2,
                'subject': 'Payroll Discrepancy',
                'staff': 'Jane Smith',
                'department': 'Finance',
                'status': 'In Progress',
                'priority': 'High',
                'submitted_at': '2025-09-01 09:15:00',
                'description': 'Overtime hours not reflected in last payroll'
            }
        ]
        
        # Categories for filtering
        categories = [
            {'id': 1, 'name': 'Leave'},
            {'id': 2, 'name': 'Payroll'},
            {'id': 3, 'name': 'Benefits'},
            {'id': 4, 'name': 'General'}
        ]
        
        return render_template('hr/queries/index.html',
                             stats=stats,
                             queries=queries_list,
                             categories=categories)
    except Exception as e:
        current_app.logger.error(f"Staff queries error: {str(e)}")
        flash("Error loading staff queries", "error")
        return render_template('error.html'), 500

# Attendance Management Routes
@hr_bp.route("/attendance")
@role_required([Roles.SUPER_HQ, Roles.HQ_HR])
def attendance():
    try:
        attendance_data = {
            'present': 232,
            'absent': 14,
            'late': 8,
            'on_leave': 12
        }
        return render_template('hr/attendance/index.html', attendance=attendance_data)
    except Exception as e:
        current_app.logger.error(f"Attendance error: {str(e)}")
        flash("Error loading attendance", "error")
        return render_template('error.html'), 500

# Task Assignment Routes
@hr_bp.route("/tasks")
@role_required([Roles.SUPER_HQ, Roles.HQ_HR])
def tasks():
    try:
        # Add task statistics
        stats = {
            'total': 45,
            'completed': 27,
            'in_progress': 12,
            'pending': 6,
            'overdue': 3
        }
        
        # Mock tasks list data
        tasks_list = [
            {
                'id': 1,
                'title': 'Review Leave Requests',
                'assignee': 'John Doe',
                'due_date': '2025-09-05',
                'priority': 'High',
                'status': 'Pending',
                'description': 'Review and approve pending leave requests',
                'department': 'HR'
            },
            {
                'id': 2,
                'title': 'Payroll Processing',
                'assignee': 'Jane Smith',
                'due_date': '2025-09-10',
                'priority': 'High',
                'status': 'In Progress',
                'description': 'Process monthly payroll for all departments',
                'department': 'HR'
            }
        ]
        
        # Department list for filters
        departments = [
            {'id': 1, 'name': 'Engineering'},
            {'id': 2, 'name': 'HR'},
            {'id': 3, 'name': 'Finance'},
            {'id': 4, 'name': 'Operations'}
        ]
        
        return render_template('hr/tasks/index.html',
                             stats=stats,
                             tasks=tasks_list,
                             departments=departments)
    except Exception as e:
        current_app.logger.error(f"Tasks error: {str(e)}")
        flash("Error loading tasks", "error")
        return render_template('error.html'), 500

# Payroll Routes
@hr_bp.route("/payroll")
@role_required([Roles.SUPER_HQ, Roles.HQ_HR])
def payroll():
    try:
        payroll_data = {
            'total_payroll': 3500000,
            'regular_staff': 182,
            'contract_staff': 64,
            'next_payday': (datetime.now() + timedelta(days=15)).strftime('%Y-%m-%d')
        }
        return render_template('hr/payroll/index.html', payroll=payroll_data)
    except Exception as e:
        current_app.logger.error(f"Payroll error: {str(e)}")
        flash("Error loading payroll", "error")
        return render_template('error.html'), 500

# Staff Details Routes
@hr_bp.route("/staff")
@role_required([Roles.SUPER_HQ, Roles.HQ_HR])
def staff_list():
    try:
        # Add staff statistics
        stats = {
            'total_staff': 246,
            'active': 232,
            'departments': 8,
            'new_staff': 5
        }
        
        # Mock staff list data
        staff_list = [
            {
                'id': 1,
                'name': 'John Doe',
                'email': 'john.doe@sammy.com',
                'department': 'Engineering',
                'position': 'Software Engineer',
                'status': 'Active',
                'avatar_url': 'https://ui-avatars.com/api/?name=John+Doe'
            },
            {
                'id': 2,
                'name': 'Jane Smith',
                'email': 'jane.smith@sammy.com',
                'department': 'HR',
                'position': 'HR Manager',
                'status': 'Active',
                'avatar_url': 'https://ui-avatars.com/api/?name=Jane+Smith'
            }
        ]
        
        # Department list for filters
        departments = [
            {'id': 1, 'name': 'Engineering'},
            {'id': 2, 'name': 'HR'},
            {'id': 3, 'name': 'Finance'},
            {'id': 4, 'name': 'Operations'}
        ]
        
        return render_template('hr/staff/index.html', 
                             stats=stats,
                             staff_list=staff_list,
                             departments=departments)
    except Exception as e:
        current_app.logger.error(f"Staff list error: {str(e)}")
        flash("Error loading staff list", "error")
        return render_template('error.html'), 500

@hr_bp.route("/staff/<int:staff_id>")
@role_required([Roles.SUPER_HQ, Roles.HQ_HR])
def staff_details(staff_id):
    try:
        # Mock staff data - replace with database query
        staff = {
            'id': staff_id,
            'name': 'John Doe',
            'email': 'john.doe@sammy.com',
            'phone': '+234 123 456 7890',
            'employee_id': 'EMP001',
            'department': 'Engineering',
            'position': 'Software Engineer',
            'status': 'Active',
            'avatar_url': 'https://ui-avatars.com/api/?name=John+Doe',
            'dob': '1990-05-15',
            'address': '123 Tech Street, Lagos',
            'emergency_contact_name': 'Jane Doe',
            'emergency_contact_phone': '+234 987 654 3210',
            'date_joined': '2024-01-15',
            'employment_type': 'Full-time',
            'manager': {
                'name': 'Sarah Manager',
                'avatar_url': 'https://ui-avatars.com/api/?name=Sarah+Manager'
            },
            'recent_activities': [
                {
                    'icon': 'bx-calendar-check',
                    'description': 'Approved leave request',
                    'timestamp': '2 hours ago'
                },
                {
                    'icon': 'bx-task',
                    'description': 'Completed Project Milestone',
                    'timestamp': '1 day ago'
                }
            ],
            'leave_history': [
                {
                    'type': 'Annual Leave',
                    'start_date': '2025-08-01',
                    'end_date': '2025-08-07',
                    'status': 'Approved'
                },
                {
                    'type': 'Sick Leave',
                    'start_date': '2025-07-15',
                    'end_date': '2025-07-16',
                    'status': 'Approved'
                }
            ]
        }
        
        return render_template('hr/staff/details.html', staff=staff)
    except Exception as e:
        current_app.logger.error(f"Staff details error: {str(e)}")
        flash("Error loading staff details", "error")
        return render_template('error.html'), 500

# API Routes for AJAX calls
@hr_bp.route("/api/staff/search")
@role_required([Roles.SUPER_HQ, Roles.HQ_HR])
def search_staff():
    try:
        query = request.args.get('q', '').lower()
        # Mock staff data - replace with database query
        mock_staff = [
            {
                'id': 1,
                'name': 'John Doe',
                'employee_id': 'EMP001',
                'department': 'Engineering',
                'position': 'Software Engineer',
                'status': 'Active'
            },
            {
                'id': 2,
                'name': 'Jane Smith',
                'employee_id': 'EMP002',
                'department': 'HR',
                'position': 'HR Manager',
                'status': 'Active'
            }
        ]
        
        # Filter staff based on query
        results = [
            staff for staff in mock_staff 
            if query in staff['name'].lower() or 
               query in staff['employee_id'].lower() or 
               query in staff['department'].lower()
        ]
        
        return jsonify({
            'status': 'success',
            'data': results,
            'count': len(results)
        })
    except Exception as e:
        current_app.logger.error(f"Staff search error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)})

@hr_bp.route("/api/attendance/today")
@role_required([Roles.SUPER_HQ, Roles.HQ_HR])
def today_attendance():
    try:
        today = datetime.now().date()
        # Mock attendance data - replace with database query
        attendance_data = {
            'date': today.strftime('%Y-%m-%d'),
            'summary': {
                'present': 232,
                'absent': 14,
                'late': 8,
                'on_leave': 12
            },
            'details': [
                {
                    'employee_id': 'EMP001',
                    'name': 'John Doe',
                    'status': 'Present',
                    'check_in': '08:30',
                    'check_out': '17:00',
                    'department': 'Engineering'
                },
                {
                    'employee_id': 'EMP002',
                    'name': 'Jane Smith',
                    'status': 'Late',
                    'check_in': '09:45',
                    'check_out': None,
                    'department': 'HR'
                }
            ]
        }
        
        return jsonify({
            'status': 'success',
            'data': attendance_data
        })
    except Exception as e:
        current_app.logger.error(f"Attendance fetch error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)})

# Additional API endpoints for other functionalities
@hr_bp.route("/api/leave/pending")
@role_required([Roles.SUPER_HQ, Roles.HQ_HR])
def pending_leaves():
    try:
        # Mock pending leave data
        pending_leaves = [
            {
                'id': 1,
                'employee': 'John Doe',
                'type': 'Annual Leave',
                'start_date': '2025-09-15',
                'end_date': '2025-09-20',
                'status': 'Pending',
                'applied_on': '2025-09-02'
            }
        ]
        return jsonify({
            'status': 'success',
            'data': pending_leaves
        })
    except Exception as e:
        current_app.logger.error(f"Pending leaves fetch error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)})

@hr_bp.route("/api/tasks/summary")
@role_required([Roles.SUPER_HQ, Roles.HQ_HR])
def task_summary():
    try:
        # Mock task summary data
        summary = {
            'total': 45,
            'completed': 27,
            'in_progress': 12,
            'pending': 6,
            'overdue': 3,
            'recent_tasks': [
                {
                    'id': 1,
                    'title': 'Review Leave Requests',
                    'due_date': '2025-09-05',
                    'priority': 'High',
                    'status': 'Pending'
                }
            ]
        }
        return jsonify({
            'status': 'success',
            'data': summary
        })
    except Exception as e:
        current_app.logger.error(f"Task summary fetch error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)})

# Reports Routes
@hr_bp.route("/reports")
@role_required([Roles.SUPER_HQ, Roles.HQ_HR])
def reports():
    try:
        report_data = {
            'available_reports': [
                {
                    'id': 1,
                    'title': 'Monthly Attendance Report',
                    'type': 'attendance',
                    'last_generated': '2025-09-01',
                    'format': 'PDF'
                },
                {
                    'id': 2,
                    'title': 'Leave Statistics Q3 2025',
                    'type': 'leave',
                    'last_generated': '2025-09-01',
                    'format': 'Excel'
                },
                {
                    'id': 3,
                    'title': 'Staff Performance Review',
                    'type': 'performance',
                    'last_generated': '2025-08-30',
                    'format': 'PDF'
                },
                {
                    'id': 4,
                    'title': 'Payroll Summary',
                    'type': 'payroll',
                    'last_generated': '2025-09-01',
                    'format': 'Excel'
                }
            ],
            'recent_downloads': [
                {
                    'report_name': 'August 2025 Attendance',
                    'downloaded_at': '2025-09-01 10:30:00',
                    'downloaded_by': 'HR Manager'
                }
            ]
        }
        return render_template('hr/reports/index.html', reports=report_data)
    except Exception as e:
        current_app.logger.error(f"Reports error: {str(e)}")
        flash("Error loading reports", "error")
        return render_template('error.html'), 500

@hr_bp.route("/analytics")
@role_required([Roles.SUPER_HQ, Roles.HQ_HR])
def analytics():
    try:
        analytics_data = {
            'attendance_trends': {
                'labels': ['Jun', 'Jul', 'Aug', 'Sep'],
                'present': [95, 93, 96, 94],
                'absent': [5, 7, 4, 6],
                'late': [2, 3, 2, 4]
            },
            'leave_distribution': {
                'annual': 45,
                'sick': 15,
                'maternity': 2,
                'study': 3
            },
            'department_stats': [
                {
                    'name': 'Engineering',
                    'staff_count': 85,
                    'attendance_rate': 96,
                    'leave_usage': 12
                },
                {
                    'name': 'Finance',
                    'staff_count': 45,
                    'attendance_rate': 98,
                    'leave_usage': 8
                }
            ],
            'performance_metrics': {
                'high_performers': 45,
                'average_performers': 180,
                'needs_improvement': 21
            }
        }
        return render_template('hr/analytics/index.html', analytics=analytics_data)
    except Exception as e:
        current_app.logger.error(f"Analytics error: {str(e)}")
        flash("Error loading analytics", "error")
        return render_template('error.html'), 500

# API Routes for Reports and Analytics
@hr_bp.route("/api/reports/generate", methods=['POST'])
@role_required([Roles.SUPER_HQ, Roles.HQ_HR])
def generate_report():
    try:
        report_type = request.json.get('type')
        date_range = request.json.get('date_range')
        format = request.json.get('format', 'PDF')
        
        # Mock report generation response
        return jsonify({
            'status': 'success',
            'message': f'Report generation started for {report_type}',
            'job_id': '12345'
        })
    except Exception as e:
        current_app.logger.error(f"Report generation error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)})

@hr_bp.route("/api/analytics/data")
@role_required([Roles.SUPER_HQ, Roles.HQ_HR])
def analytics_data():
    try:
        metric = request.args.get('metric')
        period = request.args.get('period', 'monthly')
        
        # Mock analytics data response
        data = {
            'labels': ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
            'values': [92, 95, 88, 93],
            'trend': 'positive',
            'change_percentage': 2.5
        }
        
        return jsonify({
            'status': 'success',
            'data': data
        })
    except Exception as e:
        current_app.logger.error(f"Analytics data fetch error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)})

@hr_bp.route('/logout')
@role_required([Roles.SUPER_HQ, Roles.HQ_HR])
def logout():
    try:
        # Clear all session data
        session.clear()
        flash("Successfully logged out", "success")
        return redirect(url_for('auth.login'))
    except Exception as e:
        current_app.logger.error(f"Logout error: {str(e)}")
        flash("Error during logout", "error")
        return redirect(url_for('hr.hr_home'))

@hr_bp.route("/profile")
@role_required([Roles.SUPER_HQ, Roles.HQ_HR])
def profile():
    try:
        user_data = {
            'name': 'John Doe',
            'position': 'HR Manager',
            'email': 'john.doe@sammy.com',
            'phone': '+234 123 456 7890',
            'avatar_url': None,  # Will use UI Avatars as fallback
            'leave_balance': 15,
            'attendance_rate': 98,
            'completed_tasks': 45,
            'recent_activities': [
                {
                    'icon': 'bx-file',
                    'description': 'Generated monthly attendance report',
                    'timestamp': '2 hours ago'
                },
                {
                    'icon': 'bx-check-circle',
                    'description': 'Approved leave request for Jane Smith',
                    'timestamp': '4 hours ago'
                }
            ]
        }
        return render_template('hr/profile/index.html', user=user_data)
    except Exception as e:
        current_app.logger.error(f"Profile error: {str(e)}")
        flash("Error loading profile", "error")
        return render_template('error.html'), 500

@hr_bp.route("/settings")
@role_required([Roles.SUPER_HQ, Roles.HQ_HR])
def settings():
    try:
        return render_template('hr/settings/index.html')
    except Exception as e:
        current_app.logger.error(f"Settings error: {str(e)}")
        flash("Error loading settings", "error")
        return render_template('error.html'), 500

