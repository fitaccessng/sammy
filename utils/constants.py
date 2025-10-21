class Roles:
    # Super Admin
    SUPER_HQ = 'super_hq'
    
    # HQ Management Roles
    HQ_FINANCE = 'hq_finance'
    HQ = 'hr'
    HQ_HR = 'hq_hr'
    HQ_PROCUREMENT = 'hq_procurement'
    QUARRY_MANAGER = 'hq_quarry'
    PROJECT_MANAGER = 'hq_project'
    HQ_COST_CONTROL = 'hq_cost_control'
    
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
        HQ_PROCUREMENT: [PROCUREMENT_STAFF],
        QUARRY_MANAGER: [QUARRY_STAFF],
        PROJECT_MANAGER: [PROJECT_STAFF]
    }