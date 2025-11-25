class Roles:
    # Super Admin
    SUPER_HQ = 'super_hq'
    
    # HQ Management Roles
    HQ_FINANCE = 'hq_finance'
    HQ_HR = 'hq_hr'
    HQ_PROCUREMENT = 'hq_procurement'
    QUARRY_MANAGER = 'hq_quarry'
    PROJECT_MANAGER = 'hq_project'
    HQ_COST_CONTROL = 'hq_cost_control'
    OFFICE_PM = 'office_pm'
    QS_MANAGER = 'qs_manager'
    
    # Staff Roles
    FINANCE_STAFF = 'finance_staff'
    HR_STAFF = 'hr_staff'
    PROCUREMENT_STAFF = 'procurement_staff'
    PROCUREMENT_OFFICER = 'procurement_officer'
    QUARRY_STAFF = 'quarry_staff'
    PROJECT_STAFF = 'project_staff'

    # Role Hierarchies
    ROLE_HIERARCHY = {
        SUPER_HQ: ['*'],  # Super HQ has access to everything
        HQ_FINANCE: [FINANCE_STAFF],
        HQ_HR: [HR_STAFF],
        HQ_PROCUREMENT: [PROCUREMENT_STAFF, PROCUREMENT_OFFICER],
        QUARRY_MANAGER: [QUARRY_STAFF],
        PROJECT_MANAGER: [PROJECT_STAFF],
        HQ_COST_CONTROL: [],
        OFFICE_PM: [],
        QS_MANAGER: []
    }
    
    # Role Display Names
    ROLE_NAMES = {
        SUPER_HQ: 'Super HQ Admin',
        HQ_FINANCE: 'HQ Finance Manager',
        HQ_HR: 'HQ HR Manager',
        HQ_PROCUREMENT: 'HQ Procurement Manager',
        QUARRY_MANAGER: 'Quarry Manager',
        PROJECT_MANAGER: 'Project Manager',
        HQ_COST_CONTROL: 'HQ Cost Control Manager',
        OFFICE_PM: 'Office Project Manager',
        QS_MANAGER: 'QS Manager',
        FINANCE_STAFF: 'Finance Staff',
        HR_STAFF: 'HR Staff',
        PROCUREMENT_STAFF: 'Procurement Staff',
        PROCUREMENT_OFFICER: 'Procurement Officer',
        QUARRY_STAFF: 'Quarry Staff',
        PROJECT_STAFF: 'Project Staff'
    }
    
    # Role Descriptions
    ROLE_DESCRIPTIONS = {
        SUPER_HQ: 'Full system access and user management',
        HQ_FINANCE: 'Manage finance, budgets, and payroll',
        HQ_HR: 'Manage employees, attendance, and performance',
        HQ_PROCUREMENT: 'Manage procurement and suppliers',
        QUARRY_MANAGER: 'Manage quarry operations',
        PROJECT_MANAGER: 'Manage site projects and progress',
        HQ_COST_CONTROL: 'Monitor and control project costs',
        OFFICE_PM: 'Manage office-level project coordination and reporting',
        QS_MANAGER: 'Manage quantity surveying and cost estimation',
        FINANCE_STAFF: 'Handle daily finance operations',
        HR_STAFF: 'Handle HR administrative tasks',
        PROCUREMENT_STAFF: 'Process procurement requests',
        PROCUREMENT_OFFICER: 'Approve procurement activities',
        QUARRY_STAFF: 'Handle quarry daily operations',
        PROJECT_STAFF: 'Assist with site project tasks'
    }
    
    @classmethod
    def get_management_roles(cls):
        """Get all management/HQ roles"""
        return [
            cls.SUPER_HQ,
            cls.HQ_FINANCE,
            cls.HQ_HR,
            cls.HQ_PROCUREMENT,
            cls.QUARRY_MANAGER,
            cls.PROJECT_MANAGER,
            cls.HQ_COST_CONTROL
        ]
    
    @classmethod
    def get_staff_roles(cls):
        """Get all staff roles"""
        return [
            cls.FINANCE_STAFF,
            cls.HR_STAFF,
            cls.PROCUREMENT_STAFF,
            cls.PROCUREMENT_OFFICER,
            cls.QUARRY_STAFF,
            cls.PROJECT_STAFF
        ]
    
    @classmethod
    def get_all_roles(cls):
        """Get all roles"""
        return cls.get_management_roles() + cls.get_staff_roles()