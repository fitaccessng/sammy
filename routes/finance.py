from datetime import datetime, timedelta
from flask import Blueprint, render_template, current_app, flash, request, jsonify, url_for, redirect, send_file, session
from flask_login import current_user, logout_user
from utils.decorators import role_required
from utils.constants import Roles
from models import Payroll, Document, Audit, Expense, Report, BankReconciliation, Checkbook, Transaction, User
from sqlalchemy import func, desc, or_, and_, case
from werkzeug.utils import secure_filename
import os
import pandas as pd
from io import BytesIO
from extensions import db
import json
import csv

finance_bp = Blueprint('finance', __name__, url_prefix='/finance')

# Dashboard Routes
@finance_bp.route('/')
@role_required([Roles.SUPER_HQ, Roles.HQ_FINANCE])
def finance_home():
    try:
        # Get current month and year for filtering
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        # Calculate previous month for comparison
        prev_month_date = datetime.now() - timedelta(days=30)
        prev_month = prev_month_date.month
        prev_year = prev_month_date.year
        
        # Enhanced financial summary
        summary = {
            'bank_balance': db.session.query(func.sum(BankReconciliation.balance)).scalar() or 0,
            'monthly_expenses': db.session.query(func.sum(Expense.amount)).filter(
                func.extract('month', Expense.date) == current_month,
                func.extract('year', Expense.date) == current_year
            ).scalar() or 0,
            'prev_month_expenses': db.session.query(func.sum(Expense.amount)).filter(
                func.extract('month', Expense.date) == prev_month,
                func.extract('year', Expense.date) == prev_year
            ).scalar() or 0,
            'pending_payroll': db.session.query(func.sum(Payroll.amount)).filter(Payroll.status == 'pending').scalar() or 0,
            'outstanding_payments': db.session.query(func.sum(Expense.amount)).filter(Expense.status == 'outstanding').scalar() or 0,
            'total_documents': db.session.query(Document).count(),
            'recent_uploads': db.session.query(Document).filter(Document.uploaded_at >= datetime.now() - timedelta(days=7)).count(),
            'storage_used': f"{round(db.session.query(func.sum(Document.size)).scalar() or 0 / (1024**3), 2)}GB",
            'pending_review': db.session.query(Document).filter(Document.status == 'pending_review').count(),
            'total_income': db.session.query(func.sum(Transaction.amount)).filter(
                Transaction.type == 'income',
                Transaction.status == 'completed'
            ).scalar() or 0,
            'cash_flow': db.session.query(
                func.sum(case((Transaction.type == 'income', Transaction.amount), else_=0)) - 
                func.sum(case((Transaction.type == 'expense', Transaction.amount), else_=0))
            ).filter(
                func.extract('month', Transaction.date) == current_month,
                func.extract('year', Transaction.date) == current_year
            ).scalar() or 0
        }
        
        # Recent transactions for dashboard
        recent_transactions = Transaction.query.order_by(desc(Transaction.date)).limit(10).all()
        
        # Expense breakdown by category
        expense_categories = db.session.query(
            Expense.category, 
            func.sum(Expense.amount).label('total')
        ).filter(
            func.extract('month', Expense.date) == current_month,
            func.extract('year', Expense.date) == current_year
        ).group_by(Expense.category).all()
        
        return render_template('finance/index.html', 
                              summary=summary, 
                              transactions=recent_transactions,
                              expense_categories=expense_categories)
    except Exception as e:
        current_app.logger.error(f"Finance dashboard error: {str(e)}")
        flash("Error loading finance dashboard", "error")
        return render_template('error.html'), 500

# Payroll Management
@finance_bp.route('/payroll')
@role_required([Roles.SUPER_HQ, Roles.HQ_FINANCE])
def payroll():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status_filter = request.args.get('status', 'all')
        
        query = Payroll.query
        
        if status_filter != 'all':
            query = query.filter(Payroll.status == status_filter)
            
        payrolls = query.order_by(desc(Payroll.date)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return render_template('finance/payroll/index.html', 
                             payrolls=payrolls, 
                             status_filter=status_filter)
    except Exception as e:
        current_app.logger.error(f"Payroll loading error: {str(e)}")
        flash('Error loading payroll', 'error')
        return render_template('error.html'), 500

@finance_bp.route('/payroll/<int:payroll_id>')
@role_required([Roles.SUPER_HQ, Roles.HQ_FINANCE])
def payroll_detail(payroll_id):
    try:
        payroll = Payroll.query.get_or_404(payroll_id)
        return render_template('finance/payroll/detail.html', payroll=payroll)
    except Exception as e:
        current_app.logger.error(f"Payroll detail error: {str(e)}")
        flash('Error loading payroll details', 'error')
        return redirect(url_for('finance.payroll'))

@finance_bp.route('/payroll/process', methods=['POST'])
@role_required([Roles.SUPER_HQ, Roles.HQ_FINANCE])
def process_payroll():
    try:
        payroll_id = request.form.get('payroll_id')
        payroll = Payroll.query.get(payroll_id)
        if not payroll:
            return jsonify({'status': 'error', 'message': 'Payroll not found'})
        
        # Create a transaction record for the payroll
        transaction = Transaction(
            description=f"Payroll: {payroll.employee_name}",
            amount=payroll.amount,
            type='expense',
            category='payroll',
            date=datetime.now(),
            status='completed',
            reference_id=f"PAY_{payroll_id}",
            created_by=current_user.id
        )
        
        payroll.status = 'processed'
        payroll.processed_at = datetime.now()
        payroll.processed_by = current_user.id
        
        db.session.add(transaction)
        db.session.commit()
        
        # Log audit event
        audit = Audit(
            event_type='payroll_processed',
            description=f'Processed payroll for {payroll.employee_name} - ${payroll.amount}',
            user_id=current_user.id,
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': 'Payroll processed successfully'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Payroll processing error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)})

@finance_bp.route('/payroll/create', methods=['GET', 'POST'])
@role_required([Roles.SUPER_HQ, Roles.HQ_FINANCE])
def create_payroll():
    if request.method == 'POST':
        try:
            data = request.form
            payroll = Payroll(
                employee_name=data.get('employee_name'),
                employee_id=data.get('employee_id'),
                amount=float(data.get('amount')),
                period_start=datetime.strptime(data.get('period_start'), '%Y-%m-%d'),
                period_end=datetime.strptime(data.get('period_end'), '%Y-%m-%d'),
                description=data.get('description', ''),
                status='pending',
                created_by=current_user.id
            )
            db.session.add(payroll)
            db.session.commit()
            
            flash('Payroll entry created successfully', 'success')
            return redirect(url_for('finance.payroll'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Payroll creation error: {str(e)}")
            flash('Error creating payroll entry', 'error')
    
    return render_template('finance/payroll/create.html')

# Document Management System
@finance_bp.route('/documents')
@role_required([Roles.SUPER_HQ, Roles.HQ_FINANCE])
def documents():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        doc_type = request.args.get('type', 'all')
        status_filter = request.args.get('status', 'all')
        
        query = Document.query
        
        if doc_type != 'all':
            query = query.filter(Document.document_type == doc_type)
            
        if status_filter != 'all':
            query = query.filter(Document.status == status_filter)
            
        documents = query.order_by(desc(Document.uploaded_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return render_template('finance/documents/index.html', 
                             documents=documents,
                             doc_type=doc_type,
                             status_filter=status_filter)
    except Exception as e:
        current_app.logger.error(f"Documents loading error: {str(e)}")
        flash('Error loading documents', 'error')
        return render_template('error.html'), 500

@finance_bp.route('/documents/upload', methods=['POST'])
@role_required([Roles.SUPER_HQ, Roles.HQ_FINANCE])
def upload_document():
    try:
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': 'No file provided'})
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'status': 'error', 'message': 'No file selected'})
            
        if file:
            filename = secure_filename(file.filename)
            # Create directory if it doesn't exist
            upload_folder = current_app.config['UPLOAD_FOLDER']
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
                
            save_path = os.path.join(upload_folder, filename)
            file.save(save_path)
            
            doc = Document(
                filename=filename, 
                path=save_path, 
                uploaded_at=datetime.now(), 
                size=os.path.getsize(save_path), 
                status='pending_review',
                document_type=request.form.get('document_type', 'other'),
                description=request.form.get('description', ''),
                uploaded_by=current_user.id
            )
            
            db.session.add(doc)
            db.session.commit()
            
            # Log audit event
            audit = Audit(
                event_type='document_uploaded',
                description=f'Uploaded document: {filename}',
                user_id=current_user.id,
                ip_address=request.remote_addr
            )
            db.session.add(audit)
            db.session.commit()
            
            return jsonify({'status': 'success', 'message': 'Document uploaded successfully', 'document_id': doc.id})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Document upload error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)})

@finance_bp.route('/documents/<int:doc_id>')
@role_required([Roles.SUPER_HQ, Roles.HQ_FINANCE])
def document_detail(doc_id):
    try:
        document = Document.query.get_or_404(doc_id)
        return render_template('finance/documents/detail.html', document=document)
    except Exception as e:
        current_app.logger.error(f"Document detail error: {str(e)}")
        flash('Error loading document details', 'error')
        return redirect(url_for('finance.documents'))

@finance_bp.route('/documents/update-status/<int:doc_id>', methods=['POST'])
@role_required([Roles.SUPER_HQ, Roles.HQ_FINANCE])
def update_document_status(doc_id):
    try:
        document = Document.query.get_or_404(doc_id)
        new_status = request.form.get('status')
        
        if new_status not in ['pending_review', 'approved', 'rejected', 'archived']:
            return jsonify({'status': 'error', 'message': 'Invalid status'})
            
        document.status = new_status
        document.reviewed_by = current_user.id
        document.reviewed_at = datetime.now()
        
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': f'Document status updated to {new_status}'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Document status update error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)})

@finance_bp.route('/documents/search', methods=['GET'])
@role_required([Roles.SUPER_HQ, Roles.HQ_FINANCE])
def search_documents():
    try:
        query = request.args.get('q', '')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        documents = Document.query.filter(
            or_(
                Document.filename.ilike(f'%{query}%'),
                Document.description.ilike(f'%{query}%')
            )
        ).order_by(desc(Document.uploaded_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'documents': [doc.to_dict() for doc in documents.items],
            'total': documents.total,
            'pages': documents.pages,
            'current_page': page
        })
    except Exception as e:
        current_app.logger.error(f"Document search error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)})

@finance_bp.route('/documents/download/<int:doc_id>')
@role_required([Roles.SUPER_HQ, Roles.HQ_FINANCE])
def download_document(doc_id):
    try:
        doc = Document.query.get_or_404(doc_id)
        if not os.path.exists(doc.path):
            flash('File not found on server', 'error')
            return redirect(url_for('finance.documents'))
            
        # Log download activity
        audit = Audit(
            event_type='document_downloaded',
            description=f'Downloaded document: {doc.filename}',
            user_id=current_user.id,
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        db.session.commit()
        
        return send_file(doc.path, as_attachment=True, download_name=doc.filename)
    except Exception as e:
        current_app.logger.error(f"Document download error: {str(e)}")
        flash('Error downloading document', 'error')
        return redirect(url_for('finance.documents'))

# Audit Management
@finance_bp.route('/audit')
@role_required([Roles.SUPER_HQ, Roles.HQ_FINANCE])
def audit():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        event_type = request.args.get('event_type', 'all')
        user_id = request.args.get('user_id', type=int)
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        query = Audit.query
        
        if event_type != 'all':
            query = query.filter(Audit.event_type == event_type)
            
        if user_id:
            query = query.filter(Audit.user_id == user_id)
            
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
                query = query.filter(Audit.date >= date_from_obj)
            except ValueError:
                pass
                
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
                query = query.filter(Audit.date <= date_to_obj + timedelta(days=1))
            except ValueError:
                pass
        
        audits = query.order_by(desc(Audit.date)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        stats = {
            'total_audits': Audit.query.count(),
            'last_audit': Audit.query.order_by(desc(Audit.date)).first(),
            'users': User.query.filter(User.role.in_([Roles.SUPER_HQ, Roles.HQ_FINANCE])).all()
        }
        
        return render_template('finance/audit/index.html', 
                             audits=audits, 
                             stats=stats,
                             filters=request.args)
    except Exception as e:
        current_app.logger.error(f"Audit loading error: {str(e)}")
        flash('Error loading audit logs', 'error')
        return render_template('error.html'), 500

@finance_bp.route('/audit/log', methods=['POST'])
@role_required([Roles.SUPER_HQ, Roles.HQ_FINANCE])
def log_audit():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'})
            
        audit = Audit(
            event_type=data.get('event_type'),
            description=data.get('description'),
            user_id=current_user.id,
            ip_address=request.remote_addr,
            details=json.dumps(data.get('details', {})) if data.get('details') else None
        )
        db.session.add(audit)
        db.session.commit()
        
        return jsonify({'status': 'success', 'audit_id': audit.id})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Audit logging error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)})

@finance_bp.route('/audit/export', methods=['POST'])
@role_required([Roles.SUPER_HQ, Roles.HQ_FINANCE])
def export_audit_logs():
    try:
        # Get filters from request
        filters = request.get_json() or {}
        query = Audit.query
        
        if filters.get('event_type') and filters['event_type'] != 'all':
            query = query.filter(Audit.event_type == filters['event_type'])
            
        if filters.get('user_id'):
            query = query.filter(Audit.user_id == filters['user_id'])
            
        if filters.get('date_from'):
            try:
                date_from = datetime.strptime(filters['date_from'], '%Y-%m-%d')
                query = query.filter(Audit.date >= date_from)
            except ValueError:
                pass
                
        if filters.get('date_to'):
            try:
                date_to = datetime.strptime(filters['date_to'], '%Y-%m-%d')
                query = query.filter(Audit.date <= date_to + timedelta(days=1))
            except ValueError:
                pass
        
        audits = query.order_by(desc(Audit.date)).all()
        
        # Create CSV instead of Excel for better compatibility
        output = BytesIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['ID', 'Date', 'Event Type', 'Description', 'User', 'IP Address', 'Details'])
        
        # Write data
        for audit in audits:
            user = User.query.get(audit.user_id)
            username = user.username if user else 'Unknown'
            writer.writerow([
                audit.id,
                audit.date.strftime('%Y-%m-%d %H:%M:%S'),
                audit.event_type,
                audit.description,
                username,
                audit.ip_address,
                audit.details or ''
            ])
        
        output.seek(0)
        filename = f"audit_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return send_file(
            output,
            download_name=filename,
            as_attachment=True,
            mimetype='text/csv'
        )
    except Exception as e:
        current_app.logger.error(f"Audit export error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)})

@finance_bp.route('/audit/generate-report', methods=['POST'])
@role_required([Roles.SUPER_HQ, Roles.HQ_FINANCE])
def generate_audit_report():
    try:
        # Get date range from request
        data = request.get_json() or {}
        date_from = data.get('date_from')
        date_to = data.get('date_to') or datetime.now().strftime('%Y-%m-%d')
        
        query = Audit.query
        
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
                query = query.filter(Audit.date >= date_from_obj)
            except ValueError:
                pass
                
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
                query = query.filter(Audit.date <= date_to_obj + timedelta(days=1))
            except ValueError:
                pass
        
        # Generate comprehensive stats
        total_audits = query.count()
        open_issues = query.filter(Audit.status == 'open').count()
        resolved_issues = query.filter(Audit.status == 'resolved').count()
        
        # Event type breakdown
        event_types = db.session.query(
            Audit.event_type,
            func.count(Audit.id).label('count')
        ).filter(Audit.id.in_([a.id for a in query.all()])).group_by(Audit.event_type).all()
        
        # User activity
        user_activity = db.session.query(
            Audit.user_id,
            User.username,
            func.count(Audit.id).label('activity_count')
        ).join(User, Audit.user_id == User.id).filter(
            Audit.id.in_([a.id for a in query.all()])
        ).group_by(Audit.user_id, User.username).order_by(desc('activity_count')).all()
        
        stats = {
            'total_audits': total_audits,
            'open_issues': open_issues,
            'resolved_issues': resolved_issues,
            'event_types': [{'type': et[0], 'count': et[1]} for et in event_types],
            'user_activity': [{'user_id': ua[0], 'username': ua[1], 'count': ua[2]} for ua in user_activity],
            'date_range': {
                'from': date_from or 'Beginning',
                'to': date_to
            }
        }
        
        return jsonify({'status': 'success', 'report': stats})
    except Exception as e:
        current_app.logger.error(f"Audit report generation error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)})

@finance_bp.route('/audit/details/<int:audit_id>')
@role_required([Roles.SUPER_HQ, Roles.HQ_FINANCE])
def get_audit_details(audit_id):
    try:
        audit = Audit.query.get_or_404(audit_id)
        user = User.query.get(audit.user_id)
        
        response = audit.to_dict()
        response['username'] = user.username if user else 'Unknown'
        
        return jsonify(response)
    except Exception as e:
        current_app.logger.error(f"Audit details error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)})

# Purchases and Expenses
@finance_bp.route('/expenses')
@role_required([Roles.SUPER_HQ, Roles.HQ_FINANCE])
def expenses():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status_filter = request.args.get('status', 'all')
        category_filter = request.args.get('category', 'all')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        query = Expense.query
        
        if status_filter != 'all':
            query = query.filter(Expense.status == status_filter)
            
        if category_filter != 'all':
            query = query.filter(Expense.category == category_filter)
            
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
                query = query.filter(Expense.date >= date_from_obj)
            except ValueError:
                pass
                
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
                query = query.filter(Expense.date <= date_to_obj + timedelta(days=1))
            except ValueError:
                pass
        
        expenses = query.order_by(desc(Expense.date)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Get distinct categories for filter dropdown
        categories = db.session.query(Expense.category).distinct().all()
        categories = [c[0] for c in categories if c[0]]
        
        return render_template('finance/financial/expenses.html', 
                             expenses=expenses,
                             status_filter=status_filter,
                             category_filter=category_filter,
                             categories=categories,
                             filters=request.args)
    except Exception as e:
        current_app.logger.error(f"Expenses loading error: {str(e)}")
        flash('Error loading expenses', 'error')
        return render_template('error.html'), 500

@finance_bp.route('/expenses/add', methods=['POST'])
@role_required([Roles.SUPER_HQ, Roles.HQ_FINANCE])
def add_expense():
    try:
        data = request.form
        
        # Validate required fields
        if not all([data.get('description'), data.get('amount'), data.get('date')]):
            return jsonify({'status': 'error', 'message': 'Missing required fields'})
            
        expense = Expense(
            description=data.get('description'),
            amount=float(data.get('amount')),
            category=data.get('category', 'uncategorized'),
            date=datetime.strptime(data.get('date'), '%Y-%m-%d'),
            vendor=data.get('vendor', ''),
            payment_method=data.get('payment_method', ''),
            status=data.get('status', 'outstanding'),
            notes=data.get('notes', ''),
            created_by=current_user.id
        )
        
        db.session.add(expense)
        db.session.commit()
        
        # Create corresponding transaction
        transaction = Transaction(
            description=f"Expense: {expense.description}",
            amount=expense.amount,
            type='expense',
            category=expense.category,
            date=expense.date,
            status='completed' if expense.status == 'paid' else 'pending',
            reference_id=f"EXP_{expense.id}",
            created_by=current_user.id
        )
        db.session.add(transaction)
        
        # Log audit event
        audit = Audit(
            event_type='expense_added',
            description=f'Added expense: {expense.description} - ${expense.amount}',
            user_id=current_user.id,
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': 'Expense added successfully', 'expense_id': expense.id})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Expense addition error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)})

@finance_bp.route('/expenses/update-status/<int:expense_id>', methods=['POST'])
@role_required([Roles.SUPER_HQ, Roles.HQ_FINANCE])
def update_expense_status(expense_id):
    try:
        expense = Expense.query.get_or_404(expense_id)
        new_status = request.form.get('status')
        
        if new_status not in ['outstanding', 'paid', 'cancelled']:
            return jsonify({'status': 'error', 'message': 'Invalid status'})
            
        old_status = expense.status
        expense.status = new_status
        
        # Update corresponding transaction if exists
        transaction = Transaction.query.filter_by(reference_id=f"EXP_{expense_id}").first()
        if transaction:
            transaction.status = 'completed' if new_status == 'paid' else 'pending'
        
        db.session.commit()
        
        # Log audit event
        audit = Audit(
            event_type='expense_status_updated',
            description=f'Updated expense status from {old_status} to {new_status} for: {expense.description}',
            user_id=current_user.id,
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': f'Expense status updated to {new_status}'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Expense status update error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)})

@finance_bp.route('/expenses/categories')
@role_required([Roles.SUPER_HQ, Roles.HQ_FINANCE])
def expense_categories():
    try:
        categories = db.session.query(Expense.category).distinct().all()
        return jsonify([c[0] for c in categories if c[0]])
    except Exception as e:
        current_app.logger.error(f"Expense categories error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)})

@finance_bp.route('/expenses/receipt/<int:expense_id>', methods=['GET', 'POST'])
@role_required([Roles.SUPER_HQ, Roles.HQ_FINANCE])
def expense_receipt(expense_id):
    try:
        expense = Expense.query.get_or_404(expense_id)
        
        if request.method == 'POST':
            if 'receipt' not in request.files:
                return jsonify({'status': 'error', 'message': 'No file provided'})
                
            file = request.files['receipt']
            if file.filename == '':
                return jsonify({'status': 'error', 'message': 'No file selected'})
                
            if file:
                filename = secure_filename(file.filename)
                upload_folder = current_app.config['UPLOAD_FOLDER']
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)
                    
                save_path = os.path.join(upload_folder, f"expense_{expense_id}_{filename}")
                file.save(save_path)
                
                expense.receipt_path = save_path
                db.session.commit()
                
                # Log audit event
                audit = Audit(
                    event_type='expense_receipt_uploaded',
                    description=f'Uploaded receipt for expense: {expense.description}',
                    user_id=current_user.id,
                    ip_address=request.remote_addr
                )
                db.session.add(audit)
                db.session.commit()
                
                return jsonify({'status': 'success', 'message': 'Receipt uploaded successfully'})
        
        return render_template('finance/financial/expense_receipt.html', expense=expense)
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Expense receipt error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)})

@finance_bp.route('/expenses/analysis')
@role_required([Roles.SUPER_HQ, Roles.HQ_FINANCE])
def expense_analysis():
    try:
        # Get date range from request or default to current year
        year = request.args.get('year', datetime.now().year, type=int)
        
        # Monthly expenses for the selected year
        monthly_expenses = db.session.query(
            func.extract('month', Expense.date).label('month'),
            func.sum(Expense.amount).label('total')
        ).filter(
            func.extract('year', Expense.date) == year,
            Expense.status == 'paid'
        ).group_by('month').order_by('month').all()
        
        # Expenses by category for the selected year
        category_expenses = db.session.query(
            Expense.category,
            func.sum(Expense.amount).label('total')
        ).filter(
            func.extract('year', Expense.date) == year,
            Expense.status == 'paid'
        ).group_by(Expense.category).order_by(desc('total')).all()
        
        # Year-over-year comparison
        prev_year = year - 1
        current_year_total = db.session.query(func.sum(Expense.amount)).filter(
            func.extract('year', Expense.date) == year,
            Expense.status == 'paid'
        ).scalar() or 0
        
        prev_year_total = db.session.query(func.sum(Expense.amount)).filter(
            func.extract('year', Expense.date) == prev_year,
            Expense.status == 'paid'
        ).scalar() or 0
        
        yoy_change = 0
        if prev_year_total > 0:
            yoy_change = ((current_year_total - prev_year_total) / prev_year_total) * 100
        
        analysis = {
            'monthly_expenses': [{'month': int(me[0]), 'total': float(me[1])} for me in monthly_expenses],
            'category_expenses': [{'category': ce[0] or 'Uncategorized', 'total': float(ce[1])} for ce in category_expenses],
            'yearly_totals': {
                'current_year': current_year_total,
                'prev_year': prev_year_total,
                'yoy_change': yoy_change
            },
            'selected_year': year
        }
        
        return render_template('finance/financial/expense_analysis.html', analysis=analysis)
    except Exception as e:
        current_app.logger.error(f"Expense analysis error: {str(e)}")
        flash('Error loading expense analysis', 'error')
        return redirect(url_for('finance.expenses'))

# Reports and Analytics
@finance_bp.route('/reports')
@role_required([Roles.SUPER_HQ, Roles.HQ_FINANCE])
def reports():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        report_type = request.args.get('type', 'all')
        
        query = Report.query
        
        if report_type != 'all':
            query = query.filter(Report.report_type == report_type)
            
        reports = query.order_by(desc(Report.date)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return render_template('finance/reports/index.html', 
                             reports=reports,
                             report_type=report_type)
    except Exception as e:
        current_app.logger.error(f"Reports loading error: {str(e)}")
        flash('Error loading reports', 'error')
        return render_template('error.html'), 500

@finance_bp.route('/api/financial-summary')
@role_required([Roles.SUPER_HQ, Roles.HQ_FINANCE])
def financial_summary():
    try:
        month = request.args.get('month', datetime.now().month, type=int)
        year = request.args.get('year', datetime.now().year, type=int)
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(days=1)

        # Completed income/expense
        total_income = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.type == 'income',
            Transaction.status == 'completed',
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).scalar() or 0
        total_expense = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.type == 'expense',
            Transaction.status == 'completed',
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).scalar() or 0

        # Outstanding income/expense
        outstanding_income = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.type == 'income',
            Transaction.status == 'pending',
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).scalar() or 0
        outstanding_expense = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.type == 'expense',
            Transaction.status == 'pending',
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).scalar() or 0

        # Cash flow
        cash_flow = total_income - total_expense

        # Expense breakdown by category (for Chart.js)
        category_breakdown = db.session.query(
            Transaction.category,
            func.sum(Transaction.amount).label('total')
        ).filter(
            Transaction.type == 'expense',
            Transaction.status == 'completed',
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).group_by(Transaction.category).all()
        expense_labels = [c[0] or 'Uncategorized' for c in category_breakdown]
        expense_data = [float(c[1]) for c in category_breakdown]

        # Income breakdown by category (for Chart.js)
        income_breakdown = db.session.query(
            Transaction.category,
            func.sum(Transaction.amount).label('total')
        ).filter(
            Transaction.type == 'income',
            Transaction.status == 'completed',
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).group_by(Transaction.category).all()
        income_labels = [c[0] or 'Uncategorized' for c in income_breakdown]
        income_data = [float(c[1]) for c in income_breakdown]

        # Monthly trend for Chart.js (income/expense per day)
        days_in_month = (end_date - start_date).days + 1
        daily_income = [0] * days_in_month
        daily_expense = [0] * days_in_month
        for day in range(days_in_month):
            day_date = start_date + timedelta(days=day)
            income = db.session.query(func.sum(Transaction.amount)).filter(
                Transaction.type == 'income',
                Transaction.status == 'completed',
                func.date(Transaction.date) == day_date.date()
            ).scalar() or 0
            expense = db.session.query(func.sum(Transaction.amount)).filter(
                Transaction.type == 'expense',
                Transaction.status == 'completed',
                func.date(Transaction.date) == day_date.date()
            ).scalar() or 0
            daily_income[day] = float(income)
            daily_expense[day] = float(expense)
        daily_labels = [(start_date + timedelta(days=day)).strftime('%Y-%m-%d') for day in range(days_in_month)]

        summary = {
            'month': month,
            'year': year,
            'total_income': total_income,
            'total_expense': total_expense,
            'outstanding_income': outstanding_income,
            'outstanding_expense': outstanding_expense,
            'cash_flow': cash_flow,
            'expense_chart': {
                'labels': expense_labels,
                'datasets': [{
                    'label': 'Expenses by Category',
                    'data': expense_data
                }]
            },
            'income_chart': {
                'labels': income_labels,
                'datasets': [{
                    'label': 'Income by Category',
                    'data': income_data
                }]
            },
            'trend_chart': {
                'labels': daily_labels,
                'datasets': [
                    {'label': 'Daily Income', 'data': daily_income},
                    {'label': 'Daily Expense', 'data': daily_expense}
                ]
            }
        }
        return jsonify({'status': 'success', 'summary': summary})
    except Exception as e:
        current_app.logger.error(f"Financial summary error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)})

@finance_bp.route('/bank-reconciliation')
@role_required([Roles.SUPER_HQ, Roles.HQ_FINANCE])
def bank_reconciliation():
    return render_template('finance/bank_reconciliation.html')

@finance_bp.route('/settings')
@role_required([Roles.SUPER_HQ, Roles.HQ_FINANCE])
def settings():
    return render_template('finance/settings.html')

@finance_bp.route('/logout')
@role_required([Roles.SUPER_HQ, Roles.HQ_FINANCE])
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))