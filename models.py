
# --- Admin/Manager Models ---
from datetime import datetime, timezone
from extensions import db

class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, nullable=False)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# --- HR Query Model Stub ---
class Query(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer)
    subject = db.Column(db.String(128))
    status = db.Column(db.String(32))
    priority = db.Column(db.String(32))
    category = db.Column(db.String(64))
    submitted_at = db.Column(db.DateTime)
    description = db.Column(db.Text)

class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

class ReportingLine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    manager_id = db.Column(db.Integer, nullable=False)
    staff_id = db.Column(db.Integer, nullable=False)

class ApprovalHierarchy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    process = db.Column(db.String(50), nullable=False)
    level = db.Column(db.Integer, nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)

class Permission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)
    resource = db.Column(db.String(50), nullable=False)
    action = db.Column(db.String(20), nullable=False)
# --- Cost Control Models ---
from extensions import db

class CostCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)

class Machinery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    serial_no = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    model = db.Column(db.String(100))
    status = db.Column(db.String(50))
    rate = db.Column(db.Float)
    days_active = db.Column(db.Integer)
    monthly_cost = db.Column(db.Float)
    warning_flag = db.Column(db.Boolean, default=False)

class FuelLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    serial_no = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    equipment_code = db.Column(db.String(100))
    reg_no = db.Column(db.String(100))
    operator = db.Column(db.String(100))
    start_meter = db.Column(db.Float)
    end_meter = db.Column(db.Float)
    total_hours = db.Column(db.Float)
    fuel_consumed = db.Column(db.Float)

class CostVarianceReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    planned_amount = db.Column(db.Float, nullable=False)
    actual_amount = db.Column(db.Float, nullable=False)
    variance = db.Column(db.Float, nullable=False)

class CostTrackingEntry(db.Model):
    __tablename__ = 'cost_tracking_entries'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('cost_category.id'), nullable=True)
    entry_date = db.Column(db.Date, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    planned_cost = db.Column(db.Float, default=0.0)
    actual_cost = db.Column(db.Float, default=0.0)
    variance = db.Column(db.Float, default=0.0)
    variance_percentage = db.Column(db.Float, default=0.0)
    cost_type = db.Column(db.String(50), nullable=False)  # material, labor, equipment, overhead
    quantity = db.Column(db.Float, nullable=True)
    unit = db.Column(db.String(50), nullable=True)
    unit_cost = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(32), default='pending')  # pending, approved, rejected
    approval_required = db.Column(db.Boolean, default=False)
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def calculate_variance(self):
        """Calculate variance and variance percentage"""
        self.variance = self.actual_cost - self.planned_cost
        if self.planned_cost > 0:
            self.variance_percentage = (self.variance / self.planned_cost) * 100
        else:
            self.variance_percentage = 0
    
    def __repr__(self):
        return f'<CostTrackingEntry {self.id} - {self.description}>'

class CostApproval(db.Model):
    __tablename__ = 'cost_approvals'
    
    id = db.Column(db.Integer, primary_key=True)
    reference_type = db.Column(db.String(64), nullable=False)  # 'cost_entry', 'budget_adjustment'
    reference_id = db.Column(db.Integer, nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    required_role = db.Column(db.String(64), nullable=False)  # Role needed to approve
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=False)
    
    # Approval tracking
    status = db.Column(db.String(32), default='pending')  # pending, approved, rejected
    approver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    comments = db.Column(db.Text, nullable=True)
    action_taken = db.Column(db.String(32), nullable=True)  # approved, rejected
    
    # Metadata
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    project = db.relationship('Project', backref='cost_approvals')
    approver = db.relationship('User', foreign_keys=[approver_id], backref='approved_costs')
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_approvals')
    
    def __repr__(self):
        return f'<CostApproval {self.id} - {self.reference_type} - {self.status}>'

class BudgetAdjustment(db.Model):
    __tablename__ = 'budget_adjustments'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    budget_id = db.Column(db.Integer, db.ForeignKey('budgets.id'), nullable=False)
    category = db.Column(db.String(64), nullable=False)
    
    # Adjustment details
    old_amount = db.Column(db.Float, nullable=False)
    new_amount = db.Column(db.Float, nullable=False)
    adjustment_amount = db.Column(db.Float, nullable=False)
    adjustment_type = db.Column(db.String(32), nullable=False)  # 'increase', 'decrease'
    reason = db.Column(db.Text, nullable=False)
    impact_analysis = db.Column(db.Text, nullable=True)
    
    # Approval tracking
    status = db.Column(db.String(32), default='pending')  # pending, approved, rejected
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    approval_comments = db.Column(db.Text, nullable=True)
    
    # Metadata
    requested_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    requested_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    project = db.relationship('Project', backref='budget_adjustments')
    budget = db.relationship('Budget', backref='adjustments')
    approver = db.relationship('User', foreign_keys=[approved_by], backref='approved_adjustments')
    requester = db.relationship('User', foreign_keys=[requested_by], backref='requested_adjustments')
    
    def __repr__(self):
        return f'<BudgetAdjustment {self.id} - {self.category} - {self.adjustment_type}>'

## --- Procurement Models ---
class ProcurementRequest(db.Model):
    __tablename__ = 'procurement_requests'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    item_name = db.Column(db.String(128), nullable=False)
    price = db.Column(db.Float, nullable=False)
    qty = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(32), nullable=False)
    status = db.Column(db.String(32), default='pending')
    current_approver = db.Column(db.String(128), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<ProcurementRequest {self.id}>'

class Vendor(db.Model):
    __tablename__ = 'vendors'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    category = db.Column(db.String(64), nullable=False)
    payment_terms = db.Column(db.String(128), nullable=True)
    validated = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Vendor {self.name}>'

class InventoryItem(db.Model):
    __tablename__ = 'inventory_items'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(256), nullable=False)
    group = db.Column(db.String(64), nullable=True)
    category = db.Column(db.String(64), nullable=True)
    qty_available = db.Column(db.Float, default=0.0)
    unit_cost = db.Column(db.Float, nullable=False)
    uom = db.Column(db.String(32), nullable=False)
    total_cost = db.Column(db.Float, default=0.0)
    price_change = db.Column(db.Float, default=0.0)
    location = db.Column(db.String(255), nullable=True)  # Physical location/address
    previous_location = db.Column(db.String(255), nullable=True)  # Previous location for history
    latitude = db.Column(db.Float, nullable=True)  # GPS latitude
    longitude = db.Column(db.Float, nullable=True)  # GPS longitude
    status = db.Column(db.String(32), default='Active')  # Active, In Transit, In Maintenance, Retired
    last_location_update = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<InventoryItem {self.code}>'

class Technician(db.Model):
    __tablename__ = 'technicians'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(128), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    specialization = db.Column(db.String(128), nullable=True)
    status = db.Column(db.String(20), default='active')  # active, inactive, on_leave
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Technician {self.name}>'

class MaintenanceSchedule(db.Model):
    __tablename__ = 'maintenance_schedules'
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('inventory_items.id'), nullable=False)
    technician_id = db.Column(db.Integer, db.ForeignKey('technicians.id'), nullable=True)
    maintenance_type = db.Column(db.String(64), nullable=False)  # Routine, Repair, Inspection, etc.
    scheduled_date = db.Column(db.Date, nullable=False)
    completed_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default='scheduled')  # scheduled, in_progress, completed, cancelled
    notes = db.Column(db.Text, nullable=True)
    cost = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    asset = db.relationship('InventoryItem', backref='maintenance_schedules')
    technician = db.relationship('Technician', backref='maintenance_schedules')
    
    def __repr__(self):
        return f'<MaintenanceSchedule {self.id} - Asset {self.asset_id}>'

from extensions import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# --- Finance Models ---
class ChartOfAccount(db.Model):
    __tablename__ = 'chart_of_accounts'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    type = db.Column(db.String(64), nullable=False)  # e.g., Asset, Liability, Equity, Revenue, Expense
    parent_id = db.Column(db.Integer, db.ForeignKey('chart_of_accounts.id'), nullable=True)
    parent = db.relationship('ChartOfAccount', remote_side=[id], backref='children')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<ChartOfAccount {self.name}>'

class PaymentRequest(db.Model):
    __tablename__ = 'payment_requests'
    id = db.Column(db.Integer, primary_key=True)
    department_id = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(32), default='pending')  # pending, approved, disbursed, rejected
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    disbursed_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    requester_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f'<PaymentRequest {self.id}>'

class Budget(db.Model):
    __tablename__ = 'budgets'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    category = db.Column(db.String(64), nullable=False)  # e.g., payroll, procurement, etc.
    allocated_amount = db.Column(db.Float, nullable=False)
    spent_amount = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(32), nullable=False, default='active')  # active, completed, cancelled
    fiscal_year = db.Column(db.Integer, nullable=True)  # e.g., 2025
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Note: Relationship is defined on Project model

    @property
    def remaining_amount(self):
        """Calculate remaining budget amount"""
        return max(0, self.allocated_amount - self.spent_amount)
    
    @property
    def usage_percentage(self):
        """Calculate budget usage percentage"""
        if self.allocated_amount <= 0:
            return 0
        return min(100, (self.spent_amount / self.allocated_amount) * 100)

    def __repr__(self):
        return f'<Budget {self.project_id} - {self.category}>'

class CashFlowForecast(db.Model):
    __tablename__ = 'cash_flow_forecasts'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True)
    forecast_period = db.Column(db.String(64), nullable=False)  # e.g., "Q1 2025", "January 2025"
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)
    forecast_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    
    # Cash flow components
    expected_inflow = db.Column(db.Float, default=0.0)
    actual_inflow = db.Column(db.Float, default=0.0)
    expected_outflow = db.Column(db.Float, default=0.0)
    actual_outflow = db.Column(db.Float, default=0.0)
    opening_balance = db.Column(db.Float, default=0.0)
    
    # Cost breakdown
    labor_cost = db.Column(db.Float, default=0.0)
    material_cost = db.Column(db.Float, default=0.0)
    equipment_cost = db.Column(db.Float, default=0.0)
    subcontractor_cost = db.Column(db.Float, default=0.0)
    overhead_cost = db.Column(db.Float, default=0.0)
    
    notes = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(32), nullable=False, default='draft')  # draft, approved, revised
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = db.relationship('Project', backref='project_cash_flow_forecasts')
    creator = db.relationship('User', backref='created_forecasts', foreign_keys=[created_by])
    
    @property
    def closing_balance(self):
        """Calculate closing balance"""
        return self.opening_balance + self.actual_inflow - self.actual_outflow
    
    @property
    def variance_inflow(self):
        """Calculate variance between expected and actual inflow"""
        return self.actual_inflow - self.expected_inflow
    
    @property
    def variance_outflow(self):
        """Calculate variance between expected and actual outflow"""
        return self.actual_outflow - self.expected_outflow
    
    @property
    def total_cost(self):
        """Calculate total cost from all components"""
        return (self.labor_cost + self.material_cost + self.equipment_cost + 
                self.subcontractor_cost + self.overhead_cost)
    
    def __repr__(self):
        return f'<CashFlowForecast {self.forecast_period}>'

class Invoice(db.Model):
    __tablename__ = 'invoices'
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(64), unique=True, nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True)
    customer_name = db.Column(db.String(128), nullable=False)
    customer_email = db.Column(db.String(128), nullable=True)
    customer_address = db.Column(db.Text, nullable=True)
    invoice_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(32), nullable=False, default='draft')  # draft, sent, partially_paid, paid, cancelled, overdue
    payment_status = db.Column(db.String(32), nullable=True)  # unpaid, partially_paid, paid
    subtotal = db.Column(db.Float, default=0.0)
    tax_amount = db.Column(db.Float, default=0.0)
    discount_amount = db.Column(db.Float, default=0.0)
    total_amount = db.Column(db.Float, nullable=False, default=0.0)
    paid_amount = db.Column(db.Float, default=0.0)
    notes = db.Column(db.Text, nullable=True)
    terms = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Relationships
    project = db.relationship('Project', backref='project_invoices')
    creator = db.relationship('User', backref='created_invoices', foreign_keys=[created_by])
    
    @property
    def balance_due(self):
        """Calculate remaining balance"""
        return max(0, self.total_amount - self.paid_amount)
    
    @property
    def is_overdue(self):
        """Check if invoice is overdue"""
        from datetime import datetime
        if self.due_date and self.status not in ['paid', 'cancelled']:
            return datetime.now().date() > self.due_date
        return False
    
    @property
    def days_overdue(self):
        """Calculate days overdue"""
        from datetime import datetime
        if self.is_overdue:
            return (datetime.now().date() - self.due_date).days
        return 0
    
    def calculate_totals(self):
        """Calculate invoice totals from line items"""
        # This method can be enhanced when InvoiceLineItem model is added
        self.total_amount = self.subtotal + self.tax_amount - self.discount_amount
    
    def update_status(self):
        """Update invoice status based on payment and due date"""
        from datetime import datetime
        
        # Check if fully paid
        if self.paid_amount >= self.total_amount:
            self.status = 'paid'
            self.payment_status = 'paid'
        # Check if partially paid
        elif self.paid_amount > 0:
            self.status = 'partially_paid'
            self.payment_status = 'partially_paid'
        # Check if overdue
        elif self.due_date and datetime.now().date() > self.due_date and self.status not in ['paid', 'cancelled', 'draft']:
            self.status = 'overdue'
        # Otherwise keep current status (draft, sent, etc.)
        
    def record_payment(self, amount):
        """Record a payment against this invoice"""
        self.paid_amount = (self.paid_amount or 0) + amount
        self.update_status()
        
    def __repr__(self):
        return f'<Invoice {self.invoice_number} - {self.customer_name}>'

class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True)
    payment_number = db.Column(db.String(64), unique=True, nullable=False)
    payment_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    payment_type = db.Column(db.String(32), nullable=False)  # receipt, disbursement
    payment_method = db.Column(db.String(32), nullable=False)  # cash, check, bank_transfer, card
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(32), nullable=False, default='pending')  # pending, approved, rejected, completed
    reference_number = db.Column(db.String(128), nullable=True)
    description = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    request_date = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Relationships
    invoice = db.relationship('Invoice', backref='invoice_payments')
    project = db.relationship('Project', backref='project_payments')
    creator = db.relationship('User', backref='created_payments', foreign_keys=[created_by])
    
    def __repr__(self):
        return f'<Payment {self.payment_number} - ₦{self.amount}>'

class AccountsReceivable(db.Model):
    __tablename__ = 'accounts_receivable'
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True)
    customer_name = db.Column(db.String(128), nullable=False)
    invoice_number = db.Column(db.String(64), nullable=True)
    balance = db.Column(db.Float, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(32), nullable=False, default='outstanding')  # outstanding, partially_paid, paid
    aging_bucket = db.Column(db.String(32), nullable=True)  # current, 1-30, 31-60, 61-90, 90+
    days_outstanding = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    invoice = db.relationship('Invoice', backref='receivables')
    project = db.relationship('Project', backref='project_receivables')
    
    def calculate_aging(self):
        """Calculate aging bucket based on days outstanding"""
        from datetime import datetime
        today = datetime.now().date()
        self.days_outstanding = (today - self.due_date).days if self.due_date else 0
        
        if self.days_outstanding <= 0:
            self.aging_bucket = 'current'
        elif self.days_outstanding <= 30:
            self.aging_bucket = '1-30'
        elif self.days_outstanding <= 60:
            self.aging_bucket = '31-60'
        elif self.days_outstanding <= 90:
            self.aging_bucket = '61-90'
        else:
            self.aging_bucket = '90+'
    
    def __repr__(self):
        return f'<AccountsReceivable {self.customer_name} - ₦{self.balance}>'

class AccountsPayable(db.Model):
    __tablename__ = 'accounts_payable'
    id = db.Column(db.Integer, primary_key=True)
    vendor_name = db.Column(db.String(128), nullable=False)
    vendor_email = db.Column(db.String(128), nullable=True)
    bill_number = db.Column(db.String(64), nullable=True)
    bill_date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    amount_due = db.Column(db.Float, nullable=False)
    balance = db.Column(db.Float, nullable=False)
    paid_amount = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(32), nullable=False, default='unpaid')  # unpaid, partially_paid, paid, overdue
    payment_terms = db.Column(db.String(64), nullable=True)  # Net 30, Net 60, etc.
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(64), nullable=True)  # Materials, Services, Equipment, etc.
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = db.relationship('Project', backref='project_payables')
    creator = db.relationship('User', backref='created_payables', foreign_keys=[created_by])
    
    @property
    def days_overdue(self):
        """Calculate days overdue"""
        from datetime import datetime
        if self.due_date and self.status in ['unpaid', 'partially_paid']:
            days = (datetime.now().date() - self.due_date).days
            return max(0, days)
        return 0
    
    @property
    def is_overdue(self):
        """Check if payable is overdue"""
        return self.days_overdue > 0
    
    def calculate_aging(self):
        """Calculate aging bucket based on days overdue"""
        days = self.days_overdue
        
        if days <= 0:
            self.aging_bucket = 'current'
        elif days <= 30:
            self.aging_bucket = '1-30'
        elif days <= 60:
            self.aging_bucket = '31-60'
        elif days <= 90:
            self.aging_bucket = '61-90'
        else:
            self.aging_bucket = '90+'
    
    def __repr__(self):
        return f'<AccountsPayable {self.vendor_name} - ₦{self.balance}>'

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    verification_code = db.Column(db.String(6), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_role(self, role):
        return str(self.role).strip().upper() == str(role).strip().upper()

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)


class FinancialTransaction(db.Model):
    """General ledger transactions for double-entry accounting"""
    __tablename__ = 'financial_transactions'
    id = db.Column(db.Integer, primary_key=True)
    transaction_number = db.Column(db.String(64), unique=True, nullable=False)
    transaction_type = db.Column(db.String(64), nullable=False)  # income, expense, transfer, adjustment
    transaction_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    
    # Chart of accounts
    account_code = db.Column(db.String(32), nullable=True)
    account_name = db.Column(db.String(128), nullable=True)
    
    # Double-entry amounts
    debit_amount = db.Column(db.Float, default=0.0)
    credit_amount = db.Column(db.Float, default=0.0)
    
    # Additional details
    category = db.Column(db.String(64), nullable=True)
    description = db.Column(db.Text, nullable=True)
    reference_number = db.Column(db.String(64), nullable=True)
    
    # Links to other records
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=True)
    payment_id = db.Column(db.Integer, db.ForeignKey('payments.id'), nullable=True)
    
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @property
    def balance(self):
        """Calculate the net balance (debit - credit)"""
        return self.debit_amount - self.credit_amount
    
    def __repr__(self):
        return f'<FinancialTransaction {self.transaction_number}>'

class Project(db.Model):
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    status = db.Column(db.String(50), default='Planning')
    project_manager = db.Column(db.String(255))
    budget = db.Column(db.Float, default=0.0)
    progress = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Enhanced business fields
    project_type = db.Column(db.String(100))  # Construction, Infrastructure, etc.
    priority = db.Column(db.String(50), default='Medium')  # Low, Medium, High, Critical
    client_name = db.Column(db.String(255))  # Primary client/stakeholder
    site_location = db.Column(db.String(500))  # Project site address
    funding_source = db.Column(db.String(100))  # Internal, Client Payment, Bank Loan, etc.
    risk_level = db.Column(db.String(50), default='Low')  # Low, Medium, High, Critical
    safety_requirements = db.Column(db.String(100), default='Standard')  # Standard, Enhanced, High Security, Specialized
    regulatory_requirements = db.Column(db.Text)  # Permits, licenses, compliance standards
    
    # Relationships
    milestones = db.relationship('Milestone', backref='project', lazy=True)
    tasks = db.relationship('Task', backref='project', lazy=True)
    schedules = db.relationship('Schedule', backref='project', lazy=True)
    procurement_requests = db.relationship('ProcurementRequest', backref='project', lazy=True)
    budgets = db.relationship('Budget', backref='project', lazy=True)
    purchase_orders = db.relationship('PurchaseOrder', backref='project', lazy=True)
    staff_assignments = db.relationship('StaffAssignment', backref='project', lazy=True)
    
    def __repr__(self):
        return f'<Project {self.name}>'
class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    staff_code = db.Column(db.String(32), unique=True, index=True)  # Staff ID / S/N
    name = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(128), nullable=True)  # Removed unique constraint
    role = db.Column(db.String(64))
    department = db.Column(db.String(128))  # Added department column
    status = db.Column(db.String(32), default='Active')
    site = db.Column(db.String(128))
    dob = db.Column(db.Date)
    next_of_kin = db.Column(db.String(128))
    next_of_kin_relationship = db.Column(db.String(64))
    next_of_kin_address = db.Column(db.String(255))
    next_of_kin_phone = db.Column(db.String(32))
    position = db.Column(db.String(128))
    date_of_employment = db.Column(db.Date)
    employment_letter = db.Column(db.String(16))
    sectional_head = db.Column(db.String(128))
    job_description = db.Column(db.Text)
    academic_qualification_at_employment = db.Column(db.String(255))
    present_academic_qualification = db.Column(db.String(255))
    current_address = db.Column(db.String(255))
    permanent_address = db.Column(db.String(255))
    phone = db.Column(db.String(20))
    degree = db.Column(db.String(100))
    institution = db.Column(db.String(255))
    current_certification = db.Column(db.String(100))
    present_assignment = db.Column(db.String(100))
    employment_dates = db.Column(db.String(100))
    past_job_title = db.Column(db.String(100))
    past_employer_dates = db.Column(db.String(255))
    past_accomplishments = db.Column(db.String(255))
    technical_skills = db.Column(db.String(255))
    soft_skills = db.Column(db.String(255))
    certifications = db.Column(db.String(255))
    team_info = db.Column(db.String(100))
    notes = db.Column(db.String(255))
    sectional_head_upgrade = db.Column(db.String(100))
    job_description_upgrade = db.Column(db.String(255))
    
    # Comprehensive Salary Structure
    basic_salary = db.Column(db.Float, default=0.0)  # Base salary
    housing_allowance = db.Column(db.Float, default=0.0)  # Housing allowance
    transport_allowance = db.Column(db.Float, default=0.0)  # Transport allowance
    medical_allowance = db.Column(db.Float, default=0.0)  # Medical allowance
    special_allowance = db.Column(db.Float, default=0.0)  # Special/other allowances
    overtime_rate = db.Column(db.Float, default=0.0)  # Overtime hourly rate
    
    # Tax and Deduction Information
    tax_number = db.Column(db.String(50))  # Tax identification number
    pension_number = db.Column(db.String(50))  # Pension fund number
    bank_name = db.Column(db.String(128))  # Bank name for salary payment
    bank_account_number = db.Column(db.String(50))  # Bank account number
    bank_sort_code = db.Column(db.String(20))  # Bank sort code
    
    # Employment Type and Grade
    employment_type = db.Column(db.String(32), default='Full-time')  # Full-time, Part-time, Contract
    grade_level = db.Column(db.String(20))  # Employee grade/level
    step = db.Column(db.Integer, default=1)  # Step within grade
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def calculate_gross_salary(self, overtime_hours=0):
        """Calculate total gross salary including allowances and overtime"""
        gross = (self.basic_salary or 0) + (self.housing_allowance or 0) + \
                (self.transport_allowance or 0) + (self.medical_allowance or 0) + \
                (self.special_allowance or 0) + \
                ((self.overtime_rate or 0) * overtime_hours)
        return gross
    
    def calculate_paye_tax(self, gross_salary):
        """Calculate PAYE tax based on Nigerian tax rates"""
        # Nigerian PAYE tax brackets (simplified)
        if gross_salary <= 300000:  # First ₦300,000 is tax-free annually (₦25,000 monthly)
            return 0
        elif gross_salary <= 600000:  # Next ₦300,000 at 7%
            return (gross_salary - 300000) * 0.07
        elif gross_salary <= 1100000:  # Next ₦500,000 at 11%
            return 300000 * 0.07 + (gross_salary - 600000) * 0.11
        elif gross_salary <= 1600000:  # Next ₦500,000 at 15%
            return 300000 * 0.07 + 500000 * 0.11 + (gross_salary - 1100000) * 0.15
        else:  # Above ₦1,600,000 at 24%
            return 300000 * 0.07 + 500000 * 0.11 + 500000 * 0.15 + (gross_salary - 1600000) * 0.24
    
    def calculate_pension_contribution(self, gross_salary):
        """Calculate pension contribution (8% of gross - employee portion)"""
        return gross_salary * 0.08
    
    def calculate_nhf_contribution(self, gross_salary):
        """Calculate National Housing Fund contribution (2.5% of gross, max ₦5,000 monthly)"""
        nhf = gross_salary * 0.025
        return min(nhf, 5000)  # Cap at ₦5,000 monthly
    payrolls = db.relationship('Payroll', backref='employee', lazy='dynamic')
    attendances = db.relationship('Attendance', backref='employee', lazy='dynamic')
    # Payroll breakdowns (detailed monthly payroll information)
    payroll_breakdowns = db.relationship('StaffPayroll', backref='employee', lazy='dynamic')

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    checkin_time = db.Column(db.Time)
    checkout_time = db.Column(db.Time)
    status = db.Column(db.String(32))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Asset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    type = db.Column(db.String(64))
    status = db.Column(db.String(32), default='Active')
    location = db.Column(db.String(128))
    purchase_date = db.Column(db.Date)
    purchase_cost = db.Column(db.Float, default=0.0)
    current_value = db.Column(db.Float, default=0.0)
    depreciation_rate = db.Column(db.Float, default=0.0)
    retired_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Stock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    quantity = db.Column(db.Integer, default=0)
    unit = db.Column(db.String(32))
    status = db.Column(db.String(32), default='Available')
    low_stock_threshold = db.Column(db.Integer, default=10)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PurchaseOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(64), unique=True, nullable=False)
    supplier_name = db.Column(db.String(128), nullable=False)
    supplier_contact = db.Column(db.String(128))
    supplier_email = db.Column(db.String(128))
    supplier_phone = db.Column(db.String(32))
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))
    status = db.Column(db.String(32), default='Draft')  # Draft, Pending_Cost_Control, Pending_Finance, Approved, Rejected, Ordered, Delivered, Cancelled
    priority = db.Column(db.String(32), default='Normal')  # Low, Normal, High, Urgent
    description = db.Column(db.Text)
    subtotal = db.Column(db.Float, default=0.0)
    tax_rate = db.Column(db.Float, default=0.0)
    tax_amount = db.Column(db.Float, default=0.0)
    total_amount = db.Column(db.Float, default=0.0)
    expected_delivery = db.Column(db.Date)
    requested_by = db.Column(db.Integer, db.ForeignKey('employee.id'))
    
    # Approval workflow fields
    workflow_id = db.Column(db.Integer, db.ForeignKey('approval_workflows.id'))  # Link to approval workflow
    cost_control_approved_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    cost_control_approved_at = db.Column(db.DateTime)
    cost_control_comments = db.Column(db.Text)
    finance_approved_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    finance_approved_at = db.Column(db.DateTime)
    finance_comments = db.Column(db.Text)
    
    # Legacy approval field (kept for backward compatibility)
    approved_by = db.Column(db.Integer, db.ForeignKey('employee.id'))
    approval_date = db.Column(db.DateTime)
    
    delivery_address = db.Column(db.Text)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    requested_by_employee = db.relationship('Employee', foreign_keys=[requested_by], backref='requested_orders')
    approved_by_employee = db.relationship('Employee', foreign_keys=[approved_by], backref='approved_orders')
    cost_control_approver = db.relationship('User', foreign_keys=[cost_control_approved_by], backref='cost_control_approved_pos')
    finance_approver = db.relationship('User', foreign_keys=[finance_approved_by], backref='finance_approved_pos')
    workflow = db.relationship('ApprovalWorkflow', foreign_keys=[workflow_id], backref='purchase_orders')
    line_items = db.relationship('PurchaseOrderLineItem', backref='purchase_order', cascade='all, delete-orphan')

class PurchaseOrderLineItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    purchase_order_id = db.Column(db.Integer, db.ForeignKey('purchase_order.id'), nullable=False)
    item_name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(32))
    unit_price = db.Column(db.Float, nullable=False)
    line_total = db.Column(db.Float, nullable=False)
    stock_id = db.Column(db.Integer, db.ForeignKey('stock.id'))  # Link to stock for automatic updates
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    stock_item = db.relationship('Stock', backref='purchase_order_items')

class Supplier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False, unique=True)
    contact_person = db.Column(db.String(128))
    email = db.Column(db.String(128))
    phone = db.Column(db.String(32))
    address = db.Column(db.Text)
    tax_id = db.Column(db.String(64))
    payment_terms = db.Column(db.String(128))
    status = db.Column(db.String(32), default='Active')  # Active, Inactive, Blacklisted
    rating = db.Column(db.Float)  # 1-5 rating
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Audit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(32), default='Pending')
    approved_by = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Payroll(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    deductions = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(32), default='Generated')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class StaffPayroll(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    # Period information
    period_year = db.Column(db.Integer)
    period_month = db.Column(db.Integer)
    # Spreadsheet fields
    site = db.Column(db.String(128))
    employment_date = db.Column(db.Date)
    bank_name = db.Column(db.String(128))
    account_number = db.Column(db.String(64))
    designation = db.Column(db.String(128))
    work_days = db.Column(db.Integer)
    days_worked = db.Column(db.Integer)
    overtime_hours = db.Column(db.Float)
    
    # Salary components
    basic_salary = db.Column(db.Float, default=0.0)  # Base salary
    housing_allowance = db.Column(db.Float, default=0.0)
    transport_allowance = db.Column(db.Float, default=0.0)
    meal_allowance = db.Column(db.Float, default=0.0)
    other_allowances = db.Column(db.Float, default=0.0)
    
    gross = db.Column(db.Float)
    arrears = db.Column(db.Float)
    rice_contribution = db.Column(db.Float)
    loan_or_salary_advance = db.Column(db.Float)
    jaco = db.Column(db.Float)
    minna_paye = db.Column(db.Float)
    late_deduction = db.Column(db.Float)
    balance_salary = db.Column(db.Float)
    # Approval workflow fields
    approval_status = db.Column(db.String(32), default='pending_admin')  # pending_admin, pending_finance, approved, rejected
    approved_by_admin = db.Column(db.Integer, db.ForeignKey('user.id'))
    approved_by_finance = db.Column(db.Integer, db.ForeignKey('user.id'))
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    admin_approved_at = db.Column(db.DateTime)
    finance_approved_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class StaffDeduction(db.Model):
    """Model for managing custom staff deductions"""
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    deduction_type = db.Column(db.String(64), nullable=False)  # loan, advance, disciplinary, etc.
    amount = db.Column(db.Float, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(32), default='active')  # active, completed, cancelled
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    applied_at = db.Column(db.DateTime)  # When deduction was applied to payroll
    
    # Relationships
    employee = db.relationship('Employee', backref='custom_deductions')
    creator = db.relationship('User', backref='created_deductions')

class PayrollApproval(db.Model):
    """Model for tracking payroll approval workflow"""
    id = db.Column(db.Integer, primary_key=True)
    period_year = db.Column(db.Integer, nullable=False)
    period_month = db.Column(db.Integer, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    employee_count = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(32), default='pending_admin')  # pending_admin, approved_by_admin, processed_by_finance, rejected, paid
    submitted_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    admin_approved_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    finance_processed_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    rejected_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    admin_approved_at = db.Column(db.DateTime)
    finance_processed_at = db.Column(db.DateTime)
    rejected_at = db.Column(db.DateTime)
    rejection_reason = db.Column(db.Text)
    finance_comments = db.Column(db.Text)
    # Payment tracking fields
    paid_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    paid_at = db.Column(db.DateTime)
    payment_reference = db.Column(db.String(128))
    payment_notes = db.Column(db.Text)
    
    # Relationships
    submitter = db.relationship('User', foreign_keys=[submitted_by], backref='submitted_payroll_approvals')
    admin_approver = db.relationship('User', foreign_keys=[admin_approved_by], backref='admin_approved_payrolls')
    finance_processor = db.relationship('User', foreign_keys=[finance_processed_by], backref='finance_processed_payrolls')
    rejector = db.relationship('User', foreign_keys=[rejected_by], backref='rejected_payroll_approvals')
    payer = db.relationship('User', foreign_keys=[paid_by], backref='paid_payrolls')

class Inspection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    site = db.Column(db.String(128), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(32), default='Scheduled')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
class UploadedFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    path = db.Column(db.String(255), nullable=False)
    folder = db.Column(db.String(255), nullable=True)
    tags = db.Column(db.String(255), nullable=True)
    file_size = db.Column(db.Integer, nullable=True)
    file_type = db.Column(db.String(100), nullable=True)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=True)  # Associate with staff
    uploaded_at = db.Column(db.DateTime, default=db.func.now())
    
    uploader = db.relationship('User', backref='uploaded_files')
    employee = db.relationship('Employee', backref='documents')
    
    def __repr__(self):
        return f'<UploadedFile {self.filename}>'

class StaffAssignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    role = db.Column(db.String(64), nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)

    staff = db.relationship('User', backref='project_assignments')

class EmployeeAssignment(db.Model):
    """Model for tracking Employee assignments to projects"""
    __tablename__ = 'employee_assignments'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    role = db.Column(db.String(64), nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    assigned_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    status = db.Column(db.String(32), default='Active')  # Active, Inactive, Completed
    
    # Relationships
    employee = db.relationship('Employee', backref='project_assignments')
    project = db.relationship('Project', backref='employee_assignments')
    assigner = db.relationship('User', foreign_keys=[assigned_by])

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    status = db.Column(db.String(32), default='pending')
    due_date = db.Column(db.Date)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    from_item = db.Column(db.String(128))
    to_item = db.Column(db.String(128))
    quantity = db.Column(db.Float, default=0.0)
    percent_complete = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Equipment(db.Model):
    __tablename__ = 'equipment'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    maintenance_due = db.Column(db.Date, nullable=True)
    machine_hours = db.Column(db.Float, default=0)
    diesel_consumption = db.Column(db.Float, default=0)
    remarks = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(32), default='Active')  # Added status column
    
    project = db.relationship('Project', backref=db.backref('equipments', lazy=True))

    def __repr__(self):
        return f'<Equipment {self.name}>'

class Material(db.Model):
    __tablename__ = 'materials'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    delivered = db.Column(db.Float, default=0)
    used = db.Column(db.Float, default=0)
    balance = db.Column(db.Float, default=0)
    # Add any additional fields as needed

    def __repr__(self):
        return f'<Material {self.name}>'

class Report(db.Model):
    __tablename__ = 'reports'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(256), nullable=False)
    type = db.Column(db.String(64), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    uploader_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    # Add any additional fields as needed

    def __repr__(self):
        return f'<Report {self.filename}>'

class Document(db.Model):
    __tablename__ = 'documents'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(256), nullable=False)
    original_name = db.Column(db.String(256), nullable=True)  # User-friendly name
    description = db.Column(db.Text, nullable=True)
    file_type = db.Column(db.String(10), nullable=True)  # pdf, jpg, png, etc.
    category = db.Column(db.String(64), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True)  # Project association
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    uploader_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(32), default='pending')
    size = db.Column(db.Integer, default=0)
    
    # Relationships
    project = db.relationship('Project', backref='documents')
    uploader = db.relationship('User', backref='uploaded_documents')

    def __repr__(self):
        return f'<Document {self.filename}>'

class Milestone(db.Model):
    __tablename__ = 'milestones'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    title = db.Column(db.String(128), nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(32), default='Pending')
    # Add any additional fields as needed

    def __repr__(self):
        return f'<Milestone {self.title}>'

class Expense(db.Model):
    __tablename__ = 'expenses'
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(256), nullable=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(50), default='pending')
    category = db.Column(db.String(64), default='uncategorized')  # Added category field
    # Add any additional fields as needed

    def __repr__(self):
        return f'<Expense {self.id}>'

class BankAccount(db.Model):
    __tablename__ = 'bank_accounts'
    id = db.Column(db.Integer, primary_key=True)
    account_name = db.Column(db.String(128), nullable=False, unique=True)
    account_number = db.Column(db.String(50), nullable=False)
    bank_name = db.Column(db.String(128), nullable=False)
    account_type = db.Column(db.String(50), default='Checking')  # Checking, Savings, etc.
    current_balance = db.Column(db.Float, default=0.0)
    book_balance = db.Column(db.Float, default=0.0)  # Internal balance tracking
    currency = db.Column(db.String(10), default='NGN')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    transactions = db.relationship('BankTransaction', backref='bank_account', lazy=True)
    reconciliations = db.relationship('BankReconciliation', backref='bank_account', lazy=True)
    
    def update_balance(self, amount, operation='add'):
        """Update the book balance based on transaction"""
        if operation == 'add':
            self.book_balance += amount
        elif operation == 'subtract':
            self.book_balance -= amount
        self.updated_at = datetime.utcnow()
    
    def calculate_difference(self):
        """Calculate difference between current balance and book balance"""
        return self.current_balance - self.book_balance
    
    def __repr__(self):
        return f'<BankAccount {self.account_name}>'

class BankTransaction(db.Model):
    __tablename__ = 'bank_transactions'
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('bank_accounts.id'), nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # Credit, Debit
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    reference_number = db.Column(db.String(100), nullable=True)
    transaction_date = db.Column(db.Date, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    is_reconciled = db.Column(db.Boolean, default=False)
    reconciliation_id = db.Column(db.Integer, db.ForeignKey('bank_reconciliations.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<BankTransaction {self.id}: {self.transaction_type} {self.amount}>'

class BankReconciliation(db.Model):
    __tablename__ = 'bank_reconciliations'
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('bank_accounts.id'), nullable=False)
    reconciliation_date = db.Column(db.Date, nullable=False)
    statement_balance = db.Column(db.Float, nullable=False)
    book_balance = db.Column(db.Float, nullable=False)
    difference = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(32), default='Pending')  # Pending, Reconciled, Discrepancy
    notes = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    reconciled_transactions = db.relationship('BankTransaction', backref='reconciliation', lazy=True)
    
    def calculate_difference(self):
        """Calculate and update the difference"""
        self.difference = self.statement_balance - self.book_balance
        return self.difference
    
    def mark_as_reconciled(self):
        """Mark reconciliation as completed"""
        self.status = 'Reconciled'
        self.completed_at = datetime.utcnow()
        
        # Update account current balance
        account = BankAccount.query.get(self.account_id)
        if account:
            account.current_balance = self.statement_balance
            account.updated_at = datetime.utcnow()
    
    def __repr__(self):
        return f'<BankReconciliation {self.id}: {self.status}>'

class Checkbook(db.Model):
    __tablename__ = 'checkbooks'
    id = db.Column(db.Integer, primary_key=True)
    account_name = db.Column(db.String(128), nullable=False)
    bank_name = db.Column(db.String(128), nullable=False)
    balance = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(32), default='Active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Add any additional fields as needed

    def __repr__(self):
        return f'<Checkbook {self.account_name}>'

class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    checkbook_id = db.Column(db.Integer, db.ForeignKey('checkbooks.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(32), nullable=False)  # e.g., 'credit', 'debit'
    description = db.Column(db.String(256), nullable=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(32), default='Pending')
    # Add any additional fields as needed

    checkbook = db.relationship('Checkbook', backref='transactions')

    def __repr__(self):
        return f'<Transaction {self.id}>'

class Incident(db.Model):
    __tablename__ = 'incidents'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(32), default='Open')
    reported_by = db.Column(db.String(128))
    date_reported = db.Column(db.DateTime, default=datetime.utcnow)
    severity = db.Column(db.String(32))
    # Add any additional fields as needed

    def __repr__(self):
        return f'<Incident {self.title}>'

class Alert(db.Model):
    __tablename__ = 'alerts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    type = db.Column(db.String(64), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(32), default='Active')
    severity = db.Column(db.String(32))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Add any additional fields as needed

    def __repr__(self):
        return f'<Alert {self.title}>'

class Schedule(db.Model):
    __tablename__ = 'schedules'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)  # Link to Project
    title = db.Column(db.String(128), nullable=False)
    type = db.Column(db.String(64), nullable=False)
    description = db.Column(db.Text)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(32), default='Scheduled')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Add any additional fields as needed

    def __repr__(self):
        return f'<Schedule {self.title}>'

class PayrollHistory(db.Model):
    __tablename__ = 'payroll_history'
    id = db.Column(db.Integer, primary_key=True)
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)
    total_payroll = db.Column(db.Float, nullable=False)
    total_deductions = db.Column(db.Float, default=0.0)
    generated_by = db.Column(db.String(128))  # User who generated payroll
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    employees = db.relationship('EmployeeSalaryHistory', backref='payroll_history', lazy='dynamic')

class EmployeeSalaryHistory(db.Model):
    __tablename__ = 'employee_salary_history'
    id = db.Column(db.Integer, primary_key=True)
    payroll_history_id = db.Column(db.Integer, db.ForeignKey('payroll_history.id'), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    salary = db.Column(db.Float, nullable=False)
    deduction = db.Column(db.Float, default=0.0)
    net_pay = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PayrollTransaction(db.Model):
    __tablename__ = 'payroll_transactions'
    id = db.Column(db.Integer, primary_key=True)
    payroll_history_id = db.Column(db.Integer, db.ForeignKey('payroll_history.id'), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    amount_paid = db.Column(db.Float, nullable=False)
    transaction_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(32), default='Completed')


class MonthlyPayrollSummary(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    total_salary = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# --- HR Leave Model Stub ---
class Leave(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer)
    type = db.Column(db.String(64))
    status = db.Column(db.String(32))
    start = db.Column(db.Date)
    end = db.Column(db.Date)
    created_at = db.Column(db.DateTime)

# --- Additional Project Management Models ---
class BOQItem(db.Model):
    """Bill of Quantities line items for construction projects"""
    __tablename__ = 'boq_items'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    
    # BOQ classification
    bill_no = db.Column(db.String(50))  # e.g., "BILL NO. 4", "SUBSTRUCTURE"
    item_no = db.Column(db.String(50))  # e.g., "4.01", "4.02", "A1"
    
    # Legacy fields (keeping for compatibility)
    item_description = db.Column(db.String(256), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(50), nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_cost = db.Column(db.Float, nullable=False)
    
    # Enhanced fields
    item_type = db.Column(db.String(50))  # Bridge, Building, Road, Culvert, etc.
    category = db.Column(db.String(100), nullable=True)  # Pavements, Substructure, Roof, etc.
    is_template = db.Column(db.Boolean, default=False)  # Template items vs project-specific
    status = db.Column(db.String(20), default='Pending')  # Pending, Ordered, Delivered, Used
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    material_schedules = db.relationship('MaterialSchedule', backref='boq_item', lazy=True)
    
    def calculate_total_cost(self):
        """Calculate total cost from quantity and unit price"""
        self.total_cost = self.quantity * self.unit_price
        return self.total_cost
    
    def __repr__(self):
        return f'<BOQItem {self.item_description}>'

class ProjectActivity(db.Model):
    """Activity log for project events and changes"""
    __tablename__ = 'project_activities'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    action_type = db.Column(db.String(100), nullable=False)  # milestone_added, staff_assigned, etc.
    description = db.Column(db.Text, nullable=False)
    user_name = db.Column(db.String(128), nullable=True)  # Cached user name
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ProjectActivity {self.action_type}>'

class ProjectDocument(db.Model):
    """Enhanced document model specifically for projects"""
    __tablename__ = 'project_documents'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    filename = db.Column(db.String(256), nullable=False)
    original_filename = db.Column(db.String(256), nullable=False)
    document_type = db.Column(db.String(64), nullable=False)  # Contract, Drawing, etc.
    description = db.Column(db.Text, nullable=True)
    file_size = db.Column(db.Integer, nullable=False)
    file_path = db.Column(db.String(512), nullable=False)
    uploader_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    uploader_name = db.Column(db.String(128), nullable=True)  # Cached uploader name
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    project = db.relationship('Project', backref='project_documents')
    uploader = db.relationship('User', backref='uploaded_project_documents')
    
    @property
    def file_type(self):
        """Extract file extension from filename"""
        if self.original_filename:
            return self.original_filename.split('.')[-1].lower()
        return 'unknown'
    
    @property
    def formatted_file_size(self):
        """Format file size in human readable format"""
        if not self.file_size:
            return 'Unknown size'
        
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def __repr__(self):
        return f'<ProjectDocument {self.original_filename}>'


# --- Daily Production Report (DPR) Models ---

class DailyProductionReport(db.Model):
    """Main DPR model for managing daily production reports"""
    __tablename__ = 'daily_production_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    report_date = db.Column(db.Date, nullable=False)
    
    # Workflow status
    status = db.Column(db.String(32), default='draft')  # draft, sent_to_staff, completed, reviewed
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Project Manager
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Project Staff
    completed_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Who filled it
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sent_at = db.Column(db.DateTime, nullable=True)  # When sent to staff
    completed_at = db.Column(db.DateTime, nullable=True)  # When staff completed it
    reviewed_at = db.Column(db.DateTime, nullable=True)  # When manager reviewed
    
    # Issues and signatures
    issues = db.Column(db.Text, nullable=True)
    prepared_by = db.Column(db.String(128), nullable=True)
    checked_by = db.Column(db.String(128), nullable=True)
    
    # Relationships
    project = db.relationship('Project', backref='daily_reports')
    created_by = db.relationship('User', foreign_keys=[created_by_id], backref='created_dprs')
    assigned_to = db.relationship('User', foreign_keys=[assigned_to_id], backref='assigned_dprs') 
    completed_by = db.relationship('User', foreign_keys=[completed_by_id], backref='completed_dprs')
    
    def __repr__(self):
        return f'<DPR {self.report_date} - Project {self.project_id}>'


class DPRProductionItem(db.Model):
    """Production items in the DPR (Earthworks, Concrete, etc.)"""
    __tablename__ = 'dpr_production_items'
    
    id = db.Column(db.Integer, primary_key=True)
    dpr_id = db.Column(db.Integer, db.ForeignKey('daily_production_reports.id'), nullable=False)
    
    # Item details
    item_code = db.Column(db.String(16), nullable=False)  # e.g., "1.01", "2.03"
    description = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(128), nullable=True)
    unit = db.Column(db.String(16), nullable=False)  # M3, M2, M, TONS, etc.
    
    # Quantities
    target_qty = db.Column(db.Float, default=0.0)
    previous_qty_done = db.Column(db.Float, default=0.0)
    day_production = db.Column(db.Float, default=0.0)
    total_qty_done = db.Column(db.Float, default=0.0)
    
    # Relationship
    dpr = db.relationship('DailyProductionReport', backref='production_items')
    
    def __repr__(self):
        return f'<DPRProductionItem {self.item_code}: {self.description}>'


class DPRMaterialUsage(db.Model):
    """Material usage items in the DPR"""
    __tablename__ = 'dpr_material_usage'
    
    id = db.Column(db.Integer, primary_key=True)
    dpr_id = db.Column(db.Integer, db.ForeignKey('daily_production_reports.id'), nullable=False)
    
    # Material details
    item_number = db.Column(db.Integer, nullable=False)  # 1, 2, 3, etc.
    description = db.Column(db.String(255), nullable=False)
    unit = db.Column(db.String(16), nullable=False)  # bag, trucks, ltr, m3, tons
    
    # Usage quantities
    previous_qty_used = db.Column(db.Float, default=0.0)
    day_usage = db.Column(db.Float, default=0.0)
    total_qty_used = db.Column(db.Float, default=0.0)
    
    # Relationship
    dpr = db.relationship('DailyProductionReport', backref='material_usage')
    
    def __repr__(self):
        return f'<DPRMaterialUsage {self.item_number}: {self.description}>'


# --- Material Schedule Model ---
class MaterialSchedule(db.Model):
    """Material schedule tracking for BOQ items"""
    __tablename__ = 'material_schedules'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True)  # Nullable for templates
    boq_item_id = db.Column(db.Integer, db.ForeignKey('boq_items.id'), nullable=True)
    
    # Material details
    material_name = db.Column(db.String(255), nullable=False)
    specification = db.Column(db.Text)  # Technical specifications
    
    # Quantity planning
    required_qty = db.Column(db.Float, default=0.0)
    ordered_qty = db.Column(db.Float, default=0.0)
    received_qty = db.Column(db.Float, default=0.0)
    used_qty = db.Column(db.Float, default=0.0)
    
    unit = db.Column(db.String(50))  # m², m³, kg, nos, etc.
    
    # Cost tracking
    unit_cost = db.Column(db.Float, default=0.0)
    total_cost = db.Column(db.Float, default=0.0)
    
    # Schedule
    required_date = db.Column(db.Date)
    delivery_date = db.Column(db.Date)
    
    # Status
    status = db.Column(db.String(50), default='Planned')  # Planned, Ordered, Delivered, In Use, Depleted
    
    # Supplier information
    supplier_name = db.Column(db.String(255))
    supplier_contact = db.Column(db.String(100))
    
    # Tracking
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = db.relationship('Project', backref='material_schedules')
    
    def calculate_total_cost(self):
        """Calculate total cost from quantity and unit cost"""
        self.total_cost = self.required_qty * self.unit_cost
        return self.total_cost
    
    def remaining_qty(self):
        """Calculate remaining quantity to be received"""
        return self.ordered_qty - self.received_qty
    
    def __repr__(self):
        return f'<MaterialSchedule {self.material_name}: {self.required_qty} {self.unit}>'


# --- Approval Workflow Models ---
class ApprovalWorkflow(db.Model):
    """Master model for tracking multi-stage approval workflows"""
    __tablename__ = 'approval_workflows'
    
    id = db.Column(db.Integer, primary_key=True)
    workflow_type = db.Column(db.String(64), nullable=False)  # purchase_order, payroll, budget_adjustment, expense, etc.
    reference_id = db.Column(db.Integer, nullable=False)  # ID of the item being approved
    reference_number = db.Column(db.String(128))  # Human-readable reference (PO-001, PAY-2024-01)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))
    
    # Workflow status
    current_stage = db.Column(db.String(64), nullable=False)  # procurement, cost_control, finance, admin, hr
    overall_status = db.Column(db.String(32), default='pending')  # pending, in_progress, approved, rejected, cancelled
    
    # Tracking
    initiated_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    initiated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = db.Column(db.DateTime)
    
    # Metadata
    total_amount = db.Column(db.Float)
    description = db.Column(db.Text)
    priority = db.Column(db.String(32), default='normal')  # low, normal, high, urgent
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    initiator = db.relationship('User', foreign_keys=[initiated_by], backref='initiated_workflows')
    project = db.relationship('Project', backref='approval_workflows')
    steps = db.relationship('WorkflowStep', backref='workflow', cascade='all, delete-orphan', order_by='WorkflowStep.step_order')
    
    def __repr__(self):
        return f'<ApprovalWorkflow {self.workflow_type} - {self.reference_number}: {self.overall_status}>'


class WorkflowStep(db.Model):
    """Individual approval steps within a workflow"""
    __tablename__ = 'workflow_steps'
    
    id = db.Column(db.Integer, primary_key=True)
    workflow_id = db.Column(db.Integer, db.ForeignKey('approval_workflows.id'), nullable=False)
    
    # Step details
    step_order = db.Column(db.Integer, nullable=False)  # 1, 2, 3 for sequential steps
    step_name = db.Column(db.String(64), nullable=False)  # cost_control_approval, finance_approval, etc.
    required_role = db.Column(db.String(64), nullable=False)  # hq_cost_control, hq_finance, admin, etc.
    
    # Status
    status = db.Column(db.String(32), default='pending')  # pending, approved, rejected, skipped
    
    # Approval details
    approver_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    action_taken_at = db.Column(db.DateTime)
    comments = db.Column(db.Text)
    
    # Notifications
    notification_sent = db.Column(db.Boolean, default=False)
    notification_sent_at = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    approver = db.relationship('User', foreign_keys=[approver_id], backref='workflow_steps')
    
    def __repr__(self):
        return f'<WorkflowStep {self.step_name}: {self.status}>'


# --- Notification System ---
class Notification(db.Model):
    """In-app notifications for users"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Notification content
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(64))  # approval_request, approval_granted, approval_rejected, info, warning, success
    
    # Reference to source
    reference_type = db.Column(db.String(64))  # purchase_order, payroll, budget_adjustment, etc.
    reference_id = db.Column(db.Integer)
    action_url = db.Column(db.String(255))  # Link to take action
    
    # Status
    is_read = db.Column(db.Boolean, default=False)
    read_at = db.Column(db.DateTime)
    
    # Email notification tracking
    email_sent = db.Column(db.Boolean, default=False)
    email_sent_at = db.Column(db.DateTime)
    
    # Priority
    priority = db.Column(db.String(32), default='normal')  # low, normal, high, urgent
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = db.Column(db.DateTime)  # Optional expiration
    
    # Relationships
    user = db.relationship('User', backref='notifications')
    
    def __repr__(self):
        return f'<Notification {self.title} for User {self.user_id}>'


# --- Audit Log System ---
class AuditLog(db.Model):
    """Comprehensive audit log for all system activities"""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Who performed the action
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user_name = db.Column(db.String(128))  # Cached for deleted users
    user_role = db.Column(db.String(64))
    
    # What action was performed
    action = db.Column(db.String(128), nullable=False)  # created, updated, deleted, approved, rejected, submitted
    module = db.Column(db.String(64), nullable=False)  # procurement, hr, finance, cost_control, admin
    
    # What was affected
    reference_type = db.Column(db.String(64), nullable=False)  # purchase_order, payroll, user, project, etc.
    reference_id = db.Column(db.Integer)
    reference_number = db.Column(db.String(128))  # Human-readable reference
    
    # Details
    description = db.Column(db.Text)  # Human-readable description
    old_values = db.Column(db.Text)  # JSON string of old values
    new_values = db.Column(db.Text)  # JSON string of new values
    
    # Context
    ip_address = db.Column(db.String(45))  # IPv4 or IPv6
    user_agent = db.Column(db.String(255))
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))
    
    # Metadata
    severity = db.Column(db.String(32), default='info')  # info, warning, critical
    success = db.Column(db.Boolean, default=True)
    error_message = db.Column(db.Text)
    
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    
    # Relationships
    user = db.relationship('User', backref='audit_logs')
    project = db.relationship('Project', backref='audit_logs')
    
    def __repr__(self):
        return f'<AuditLog {self.action} on {self.reference_type} by {self.user_name}>'
