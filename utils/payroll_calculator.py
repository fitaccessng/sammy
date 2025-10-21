"""
Comprehensive Payroll Calculation Engine
Business Logic for Salary, Allowances, and Deductions
"""
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP


class PayrollCalculator:
    """
    Professional payroll calculation engine following Nigerian employment standards
    """
    
    # Standard deduction rates
    PENSION_RATE = 0.08  # 8% employee contribution
    PENSION_EMPLOYER_RATE = 0.10  # 10% employer contribution
    NHF_RATE = 0.025  # 2.5% National Housing Fund
    NHF_MAX_MONTHLY = 5000  # Maximum ₦5,000 monthly
    LIFE_INSURANCE_RATE = 0.005  # 0.5% life insurance
    
    def __init__(self, employee):
        self.employee = employee
        self.gross_salary = 0
        self.total_allowances = 0
        self.total_deductions = 0
        self.net_salary = 0
        self.calculation_breakdown = {}
    
    def calculate_gross_salary(self, overtime_hours=0, bonus=0):
        """Calculate total gross salary including all components"""
        
        # Basic components
        basic = self.employee.basic_salary or 0
        housing = self.employee.housing_allowance or 0
        transport = self.employee.transport_allowance or 0
        medical = self.employee.medical_allowance or 0
        special = self.employee.special_allowance or 0
        
        # Overtime calculation
        overtime_amount = (self.employee.overtime_rate or 0) * overtime_hours
        
        # Total allowances
        self.total_allowances = housing + transport + medical + special
        
        # Gross salary
        self.gross_salary = basic + self.total_allowances + overtime_amount + bonus
        
        self.calculation_breakdown['basic_salary'] = self._round_currency(basic)
        self.calculation_breakdown['housing_allowance'] = self._round_currency(housing)
        self.calculation_breakdown['transport_allowance'] = self._round_currency(transport)
        self.calculation_breakdown['medical_allowance'] = self._round_currency(medical)
        self.calculation_breakdown['special_allowance'] = self._round_currency(special)
        self.calculation_breakdown['overtime_hours'] = overtime_hours
        self.calculation_breakdown['overtime_amount'] = self._round_currency(overtime_amount)
        self.calculation_breakdown['bonus'] = self._round_currency(bonus)
        self.calculation_breakdown['total_allowances'] = self._round_currency(self.total_allowances)
        self.calculation_breakdown['gross_salary'] = self._round_currency(self.gross_salary)
        
        return self.gross_salary
    
    def calculate_statutory_deductions(self):
        """Calculate all statutory deductions"""
        deductions = {}
        
        # PAYE Tax calculation
        annual_gross = self.gross_salary * 12
        annual_tax = self._calculate_paye_tax(annual_gross)
        monthly_tax = annual_tax / 12
        deductions['paye_tax'] = self._round_currency(monthly_tax)
        
        # Pension contribution (8% employee)
        pension = self.gross_salary * self.PENSION_RATE
        deductions['pension'] = self._round_currency(pension)
        
        # National Housing Fund (2.5%, max ₦5,000)
        nhf = min(self.gross_salary * self.NHF_RATE, self.NHF_MAX_MONTHLY)
        deductions['nhf'] = self._round_currency(nhf)
        
        # Life Insurance (0.5% of gross, optional but common)
        life_insurance = self.gross_salary * self.LIFE_INSURANCE_RATE
        deductions['life_insurance'] = self._round_currency(life_insurance)
        
        return deductions
    
    def calculate_custom_deductions(self, staff_deductions):
        """Calculate custom deductions for this employee"""
        custom_deductions = {}
        total_custom = 0
        
        for deduction in staff_deductions:
            if deduction.status == 'active':
                custom_deductions[deduction.deduction_type] = {
                    'amount': self._round_currency(deduction.amount),
                    'reason': deduction.reason,
                    'id': deduction.id
                }
                total_custom += deduction.amount
        
        custom_deductions['total_custom'] = self._round_currency(total_custom)
        return custom_deductions
    
    def calculate_complete_payroll(self, overtime_hours=0, bonus=0, staff_deductions=None):
        """Complete payroll calculation for employee"""
        
        # Calculate gross salary
        self.calculate_gross_salary(overtime_hours, bonus)
        
        # Calculate statutory deductions
        statutory = self.calculate_statutory_deductions()
        
        # Calculate custom deductions
        custom = self.calculate_custom_deductions(staff_deductions or [])
        
        # Total deductions
        total_statutory = sum(statutory.values())
        total_custom = custom.get('total_custom', 0)
        self.total_deductions = total_statutory + total_custom
        
        # Net salary
        self.net_salary = self.gross_salary - self.total_deductions
        
        # Complete breakdown
        self.calculation_breakdown.update({
            'statutory_deductions': statutory,
            'custom_deductions': custom,
            'total_statutory_deductions': self._round_currency(total_statutory),
            'total_custom_deductions': self._round_currency(total_custom),
            'total_deductions': self._round_currency(self.total_deductions),
            'net_salary': self._round_currency(self.net_salary)
        })
        
        return {
            'employee_id': self.employee.id,
            'employee_name': self.employee.name,
            'gross_salary': self._round_currency(self.gross_salary),
            'total_deductions': self._round_currency(self.total_deductions),
            'net_salary': self._round_currency(self.net_salary),
            'breakdown': self.calculation_breakdown
        }
    
    def _calculate_paye_tax(self, annual_gross):
        """Calculate Nigerian PAYE tax based on current rates"""
        # 2024 Nigerian tax brackets
        tax = 0
        
        if annual_gross <= 300000:
            tax = 0
        elif annual_gross <= 600000:
            tax = (annual_gross - 300000) * 0.07
        elif annual_gross <= 1100000:
            tax = 21000 + (annual_gross - 600000) * 0.11
        elif annual_gross <= 1600000:
            tax = 21000 + 55000 + (annual_gross - 1100000) * 0.15
        elif annual_gross <= 3200000:
            tax = 21000 + 55000 + 75000 + (annual_gross - 1600000) * 0.19
        else:
            tax = 21000 + 55000 + 75000 + 304000 + (annual_gross - 3200000) * 0.24
        
        return tax
    
    def _round_currency(self, amount):
        """Round currency to 2 decimal places"""
        if amount is None:
            return 0.00
        return float(Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
    
    def generate_payslip_data(self):
        """Generate formatted data for payslip"""
        return {
            'employee': {
                'name': self.employee.name,
                'staff_code': self.employee.staff_code,
                'department': self.employee.department,
                'position': self.employee.position,
                'bank_name': self.employee.bank_name,
                'account_number': self.employee.bank_account_number
            },
            'period': {
                'month': datetime.now().strftime('%B'),
                'year': datetime.now().year
            },
            'earnings': {
                'basic_salary': self.calculation_breakdown.get('basic_salary', 0),
                'housing_allowance': self.calculation_breakdown.get('housing_allowance', 0),
                'transport_allowance': self.calculation_breakdown.get('transport_allowance', 0),
                'medical_allowance': self.calculation_breakdown.get('medical_allowance', 0),
                'special_allowance': self.calculation_breakdown.get('special_allowance', 0),
                'overtime': self.calculation_breakdown.get('overtime_amount', 0),
                'bonus': self.calculation_breakdown.get('bonus', 0),
                'gross_total': self.calculation_breakdown.get('gross_salary', 0)
            },
            'deductions': {
                'paye_tax': self.calculation_breakdown.get('statutory_deductions', {}).get('paye_tax', 0),
                'pension': self.calculation_breakdown.get('statutory_deductions', {}).get('pension', 0),
                'nhf': self.calculation_breakdown.get('statutory_deductions', {}).get('nhf', 0),
                'life_insurance': self.calculation_breakdown.get('statutory_deductions', {}).get('life_insurance', 0),
                'custom_deductions': self.calculation_breakdown.get('custom_deductions', {}),
                'total_deductions': self.calculation_breakdown.get('total_deductions', 0)
            },
            'summary': {
                'gross_salary': self.calculation_breakdown.get('gross_salary', 0),
                'total_deductions': self.calculation_breakdown.get('total_deductions', 0),
                'net_salary': self.calculation_breakdown.get('net_salary', 0)
            }
        }


class PayrollBatch:
    """
    Handle batch payroll processing for multiple employees
    """
    
    def __init__(self):
        self.employees_payroll = []
        self.batch_summary = {}
    
    def process_employees(self, employees, staff_deductions_dict=None, overtime_dict=None, bonus_dict=None):
        """Process payroll for multiple employees"""
        
        total_gross = 0
        total_deductions = 0
        total_net = 0
        employee_count = 0
        
        for employee in employees:
            if employee.status != 'Active':
                continue
                
            # Get employee-specific data
            overtime_hours = overtime_dict.get(employee.id, 0) if overtime_dict else 0
            bonus = bonus_dict.get(employee.id, 0) if bonus_dict else 0
            deductions = staff_deductions_dict.get(employee.id, []) if staff_deductions_dict else []
            
            # Calculate payroll
            calculator = PayrollCalculator(employee)
            payroll_result = calculator.calculate_complete_payroll(
                overtime_hours=overtime_hours,
                bonus=bonus,
                staff_deductions=deductions
            )
            
            self.employees_payroll.append(payroll_result)
            
            # Update totals
            total_gross += payroll_result['gross_salary']
            total_deductions += payroll_result['total_deductions']
            total_net += payroll_result['net_salary']
            employee_count += 1
        
        # Batch summary
        self.batch_summary = {
            'period': datetime.now().strftime('%B %Y'),
            'employee_count': employee_count,
            'total_gross_salary': PayrollCalculator(None)._round_currency(total_gross),
            'total_deductions': PayrollCalculator(None)._round_currency(total_deductions),
            'total_net_salary': PayrollCalculator(None)._round_currency(total_net),
            'average_gross': PayrollCalculator(None)._round_currency(total_gross / employee_count) if employee_count > 0 else 0,
            'average_net': PayrollCalculator(None)._round_currency(total_net / employee_count) if employee_count > 0 else 0,
            'generated_at': datetime.now(),
            'status': 'draft'
        }
        
        return {
            'employees': self.employees_payroll,
            'summary': self.batch_summary
        }
    
    def get_payroll_summary(self):
        """Get summary for approval submission"""
        return self.batch_summary