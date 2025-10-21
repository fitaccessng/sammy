
# --- Multi-level Approval Endpoint ---

from flask import Blueprint, render_template, request, jsonify, current_app, flash, send_file, session,redirect, url_for
from datetime import datetime, timedelta
from utils.decorators import role_required
from utils.constants import Roles
import pandas as pd
from io import BytesIO
import os
from sqlalchemy.exc import SQLAlchemyError
from flask import session
from extensions import db
from models import Settings

procurement_bp = Blueprint("procurement", __name__, url_prefix='/procurement')

# Dashboard Route
# Search Endpoint
@procurement_bp.route("/search", methods=["GET", "POST"])
@role_required([Roles.HQ_PROCUREMENT])
def search():
    try:
        query = request.args.get('q', '').strip() if request.method == 'GET' else request.form.get('q', '').strip()
        results = {'assets': [], 'purchases': [], 'suppliers': []}
        if query:
            # Search assets
            results['assets'] = InventoryItem.query.filter(
                (InventoryItem.code.ilike(f"%{query}%")) |
                (InventoryItem.description.ilike(f"%{query}%")) |
                (InventoryItem.category.ilike(f"%{query}%"))
            ).all()
            # Search purchases
            results['purchases'] = ProcurementRequest.query.filter(
                (ProcurementRequest.item_name.ilike(f"%{query}%")) |
                (ProcurementRequest.status.ilike(f"%{query}%"))
            ).all()
            # Search suppliers
            results['suppliers'] = Vendor.query.filter(
                (Vendor.name.ilike(f"%{query}%")) |
                (Vendor.category.ilike(f"%{query}%"))
            ).all()
        return render_template('procurement/search/index.html', query=query, results=results)
    except Exception as e:
        current_app.logger.error(f"Search error: {str(e)}")
        flash("Error performing search", "error")
        return render_template('error.html'), 500
# Notifications Endpoint
@procurement_bp.route("/notifications")
@role_required([Roles.HQ_PROCUREMENT])
def notifications():
    try:
        alerts = Alert.query.order_by(Alert.created_at.desc()).limit(50).all()
        alert_data = [
            {
                'id': a.id,
                'title': a.title,
                'type': a.type,
                'description': a.description,
                'status': a.status,
                'severity': a.severity,
                'created_at': a.created_at.strftime('%Y-%m-%d %H:%M:%S') if a.created_at else ''
            }
            for a in alerts
        ]
        return render_template('procurement/notifications/index.html', alerts=alert_data)
    except Exception as e:
        current_app.logger.error(f"Notifications error: {str(e)}")
        flash("Error loading notifications", "error")
        return render_template('error.html'), 500
# Budget Endpoint
@procurement_bp.route("/budget")
@role_required([Roles.HQ_PROCUREMENT])
def budget():
    try:
        # Summarize by project and category
        budgets = Budget.query.all()
        budget_summary = {}
        for b in budgets:
            key = f"{b.project_id}:{b.category}"
            if key not in budget_summary:
                budget_summary[key] = {
                    'project_id': b.project_id,
                    'category': b.category,
                    'allocated': 0.0,
                    'spent': 0.0,
                    'remaining': 0.0
                }
            budget_summary[key]['allocated'] += b.allocated_amount
            budget_summary[key]['spent'] += b.spent_amount
            budget_summary[key]['remaining'] = budget_summary[key]['allocated'] - budget_summary[key]['spent']
        summary_list = list(budget_summary.values())
        return render_template('procurement/budget/index.html', summary=summary_list)
    except Exception as e:
        current_app.logger.error(f"Budget error: {str(e)}")
        flash("Error loading budget data", "error")
        return render_template('error.html'), 500
# Maintenance Endpoint
@procurement_bp.route("/maintenance")
@role_required([Roles.HQ_PROCUREMENT])
def maintenance():
    try:
        # Assets due for maintenance (maintenance_due in next 30 days)
        from datetime import datetime, timedelta
        today = datetime.utcnow().date()
        soon = today + timedelta(days=30)
        due_soon = InventoryItem.query.filter(
            InventoryItem.maintenance_due != None,
            InventoryItem.maintenance_due >= today,
            InventoryItem.maintenance_due <= soon
        ).all()

        # Overdue maintenance
        overdue = InventoryItem.query.filter(
            InventoryItem.maintenance_due != None,
            InventoryItem.maintenance_due < today
        ).all()

        # Maintenance history (assets with past due dates)
        history = InventoryItem.query.filter(
            InventoryItem.maintenance_due != None,
            InventoryItem.maintenance_due < today
        ).order_by(InventoryItem.maintenance_due.desc()).limit(20).all()

        maintenance_data = {
            'due_soon': due_soon,
            'overdue': overdue,
            'history': history
        }
        return render_template('procurement/maintenance/index.html', data=maintenance_data)
    except Exception as e:
        current_app.logger.error(f"Maintenance error: {str(e)}")
        flash("Error loading maintenance data", "error")
        return render_template('error.html'), 500
# Analytics Endpoint
@procurement_bp.route("/analytics")
@role_required([Roles.HQ_PROCUREMENT])
def analytics():
    try:
        # Top categories by spend
        category_spend = db.session.query(
            ProcurementRequest.item_name,
            db.func.sum(ProcurementRequest.price * ProcurementRequest.qty).label('total_spend')
        ).group_by(ProcurementRequest.item_name).order_by(db.desc('total_spend')).limit(5).all()

        # Spend by month (last 6 months)
        spend_by_month = db.session.query(
            db.func.strftime('%Y-%m', ProcurementRequest.created_at),
            db.func.sum(ProcurementRequest.price * ProcurementRequest.qty)
        ).group_by(db.func.strftime('%Y-%m', ProcurementRequest.created_at)).order_by(db.desc(db.func.strftime('%Y-%m', ProcurementRequest.created_at))).limit(6).all()

        # Supplier performance (number of completed requests per supplier)
        supplier_performance = db.session.query(
            Vendor.name,
            db.func.count(ProcurementRequest.id)
        ).join(ProcurementRequest, ProcurementRequest.vendor_id == Vendor.id).filter(ProcurementRequest.status == 'completed').group_by(Vendor.name).order_by(db.desc(db.func.count(ProcurementRequest.id))).limit(5).all()

        analytics_data = {
            'category_spend': [{'item_name': c[0], 'total_spend': c[1]} for c in category_spend],
            'spend_by_month': [{'month': m[0], 'total_spend': m[1]} for m in spend_by_month],
            'supplier_performance': [{'supplier': s[0], 'completed_orders': s[1]} for s in supplier_performance]
        }
        return render_template('procurement/analytics/index.html', data=analytics_data)
    except Exception as e:
        current_app.logger.error(f"Analytics error: {str(e)}")
        flash("Error loading analytics", "error")
        return render_template('error.html'), 500
@procurement_bp.route("/purchases")
@role_required([Roles.HQ_PROCUREMENT])
def purchases():
    try:
        total_orders = ProcurementRequest.query.count()
        pending = ProcurementRequest.query.filter(ProcurementRequest.status == 'pending').count()
        in_transit = ProcurementRequest.query.filter(ProcurementRequest.status.ilike('%transit%')).count() if hasattr(ProcurementRequest, 'status') else 0
        completed = ProcurementRequest.query.filter(ProcurementRequest.status == 'completed').count() if hasattr(ProcurementRequest, 'status') else 0
        # Budget info
        total_budget = db.session.query(db.func.sum(Budget.allocated_amount)).scalar() or 0
        utilized = db.session.query(db.func.sum(ProcurementRequest.price * ProcurementRequest.qty)).filter(ProcurementRequest.status == 'disbursed').scalar() or 0
        remaining = total_budget - utilized
        purchase_data = {
            'stats': {
                'total_orders': total_orders,
                'pending': pending,
                'in_transit': in_transit,
                'completed': completed
            },
            'budget': {
                'total': total_budget,
                'utilized': utilized,
                'remaining': remaining
            }
        }
        return render_template('procurement/purchases/index.html', data=purchase_data)
    except Exception as e:
        current_app.logger.error(f"Purchase management error: {str(e)}")
        flash("Error loading purchases", "error")
        return render_template('error.html'), 500

@procurement_bp.route("/suppliers")
@role_required([Roles.HQ_PROCUREMENT])
def suppliers():
    try:
        total = Vendor.query.count()
        active = Vendor.query.filter(Vendor.validated == True).count()
        # Blacklisted logic: if 'blacklisted' field exists
        blacklisted = 0
        if hasattr(Vendor, 'blacklisted'):
            blacklisted = Vendor.query.filter(Vendor.blacklisted == True).count()
        # Pending review: not validated and not blacklisted
        if hasattr(Vendor, 'blacklisted'):
            pending_review = Vendor.query.filter(Vendor.validated == False, Vendor.blacklisted == False).count()
        else:
            pending_review = Vendor.query.filter(Vendor.validated == False).count()
        supplier_data = {
            'stats': {
                'total': total,
                'active': active,
                'blacklisted': blacklisted,
                'pending_review': pending_review
            }
        }
        return render_template('procurement/suppliers/index.html', data=supplier_data)
    except Exception as e:
        current_app.logger.error(f"Supplier management error: {str(e)}")
        flash("Error loading suppliers", "error")
        return render_template('error.html'), 500

# Asset Tracking Route
@procurement_bp.route("/tracking")
@role_required([Roles.HQ_PROCUREMENT])
def tracking():
    try:
        total_tracked = InventoryItem.query.count()
        in_use = InventoryItem.query.filter(InventoryItem.qty_available > 0).count()
        in_transit = InventoryItem.query.filter(InventoryItem.status.ilike('%transit%')).count() if hasattr(InventoryItem, 'status') else 0
        in_maintenance = InventoryItem.query.filter(InventoryItem.status.ilike('%maintenance%')).count() if hasattr(InventoryItem, 'status') else 0
        tracking_data = {
            'stats': {
                'total_tracked': total_tracked,
                'in_use': in_use,
                'in_transit': in_transit,
                'in_maintenance': in_maintenance
            }
        }
        return render_template('procurement/tracking/index.html', data=tracking_data)
    except Exception as e:
        current_app.logger.error(f"Asset tracking error: {str(e)}")
        flash("Error loading tracking data", "error")
        return render_template('error.html'), 500

# API: Get Asset Details
@procurement_bp.route("/api/assets/<int:asset_id>")
@role_required([Roles.HQ_PROCUREMENT])
def get_asset(asset_id):
    try:
        asset = InventoryItem.query.get_or_404(asset_id)
        asset_data = {
            'id': asset.id,
            'code': asset.code,
            'name': asset.description,
            'category': asset.category,
            'qty_available': asset.qty_available,
            'unit_cost': asset.unit_cost,
            'uom': asset.uom,
            'total_cost': asset.total_cost,
            'price_change': asset.price_change,
            'status': getattr(asset, 'status', 'Active'),
            'group': asset.group,
            'created_at': asset.created_at.strftime('%Y-%m-%d') if asset.created_at else None,
            'updated_at': asset.updated_at.strftime('%Y-%m-%d') if asset.updated_at else None
        }
        return jsonify(asset_data)
    except Exception as e:
        current_app.logger.error(f"Asset fetch error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# API: Get Purchase Details
@procurement_bp.route("/api/purchases/<int:purchase_id>")
@role_required([Roles.HQ_PROCUREMENT])
def get_purchase(purchase_id):
    try:
        purchase = ProcurementRequest.query.get_or_404(purchase_id)
        purchase_data = {
            'id': purchase.id,
            'project_id': purchase.project_id,
            'item_name': purchase.item_name,
            'price': purchase.price,
            'qty': purchase.qty,
            'unit': purchase.unit,
            'status': purchase.status,
            'current_approver': purchase.current_approver,
            'created_at': purchase.created_at.strftime('%Y-%m-%d') if purchase.created_at else None,
            'updated_at': purchase.updated_at.strftime('%Y-%m-%d') if purchase.updated_at else None
        }
        return jsonify(purchase_data)
    except Exception as e:
        current_app.logger.error(f"Purchase fetch error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Asset CRUD Endpoints
@procurement_bp.route("/assets/add", methods=['POST'])
@role_required([Roles.HQ_PROCUREMENT])
def add_asset():
    try:
        data = request.get_json()
        asset = InventoryItem(
            code=data.get('code'),
            description=data.get('description'),
            group=data.get('group'),
            category=data.get('category'),
            qty_available=data.get('qty_available', 0.0),
            unit_cost=data.get('unit_cost'),
            uom=data.get('uom'),
            total_cost=data.get('total_cost', 0.0),
            price_change=data.get('price_change', 0.0)
        )
        db.session.add(asset)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Asset added successfully', 'id': asset.id})
    except Exception as e:
        current_app.logger.error(f"Add asset error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@procurement_bp.route("/assets/update/<int:asset_id>", methods=['POST'])
@role_required([Roles.HQ_PROCUREMENT])
def update_asset(asset_id):
    try:
        data = request.get_json()
        asset = InventoryItem.query.get_or_404(asset_id)
        asset.code = data.get('code', asset.code)
        asset.description = data.get('description', asset.description)
        asset.group = data.get('group', asset.group)
        asset.category = data.get('category', asset.category)
        asset.qty_available = data.get('qty_available', asset.qty_available)
        asset.unit_cost = data.get('unit_cost', asset.unit_cost)
        asset.uom = data.get('uom', asset.uom)
        asset.total_cost = data.get('total_cost', asset.total_cost)
        asset.price_change = data.get('price_change', asset.price_change)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Asset updated successfully'})
    except Exception as e:
        current_app.logger.error(f"Update asset error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@procurement_bp.route("/assets/delete/<int:asset_id>", methods=['POST'])
@role_required([Roles.HQ_PROCUREMENT])
def delete_asset(asset_id):
    try:
        asset = InventoryItem.query.get_or_404(asset_id)
        db.session.delete(asset)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Asset deleted successfully'})
    except Exception as e:
        current_app.logger.error(f"Delete asset error: {str(e)}")
        return jsonify({'error': str(e)}), 500
from utils.email import send_email
from models import User, ProcurementRequest, Vendor, InventoryItem, Budget, Report
# Reports Endpoint
@procurement_bp.route("/reports")
@role_required([Roles.HQ_PROCUREMENT])
def reports():
    try:
        reports = Report.query.order_by(Report.uploaded_at.desc()).all()
        report_data = [
            {
                'id': r.id,
                'filename': r.filename,
                'type': r.type,
                'uploaded_at': r.uploaded_at.strftime('%Y-%m-%d %H:%M:%S') if r.uploaded_at else '',
                'uploader': User.query.get(r.uploader_id).name if r.uploader_id else 'Unknown',
                'date': r.date.strftime('%Y-%m-%d') if r.date else ''
            }
            for r in reports
        ]
        return render_template('procurement/reports/index.html', reports=report_data)
    except Exception as e:
        current_app.logger.error(f"Reports error: {str(e)}")
        flash("Error loading reports", "error")
        return render_template('error.html'), 500
# Dashboard Route
@procurement_bp.route("/")
@role_required([Roles.HQ_PROCUREMENT])
def procurement_home():
    try:
        total_assets = InventoryItem.query.count()
        pending_requests = ProcurementRequest.query.filter(ProcurementRequest.status == 'pending').count()
        # Maintenance due: count assets with a 'maintenance_due' flag or similar, else 0
        maintenance_due = 0
        if hasattr(InventoryItem, 'maintenance_due'):
            maintenance_due = InventoryItem.query.filter_by(maintenance_due=True).count()
        # Total purchases: all procurement requests
        total_purchases = ProcurementRequest.query.count()
        # Budget utilized: sum of all disbursed requests / total budget
        disbursed_sum = db.session.query(db.func.sum(ProcurementRequest.price * ProcurementRequest.qty)).filter(ProcurementRequest.status == 'disbursed').scalar() or 0
        # Try to get total budget from Budget model
        total_budget = db.session.query(db.func.sum(Budget.allocated_amount)).scalar() or 0
        budget_utilized = (disbursed_sum / total_budget * 100) if total_budget else 0
        active_suppliers = Vendor.query.filter(Vendor.validated == True).count()
        summary = {
            'total_assets': total_assets,
            'pending_requests': pending_requests,
            'maintenance_due': maintenance_due,
            'total_purchases': total_purchases,
            'budget_utilized': round(budget_utilized, 2),
            'active_suppliers': active_suppliers
        }
        return render_template('procurement/index.html', summary=summary)
    except Exception as e:
        current_app.logger.error(f"Procurement dashboard error: {str(e)}")
        flash("Error loading procurement dashboard", "error")
        return render_template('error.html'), 500

# Asset Management Routes
@procurement_bp.route("/assets")
@role_required([Roles.HQ_PROCUREMENT])
def assets():
    try:
        assets = InventoryItem.query.all()
        categories = list(set([a.category for a in assets if a.category]))
        # Maintenance: count assets with a 'maintenance_due' flag or similar
        maintenance = 0
        retired = 0
        if hasattr(InventoryItem, 'maintenance_due'):
            maintenance = InventoryItem.query.filter_by(maintenance_due=True).count()
        if hasattr(InventoryItem, 'status'):
            retired = InventoryItem.query.filter(InventoryItem.status.ilike('%retired%')).count()
        stats = {
            'total': len(assets),
            'active': len([a for a in assets if (not hasattr(a, 'status') or (a.status and a.status.lower() == 'active')) and a.qty_available > 0]),
            'maintenance': maintenance,
            'retired': retired
        }
        categories_data = [{'id': idx+1, 'name': cat} for idx, cat in enumerate(categories)]
        assets_data = {'stats': stats, 'categories': categories_data}
        return render_template('procurement/assets/index.html', data=assets_data)
    except Exception as e:
        current_app.logger.error(f"Asset management error: {str(e)}")
        flash("Error loading assets", "error")
        return render_template('error.html'), 500

# Settings Route

@procurement_bp.route("/settings")
@role_required([Roles.HQ_PROCUREMENT])
def settings():
    try:
        settings_obj = Settings.query.first()
        if not settings_obj:
            # Create default settings if not present
            settings_obj = Settings()
            db.session.add(settings_obj)
            db.session.commit()
        settings_data = {
            'user_settings': {
                'notifications': {
                    'email_alerts': settings_obj.email_alerts,
                    'browser_notifications': settings_obj.browser_notifications,
                    'sms_alerts': settings_obj.sms_alerts
                },
                'display': {
                    'theme': settings_obj.theme,
                    'language': settings_obj.language,
                    'timezone': settings_obj.timezone
                }
            },
            'system_settings': {
                'approval_thresholds': {
                    'purchase_limit': settings_obj.purchase_limit,
                    'asset_value_limit': settings_obj.asset_value_limit
                },
                'reorder_points': {
                    'minimum_stock': settings_obj.minimum_stock,
                    'warning_threshold': settings_obj.warning_threshold
                },
                'workflow': {
                    'require_approval': settings_obj.require_approval,
                    'auto_reorder': settings_obj.auto_reorder
                }
            }
        }
        return render_template('procurement/settings/index.html', data=settings_data)
    except Exception as e:
        current_app.logger.error(f"Settings error: {str(e)}")
        flash("Error loading settings", "error")
        return render_template('error.html'), 500

@procurement_bp.route("/settings/update", methods=['POST'])
@role_required([Roles.HQ_PROCUREMENT])
def update_settings():
    try:
        data = request.get_json()
        settings_obj = Settings.query.first()
        if not settings_obj:
            settings_obj = Settings()
            db.session.add(settings_obj)
        # User settings
        user_settings = data.get('user_settings', {})
        notifications = user_settings.get('notifications', {})
        display = user_settings.get('display', {})
        settings_obj.email_alerts = notifications.get('email_alerts', settings_obj.email_alerts)
        settings_obj.browser_notifications = notifications.get('browser_notifications', settings_obj.browser_notifications)
        settings_obj.sms_alerts = notifications.get('sms_alerts', settings_obj.sms_alerts)
        settings_obj.theme = display.get('theme', settings_obj.theme)
        settings_obj.language = display.get('language', settings_obj.language)
        settings_obj.timezone = display.get('timezone', settings_obj.timezone)
        # System settings
        system_settings = data.get('system_settings', {})
        approval_thresholds = system_settings.get('approval_thresholds', {})
        reorder_points = system_settings.get('reorder_points', {})
        workflow = system_settings.get('workflow', {})
        settings_obj.purchase_limit = approval_thresholds.get('purchase_limit', settings_obj.purchase_limit)
        settings_obj.asset_value_limit = approval_thresholds.get('asset_value_limit', settings_obj.asset_value_limit)
        settings_obj.minimum_stock = reorder_points.get('minimum_stock', settings_obj.minimum_stock)
        settings_obj.warning_threshold = reorder_points.get('warning_threshold', settings_obj.warning_threshold)
        settings_obj.require_approval = workflow.get('require_approval', settings_obj.require_approval)
        settings_obj.auto_reorder = workflow.get('auto_reorder', settings_obj.auto_reorder)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Settings updated successfully'})
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Update settings error: {str(e)}")
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        current_app.logger.error(f"Update settings error: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
    
@procurement_bp.route('/logout')
@role_required([Roles.SUPER_HQ, Roles.HQ_PROCUREMENT])
def logout():
    # Profile Route
    @procurement_bp.route("/profile")
    @role_required([Roles.HQ_PROCUREMENT])
    def profile():
        try:
            user_id = session.get('user_id')
            user = User.query.get(user_id) if user_id else None
            if not user:
                flash("User not found", "error")
                return render_template('error.html'), 404
            purchases_initiated = ProcurementRequest.query.filter_by(requested_by=user.id).count() if hasattr(ProcurementRequest, 'requested_by') else 0
            assets_managed = InventoryItem.query.filter_by(assigned_to=user.id).count() if hasattr(InventoryItem, 'assigned_to') else 0
            suppliers_handled = Vendor.query.filter_by(added_by=user.id).count() if hasattr(Vendor, 'added_by') else 0
            reports_generated = 0  # Implement if report logs exist
            recent_activity = []
            if hasattr(ProcurementRequest, 'requested_by'):
                recent_reqs = ProcurementRequest.query.filter_by(requested_by=user.id).order_by(ProcurementRequest.created_at.desc()).limit(3).all()
                for req in recent_reqs:
                    recent_activity.append({
                        'action': 'Created Purchase Order',
                        'reference': f'PO-{req.id}',
                        'timestamp': req.created_at.strftime('%Y-%m-%d %H:%M:%S') if req.created_at else ''
                    })
            profile_data = {
                'user': {
                    'name': user.name,
                    'email': user.email,
                    'role': user.role,
                    'department': getattr(user, 'department', ''),
                    'joined_date': user.created_at.strftime('%Y-%m-%d') if hasattr(user, 'created_at') and user.created_at else '',
                    'last_login': user.last_login.strftime('%Y-%m-%d %H:%M:%S') if hasattr(user, 'last_login') and user.last_login else ''
                },
                'stats': {
                    'purchases_initiated': purchases_initiated,
                    'assets_managed': assets_managed,
                    'suppliers_handled': suppliers_handled,
                    'reports_generated': reports_generated
                },
                'recent_activity': recent_activity
            }
            return render_template('procurement/profile/index.html', data=profile_data)
        except Exception as e:
            current_app.logger.error(f"Profile error: {str(e)}")
            flash("Error loading profile data", "error")
            return render_template('error.html'), 500
    return jsonify({'message': f'Procurement request advanced to {req.current_approver}'})
# --- Inventory CRUD Endpoints ---
@procurement_bp.route('/inventory', methods=['GET'])
@role_required([Roles.HQ_PROCUREMENT, Roles.PROCUREMENT_OFFICER])
def get_inventory():
    items = InventoryItem.query.all()
    result = [
        {
            'id': i.id,
            'code': i.code,
            'description': i.description,
            'group': i.group,
            'category': i.category,
            'qty_available': i.qty_available,
            'unit_cost': i.unit_cost,
            'uom': i.uom,
            'total_cost': i.total_cost,
            'price_change': i.price_change
        } for i in items
    ]
    return jsonify(result)

@procurement_bp.route('/inventory', methods=['POST'])
@role_required([Roles.HQ_PROCUREMENT, Roles.PROCUREMENT_OFFICER])
def create_inventory_item():
    data = request.get_json()
    item = InventoryItem(
        code=data.get('code'),
        description=data.get('description'),
        group=data.get('group'),
        category=data.get('category'),
        qty_available=data.get('qty_available', 0.0),
        unit_cost=data.get('unit_cost'),
        uom=data.get('uom'),
        total_cost=data.get('total_cost', 0.0),
        price_change=data.get('price_change', 0.0)
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({'message': 'Inventory item created', 'id': item.id}), 201

@procurement_bp.route('/inventory/<int:item_id>', methods=['PUT'])
@role_required([Roles.HQ_PROCUREMENT, Roles.PROCUREMENT_OFFICER])
def update_inventory_item(item_id):
    item = InventoryItem.query.get_or_404(item_id)
    data = request.get_json()
    item.code = data.get('code', item.code)
    item.description = data.get('description', item.description)
    item.group = data.get('group', item.group)
    item.category = data.get('category', item.category)
    item.qty_available = data.get('qty_available', item.qty_available)
    item.unit_cost = data.get('unit_cost', item.unit_cost)
    item.uom = data.get('uom', item.uom)
    item.total_cost = data.get('total_cost', item.total_cost)
    item.price_change = data.get('price_change', item.price_change)
    db.session.commit()
    return jsonify({'message': 'Inventory item updated'})

@procurement_bp.route('/inventory/<int:item_id>', methods=['DELETE'])
@role_required([Roles.HQ_PROCUREMENT, Roles.PROCUREMENT_OFFICER])
def delete_inventory_item(item_id):
    item = InventoryItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'Inventory item deleted'})
# --- Vendor Creation & Validation Endpoint ---
@procurement_bp.route('/vendor', methods=['POST'])
@role_required([Roles.HQ_PROCUREMENT, Roles.PROCUREMENT_OFFICER])
def create_vendor():
    data = request.get_json()
    name = data.get('name')
    category = data.get('category')
    payment_terms = data.get('payment_terms')
    existing = Vendor.query.filter_by(name=name, category=category).first()
    if existing:
        return jsonify({'message': 'Vendor already exists', 'id': existing.id, 'validated': existing.validated}), 200
    vendor = Vendor(
        name=name,
        category=category,
        payment_terms=payment_terms,
        validated=True  # Assume validated on creation for now
    )
    db.session.add(vendor)
    db.session.commit()
    return jsonify({'message': 'Vendor created', 'id': vendor.id, 'validated': vendor.validated}), 201
from extensions import db
from models import ProcurementRequest, Vendor, InventoryItem, Project
# --- Procurement Requisition Endpoint ---
@procurement_bp.route('/requisition', methods=['POST'])
@role_required([Roles.HQ_PROCUREMENT, Roles.PROJECT_MANAGER])
def create_requisition():
    data = request.get_json()
    req = ProcurementRequest(
        project_id=data.get('project_id'),
        item_name=data.get('item_name'),
        price=data.get('price'),
        qty=data.get('qty'),
        unit=data.get('unit'),
        status='pending',
        current_approver='Procurement Manager',
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.session.add(req)
    db.session.commit()
    return jsonify({'message': 'Requisition request created', 'id': req.id}), 201