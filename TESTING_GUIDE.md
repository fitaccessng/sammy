# Approval Workflow System - Testing Guide

## Overview
This guide provides step-by-step instructions for testing the complete approval workflow system including Purchase Order approvals and Payroll approvals.

## Setup

### 1. Generate Sample Data
Run the sample data creation script to populate the database with test workflows:

```powershell
python create_sample_workflow_data.py
```

This will create:
- **4 Purchase Orders** (Pending Cost Control, Pending Finance, Approved, Rejected)
- **1 Payroll Approval** (Pending Finance)
- **5 Test Users** with different roles

### 2. Test User Credentials
```
Procurement Manager: procurement@test.com / password123
Cost Control Manager: costcontrol@test.com / password123
Finance Manager: finance@test.com / password123
HR Manager: hr@test.com / password123
Admin (Super HQ): admin@test.com / password123
```

---

## Test Cases

### Test Case 1: Purchase Order Approval Flow (Complete Success Path)

#### **Step 1: Login as Cost Control Manager**
1. Navigate to: `http://localhost:5000/auth/login`
2. Login with: `costcontrol@test.com` / `password123`
3. You should see the Cost Control dashboard

#### **Step 2: View Pending Purchase Orders**
1. Click on "PO Approvals" in the sidebar (or navigate to `/cost-control/manager/purchase-order-approvals`)
2. Verify you see:
   - Badge showing "1" pending approval
   - PO-YYYYMMDD-001 card displayed
   - Priority badge showing "HIGH"
   - Total amount: ₦1,250,000.00
   - Supplier: ABC Suppliers Ltd
   - Line items (collapsible)

#### **Step 3: Approve Purchase Order**
1. Click "Show Items" to expand line items
2. Verify line items displayed correctly
3. Enter comment: "Approved. Prices verified and within budget."
4. Click "Approve" button
5. Verify:
   - Flash message: "Purchase order approved successfully"
   - PO no longer appears in pending list
   - Notification sent to Finance Manager

#### **Step 4: Verify Notification Sent**
1. Check notification bell icon (top right)
2. Verify badge count increased
3. Check email inbox for Finance Manager (if email configured)

#### **Step 5: Login as Finance Manager**
1. Logout from Cost Control account
2. Login with: `finance@test.com` / `password123`

#### **Step 6: View Finance Pending Approvals**
1. Navigate to `/finance/purchase-order-approvals`
2. Verify you see:
   - 2 pending POs (the one you just approved + PO-002 from sample data)
   - "COST CONTROL APPROVED" badge on each PO
   - Green info box showing Cost Control approval details
   - Budget impact warning (yellow box)

#### **Step 7: Give Final Approval**
1. Locate PO-YYYYMMDD-001
2. Review Cost Control comments
3. Enter Finance comment: "Approved. Funds released."
4. Click "Final Approval - Release Funds" button
5. Verify:
   - Flash message: "Purchase order approved and funds released"
   - PO removed from pending list
   - Procurement user receives notification
   - Budget updated for associated project

#### **Step 8: Verify Complete Workflow**
1. Login as Admin: `admin@test.com` / `password123`
2. Navigate to `/admin/audit-logs`
3. Filter by Module: "Procurement"
4. Verify audit trail shows:
   - PO created by Procurement
   - Approved by Cost Control
   - Approved by Finance
   - All timestamps and comments recorded

---

### Test Case 2: Purchase Order Rejection Flow

#### **Step 1: Login as Finance Manager**
1. Login with: `finance@test.com` / `password123`
2. Navigate to `/finance/purchase-order-approvals`

#### **Step 2: Reject a Purchase Order**
1. Locate PO-YYYYMMDD-002 (₦3,500,000.00)
2. Enter rejection reason: "Exceeds current budget allocation. Please resubmit with revised amount."
3. Click "Reject" button
4. Confirm rejection in dialog
5. Verify:
   - Flash message: "Purchase order rejected"
   - PO removed from pending list
   - Procurement user receives rejection notification
   - Email sent to Procurement

#### **Step 3: Verify Rejection Notification**
1. Login as Procurement: `procurement@test.com` / `password123`
2. Click notification bell icon
3. Verify rejection notification displayed with:
   - Red "X" icon
   - Rejection reason
   - Link to view PO

#### **Step 4: Check Audit Log**
1. Login as Admin
2. Navigate to `/admin/audit-logs`
3. Filter by Action: "rejected"
4. Verify rejection logged with:
   - User: Finance Manager
   - Reference: PO-YYYYMMDD-002
   - Comments: Rejection reason
   - IP address and timestamp

---

### Test Case 3: Payroll Approval Flow

#### **Step 1: Login as Finance Manager**
1. Login with: `finance@test.com` / `password123`

#### **Step 2: View Pending Payroll Approvals**
1. Navigate to `/finance/payroll-approvals` (or HR Payroll section)
2. Verify sample payroll displayed:
   - Month and Year
   - Total Amount: ₦5,000,000.00
   - Employee Count: 20
   - Prepared by: HR Manager

#### **Step 3: Approve Payroll**
1. Click "Approve" on payroll entry
2. Enter approval comments
3. Submit approval
4. Verify:
   - Flash message: "Payroll approved"
   - **IMPORTANT**: Check that BOTH Admin and HR receive notifications
   - Email sent to Admin and HR

#### **Step 4: Verify Admin Notification**
1. Login as Admin: `admin@test.com` / `password123`
2. Click notification bell
3. Verify notification received:
   - Title: "Payroll Approved for Processing"
   - Message mentions Finance approved the payroll
   - Action items listed for Admin

#### **Step 5: Verify HR Notification**
1. Login as HR: `hr@test.com` / `password123`
2. Check notifications
3. Verify confirmation notification received
4. Check email for payroll approval confirmation

---

### Test Case 4: Notification Center Functionality

#### **Step 1: Test Notification Badge**
1. Login as any user with pending notifications
2. Verify:
   - Red badge displays unread count
   - Badge hidden when no unread notifications

#### **Step 2: Test Notification Dropdown**
1. Click notification bell icon
2. Verify dropdown opens showing:
   - Recent notifications (up to 10)
   - Unread notifications highlighted in blue
   - Blue dot indicator for unread
   - Timestamps ("2 hours ago", etc.)
   - Correct icons for notification types

#### **Step 3: Mark Single Notification as Read**
1. Click on any unread notification in dropdown
2. Verify:
   - Notification marked as read
   - Blue highlight removed
   - Badge count decreases
   - Redirected to action URL (if applicable)

#### **Step 4: Mark All as Read**
1. Click "Mark all as read" button in dropdown
2. Verify:
   - All notifications marked as read
   - Badge disappears
   - Dropdown shows all items without blue highlight

#### **Step 5: Test Full Notifications Page**
1. Click "View all notifications →" in dropdown footer
2. Navigate to `/notifications`
3. Verify:
   - All notifications displayed in cards
   - Filter tabs work (All, Unread, Approvals, Budget Alerts)
   - Pagination works (if > 50 notifications)
   - Can mark individual notifications as read

---

### Test Case 5: Admin Audit Log Dashboard

#### **Step 1: Access Audit Log**
1. Login as Admin: `admin@test.com` / `password123`
2. Navigate to `/admin/audit-logs`

#### **Step 2: Verify Stats Cards**
1. Check dashboard shows:
   - Total Activities count
   - Today's Activities count
   - Active Users count
   - Critical Events count (rejections, deletions, errors)

#### **Step 3: Test Filters**
1. **Date Filter**:
   - Set "Date From" to 3 days ago
   - Set "Date To" to today
   - Click "Apply Filters"
   - Verify only logs within date range displayed

2. **Module Filter**:
   - Select "Procurement"
   - Click "Apply Filters"
   - Verify only procurement-related logs shown

3. **Action Filter**:
   - Select "approved"
   - Click "Apply Filters"
   - Verify only approval actions shown

4. **User Filter**:
   - Enter user name in search
   - Click "Apply Filters"
   - Verify only logs for that user shown

#### **Step 4: View Log Details**
1. Click "eye" icon on any log entry
2. Verify modal opens showing:
   - Full timestamp
   - User details (name, role)
   - Action and module
   - Description
   - IP address and User Agent
   - Old values and New values (if applicable)
   - Success/failure status

#### **Step 5: Export Audit Log**
1. Apply desired filters
2. Click "Export CSV" button
3. Verify:
   - CSV file downloaded
   - Filename format: `audit_logs_YYYYMMDD_HHMMSS.csv`
   - CSV contains all filtered results (max 10,000)
   - All columns exported correctly

#### **Step 6: Test Pagination**
1. Verify pagination controls at bottom of table
2. Click "Next" button
3. Verify next page of results loads
4. Check page indicator updates ("Page 2 of X")

---

## Email Testing

### Setup Email Testing (Optional)
If you want to test email notifications:

1. **Configure Flask-Mail** in `app.py`:
```python
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your-email@gmail.com'
app.config['MAIL_PASSWORD'] = 'your-app-password'
app.config['MAIL_DEFAULT_SENDER'] = 'your-email@gmail.com'
```

2. **Test Email Delivery**:
   - Complete an approval action
   - Check recipient's email inbox
   - Verify email contains:
     - Professional formatting
     - Workflow details
     - Action button (for approval requests)
     - Correct subject line

---

## Performance Testing

### Test Notification Polling
1. Open browser developer tools (F12)
2. Go to Network tab
3. Login and stay on any page
4. Verify `/api/notifications/unread-count` called every 30 seconds
5. Check response time (should be < 100ms)

### Test Audit Log Performance
1. Navigate to `/admin/audit-logs`
2. Apply no filters
3. Verify page loads in < 2 seconds
4. Test pagination response time
5. Test CSV export with large dataset

---

## Security Testing

### Test CSRF Protection
1. Try submitting approval form without CSRF token
2. Verify request blocked with 400 error

### Test Role-Based Access
1. **Test Unauthorized Access**:
   - Login as Procurement user
   - Try to access `/finance/purchase-order-approvals`
   - Verify access denied (403 error)

2. **Test Cost Control Access**:
   - Login as Cost Control user
   - Access `/cost-control/manager/purchase-order-approvals`
   - Verify access granted
   - Try to approve PO already at Finance stage
   - Verify error or no action

3. **Test Finance Access**:
   - Login as Finance user
   - Try to approve PO still at Cost Control stage
   - Verify PO not visible in Finance pending list

### Test Audit Logging
1. Perform various actions (create, approve, reject)
2. Check audit log for each action
3. Verify:
   - User ID recorded correctly
   - IP address captured
   - User agent captured
   - Action type correct
   - Old/new values captured for updates

---

## Edge Cases & Error Handling

### Test Double Submission
1. Login as Cost Control
2. Approve a PO
3. Try to approve the same PO again
4. Verify:
   - Error message displayed
   - No duplicate workflow steps created
   - Audit log shows attempted duplicate action

### Test Concurrent Approvals
1. Open two browser windows
2. Login as Finance in both
3. Try to approve same PO in both windows simultaneously
4. Verify:
   - Only one approval succeeds
   - Other shows error message
   - Database integrity maintained

### Test Invalid Data
1. Try to approve PO with empty comments (if required)
2. Verify validation error displayed
3. Try to submit invalid date ranges in audit log filters
4. Verify graceful error handling

---

## Checklist Summary

### Purchase Order Workflow
- [ ] Procurement can submit PO for approval
- [ ] Cost Control receives notification
- [ ] Cost Control can view pending POs
- [ ] Cost Control can approve PO
- [ ] Finance receives notification after Cost Control approval
- [ ] Finance can view pending POs with Cost Control details
- [ ] Finance can give final approval
- [ ] Procurement receives completion notification
- [ ] Budget updated on final approval
- [ ] All actions logged in audit trail

### Payroll Workflow
- [ ] HR can submit payroll for approval
- [ ] Finance receives notification
- [ ] Finance can approve payroll
- [ ] **Admin receives notification on Finance approval**
- [ ] **HR receives confirmation notification**
- [ ] All actions logged

### Rejection Flow
- [ ] Cost Control can reject PO
- [ ] Finance can reject PO
- [ ] Finance can reject payroll
- [ ] Initiator receives rejection notification with reason
- [ ] Email sent for rejections
- [ ] Rejection logged in audit trail

### Notification System
- [ ] Badge shows correct unread count
- [ ] Dropdown displays recent notifications
- [ ] Click notification marks as read
- [ ] Click notification navigates to action URL
- [ ] Mark all as read works
- [ ] Full notifications page works
- [ ] Filter tabs work
- [ ] Notification polling every 30 seconds
- [ ] Email notifications sent

### Audit Log System
- [ ] Admin can access audit log
- [ ] Stats cards display correct counts
- [ ] Date filter works
- [ ] Module filter works
- [ ] Action filter works
- [ ] User filter works
- [ ] Log details modal works
- [ ] CSV export works
- [ ] Pagination works
- [ ] All actions properly logged

### Security & Access Control
- [ ] CSRF protection enabled
- [ ] Role-based access enforced
- [ ] Unauthorized access denied
- [ ] IP address captured in logs
- [ ] User agent captured in logs

---

## Troubleshooting

### Issue: Notifications not appearing
**Solution**: 
- Check if notification was created in database: `SELECT * FROM notifications ORDER BY created_at DESC LIMIT 10;`
- Verify user role matches `required_role` in workflow step
- Check browser console for JavaScript errors

### Issue: Email not sending
**Solution**:
- Verify Flask-Mail configuration
- Check email credentials
- Look for errors in application logs
- Test with local SMTP server (MailHog/Papercut)

### Issue: Audit log missing entries
**Solution**:
- Verify `log_audit()` called in route
- Check if database transaction committed
- Look for errors in application logs

### Issue: Workflow stuck at one stage
**Solution**:
- Check workflow status in database: `SELECT * FROM approval_workflows WHERE id = X;`
- Check workflow steps: `SELECT * FROM workflow_steps WHERE workflow_id = X;`
- Verify `approve_workflow_step()` completed successfully
- Check for transaction rollbacks in logs

---

## Success Criteria

The approval workflow system is considered fully functional when:

1. ✅ All purchase orders follow the 3-stage approval path (Procurement → Cost Control → Finance)
2. ✅ All payroll approvals follow the 2-stage path with Admin/HR auto-notification
3. ✅ Notifications are delivered immediately to correct roles
4. ✅ Emails are sent at each workflow stage
5. ✅ Audit log captures all user actions with complete details
6. ✅ UI displays pending approvals correctly for each role
7. ✅ Rejection flow works and notifies initiators
8. ✅ Security controls prevent unauthorized access
9. ✅ System handles edge cases gracefully
10. ✅ Performance meets requirements (< 2s page load, < 100ms API calls)

---

## Next Steps

After successful testing:

1. **Production Deployment**:
   - Configure production email server
   - Set up database backups
   - Configure monitoring and alerting
   - Set up log rotation for audit logs

2. **User Training**:
   - Train Cost Control users on PO approval process
   - Train Finance users on final approval process
   - Train Admin on audit log usage
   - Create user documentation

3. **Monitoring**:
   - Monitor notification delivery rates
   - Track average approval times
   - Monitor email bounce rates
   - Review audit logs regularly

4. **Enhancements** (Future):
   - Add SMS notifications
   - Implement approval delegation
   - Add workflow escalation (auto-escalate if not approved within X days)
   - Add dashboard analytics (approval time metrics, rejection rates)
   - Implement bulk approval functionality
   - Add approval comments history timeline view
