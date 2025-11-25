# Cost Tracking Quick Reference Guide

## System Status
✅ **FULLY OPERATIONAL** - All components configured and tested

## Quick Facts
- **Project:** HR Operations (ID: 1)
- **Status:** In Progress
- **Categories:** 10 standard cost categories
- **Budget:** ₦2,750,000 total allocated
- **Cost Entries:** 0 (ready to accept)
- **Pending Approvals:** 0

## Budget Allocation Summary
| Category | Budget | Status |
|----------|--------|--------|
| Material | ₦500,000 | 0% used |
| Labor | ₦1,000,000 | 0% used |
| Equipment | ₦300,000 | 0% used |
| Subcontractor | ₦200,000 | 0% used |
| Overhead | ₦150,000 | 0% used |
| Transportation | ₦100,000 | 0% used |
| Professional Services | ₦250,000 | 0% used |
| Safety | ₦75,000 | 0% used |
| Utilities | ₦125,000 | 0% used |
| Miscellaneous | ₦50,000 | 0% used |

## How to Use

### Access Cost Tracking
1. Login as Cost Control user
2. Navigate to: **Cost Control → Cost Tracking**
3. Page displays form, filters, and cost entries table

### Create Cost Entry

**Step 1: Select Project**
- Choose "HR Operations" from dropdown
- Categories will load automatically

**Step 2: Select Category**
- After project selection, category dropdown populates
- Choose appropriate category (e.g., "Direct Materials")

**Step 3: Enter Details**
- Cost Type: Select type (material, labor, equipment, etc.)
- Date: Default is today
- Description: Brief description of expense
- Planned Cost: Budgeted amount in ₦
- Actual Cost: Real amount spent in ₦
- Quantity (optional): Amount of units
- Unit (optional): Unit of measurement

**Step 4: Review Variance**
- As you enter planned/actual costs, variance calculates automatically
- Shows difference in ₦ and percentage
- If variance > 10%, warning appears about approval requirement

**Step 5: Submit**
- Click "Add Cost Entry"
- System will:
  - Save entry to database
  - Update budget spent amount
  - Create approval if variance > 10%
  - Show success/warning message
  - Redirect back to page

### View Budget Summary
1. Use filter section
2. Select "HR Operations" project
3. Click "Apply Filters"
4. Budget cards appear at top showing:
   - Spent vs allocated
   - Progress bar (color-coded)
   - Remaining amount
   - Usage percentage

### Filter Cost Entries
Use filter form to narrow down entries:
- **Project:** Filter by project
- **Cost Type:** Filter by type (material, labor, etc.)
- **Date From:** Start date range
- **Date To:** End date range

## Business Logic

### Variance Calculation
```
Variance = Actual Cost - Planned Cost
Variance % = (Variance / Planned Cost) × 100
```

### Approval Triggers
- **Variance ≤ 10%:** Auto-approved, no review needed
- **Variance > 10%:** Requires Cost Control Manager approval

### Budget Updates
- When cost entry created, `Budget.spent_amount` increases
- Remaining budget automatically recalculates
- If budget exceeded, warning shows but doesn't block entry

### Status Badges
- 🟢 **Approved:** Entry approved (variance ≤ 10% or manually approved)
- 🟡 **Pending:** Awaiting approval (variance > 10%)
- 🔴 **Rejected:** Approval denied

## Example Scenarios

### Scenario 1: Normal Purchase (No Approval Needed)
```
Project: HR Operations
Category: Direct Materials
Cost Type: material
Description: Steel reinforcement bars
Planned: ₦10,000
Actual: ₦10,500
Variance: +₦500 (+5%)

Result:
✓ Entry created with "Approved" status
✓ Material budget: ₦10,500 spent, ₦489,500 remaining
✓ No approval needed
```

### Scenario 2: High Variance (Approval Required)
```
Project: HR Operations
Category: Direct Labor
Cost Type: labor
Description: Overtime for foundation work
Planned: ₦20,000
Actual: ₦25,000
Variance: +₦5,000 (+25%)

Result:
⚠️  Entry created with "Pending" status
✓ Labor budget: ₦25,000 spent, ₦975,000 remaining
⚠️  Approval request created
⚠️  Cost Control Manager can review and approve/reject
```

### Scenario 3: Budget Overage (Warning Only)
```
Project: HR Operations
Category: Safety
Budget Allocated: ₦75,000
Entry Actual Cost: ₦80,000

Result:
⚠️  Warning: "Budget exceeded by ₦5,000 for safety"
✓ Entry still created (no blocking)
✓ Budget shows 106.7% usage
✓ Audit log records overage
```

## Key Features

### Real-Time Features
- ✓ Dynamic category loading by project
- ✓ Live variance calculation
- ✓ Auto approval warning
- ✓ Budget progress visualization

### Data Integrity
- ✓ All data from backend database
- ✓ No dummy/hardcoded data
- ✓ CSRF protection
- ✓ Transaction rollback on errors

### Audit & Compliance
- ✓ All entries logged with user ID
- ✓ Timestamp tracking (created/updated)
- ✓ Budget overages logged
- ✓ Approval workflow tracked

### User Experience
- ✓ Empty state messages
- ✓ Success/error flash messages
- ✓ Color-coded status indicators
- ✓ Responsive design
- ✓ Loading states during AJAX

## API Endpoints

### Get Project Categories
```
GET /cost-control/manager/api/categories/<project_id>

Response:
{
  "success": true,
  "categories": [
    {"id": 1, "name": "Direct Materials", "type": "material"},
    {"id": 2, "name": "Direct Labor", "type": "labor"},
    ...
  ]
}
```

### Submit Cost Entry
```
POST /cost-control/manager/cost-tracking

Form Data:
- project_id: int
- category_id: int
- cost_type: string
- entry_date: date (YYYY-MM-DD)
- description: string
- planned_cost: float
- actual_cost: float
- quantity: float (optional)
- unit: string (optional)
- csrf_token: string

Response: Redirect with flash message
```

## Database Schema

### CostTrackingEntry Table
```sql
id                  INTEGER PRIMARY KEY
project_id          INTEGER FOREIGN KEY → projects.id
category_id         INTEGER FOREIGN KEY → cost_category.id
entry_date          DATE
description         VARCHAR(500)
planned_cost        FLOAT
actual_cost         FLOAT
variance            FLOAT (calculated)
variance_percentage FLOAT (calculated)
cost_type           VARCHAR(50)
quantity            FLOAT (nullable)
unit                VARCHAR(50) (nullable)
status              VARCHAR(32) (pending/approved/rejected)
requires_approval   BOOLEAN
created_by          INTEGER FOREIGN KEY → user.id
created_at          DATETIME
updated_at          DATETIME
```

### Budget Table
```sql
id               INTEGER PRIMARY KEY
project_id       INTEGER FOREIGN KEY → projects.id
category         VARCHAR(64)
allocated_amount FLOAT
spent_amount     FLOAT
status           VARCHAR(32)
fiscal_year      INTEGER
created_at       DATETIME
updated_at       DATETIME
```

### CostCategory Table
```sql
id         INTEGER PRIMARY KEY
project_id INTEGER FOREIGN KEY → projects.id (but not enforced in schema)
name       VARCHAR(100)
type       VARCHAR(50)
```

## Troubleshooting

### Categories Not Loading
**Problem:** Category dropdown shows "Select Project First"
**Solution:** Make sure project is selected first, wait for AJAX call

### Variance Not Calculating
**Problem:** No variance shown when entering costs
**Solution:** Enter both planned AND actual costs (both must have values)

### Budget Not Updating
**Problem:** Budget shows 0% usage after entries
**Solution:** 
1. Check category.type matches budget.category
2. Verify budget exists for that category
3. Check console for errors

### Approval Not Creating
**Problem:** High variance but no "Pending" status
**Solution:** 
1. Verify variance is truly > 10%
2. Check CostApproval table for records
3. Review application logs

## Maintenance Scripts

### Check System Status
```bash
python test_cost_tracking.py
```

### Recreate Categories
```bash
python create_standard_cost_categories.py
```

### Reset Budgets
```bash
python create_sample_budgets.py
```

### View Database Content
```bash
python check_cost_categories.py
```

## Support

For issues or questions:
1. Check application logs: `app.log`
2. Check browser console for JavaScript errors
3. Review audit logs for user actions
4. Verify database integrity with test scripts
