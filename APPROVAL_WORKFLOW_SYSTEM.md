# Approval Workflow System - Complete Implementation

## Overview
A comprehensive multi-stage approval workflow system with notifications, email alerts, and audit logging has been implemented for the Sammy ERP system.

## Features Implemented

### 1. Database Models

#### ApprovalWorkflow
- Master table for tracking all approval workflows
- Fields: workflow_type, reference_id, reference_number, project_id, current_stage, overall_status, initiated_by, total_amount, description, priority
- Supports: purchase_order, payroll, budget_adjustment, expense workflows

#### WorkflowStep
- Individual steps within a workflow
- Fields: step_order, step_name, required_role, status, approver_id, action_taken_at, comments, notification_sent
- Tracks approval progression through multiple stages

#### Notification
- In-app notifications for users
- Fields: title, message, notification_type, reference_type, reference_id, action_url, is_read, email_sent, priority
- Supports email integration

#### AuditLog
- Comprehensive activity logging
- Fields: user_id, action, module, reference_type, reference_id, description, old_values, new_values, ip_address, user_agent, timestamp
- Tracks all system activities for admin review

### 2. Purchase Order Approval Flow

#### Workflow: Procurement → Cost Control → Finance

**Step 1: Procurement Submits PO**
- Route: `/procurement/manager/purchase-orders/create` (POST)
- Form field: `submit_for_approval` = 'yes'
- Creates ApprovalWorkflow with reference to PurchaseOrder
- PO Status: `Draft` → `Pending_Cost_Control`
- Sends notification to Cost Control users
- Sends email to Cost Control team

**Step 2: Cost Control Reviews**
- Route: `/cost-control/manager/purchase-order-approvals` (GET) - View pending POs
- Route: `/cost-control/manager/purchase-orders/<po_id>/approve` (POST) - Approve/Reject
- Actions:
  * **Approve**: Updates PO to `Pending_Finance`, notifies Finance team
  * **Reject**: Updates PO to `Rejected`, notifies Procurement team
- Tracks: cost_control_approved_by, cost_control_approved_at, cost_control_comments

**Step 3: Finance Final Approval**
- Route: `/finance/purchase-order-approvals` (GET) - View pending POs
- Route: `/finance/purchase-orders/<po_id>/approve` (POST) - Approve/Reject
- Actions:
  * **Approve**: 
    - Updates PO to `Approved`
    - Updates project budget (deducts from remaining)
    - Notifies Procurement and Cost Control
    - Sends success emails
  * **Reject**: 
    - Updates PO to `Rejected`
    - Notifies all stakeholders
    - Sends rejection emails with reason

### 3. Payroll Approval Flow

#### Workflow: HR → Finance → Admin & HR Notified

**Step 1: HR Submits Payroll**
- Route: `/hr/payroll/submit-for-approval` (POST)
- Creates PayrollApproval record
- Creates ApprovalWorkflow with type='payroll'
- Status: `draft` → `pending_finance`
- Sends notification to Finance team
- Priority: HIGH (payroll is always urgent)

**Step 2: Finance Reviews and Approves**
- Route: `/finance/payroll/<approval_id>/process` (POST)
- Uses workflow system to approve/reject
- Actions:
  * **Approve**:
    - Updates PayrollApproval status to `approved`
    - Updates all StaffPayroll records to `approved`
    - **Automatically notifies Admin users** (via workflow_completion notification)
    - **Automatically notifies HR submitter** (workflow completion)
    - Sends emails to Admin and HR
    - Creates audit log entry
  * **Reject**:
    - Updates status to `rejected`
    - Notifies HR with rejection reason
    - Sends rejection email

**Step 3: Admin Reviews (Notification Only)**
- Admin receives notification when payroll is approved by Finance
- Admin can view details at `/admin/hr/payroll-approvals`
- Admin processes payment and updates system

### 4. Notification System

#### In-App Notifications
- **API Endpoints**:
  * `GET /api/notifications` - Get user notifications
  * `GET /api/notifications/unread-count` - Get unread count (for badge)
  * `POST /api/notifications/<id>/read` - Mark single notification as read
  * `POST /api/notifications/mark-all-read` - Mark all as read
  * `GET /api/pending-approvals` - Get pending approvals for current user

#### Email Notifications
- **Templates Created**:
  * `templates/email/approval_notification.html` - Approval requests
  * `templates/email/workflow_completion.html` - Approved/rejected notifications
  * `templates/email/payroll_admin_notification.html` - Admin payroll notifications

- **Email Triggers**:
  * New approval request sent to approver role
  * Approval granted notification to initiator
  * Rejection notification to initiator
  * Payroll approval notification to Admin and HR

### 5. Audit Log System

#### What Gets Logged
- All workflow creations
- All approval/rejection actions
- Purchase order submissions
- Payroll submissions
- Status changes
- User actions with IP address and user agent

#### Admin Audit Dashboard (To be created in next step)
- View all system activities
- Filter by: date range, user, module, action type, severity
- Export audit logs
- Real-time activity feed

### 6. Utility Functions (`utils/workflow.py`)

#### Workflow Management
- `create_approval_workflow()` - Initialize new workflow
- `approve_workflow_step()` - Approve current step, move to next
- `reject_workflow_step()` - Reject workflow
- `get_pending_approvals_for_user()` - Get user's pending items

#### Notification Management
- `send_approval_notification()` - Send approval request notifications
- `send_workflow_completion_notification()` - Send final status notifications
- `get_user_notifications()` - Fetch user notifications
- `mark_notification_read()` - Mark notification as read
- `mark_all_notifications_read()` - Bulk mark as read

#### Audit Logging
- `log_audit()` - Create audit log entry
- Automatic IP address and user agent capture
- JSON storage for old/new values

## Database Changes

### New Tables Created
1. `approval_workflows` - Master workflow tracking
2. `workflow_steps` - Individual approval steps
3. `notifications` - User notifications
4. `audit_logs` - System activity logs

### Updated Tables
1. `purchase_order` - Added workflow_id, cost_control_approved_by, cost_control_approved_at, finance_approved_by, finance_approved_at, cost_control_comments, finance_comments
2. PO Status values updated: `Pending_Cost_Control`, `Pending_Finance`

## Integration Points

### Purchase Order Flow
```python
# Procurement submits
POST /procurement/manager/purchase-orders/create
{
  "submit_for_approval": "yes",
  ...other PO data
}
→ Creates workflow → Notifies Cost Control

# Cost Control approves
POST /cost-control/manager/purchase-orders/<po_id>/approve
{
  "action": "approve",
  "comments": "Approved for budget"
}
→ Updates workflow → Notifies Finance

# Finance approves
POST /finance/purchase-orders/<po_id>/approve
{
  "action": "approve",
  "comments": "Final approval granted"
}
→ Updates PO status → Updates budget → Notifies all
```

### Payroll Flow
```python
# HR submits
POST /hr/payroll/submit-for-approval
{
  "period_year": 2024,
  "period_month": 11
}
→ Creates workflow → Notifies Finance

# Finance approves
POST /finance/payroll/<approval_id>/process
{
  "action": "approve",
  "comments": "Approved for payment"
}
→ Updates payroll status → Notifies Admin → Notifies HR
```

## Email Configuration

Emails are sent using the existing mail configuration:
- SMTP server from environment variables
- Templates in `templates/email/`
- Async sending to avoid blocking

## Testing Workflow

### Test Purchase Order Approval
1. Login as Procurement user
2. Create PO with "Submit for Approval" checked
3. Verify notification sent to Cost Control
4. Login as Cost Control user
5. View `/cost-control/manager/purchase-order-approvals`
6. Approve PO
7. Verify notification sent to Finance
8. Login as Finance user
9. View `/finance/purchase-order-approvals`
10. Approve PO
11. Verify final approval and budget update
12. Check notifications received by Procurement

### Test Payroll Approval
1. Login as HR user
2. Submit payroll for approval
3. Verify notification sent to Finance
4. Login as Finance user
5. View `/finance/payroll/approvals`
6. Approve payroll
7. Verify notifications sent to Admin and HR
8. Login as Admin
9. Check notification received
10. View payroll details in admin dashboard

## Next Steps (Remaining Tasks)

1. **Create Admin Audit Log Dashboard**
   - Route: `/admin/audit-logs`
   - Filter by date, user, module, action
   - Export functionality
   - Real-time feed

2. **Create UI Templates**
   - `templates/cost_control/manager/purchase_order_approvals.html`
   - `templates/finance/purchase_order_approvals.html`
   - Update navigation menus to include new approval pages

3. **Add Notification Center UI Component**
   - Bell icon with badge count
   - Dropdown with recent notifications
   - Mark as read functionality
   - Link to full notifications page

4. **Create Sample Data**
   - Sample POs for approval workflow
   - Sample payroll submissions
   - Test notifications

## Security Considerations

- All routes protected with `@role_required` decorator
- CSRF protection on all forms
- Audit logs capture IP addresses
- Email verification before sending
- Workflow validation ensures proper progression
- User can only approve items for their role

## Performance Optimizations

- Workflow queries indexed by current_stage and overall_status
- Notifications indexed by user_id and is_read
- Audit logs indexed by timestamp
- Batch notification sending for multiple recipients
- Async email sending (non-blocking)

## Maintenance

### Cleanup Old Notifications
```python
# Delete read notifications older than 30 days
from datetime import timedelta
old_date = datetime.now() - timedelta(days=30)
Notification.query.filter(
    Notification.is_read == True,
    Notification.created_at < old_date
).delete()
```

### Archive Old Audit Logs
```python
# Archive logs older than 1 year
old_date = datetime.now() - timedelta(days=365)
AuditLog.query.filter(AuditLog.timestamp < old_date).delete()
```

## Documentation

All workflow functions include comprehensive docstrings explaining:
- Purpose
- Parameters
- Return values
- Side effects (notifications, emails, audit logs)

## Support

For issues or questions:
1. Check audit logs for activity history
2. Review workflow status in database
3. Check email logs for delivery status
4. Review notification tables for delivery confirmation

---

**Implementation Complete**: ✅ Workflow System, ✅ Notification System, ✅ Audit Logging, ✅ Email Integration
**Pending**: UI Templates, Admin Audit Dashboard, Notification Center Component
