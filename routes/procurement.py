from flask import Blueprint, render_template, request, jsonify, current_app, flash, send_file, session,redirect, url_for
from datetime import datetime, timedelta
from utils.decorators import role_required
from utils.constants import Roles
import pandas as pd
from io import BytesIO
import os

procurement_bp = Blueprint("procurement", __name__, url_prefix='/procurement')

# Dashboard Route
@procurement_bp.route("/")
@role_required([Roles.HQ_PROCUREMENT])
def procurement_home():
    try:
        summary = {
            'total_assets': 1245,
            'pending_requests': 8,
            'maintenance_due': 12,
            'total_purchases': 156,
            'budget_utilized': 75.5,  # percentage
            'active_suppliers': 24
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
        assets_data = {
            'stats': {
                'total': 1245,
                'active': 1180,
                'maintenance': 45,
                'retired': 20
            },
            'categories': [
                {'id': 1, 'name': 'Vehicles'},
                {'id': 2, 'name': 'Equipment'},
                {'id': 3, 'name': 'IT Hardware'},
                {'id': 4, 'name': 'Furniture'}
            ]
        }
        return render_template('procurement/assets/index.html', data=assets_data)
    except Exception as e:
        current_app.logger.error(f"Asset management error: {str(e)}")
        flash("Error loading assets", "error")
        return render_template('error.html'), 500

# Purchase Management Routes
@procurement_bp.route("/purchases")
@role_required([Roles.HQ_PROCUREMENT])
def purchases():
    try:
        purchase_data = {
            'stats': {
                'total_orders': 156,
                'pending': 12,
                'in_transit': 8,
                'completed': 136
            },
            'budget': {
                'total': 5000000,
                'utilized': 3775000,
                'remaining': 1225000
            }
        }
        return render_template('procurement/purchases/index.html', data=purchase_data)
    except Exception as e:
        current_app.logger.error(f"Purchase management error: {str(e)}")
        flash("Error loading purchases", "error")
        return render_template('error.html'), 500

# Supplier Management Routes
@procurement_bp.route("/suppliers")
@role_required([Roles.HQ_PROCUREMENT])
def suppliers():
    try:
        supplier_data = {
            'stats': {
                'total': 24,
                'active': 18,
                'blacklisted': 2,
                'pending_review': 4
            }
        }
        return render_template('procurement/suppliers/index.html', data=supplier_data)
    except Exception as e:
        current_app.logger.error(f"Supplier management error: {str(e)}")
        flash("Error loading suppliers", "error")
        return render_template('error.html'), 500

# Asset Tracking Routes
@procurement_bp.route("/tracking")
@role_required([Roles.HQ_PROCUREMENT])
def tracking():
    try:
        tracking_data = {
            'stats': {
                'total_tracked': 850,
                'in_use': 780,
                'in_transit': 45,
                'in_maintenance': 25
            }
        }
        return render_template('procurement/tracking/index.html', data=tracking_data)
    except Exception as e:
        current_app.logger.error(f"Asset tracking error: {str(e)}")
        flash("Error loading tracking data", "error")
        return render_template('error.html'), 500

# API Routes for AJAX requests
@procurement_bp.route("/api/assets/<int:asset_id>")
@role_required([Roles.HQ_PROCUREMENT])
def get_asset(asset_id):
    try:
        # Mock asset data - replace with database query
        asset = {
            'id': asset_id,
            'name': 'Toyota Hilux',
            'category': 'Vehicles',
            'purchase_date': '2024-01-15',
            'status': 'Active',
            'location': 'Site A',
            'last_maintenance': '2025-08-15',
            'next_maintenance': '2025-11-15',
            'value': 2500000,
            'condition': 'Good',
            'assigned_to': 'John Doe (Site Manager)'
        }
        return jsonify(asset)
    except Exception as e:
        current_app.logger.error(f"Asset fetch error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@procurement_bp.route("/api/purchases/<int:purchase_id>")
@role_required([Roles.HQ_PROCUREMENT])
def get_purchase(purchase_id):
    try:
        # Mock purchase data - replace with database query
        purchase = {
            'id': purchase_id,
            'order_number': 'PO-2025-001',
            'supplier': 'ABC Supplies Ltd',
            'items': [
                {'name': 'Laptop', 'quantity': 5, 'price': 250000},
                {'name': 'Printer', 'quantity': 2, 'price': 150000}
            ],
            'status': 'In Transit',
            'order_date': '2025-09-01',
            'expected_delivery': '2025-09-15',
            'total_amount': 1550000,
            'tracking_number': 'TRK123456789',
            'notes': 'Urgent delivery required'
        }
        return jsonify(purchase)
    except Exception as e:
        current_app.logger.error(f"Purchase fetch error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# New Asset Routes
@procurement_bp.route("/assets/add", methods=['POST'])
@role_required([Roles.HQ_PROCUREMENT])
def add_asset():
    try:
        data = request.get_json()
        # Add asset to database logic here
        return jsonify({'status': 'success', 'message': 'Asset added successfully'})
    except Exception as e:
        current_app.logger.error(f"Add asset error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@procurement_bp.route("/assets/update/<int:asset_id>", methods=['POST'])
@role_required([Roles.HQ_PROCUREMENT])
def update_asset(asset_id):
    try:
        data = request.get_json()
        # Update asset in database logic here
        return jsonify({'status': 'success', 'message': 'Asset updated successfully'})
    except Exception as e:
        current_app.logger.error(f"Update asset error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@procurement_bp.route("/assets/delete/<int:asset_id>", methods=['POST'])
@role_required([Roles.HQ_PROCUREMENT])
def delete_asset(asset_id):
    try:
        # Delete asset from database logic here
        return jsonify({'status': 'success', 'message': 'Asset deleted successfully'})
    except Exception as e:
        current_app.logger.error(f"Delete asset error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# New Purchase Routes
@procurement_bp.route("/purchases/create", methods=['POST'])
@role_required([Roles.HQ_PROCUREMENT])
def create_purchase():
    try:
        data = request.get_json()
        # Create purchase order logic here
        return jsonify({'status': 'success', 'message': 'Purchase order created successfully'})
    except Exception as e:
        current_app.logger.error(f"Create purchase error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@procurement_bp.route("/purchases/update/<int:purchase_id>", methods=['POST'])
@role_required([Roles.HQ_PROCUREMENT])
def update_purchase(purchase_id):
    try:
        data = request.get_json()
        # Update purchase order logic here
        return jsonify({'status': 'success', 'message': 'Purchase order updated successfully'})
    except Exception as e:
        current_app.logger.error(f"Update purchase error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@procurement_bp.route("/purchases/cancel/<int:purchase_id>", methods=['POST'])
@role_required([Roles.HQ_PROCUREMENT])
def cancel_purchase(purchase_id):
    try:
        # Cancel purchase order logic here
        return jsonify({'status': 'success', 'message': 'Purchase order cancelled successfully'})
    except Exception as e:
        current_app.logger.error(f"Cancel purchase error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Supplier Management Routes
@procurement_bp.route("/suppliers/add", methods=['POST'])
@role_required([Roles.HQ_PROCUREMENT])
def add_supplier():
    try:
        data = request.get_json()
        # Add supplier logic here
        return jsonify({'status': 'success', 'message': 'Supplier added successfully'})
    except Exception as e:
        current_app.logger.error(f"Add supplier error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@procurement_bp.route("/suppliers/<int:supplier_id>")
@role_required([Roles.HQ_PROCUREMENT])
def get_supplier(supplier_id):
    try:
        # Mock supplier data
        supplier = {
            'id': supplier_id,
            'name': 'ABC Supplies Ltd',
            'contact_person': 'John Smith',
            'email': 'john@abcsupplies.com',
            'phone': '+2348012345678',
            'address': '123 Business District, Lagos',
            'rating': 4.5,
            'category': 'IT Equipment',
            'payment_terms': 'Net 30',
            'status': 'Active'
        }
        return jsonify(supplier)
    except Exception as e:
        current_app.logger.error(f"Get supplier error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Reports and Analytics
@procurement_bp.route("/reports")
@role_required([Roles.HQ_PROCUREMENT])
def reports():
    try:
        return render_template('procurement/reports/index.html')
    except Exception as e:
        current_app.logger.error(f"Reports error: {str(e)}")
        flash("Error loading reports", "error")
        return render_template('error.html'), 500

@procurement_bp.route("/reports/generate", methods=['POST'])
@role_required([Roles.HQ_PROCUREMENT])
def generate_report():
    try:
        report_type = request.form.get('type')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        
        # Generate report logic here
        if report_type == 'assets':
            # Mock asset report data
            data = {
                'total_assets': 1245,
                'assets_by_category': [
                    {'category': 'Vehicles', 'count': 45},
                    {'category': 'Equipment', 'count': 320},
                    {'category': 'IT Hardware', 'count': 650},
                    {'category': 'Furniture', 'count': 230}
                ],
                'maintenance_summary': {
                    'due_this_month': 12,
                    'overdue': 3,
                    'completed_this_month': 8
                }
            }
        elif report_type == 'purchases':
            # Mock purchase report data
            data = {
                'total_spent': 3775000,
                'purchases_by_category': [
                    {'category': 'IT Equipment', 'amount': 1850000},
                    {'category': 'Office Supplies', 'amount': 450000},
                    {'category': 'Vehicles', 'amount': 1250000},
                    {'category': 'Maintenance', 'amount': 225000}
                ],
                'top_suppliers': [
                    {'supplier': 'ABC Supplies', 'amount': 1250000},
                    {'supplier': 'Tech Solutions', 'amount': 850000},
                    {'supplier': 'Office World', 'amount': 450000}
                ]
            }
        
        return jsonify({'status': 'success', 'data': data})
    except Exception as e:
        current_app.logger.error(f"Generate report error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@procurement_bp.route("/reports/export")
@role_required([Roles.HQ_PROCUREMENT])
def export_report():
    try:
        report_type = request.args.get('type')
        
        # Create Excel report
        if report_type == 'assets':
            data = {
                'Asset ID': [1, 2, 3, 4, 5],
                'Name': ['Laptop Dell XPS', 'Printer HP LaserJet', 'Vehicle Toyota Hilux', 'Desk Executive', 'Chair Ergonomic'],
                'Category': ['IT Hardware', 'IT Hardware', 'Vehicles', 'Furniture', 'Furniture'],
                'Status': ['Active', 'Maintenance', 'Active', 'Active', 'Retired'],
                'Value': [450000, 150000, 2500000, 75000, 25000]
            }
        elif report_type == 'purchases':
            data = {
                'PO Number': ['PO-2025-001', 'PO-2025-002', 'PO-2025-003'],
                'Supplier': ['ABC Supplies', 'Tech Solutions', 'Office World'],
                'Order Date': ['2025-09-01', '2025-09-05', '2025-09-10'],
                'Status': ['Delivered', 'In Transit', 'Processing'],
                'Amount': [1550000, 850000, 450000]
            }
        
        df = pd.DataFrame(data)
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Report', index=False)
        
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'{report_type}_report_{datetime.now().strftime("%Y%m%d")}.xlsx'
        )
    except Exception as e:
        current_app.logger.error(f"Export report error: {str(e)}")
        flash("Error exporting report", "error")
        return redirect(url_for('procurement.reports'))

# Maintenance Management
@procurement_bp.route("/maintenance")
@role_required([Roles.HQ_PROCUREMENT])
def maintenance():
    try:
        maintenance_data = {
            'stats': {
                'scheduled': 15,
                'in_progress': 8,
                'completed': 25,
                'overdue': 3
            }
        }
        return render_template('procurement/maintenance/index.html', data=maintenance_data)
    except Exception as e:
        current_app.logger.error(f"Maintenance error: {str(e)}")
        flash("Error loading maintenance data", "error")
        return render_template('error.html'), 500

@procurement_bp.route("/maintenance/schedule", methods=['POST'])
@role_required([Roles.HQ_PROCUREMENT])
def schedule_maintenance():
    try:
        data = request.get_json()
        # Schedule maintenance logic here
        return jsonify({'status': 'success', 'message': 'Maintenance scheduled successfully'})
    except Exception as e:
        current_app.logger.error(f"Schedule maintenance error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Budget Management
@procurement_bp.route("/budget")
@role_required([Roles.HQ_PROCUREMENT])
def budget():
    try:
        budget_data = {
            'total_budget': 5000000,
            'utilized': 3775000,
            'remaining': 1225000,
            'breakdown': [
                {'category': 'IT Equipment', 'allocated': 2000000, 'spent': 1850000},
                {'category': 'Office Supplies', 'allocated': 500000, 'spent': 450000},
                {'category': 'Vehicles', 'allocated': 2000000, 'spent': 1250000},
                {'category': 'Maintenance', 'allocated': 500000, 'spent': 225000}
            ]
        }
        return render_template('procurement/budget/index.html', data=budget_data)
    except Exception as e:
        current_app.logger.error(f"Budget error: {str(e)}")
        flash("Error loading budget data", "error")
        return render_template('error.html'), 500

# Notification endpoints
@procurement_bp.route("/api/notifications")
@role_required([Roles.HQ_PROCUREMENT])
def get_notifications():
    try:
        # Mock notifications
        notifications = [
            {
                'id': 1,
                'type': 'maintenance',
                'message': '3 assets due for maintenance this week',
                'timestamp': '2025-09-02 14:30',
                'priority': 'high'
            },
            {
                'id': 2,
                'type': 'purchase',
                'message': 'Purchase order PO-2025-005 is delayed',
                'timestamp': '2025-09-02 10:15',
                'priority': 'medium'
            },
            {
                'id': 3,
                'type': 'supplier',
                'message': 'New supplier registration requires approval',
                'timestamp': '2025-09-01 16:45',
                'priority': 'low'
            }
        ]
        return jsonify(notifications)
    except Exception as e:
        current_app.logger.error(f"Notifications error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Search functionality
@procurement_bp.route("/api/search")
@role_required([Roles.HQ_PROCUREMENT])
def search():
    try:
        query = request.args.get('q', '')
        # Mock search results
        results = {
            'assets': [
                {'id': 1, 'name': 'Laptop Dell XPS', 'type': 'IT Hardware'},
                {'id': 2, 'name': 'Printer HP LaserJet', 'type': 'IT Hardware'}
            ],
            'purchases': [
                {'id': 1, 'order_number': 'PO-2025-001', 'supplier': 'ABC Supplies'},
                {'id': 2, 'order_number': 'PO-2025-002', 'supplier': 'Tech Solutions'}
            ],
            'suppliers': [
                {'id': 1, 'name': 'ABC Supplies Ltd', 'category': 'IT Equipment'},
                {'id': 2, 'name': 'Tech Solutions', 'category': 'IT Equipment'}
            ]
        }
        return jsonify(results)
    except Exception as e:
        current_app.logger.error(f"Search error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@procurement_bp.route("/inventory")
@role_required([Roles.HQ_PROCUREMENT])
def inventory():
    try:
        # Mock inventory data - replace with database queries
        data = {
            'stats': {
                'total_items': 856,
                'low_stock': 23,
                'out_of_stock': 12,
                'pending_orders': 8
            },
            'categories': [
                {'id': 1, 'name': 'IT Equipment'},
                {'id': 2, 'name': 'Office Supplies'},
                {'id': 3, 'name': 'Vehicles'},
                {'id': 4, 'name': 'Furniture'}
            ],
            'inventory': [
                {
                    'code': 'INV001',
                    'name': 'Laptop Dell XPS',
                    'description': 'Dell XPS 15 Core i7',
                    'category': 'IT Equipment',
                    'quantity': 5,
                    'reorder_point': 3,
                    'location': 'Store Room A',
                    'status': 'In Stock',
                    'image': 'https://via.placeholder.com/40'
                },
                # Add more mock items as needed
            ]
        }
        return render_template('procurement/tracking/inventory.html', data=data)
    except Exception as e:
        current_app.logger.error(f"Inventory error: {str(e)}")
        flash("Error loading inventory data", "error")
        return render_template('error.html'), 500

# Add inventory API endpoints
@procurement_bp.route("/inventory/add", methods=['POST'])
@role_required([Roles.HQ_PROCUREMENT])
def add_inventory():
    try:
        data = request.get_json()
        # Add inventory item logic here
        return jsonify({'status': 'success', 'message': 'Item added successfully'})
    except Exception as e:
        current_app.logger.error(f"Add inventory error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@procurement_bp.route("/inventory/<string:item_code>")
@role_required([Roles.HQ_PROCUREMENT])
def get_inventory_item(item_code):
    try:
        # Mock item data - replace with database query
        item = {
            'code': item_code,
            'name': 'Sample Item',
            'description': 'Sample Description',
            'category': 'IT Equipment',
            'quantity': 10,
            'reorder_point': 5,
            'location': 'Store Room A',
            'status': 'In Stock'
        }
        return jsonify(item)
    except Exception as e:
        current_app.logger.error(f"Get inventory item error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@procurement_bp.route("/analytics")
@role_required([Roles.HQ_PROCUREMENT])
def analytics():
    try:
        # Ensure all numeric values are proper Python types
        analytics_data = {
            'overview': {
                'total_spend': float(3775000),
                'total_orders': int(156),
                'active_suppliers': int(24),
                'efficiency_score': float(85)
            },
            'trends': {
                'monthly_spend': [
                    {'month': str('Jan'), 'amount': float(250000)},
                    {'month': str('Feb'), 'amount': float(320000)},
                    {'month': str('Mar'), 'amount': float(280000)},
                    {'month': str('Apr'), 'amount': float(350000)},
                    {'month': str('May'), 'amount': float(420000)},
                    {'month': str('Jun'), 'amount': float(380000)}
                ],
                'top_categories': [
                    {'category': str('IT Equipment'), 'spend': float(1850000)},
                    {'category': str('Vehicles'), 'spend': float(1250000)},
                    {'category': str('Office Supplies'), 'spend': float(450000)},
                    {'category': str('Maintenance'), 'spend': float(225000)}
                ]
            },
            'performance': {
                'delivery_time': float(4.5),
                'order_accuracy': float(96.5),
                'supplier_reliability': float(92.8),
                'budget_variance': float(-2.3)
            }
        }
        return render_template('procurement/analytics/index.html', data=analytics_data)
    except Exception as e:
        current_app.logger.error(f"Analytics error: {str(e)}")
        flash("Error loading analytics data", "error")
        return render_template('error.html'), 500

# Profile Route
@procurement_bp.route("/profile")
@role_required([Roles.HQ_PROCUREMENT])
def profile():
    try:
        profile_data = {
            'user': {
                'name': 'John Doe',
                'email': 'john.doe@sammy.com',
                'role': 'Procurement Officer',
                'department': 'HQ Procurement',
                'joined_date': '2024-01-15',
                'last_login': '2025-09-03 10:00:00'
            },
            'stats': {
                'purchases_initiated': 45,
                'assets_managed': 156,
                'suppliers_handled': 12,
                'reports_generated': 28
            },
            'recent_activity': [
                {
                    'action': 'Created Purchase Order',
                    'reference': 'PO-2025-045',
                    'timestamp': '2025-09-02 15:30:00'
                },
                {
                    'action': 'Updated Asset Status',
                    'reference': 'AST-2025-089',
                    'timestamp': '2025-09-02 14:15:00'
                },
                {
                    'action': 'Generated Report',
                    'reference': 'RPT-2025-028',
                    'timestamp': '2025-09-02 11:45:00'
                }
            ]
        }
        return render_template('procurement/profile/index.html', data=profile_data)
    except Exception as e:
        current_app.logger.error(f"Profile error: {str(e)}")
        flash("Error loading profile data", "error")
        return render_template('error.html'), 500

# Settings Route
@procurement_bp.route("/settings")
@role_required([Roles.HQ_PROCUREMENT])
def settings():
    try:
        settings_data = {
            'user_settings': {
                'notifications': {
                    'email_alerts': True,
                    'browser_notifications': True,
                    'sms_alerts': False
                },
                'display': {
                    'theme': 'light',
                    'language': 'en',
                    'timezone': 'Africa/Lagos'
                }
            },
            'system_settings': {
                'approval_thresholds': {
                    'purchase_limit': 500000,
                    'asset_value_limit': 1000000
                },
                'reorder_points': {
                    'minimum_stock': 10,
                    'warning_threshold': 20
                },
                'workflow': {
                    'require_approval': True,
                    'auto_reorder': False
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
        # Update settings logic here
        return jsonify({'status': 'success', 'message': 'Settings updated successfully'})
    except Exception as e:
        current_app.logger.error(f"Update settings error: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
    
@procurement_bp.route('/logout')
@role_required([Roles.SUPER_HQ, Roles.HQ_PROCUREMENT])
def logout():
    try:
        # Clear all session data
        session.clear()
        flash("Successfully logged out", "success")
        return redirect(url_for('auth.login'))
    except Exception as e:
        current_app.logger.error(f"Logout error: {str(e)}")
        flash("Error during logout", "error")
        return redirect(url_for('procurement.procurement_home'))