# Cost Tracking & Budget Adjustment Workflow - Business Logic

## Complete Approval Workflow

### 1. Cost Entry Approval Workflow

**When Does It Trigger?**
- When a cost entry has variance > 10% (planned vs actual)

**Workflow Steps:**

```
Step 1: User Creates Cost Entry (Any Cost Control/Project Manager)
  ↓
Step 2: System Calculates Variance
  ↓
Step 3a: IF variance ≤ 10%
  → Entry AUTO-APPROVED
  → Budget updated immediately
  → No approval needed
  
Step 3b: IF variance > 10%
  → Entry status = "pending"
  → CostApproval record created
  → Notification sent to Cost Control Managers
  → Budget updated immediately (even if pending approval)
  ↓
Step 4: Cost Control Manager Reviews
  Location: Cost Control → Pending Approvals
  ↓
Step 5a: APPROVED
  → Entry status = "approved"
  → Creator notified
  → No budget change (already updated in Step 3b)
  
Step 5b: REJECTED
  → Entry status = "rejected"
  → Creator notified with reason
  → Budget needs manual adjustment if necessary
```

**Access Points:**
- **Create Entry:** Cost Control → Cost Tracking
- **View Approvals:** Cost Control → Pending Approvals
- **Approve/Reject:** Cost Control Manager with role HQ_COST_CONTROL or SUPER_HQ

**Notifications:**
- **To:** Cost Control Managers (HQ_COST_CONTROL, SUPER_HQ)
- **When:** Cost entry with high variance created
- **Message:** "High variance cost entry requires approval: [description] ([X]% variance)"
- **Type:** In-app notification (bell icon)

**On Approval:**
- **To:** Entry creator
- **Message:** "Your cost entry has been approved: [description]"

**On Rejection:**
- **To:** Entry creator
- **Message:** "Your cost entry was rejected: [description]. Reason: [comments]"

---

### 2. Budget Adjustment Workflow

**When Does It Trigger?**
- When Cost Control Manager requests to increase/decrease budget allocation

**Workflow Steps:**

```
Step 1: Cost Control Manager Requests Budget Adjustment
  Location: Cost Control → Budget Adjustments
  ↓
Step 2: Fill Budget Adjustment Form
  - Select Project
  - Select Budget Category
  - Enter New Amount
  - Provide Reason
  - Add Impact Analysis
  ↓
Step 3: System Creates Records
  → BudgetAdjustment record created
  → CostApproval record created (required_role: HQ_FINANCE)
  → Notifications sent to Finance users
  → Budget NOT changed yet (waiting for approval)
  ↓
Step 4: Finance Manager Reviews
  Location: Finance → Pending Approvals (or Cost Approvals)
  ↓
Step 5a: APPROVED
  → BudgetAdjustment status = "approved"
  → Budget.allocated_amount updated to new amount
  → Requester (Cost Control) notified
  → Budget.remaining_amount recalculated
  
Step 5b: REJECTED
  → BudgetAdjustment status = "rejected"
  → Budget unchanged
  → Requester notified with reason
```

**Access Points:**
- **Request Adjustment:** Cost Control → Budget Adjustments
- **View Requests:** Cost Control → Budget Adjustments (can see own requests)
- **Approve/Reject:** Finance role (HQ_FINANCE, SUPER_HQ) in Finance → Approvals

**Notifications:**
- **To:** Finance Managers (HQ_FINANCE, SUPER_HQ)
- **When:** Budget adjustment request created
- **Message:** "Budget adjustment request: [category] - [increase/decrease] of ₦[amount]"
- **Type:** In-app notification

**On Approval:**
- **To:** Cost Control Manager who requested
- **Message:** "Budget adjustment approved: [category] - New amount: ₦[amount]"

**On Rejection:**
- **To:** Cost Control Manager who requested
- **Message:** "Budget adjustment rejected: [category]. Reason: [comments]"

---

## Role-Based Access Control

### Cost Control Manager (HQ_COST_CONTROL)
**Can:**
- ✅ Create cost entries
- ✅ View all cost entries for their projects
- ✅ Request budget adjustments
- ✅ Approve/reject cost entry approvals (high variance)
- ✅ View pending cost approvals
- ✅ View budget adjustment history

**Cannot:**
- ❌ Approve budget adjustments (needs Finance)
- ❌ Modify budgets directly

**Navigation:**
- Cost Control → Cost Tracking (create entries)
- Cost Control → Pending Approvals (approve high variance entries)
- Cost Control → Budget Adjustments (request budget changes)
- Cost Control → Variance Analysis (view reports)

---

### Finance Manager (HQ_FINANCE)
**Can:**
- ✅ Approve/reject budget adjustment requests
- ✅ View all budget adjustments
- ✅ View financial reports
- ✅ Approve Purchase Orders (final approval)

**Cannot:**
- ❌ Create cost entries (Cost Control's job)
- ❌ Approve cost entry variances (Cost Control's job)

**Navigation:**
- Finance → Pending Approvals (approve budget adjustments)
- Finance → Budget Reports
- Finance → Purchase Order Approvals

---

### Project Manager (PROJECT_MANAGER)
**Can:**
- ✅ Create cost entries for their projects
- ✅ View cost tracking for their projects
- ✅ View budget status

**Cannot:**
- ❌ Approve any requests
- ❌ Request budget adjustments

---

### Super HQ (SUPER_HQ)
**Can:**
- ✅ Everything all roles can do
- ✅ Override any approval
- ✅ Access all features

---

## Database Schema

### CostApproval Table
```sql
id                  INTEGER PRIMARY KEY
reference_type      VARCHAR(64)  -- 'cost_entry' or 'budget_adjustment'
reference_id        INTEGER      -- ID of cost entry or budget adjustment
project_id          INTEGER      -- Project this relates to
required_role       VARCHAR(64)  -- Role needed to approve (e.g., 'hq_cost_control', 'hq_finance')
amount              FLOAT        -- Amount involved
description         TEXT         -- Description of what needs approval
status              VARCHAR(32)  -- 'pending', 'approved', 'rejected'
approver_id         INTEGER      -- User who approved/rejected (nullable until action taken)
approved_at         DATETIME     -- When action was taken (nullable)
comments            TEXT         -- Approver's comments (nullable)
action_taken        VARCHAR(32)  -- 'approved', 'rejected', 'escalated' (nullable)
created_by          INTEGER      -- User who created the request
created_at          DATETIME     -- When request was created
updated_at          DATETIME     -- Last update time
```

### Key Fields:
- **reference_type**: Determines what type of approval
  - `cost_entry` → Approve high-variance cost entry
  - `budget_adjustment` → Approve budget change request
  
- **reference_id**: Links to the specific cost entry or budget adjustment

- **required_role**: Who can approve
  - `hq_cost_control` → Cost Control Manager approves
  - `hq_finance` → Finance Manager approves

---

## API Endpoints

### Cost Entry Approvals
**Create (Automatic):**
```
POST /cost-control/manager/cost-tracking
→ If variance > 10%, creates CostApproval automatically
```

**View Pending:**
```
GET /cost-control/manager/approvals?status=pending
→ Shows approvals where required_role matches current user's role
```

**Approve/Reject:**
```
POST /cost-control/manager/approvals
Form Data:
  - approval_id: int
  - action: 'approve' | 'reject' | 'escalate'
  - comments: string (optional)
```

---

### Budget Adjustment Requests
**Create Request:**
```
POST /cost-control/manager/budget-adjustments
Form Data:
  - budget_id: int
  - new_amount: float
  - reason: string
  - impact_analysis: string (optional)
→ Creates BudgetAdjustment + CostApproval (required_role: hq_finance)
```

**View Requests:**
```
GET /cost-control/manager/budget-adjustments?status=pending
→ Shows budget adjustment requests
```

**Approve/Reject (Finance):**
```
POST /cost-control/manager/approvals
→ Same endpoint as cost approvals, but Finance users see budget_adjustment approvals
```

---

## Example Scenarios

### Scenario 1: Normal Cost Entry (Auto-Approved)
```
1. User: Creates entry - Planned: ₦100,000, Actual: ₦105,000
2. System: Calculates variance = 5%
3. System: Auto-approves (variance ≤ 10%)
4. System: Updates budget.spent_amount += ₦105,000
5. Result: Entry shows "Approved" status immediately
6. No approval queue involvement
```

---

### Scenario 2: High Variance Cost Entry (Needs Approval)
```
1. User (PM): Creates entry - Planned: ₦100,000, Actual: ₦150,000
2. System: Calculates variance = 50%
3. System: 
   - Sets entry status = "pending"
   - Creates CostApproval (required_role: hq_cost_control)
   - Updates budget.spent_amount += ₦150,000 (still updates!)
   - Notifies Cost Control Managers
4. Cost Control Manager: Gets notification
5. Cost Control Manager: Navigates to Cost Control → Pending Approvals
6. Cost Control Manager: Reviews and approves
7. System:
   - Sets entry status = "approved"
   - Sets approval status = "approved"
   - Notifies PM
8. Result: Entry now shows "Approved", no budget change (already updated in step 3)
```

---

### Scenario 3: Budget Adjustment Request
```
1. Cost Control Manager: Notices "Labor" budget running low
2. Cost Control Manager: Navigates to Cost Control → Budget Adjustments
3. Cost Control Manager: Fills form:
   - Budget: Labor (current: ₦1,000,000)
   - New Amount: ₦1,500,000
   - Reason: "High overtime due to project delays"
4. System:
   - Creates BudgetAdjustment record
   - Creates CostApproval (required_role: hq_finance)
   - Notifies Finance Managers
   - Budget NOT changed yet
5. Finance Manager: Gets notification
6. Finance Manager: Navigates to Finance → Pending Approvals
7. Finance Manager: Reviews impact and approves
8. System:
   - Sets adjustment status = "approved"
   - Updates Budget.allocated_amount = ₦1,500,000
   - Notifies Cost Control Manager
9. Result: Budget increased, Cost Control can continue tracking
```

---

### Scenario 4: Budget Exceeded Warning
```
1. User: Creates entry - Actual: ₦600,000
2. System: Checks budget for category (allocated: ₦500,000, spent: ₦100,000)
3. System: After this entry, spent would be ₦700,000
4. System:
   - Creates entry (doesn't block)
   - Updates budget.spent_amount = ₦700,000
   - Shows warning: "Budget exceeded by ₦200,000 for [category]"
   - Logs audit warning
5. Result: Entry created but warning shown, Cost Control should request adjustment
```

---

## Implementation Files

### Backend Routes (app.py)
- **Lines 1050-1202:** Cost tracking POST/GET handler
- **Lines 1205-1224:** Category API endpoint
- **Lines 1320-1390:** Budget adjustment request handler
- **Lines 1510-1625:** Cost approval processing (approve/reject)

### Templates
- `cost_tracking.html` - Create cost entries
- `approvals.html` - Cost Control approval queue
- `budget_adjustments.html` - Request budget changes
- Finance templates (separate) - Finance approval queue

### Database Models (models.py)
- `CostTrackingEntry` - Cost entries
- `CostApproval` - Approval records
- `BudgetAdjustment` - Budget change requests
- `Budget` - Budget allocations
- `Notification` - In-app notifications

---

## Testing the Workflow

### Test 1: Auto-Approved Entry
```bash
1. Login as Cost Control user
2. Navigate: Cost Control → Cost Tracking
3. Create entry with 5% variance
4. Verify: Shows "Approved" immediately
5. Verify: Budget updated
```

### Test 2: High Variance Approval
```bash
1. Login as Cost Control user
2. Create entry with 50% variance
3. Verify: Shows "Pending" status
4. Verify: Warning message appears
5. Navigate: Cost Control → Pending Approvals
6. Verify: Entry appears in approval queue
7. Approve the entry
8. Verify: Entry now shows "Approved"
9. Verify: Creator gets notification
```

### Test 3: Budget Adjustment
```bash
1. Login as Cost Control user
2. Navigate: Cost Control → Budget Adjustments
3. Create adjustment request
4. Verify: Confirmation message
5. Logout
6. Login as Finance user
7. Navigate: Finance → Pending Approvals
8. Verify: Budget adjustment request visible
9. Approve request
10. Verify: Budget updated
11. Logout and login as Cost Control
12. Verify: Got notification of approval
```

---

## Summary

**Cost Entry Approvals:**
- Created automatically for high variance (>10%)
- Approved by: Cost Control Manager
- Location: Cost Control → Pending Approvals
- Budget updates immediately (even before approval)

**Budget Adjustments:**
- Requested by: Cost Control Manager
- Approved by: Finance Manager
- Location: Cost Control → Budget Adjustments (request)
- Location: Finance → Approvals (approve)
- Budget updates only after approval

**All approvals tracked in `cost_approvals` table with proper workflow**
