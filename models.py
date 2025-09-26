from extensions import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

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
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    status = db.Column(db.String(32))
    progress = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    project_manager = db.Column(db.String(128))
    budget = db.Column(db.Float, default=0.0)
    schedules = db.relationship('Schedule', backref='project', lazy='dynamic')

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(128), unique=True)
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    payrolls = db.relationship('Payroll', backref='employee', lazy='dynamic')
    attendances = db.relationship('Attendance', backref='employee', lazy='dynamic')

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
    supplier = db.Column(db.String(128))
    status = db.Column(db.String(32), default='Pending')
    total_amount = db.Column(db.Float)
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

class Inspection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    site = db.Column(db.String(128), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(32), default='Scheduled')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
class UploadedFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    path = db.Column(db.String(255), nullable=False)
    tags = db.Column(db.String(255), nullable=True)
    uploaded_at = db.Column(db.DateTime, default=db.func.now())

class StaffAssignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    role = db.Column(db.String(64), nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)

    project = db.relationship('Project', backref='staff_assignments')
    staff = db.relationship('User', backref='project_assignments')

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    status = db.Column(db.String(32), default='pending')
    due_date = db.Column(db.Date)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    from_item = db.Column(db.String(128))
    to_item = db.Column(db.String(128))
    quantity = db.Column(db.Float, default=0.0)
    percent_complete = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = db.relationship('Project', backref='tasks')

class Equipment(db.Model):
    __tablename__ = 'equipment'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    maintenance_due = db.Column(db.Date, nullable=True)
    machine_hours = db.Column(db.Float, default=0)
    diesel_consumption = db.Column(db.Float, default=0)
    remarks = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(32), default='Active')  # Added status column
    # Add any additional fields as needed

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
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    uploader_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(32), default='pending')
    size = db.Column(db.Integer, default=0)
    # Add any additional fields as needed

    def __repr__(self):
        return f'<Document {self.filename}>'

class Milestone(db.Model):
    __tablename__ = 'milestones'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
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

class BankReconciliation(db.Model):
    __tablename__ = 'bank_reconciliations'
    id = db.Column(db.Integer, primary_key=True)
    account_name = db.Column(db.String(128), nullable=False)
    statement_date = db.Column(db.Date, nullable=False)
    balance = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(32), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Add any additional fields as needed

    def __repr__(self):
        return f'<BankReconciliation {self.account_name}>'

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
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)  # Link to Project
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
