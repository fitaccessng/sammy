from flask import Blueprint, request, jsonify
from extensions import db
from models import CostCategory, Machinery, FuelLog, CostVarianceReport

cost_control_bp = Blueprint('cost_control', __name__, url_prefix='/cost-control')

# POST /cost-control/categories
@cost_control_bp.route('/categories', methods=['POST'])
def add_category():
    data = request.get_json()
    category = CostCategory(
        project_id=data.get('project_id'),
        name=data.get('name'),
        type=data.get('type')
    )
    db.session.add(category)
    db.session.commit()
    return jsonify({'status': 'success', 'id': category.id})

# POST /cost-control/machinery
@cost_control_bp.route('/machinery', methods=['POST'])
def add_machinery():
    data = request.get_json()
    machinery = Machinery(
        serial_no=data.get('serial_no'),
        description=data.get('description'),
        model=data.get('model'),
        status=data.get('status'),
        rate=data.get('rate'),
        days_active=data.get('days_active'),
        monthly_cost=data.get('monthly_cost'),
        warning_flag=data.get('warning_flag', False)
    )
    db.session.add(machinery)
    db.session.commit()
    return jsonify({'status': 'success', 'id': machinery.id})

# POST /cost-control/fuel-log
@cost_control_bp.route('/fuel-log', methods=['POST'])
def add_fuel_log():
    data = request.get_json()
    fuel_log = FuelLog(
        serial_no=data.get('serial_no'),
        description=data.get('description'),
        equipment_code=data.get('equipment_code'),
        reg_no=data.get('reg_no'),
        operator=data.get('operator'),
        start_meter=data.get('start_meter'),
        end_meter=data.get('end_meter'),
        total_hours=data.get('total_hours'),
        fuel_consumed=data.get('fuel_consumed')
    )
    db.session.add(fuel_log)
    db.session.commit()
    return jsonify({'status': 'success', 'id': fuel_log.id})

# GET /cost-control/reports?project_id=123&type=variance
@cost_control_bp.route('/reports', methods=['GET'])
def get_reports():
    project_id = request.args.get('project_id')
    report_type = request.args.get('type')
    if report_type == 'variance':
        reports = CostVarianceReport.query.filter_by(project_id=project_id).all()
        result = []
        for r in reports:
            result.append({
                'id': r.id,
                'category': r.category,
                'planned_amount': r.planned_amount,
                'actual_amount': r.actual_amount,
                'variance': r.variance
            })
        return jsonify({'status': 'success', 'reports': result})
    return jsonify({'status': 'error', 'message': 'Invalid report type'}), 400
from flask import Blueprint

cost_control_bp = Blueprint("cost_control", __name__)

@cost_control_bp.route("/")
def cost_control_home():
    # Actual dashboard logic: show summary stats
    from models import CostCategory, Machinery, FuelLog, CostVarianceReport
    from flask import render_template
    project_count = len(set([c.project_id for c in CostCategory.query.all()]))
    total_categories = CostCategory.query.count()
    total_machinery = Machinery.query.count()
    total_fuel_logs = FuelLog.query.count()
    total_variance_reports = CostVarianceReport.query.count()
    summary = {
        'project_count': project_count,
        'total_categories': total_categories,
        'total_machinery': total_machinery,
        'total_fuel_logs': total_fuel_logs,
        'total_variance_reports': total_variance_reports
    }
    return render_template('cost_control/dashboard.html', summary=summary)