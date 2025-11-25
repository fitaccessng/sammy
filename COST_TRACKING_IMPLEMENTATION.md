# Cost Tracking Implementation - Complete Business Logic

## Overview
Implemented a comprehensive cost tracking system that uses real backend data with proper business logic, including:
- Real project integration
- Dynamic cost categories by project
- Automatic budget tracking and updates
- Variance calculation with approval workflows
- Audit logging

## What Was Implemented

### 1. Cost Category System
**File Created:** `create_standard_cost_categories.py`

Created 10 standard cost categories for each project:
- Direct Materials (material)
- Direct Labor (labor)
- Equipment & Machinery (equipment)
- Subcontractor Services (subcontractor)
- Overhead Costs (overhead)
- Transportation & Logistics (transportation)
- Professional Services (professional_services)
- Safety & Compliance (safety)
- Utilities (utilities)
- Miscellaneous (miscellaneous)

**Database:** 10 categories created for "HR Operations" project (ID: 1)

### 2. Budget Allocation System
**File Created:** `create_sample_budgets.py`

Created budget allocations for HR Operations project:
- Material: ₦500,000
- Labor: ₦1,000,000
- Equipment: ₦300,000
- Subcontractor: ₦200,000
- Overhead: ₦150,000
- Transportation: ₦100,000
- Professional Services: ₦250,000
- Safety: ₦75,000
- Utilities: ₦125,000
- Miscellaneous: ₦50,000

**Total Budget:** ₦2,750,000

### 3. Enhanced Cost Tracking Route
**File Modified:** `app.py` (lines 1050-1202)

**New Business Logic:**
```python
# When a cost entry is submitted:
1. Validate project exists
2. Get cost category to determine budget category
3. Create CostTrackingEntry with all details
4. Calculate variance automatically
5. If variance > 10%:
   - Mark entry as "pending"
   - Create CostApproval record for review
   - Notify user that approval is required
6. If variance <= 10%:
   - Mark entry as "approved"
   - Proceed immediately
7. Update Budget.spent_amount for the category
8. Check if budget is exceeded:
   - If exceeded, show warning with overage amount
   - Log audit trail
9. If no budget exists for category:
   - Create new budget entry with ₦0 allocated
   - Notify user to set budget allocation
10. Commit all changes
11. Log audit trail with project, category, amount, variance, and user
```

**Budget Updates:**
- Automatically updates `Budget.spent_amount` when cost entry is created
- Calculates remaining budget using `Budget.remaining_amount` property
- Calculates usage percentage using `Budget.usage_percentage` property
- Creates new budget category if doesn't exist

**Audit Logging:**
- Info log for successful cost entries
- Warning log for budget overages
- Error log for failures with full stack trace

### 4. Dynamic Category Loading API
**New Endpoint:** `/cost-control/manager/api/categories/<project_id>`

Returns categories filtered by project in JSON format:
```json
{
  "success": true,
  "categories": [
    {"id": 1, "name": "Direct Materials", "type": "material"},
    {"id": 2, "name": "Direct Labor", "type": "labor"},
    ...
  ]
}
```

### 5. Enhanced Cost Tracking Template
**File Modified:** `templates/cost_control/manager/cost_tracking.html`

**New Features:**

**Budget Summary Cards** (displayed when project is selected):
- Shows spent vs allocated for each budget category
- Visual progress bars with color coding:
  - Green: 0-75% usage
  - Yellow: 75-90% usage
  - Red: >90% usage
- Displays remaining amount and percentage

**Improved Form:**
- CSRF token protection
- Dynamic category loading via AJAX
  - Categories update when project is selected
  - Only shows categories for selected project
- Real-time variance calculation
  - Shows variance amount and percentage as you type
  - Color coded (green for under budget, red for over)
  - Warning message if variance > 10% (requires approval)
- Auto-fills today's date
- Better field labels with required indicators
- Placeholder text for guidance

**Better Data Display:**
- Empty state message when no entries
- Status badges (Approved, Pending, Rejected)
- Color-coded variance percentages
- Formatted currency display

**JavaScript Features:**
```javascript
1. Dynamic category dropdown population
2. Real-time variance calculation
3. Approval warning display
4. Auto date-filling
5. Project pre-selection handling
```

## Business Logic Flow

### Cost Entry Creation Flow:
```
1. User selects project → Categories load dynamically
2. User enters planned cost & actual cost → Variance calculates in real-time
3. If variance > 10% → Warning appears
4. User submits form
5. Backend validates data
6. Creates cost entry with variance calculation
7. Updates budget spent_amount
8. If budget exceeded → Shows warning
9. If high variance → Creates approval request
10. Logs audit trail
11. Returns to page with success/warning message
```

### Variance Approval Flow:
```
1. Cost entry created with variance > 10%
2. Status set to "pending"
3. CostApproval record created:
   - reference_type: 'cost_entry'
   - reference_id: entry.id
   - required_role: HQ_COST_CONTROL
   - amount: actual_cost
   - description: "Cost variance: X% - [description]"
4. Entry appears with "Pending" badge
5. Cost Control manager can approve/reject in approvals section
6. On approval → entry.status = 'approved'
7. On rejection → entry.status = 'rejected'
```

### Budget Tracking:
```
For each cost entry:
1. Find or create Budget record for (project_id, category)
2. Add actual_cost to spent_amount
3. Calculate remaining = allocated - spent
4. Calculate usage_percentage = (spent / allocated) * 100
5. If spent > allocated:
   - Log warning
   - Show overage in flash message
   - Continue (no blocking)
```

## Data Model Integration

### CostTrackingEntry
- Links to Project (project_id)
- Links to CostCategory (category_id)
- Stores planned_cost, actual_cost
- Auto-calculates variance, variance_percentage
- Tracks status (pending, approved, rejected)
- Links to creator (User)

### CostCategory
- Links to Project (project_id)
- Has name (e.g., "Direct Materials")
- Has type (e.g., "material") → used for budget category

### Budget
- Links to Project (project_id)
- Has category (matches CostCategory.type)
- Tracks allocated_amount, spent_amount
- Calculates remaining_amount (property)
- Calculates usage_percentage (property)

### CostApproval
- Links to CostTrackingEntry via reference_id
- Tracks approval workflow
- Status: pending, approved, rejected
- Links to approver and creator

## Testing the System

### 1. View Cost Tracking Page
Navigate to: Cost Control → Cost Tracking

**Expected:**
- Project dropdown shows "HR Operations"
- Budget summary not visible yet (no project selected)
- Form loads with empty fields
- Table shows "No cost entries found" message

### 2. Create a Normal Cost Entry (variance < 10%)
1. Select "HR Operations" project
2. Wait for categories to load (AJAX)
3. Select "Direct Materials"
4. Select cost type "material"
5. Enter date (today)
6. Enter description: "Steel reinforcement bars"
7. Enter planned: 10000
8. Enter actual: 10500 (5% variance)
9. Observe real-time variance display: +₦500 (+5.0%)
10. Submit

**Expected Result:**
- Success message: "Cost entry added successfully"
- No approval warning (variance < 10%)
- Entry appears in table with "Approved" status
- Page reloads with entry visible

### 3. Create a High Variance Entry (variance > 10%)
1. Select "HR Operations" project
2. Select "Direct Labor"
3. Enter planned: 20000
4. Enter actual: 25000 (25% variance)
5. Observe: Warning appears "⚠️ This entry will require approval..."
6. Submit

**Expected Result:**
- Warning message: "Cost entry created with 25.0% variance. Approval required."
- Entry appears with "Pending" status
- CostApproval record created in database
- Budget still updated with actual cost

### 4. View Budget Summary
1. Apply filter: Select "HR Operations" project
2. Submit filter form

**Expected Result:**
- Budget summary cards appear at top
- Shows 10 budget categories with progress bars
- Material category shows some usage from first entry
- Labor category shows some usage from second entry
- Colors change based on usage (green for low, yellow/red for high)

### 5. Test Budget Overage
1. Create entry with actual cost exceeding budget
2. Example: Material budget is ₦500,000
3. Submit entry with actual cost = 600,000

**Expected Result:**
- Warning flash: "Budget exceeded by ₦X for material"
- Entry still created (no blocking)
- Audit log created
- Budget shows 100%+ usage

## Files Modified/Created

### Created:
- `check_cost_categories.py` - Diagnostic script
- `create_standard_cost_categories.py` - Category setup script
- `create_sample_budgets.py` - Budget setup script

### Modified:
- `app.py` (lines 1050-1228):
  - Enhanced cost_tracking route (lines 1050-1202)
  - Added get_project_categories API endpoint (lines 1205-1224)
- `templates/cost_control/manager/cost_tracking.html`:
  - Complete rewrite with business logic integration
  - Added budget summary cards
  - Added dynamic category loading
  - Added real-time variance calculation
  - Added empty state handling

## Next Steps (Optional Enhancements)

### 1. Bulk Import
Add CSV upload for bulk cost entry creation

### 2. Cost Approval Interface
Create dedicated page for approving/rejecting pending cost entries

### 3. Advanced Analytics
- Trend analysis by category
- Forecasting based on current spend rate
- Alerts for categories approaching budget limits

### 4. Budget Adjustment Workflow
Interface for requesting budget increases/reallocation

### 5. Export Functionality
Export cost entries and budget reports to Excel/PDF

### 6. Dashboard Integration
Add cost tracking widgets to main dashboard:
- Budget utilization gauge
- Recent high-variance entries
- Categories needing attention

## Summary

✅ **Complete business logic implementation:**
- Real projects from backend (HR Operations)
- 10 standard cost categories per project
- Budget allocations with ₦2.75M total
- Automatic budget tracking and updates
- Variance calculation with approval triggers
- Dynamic category filtering by project
- Real-time variance preview
- Budget summary with visual progress bars
- Comprehensive audit logging
- Empty state handling
- CSRF protection
- Error handling with rollback

✅ **No dummy data:**
- All data comes from database
- Categories linked to actual projects
- Budgets linked to actual categories
- Cost entries update real budgets
- Approvals tracked in workflow system

✅ **Production-ready features:**
- Input validation
- Error handling
- Audit logging
- Transaction management (commit/rollback)
- User-friendly feedback messages
- Visual progress indicators
- Responsive design
