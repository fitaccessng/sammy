
# --- Admin/Manager Models ---
from datetime import datetime
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<InventoryItem {self.code}>'
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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
    status = db.Column(db.String(32), default='Draft')  # Draft, Pending, Approved, Rejected, Ordered, Delivered, Cancelled
    priority = db.Column(db.String(32), default='Normal')  # Low, Normal, High, Urgent
    description = db.Column(db.Text)
    subtotal = db.Column(db.Float, default=0.0)
    tax_rate = db.Column(db.Float, default=0.0)
    tax_amount = db.Column(db.Float, default=0.0)
    total_amount = db.Column(db.Float, default=0.0)
    expected_delivery = db.Column(db.Date)
    requested_by = db.Column(db.Integer, db.ForeignKey('employee.id'))
    approved_by = db.Column(db.Integer, db.ForeignKey('employee.id'))
    approval_date = db.Column(db.DateTime)
    delivery_address = db.Column(db.Text)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    requested_by_employee = db.relationship('Employee', foreign_keys=[requested_by], backref='requested_orders')
    approved_by_employee = db.relationship('Employee', foreign_keys=[approved_by], backref='approved_orders')
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
    status = db.Column(db.String(32), default='pending_admin')  # pending_admin, approved_by_admin, processed_by_finance, rejected
    submitted_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    admin_approved_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    finance_processed_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    rejected_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    admin_approved_at = db.Column(db.DateTime)
    finance_processed_at = db.Column(db.DateTime)
    rejected_at = db.Column(db.DateTime)
    rejection_reason = db.Column(db.Text)
    
    # Relationships
    submitter = db.relationship('User', foreign_keys=[submitted_by], backref='submitted_payroll_approvals')
    admin_approver = db.relationship('User', foreign_keys=[admin_approved_by], backref='admin_approved_payrolls')
    finance_processor = db.relationship('User', foreign_keys=[finance_processed_by], backref='finance_processed_payrolls')
    rejector = db.relationship('User', foreign_keys=[rejected_by], backref='rejected_payroll_approvals')

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
    category = db.Column(db.String(64), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True)  # Project association
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    uploader_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(32), default='pending')
    size = db.Column(db.Integer, default=0)
    
    # Relationships
    project = db.relationship('Project', backref='documents')
    uploader = db.relationship('User', backref='uploaded_documents')
    
    # Add any additional fields as needed

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
    """Bill of Quantities Item for project cost tracking"""
    __tablename__ = 'boq_items'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    item_description = db.Column(db.String(256), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(50), nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_cost = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
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
