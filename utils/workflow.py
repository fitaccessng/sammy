"""
Approval Workflow Management Utilities
"""
from datetime import datetime, timezone
from flask import current_app, request
from extensions import db
from models import ApprovalWorkflow, WorkflowStep, Notification, AuditLog
from utils.email import send_email
import json


def create_approval_workflow(workflow_type, reference_id, reference_number, initiated_by, 
                            total_amount=None, description=None, project_id=None, priority='normal'):
    """
    Create a new approval workflow
    
    Args:
        workflow_type: Type of workflow (purchase_order, payroll, budget_adjustment, etc.)
        reference_id: ID of the item being approved
        reference_number: Human-readable reference (PO-001, PAY-2024-01)
        initiated_by: User ID who initiated the workflow
        total_amount: Total amount (optional)
        description: Description (optional)
        project_id: Project ID (optional)
        priority: Priority level (low, normal, high, urgent)
    
    Returns:
        ApprovalWorkflow instance
    """
    # Define workflow steps based on type
    workflow_steps_config = {
        'purchase_order': [
            {'step_order': 1, 'step_name': 'cost_control_approval', 'required_role': 'hq_cost_control'},
            {'step_order': 2, 'step_name': 'finance_approval', 'required_role': 'hq_finance'}
        ],
        'payroll': [
            {'step_order': 1, 'step_name': 'finance_approval', 'required_role': 'hq_finance'}
        ],
        'budget_adjustment': [
            {'step_order': 1, 'step_name': 'finance_approval', 'required_role': 'hq_finance'}
        ],
        'expense': [
            {'step_order': 1, 'step_name': 'cost_control_approval', 'required_role': 'hq_cost_control'},
            {'step_order': 2, 'step_name': 'finance_approval', 'required_role': 'hq_finance'}
        ]
    }
    
    steps_config = workflow_steps_config.get(workflow_type, [])
    
    # Determine initial stage
    current_stage = steps_config[0]['required_role'] if steps_config else 'pending'
    
    # Create workflow
    workflow = ApprovalWorkflow(
        workflow_type=workflow_type,
        reference_id=reference_id,
        reference_number=reference_number,
        project_id=project_id,
        current_stage=current_stage,
        overall_status='pending',
        initiated_by=initiated_by,
        initiated_at=datetime.now(timezone.utc),
        total_amount=total_amount,
        description=description,
        priority=priority
    )
    
    db.session.add(workflow)
    db.session.flush()  # Get workflow ID
    
    # Create workflow steps
    for step_config in steps_config:
        step = WorkflowStep(
            workflow_id=workflow.id,
            step_order=step_config['step_order'],
            step_name=step_config['step_name'],
            required_role=step_config['required_role'],
            status='pending' if step_config['step_order'] == 1 else 'pending'
        )
        db.session.add(step)
    
    db.session.commit()
    
    # Log workflow creation
    log_audit(
        user_id=initiated_by,
        action='created',
        module=workflow_type.split('_')[0],  # procurement, payroll, etc.
        reference_type='approval_workflow',
        reference_id=workflow.id,
        reference_number=reference_number,
        description=f"Created approval workflow for {workflow_type}",
        new_values=json.dumps({
            'workflow_type': workflow_type,
            'reference_number': reference_number,
            'total_amount': total_amount,
            'status': 'pending'
        })
    )
    
    # Send notification to first approver
    if steps_config:
        send_approval_notification(
            workflow_id=workflow.id,
            step_order=1,
            action='request'
        )
    
    return workflow


def approve_workflow_step(workflow_id, step_order, approver_id, comments=None):
    """
    Approve a workflow step and move to next step
    
    Args:
        workflow_id: ID of the workflow
        step_order: Order of the step to approve
        approver_id: User ID who is approving
        comments: Optional comments
    
    Returns:
        tuple: (success: bool, message: str, next_step: WorkflowStep or None)
    """
    workflow = ApprovalWorkflow.query.get(workflow_id)
    if not workflow:
        return False, "Workflow not found", None
    
    step = WorkflowStep.query.filter_by(
        workflow_id=workflow_id,
        step_order=step_order
    ).first()
    
    if not step:
        return False, "Workflow step not found", None
    
    if step.status != 'pending':
        return False, f"Step is already {step.status}", None
    
    # Update step
    step.status = 'approved'
    step.approver_id = approver_id
    step.action_taken_at = datetime.now(timezone.utc)
    step.comments = comments
    
    # Check if there's a next step
    next_step = WorkflowStep.query.filter_by(
        workflow_id=workflow_id,
        step_order=step_order + 1
    ).first()
    
    if next_step:
        # Move to next step
        workflow.current_stage = next_step.required_role
        workflow.overall_status = 'in_progress'
        db.session.commit()
        
        # Send notification for next step (to next approver)
        send_approval_notification(
            workflow_id=workflow_id,
            step_order=step_order + 1,
            action='request'
        )
        
        # Notify initiator of progress (for POs, notify Procurement that Cost Control approved)
        send_step_progress_notification(
            workflow_id=workflow_id,
            step_name=step.step_name,
            approver_id=approver_id,
            next_step_name=next_step.step_name
        )
        
        # Log approval
        log_audit(
            user_id=approver_id,
            action='approved',
            module=workflow.workflow_type.split('_')[0],
            reference_type='approval_workflow',
            reference_id=workflow.id,
            reference_number=workflow.reference_number,
            description=f"Approved {step.step_name} for {workflow.workflow_type}",
            new_values=json.dumps({
                'step': step.step_name,
                'step_order': step_order,
                'comments': comments,
                'next_step': next_step.step_name
            })
        )
        
        return True, f"Approved. Moving to {next_step.step_name}", next_step
    else:
        # Final approval - workflow complete
        workflow.overall_status = 'approved'
        workflow.completed_at = datetime.now(timezone.utc)
        db.session.commit()
        
        # Notify initiator of final approval
        send_workflow_completion_notification(
            workflow_id=workflow_id,
            approved=True
        )
        
        # Log final approval
        log_audit(
            user_id=approver_id,
            action='approved',
            module=workflow.workflow_type.split('_')[0],
            reference_type='approval_workflow',
            reference_id=workflow.id,
            reference_number=workflow.reference_number,
            description=f"Final approval for {workflow.workflow_type}",
            new_values=json.dumps({
                'step': step.step_name,
                'step_order': step_order,
                'comments': comments,
                'status': 'approved'
            })
        )
        
        return True, "Workflow fully approved", None


def reject_workflow_step(workflow_id, step_order, rejector_id, comments):
    """
    Reject a workflow step
    
    Args:
        workflow_id: ID of the workflow
        step_order: Order of the step to reject
        rejector_id: User ID who is rejecting
        comments: Rejection reason (required)
    
    Returns:
        tuple: (success: bool, message: str)
    """
    workflow = ApprovalWorkflow.query.get(workflow_id)
    if not workflow:
        return False, "Workflow not found"
    
    step = WorkflowStep.query.filter_by(
        workflow_id=workflow_id,
        step_order=step_order
    ).first()
    
    if not step:
        return False, "Workflow step not found"
    
    # Update step
    step.status = 'rejected'
    step.approver_id = rejector_id
    step.action_taken_at = datetime.now(timezone.utc)
    step.comments = comments
    
    # Update workflow
    workflow.overall_status = 'rejected'
    workflow.completed_at = datetime.now(timezone.utc)
    
    db.session.commit()
    
    # Notify initiator of rejection
    send_workflow_completion_notification(
        workflow_id=workflow_id,
        approved=False,
        rejection_reason=comments
    )
    
    # Log rejection
    log_audit(
        user_id=rejector_id,
        action='rejected',
        module=workflow.workflow_type.split('_')[0],
        reference_type='approval_workflow',
        reference_id=workflow.id,
        reference_number=workflow.reference_number,
        description=f"Rejected {step.step_name} for {workflow.workflow_type}",
        new_values=json.dumps({
            'step': step.step_name,
            'step_order': step_order,
            'comments': comments,
            'status': 'rejected'
        })
    )
    
    return True, "Workflow rejected"


def send_approval_notification(workflow_id, step_order, action='request'):
    """
    Send notification for approval request
    
    Args:
        workflow_id: ID of the workflow
        step_order: Order of the step
        action: Type of action (request, approved, rejected)
    """
    from models import User
    
    workflow = ApprovalWorkflow.query.get(workflow_id)
    if not workflow:
        return
    
    step = WorkflowStep.query.filter_by(
        workflow_id=workflow_id,
        step_order=step_order
    ).first()
    
    if not step:
        return
    
    # Get users with the required role
    users = User.query.filter_by(role=step.required_role).all()
    
    for user in users:
        # Determine notification title and message
        if action == 'request':
            title = f"New Approval Request: {workflow.reference_number}"
            message = f"You have a new {workflow.workflow_type.replace('_', ' ').title()} approval request."
            notification_type = 'approval_request'
            action_url = get_approval_url(workflow.workflow_type, workflow.id)
        elif action == 'approved':
            title = f"Approval Granted: {workflow.reference_number}"
            message = f"Your {workflow.workflow_type.replace('_', ' ').title()} has been approved."
            notification_type = 'approval_granted'
            action_url = None
        else:
            title = f"Approval Rejected: {workflow.reference_number}"
            message = f"Your {workflow.workflow_type.replace('_', ' ').title()} has been rejected."
            notification_type = 'approval_rejected'
            action_url = None
        
        # Create notification
        notification = Notification(
            user_id=user.id,
            title=title,
            message=message,
            notification_type=notification_type,
            reference_type=workflow.workflow_type,
            reference_id=workflow.reference_id,
            action_url=action_url,
            priority=workflow.priority
        )
        
        db.session.add(notification)
    
        # Send email notification
        try:
            if user.email:
                send_email(
                    to=user.email,
                    subject=title,
                    template='email/approval_notification.html',
                    workflow=workflow,
                    step=step,
                    action=action,
                    action_url=action_url
                )
                notification.email_sent = True
                notification.email_sent_at = datetime.now(timezone.utc)
        except Exception as e:
            current_app.logger.error(f"Failed to send email to {user.email}: {str(e)}")
    
    # Update step notification status
    step.notification_sent = True
    step.notification_sent_at = datetime.now(timezone.utc)
    
    db.session.commit()


def send_workflow_completion_notification(workflow_id, approved, rejection_reason=None):
    """
    Send notification when workflow is completed (approved or rejected)
    Notifies initiator and all approvers in the chain
    """
    from models import User
    
    workflow = ApprovalWorkflow.query.get(workflow_id)
    if not workflow:
        return
    
    # Notify initiator
    initiator = User.query.get(workflow.initiated_by)
    if not initiator:
        return
    
    if approved:
        title = f"✅ Approved: {workflow.reference_number}"
        message = f"Your {workflow.workflow_type.replace('_', ' ').title()} has been fully approved!"
        notification_type = 'success'
    else:
        title = f"❌ Rejected: {workflow.reference_number}"
        message = f"Your {workflow.workflow_type.replace('_', ' ').title()} has been rejected. Reason: {rejection_reason}"
        notification_type = 'warning'
    
    # Notify initiator (Procurement)
    notification = Notification(
        user_id=initiator.id,
        title=title,
        message=message,
        notification_type=notification_type,
        reference_type=workflow.workflow_type,
        reference_id=workflow.reference_id,
        priority=workflow.priority
    )
    
    db.session.add(notification)
    
    # Send email to initiator
    try:
        if initiator.email:
            send_email(
                to=initiator.email,
                subject=title,
                template='email/workflow_completion.html',
                workflow=workflow,
                approved=approved,
                rejection_reason=rejection_reason
            )
            notification.email_sent = True
            notification.email_sent_at = datetime.now(timezone.utc)
    except Exception as e:
        current_app.logger.error(f"Failed to send email to {initiator.email}: {str(e)}")
    
    # For Purchase Orders: Notify all approvers in the chain (Cost Control and Finance)
    if workflow.workflow_type == 'purchase_order':
        # Get all workflow steps
        workflow_steps = WorkflowStep.query.filter_by(workflow_id=workflow.id).all()
        
        notified_users = {initiator.id}  # Track to avoid duplicate notifications
        
        for step in workflow_steps:
            # Get all users with this role
            role_users = User.query.filter_by(role=step.required_role).all()
            
            for user in role_users:
                if user.id in notified_users:
                    continue
                    
                notified_users.add(user.id)
                
                # Create notification for approver
                approver_notification = Notification(
                    user_id=user.id,
                    title=title,
                    message=f"Purchase Order {workflow.reference_number} has been {('fully approved' if approved else 'rejected')}.",
                    notification_type=notification_type,
                    reference_type=workflow.workflow_type,
                    reference_id=workflow.reference_id,
                    priority=workflow.priority
                )
                
                db.session.add(approver_notification)
                
                # Send email to approver
                try:
                    if user.email:
                        send_email(
                            to=user.email,
                            subject=title,
                            template='email/workflow_completion.html',
                            workflow=workflow,
                            approved=approved,
                            rejection_reason=rejection_reason,
                            recipient_role=step.required_role
                        )
                        approver_notification.email_sent = True
                        approver_notification.email_sent_at = datetime.now(timezone.utc)
                except Exception as e:
                    current_app.logger.error(f"Failed to send email to {user.email}: {str(e)}")
    
    # Notify admin for payroll approvals
    if workflow.workflow_type == 'payroll' and approved:
        admin_users = User.query.filter_by(role='admin').all()
        for admin in admin_users:
            admin_notification = Notification(
                user_id=admin.id,
                title=f"Payroll Approved: {workflow.reference_number}",
                message=f"Payroll for {workflow.reference_number} has been approved by Finance.",
                notification_type='info',
                reference_type='payroll',
                reference_id=workflow.reference_id,
                priority='normal'
            )
            db.session.add(admin_notification)
            
            # Send email to admin
            try:
                if admin.email:
                    send_email(
                        to=admin.email,
                        subject=f"Payroll Approved: {workflow.reference_number}",
                        template='email/payroll_admin_notification.html',
                        workflow=workflow
                    )
                    admin_notification.email_sent = True
                    admin_notification.email_sent_at = datetime.now(timezone.utc)
            except Exception as e:
                current_app.logger.error(f"Failed to send email to admin {admin.email}: {str(e)}")
    
    db.session.commit()


def send_step_progress_notification(workflow_id, step_name, approver_id, next_step_name):
    """
    Send notification to workflow initiator when a step is approved and moves to next step
    Example: When Cost Control approves, notify Procurement that it's moving to Finance
    
    Args:
        workflow_id: ID of the workflow
        step_name: Name of the step that was just approved
        approver_id: ID of user who approved
        next_step_name: Name of the next step
    """
    from models import User
    
    workflow = ApprovalWorkflow.query.get(workflow_id)
    if not workflow:
        return
    
    # Get initiator
    initiator = User.query.get(workflow.initiated_by)
    if not initiator:
        return
    
    # Get approver
    approver = User.query.get(approver_id)
    approver_name = approver.name if approver else "Approver"
    
    # Format step names for display
    step_display = step_name.replace('_', ' ').title()
    next_step_display = next_step_name.replace('_', ' ').title()
    
    title = f"✓ Progress Update: {workflow.reference_number}"
    message = f"{step_display} approved by {approver_name}. Now pending {next_step_display}."
    
    # Create notification for initiator
    notification = Notification(
        user_id=initiator.id,
        title=title,
        message=message,
        notification_type='info',
        reference_type=workflow.workflow_type,
        reference_id=workflow.reference_id,
        priority=workflow.priority
    )
    
    db.session.add(notification)
    
    # Send email to initiator
    try:
        if initiator.email:
            send_email(
                to=initiator.email,
                subject=title,
                template='email/workflow_progress.html',
                workflow=workflow,
                step_name=step_display,
                approver_name=approver_name,
                next_step_name=next_step_display
            )
            notification.email_sent = True
            notification.email_sent_at = datetime.now(timezone.utc)
    except Exception as e:
        current_app.logger.error(f"Failed to send progress email to {initiator.email}: {str(e)}")
    
    db.session.commit()



def get_approval_url(workflow_type, workflow_id):
    """Get the URL for approving a workflow"""
    url_map = {
        'purchase_order': f'/cost-control/manager/approvals?workflow_id={workflow_id}',
        'payroll': f'/finance/payroll/approvals?workflow_id={workflow_id}',
        'budget_adjustment': f'/cost-control/manager/approvals?workflow_id={workflow_id}',
        'expense': f'/cost-control/manager/approvals?workflow_id={workflow_id}'
    }
    return url_map.get(workflow_type, '/dashboard')


def log_audit(user_id, action, module, reference_type, reference_id=None, 
              reference_number=None, description=None, old_values=None, 
              new_values=None, project_id=None, severity='info', success=True):
    """
    Log an action to the audit log
    
    Args:
        user_id: ID of the user performing the action
        action: Action performed (created, updated, deleted, approved, rejected, etc.)
        module: Module name (procurement, hr, finance, cost_control, admin)
        reference_type: Type of object affected (purchase_order, payroll, user, etc.)
        reference_id: ID of the affected object
        reference_number: Human-readable reference
        description: Human-readable description
        old_values: JSON string of old values
        new_values: JSON string of new values
        project_id: Associated project ID
        severity: Severity level (info, warning, critical)
        success: Whether the action succeeded
    """
    from models import User
    
    user = User.query.get(user_id) if user_id else None
    
    # Get request info
    ip_address = None
    user_agent = None
    try:
        if request:
            ip_address = request.remote_addr
            user_agent = request.headers.get('User-Agent', '')[:255]
    except:
        pass
    
    audit_log = AuditLog(
        user_id=user_id,
        user_name=user.name if user else 'System',
        user_role=user.role if user else None,
        action=action,
        module=module,
        reference_type=reference_type,
        reference_id=reference_id,
        reference_number=reference_number,
        description=description,
        old_values=old_values,
        new_values=new_values,
        ip_address=ip_address,
        user_agent=user_agent,
        project_id=project_id,
        severity=severity,
        success=success,
        timestamp=datetime.now(timezone.utc)
    )
    
    db.session.add(audit_log)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to log audit: {str(e)}")


def get_pending_approvals_for_user(user):
    """
    Get all pending approvals for a user based on their role
    
    Args:
        user: User instance
    
    Returns:
        List of pending workflows
    """
    # Find workflows with pending steps for this user's role
    workflows = ApprovalWorkflow.query.join(
        WorkflowStep, WorkflowStep.workflow_id == ApprovalWorkflow.id
    ).filter(
        ApprovalWorkflow.overall_status.in_(['pending', 'in_progress']),
        WorkflowStep.required_role == user.role,
        WorkflowStep.status == 'pending'
    ).order_by(ApprovalWorkflow.created_at.desc()).all()
    
    return workflows


def get_user_notifications(user_id, unread_only=False, limit=50):
    """
    Get notifications for a user
    
    Args:
        user_id: User ID
        unread_only: If True, only return unread notifications
        limit: Maximum number of notifications to return
    
    Returns:
        List of Notification instances
    """
    query = Notification.query.filter_by(user_id=user_id)
    
    if unread_only:
        query = query.filter_by(is_read=False)
    
    notifications = query.order_by(
        Notification.created_at.desc()
    ).limit(limit).all()
    
    return notifications


def mark_notification_read(notification_id, user_id):
    """Mark a notification as read"""
    notification = Notification.query.filter_by(
        id=notification_id,
        user_id=user_id
    ).first()
    
    if notification and not notification.is_read:
        notification.is_read = True
        notification.read_at = datetime.now(timezone.utc)
        db.session.commit()
        return True
    
    return False


def mark_all_notifications_read(user_id):
    """Mark all notifications as read for a user"""
    notifications = Notification.query.filter_by(
        user_id=user_id,
        is_read=False
    ).all()
    
    for notification in notifications:
        notification.is_read = True
        notification.read_at = datetime.now(timezone.utc)
    
    db.session.commit()
    return len(notifications)
