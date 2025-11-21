"""
Script to add all missing CRUD endpoints for finance modules
Run this to add delete/edit endpoints for all finance features
"""

# Add these endpoints to app.py after the existing finance manager routes

ENDPOINTS_TO_ADD = """

# ============= BUDGET CRUD OPERATIONS =============
@app.route('/finance/manager/budgets/<int:budget_id>/view', methods=['GET'], endpoint='finance_mgr.view_budget')
@role_required([Roles.HQ_FINANCE, Roles.SUPER_HQ])
def view_budget(budget_id):
    budget = Budget.query.get_or_404(budget_id)
    return jsonify({
        'id': budget.id,
        'budget_code': budget.budget_code,
        'budget_name': budget.budget_name,
        'budget_type': budget.budget_type,
        'fiscal_year': budget.fiscal_year,
        'total_budget': budget.total_budget,
        'spent_amount': budget.spent_amount,
        'committed_amount': budget.committed_amount,
        'available_amount': budget.available_amount,
        'status': budget.status,
        'start_date': budget.start_date.strftime('%Y-%m-%d'),
        'end_date': budget.end_date.strftime('%Y-%m-%d'),
        'description': budget.description or '',
        'department': budget.department or ''
    })

@app.route('/finance/manager/budgets/<int:budget_id>/delete', methods=['POST', 'DELETE'], endpoint='finance_mgr.delete_budget')
@role_required([Roles.HQ_FINANCE, Roles.SUPER_HQ])
def delete_budget(budget_id):
    try:
        budget = Budget.query.get_or_404(budget_id)
        db.session.delete(budget)
        db.session.commit()
        if request.is_json:
            return jsonify({'status': 'success', 'message': 'Budget deleted successfully'})
        flash('Budget deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({'status': 'error', 'message': str(e)}), 400
        flash(f'Error deleting budget: {str(e)}', 'error')
    return redirect(url_for('finance_mgr.budgets'))

# ============= CASH FLOW FORECAST CRUD OPERATIONS =============
@app.route('/finance/manager/cashflow/<int:forecast_id>/delete', methods=['POST', 'DELETE'], endpoint='finance_mgr.delete_cashflow')
@role_required([Roles.HQ_FINANCE, Roles.SUPER_HQ])
def delete_cashflow(forecast_id):
    try:
        forecast = CashFlowForecast.query.get_or_404(forecast_id)
        db.session.delete(forecast)
        db.session.commit()
        if request.is_json:
            return jsonify({'status': 'success', 'message': 'Cash flow forecast deleted successfully'})
        flash('Cash flow forecast deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({'status': 'error', 'message': str(e)}), 400
        flash(f'Error deleting forecast: {str(e)}', 'error')
    return redirect(url_for('finance_mgr.cashflow'))

# ============= INVOICE CRUD OPERATIONS =============
@app.route('/finance/manager/invoices/<int:invoice_id>/view', methods=['GET'], endpoint='finance_mgr.view_invoice')
@role_required([Roles.HQ_FINANCE, Roles.SUPER_HQ])
def view_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    return jsonify({
        'id': invoice.id,
        'invoice_number': invoice.invoice_number,
        'client_name': invoice.client_name,
        'issue_date': invoice.issue_date.strftime('%Y-%m-%d'),
        'due_date': invoice.due_date.strftime('%Y-%m-%d'),
        'subtotal': invoice.subtotal,
        'tax_amount': invoice.tax_amount,
        'total_amount': invoice.total_amount,
        'status': invoice.status,
        'notes': invoice.notes or ''
    })

@app.route('/finance/manager/invoices/<int:invoice_id>/delete', methods=['POST', 'DELETE'], endpoint='finance_mgr.delete_invoice')
@role_required([Roles.HQ_FINANCE, Roles.SUPER_HQ])
def delete_invoice(invoice_id):
    try:
        invoice = Invoice.query.get_or_404(invoice_id)
        db.session.delete(invoice)
        db.session.commit()
        if request.is_json:
            return jsonify({'status': 'success', 'message': 'Invoice deleted successfully'})
        flash('Invoice deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({'status': 'error', 'message': str(e)}), 400
        flash(f'Error deleting invoice: {str(e)}', 'error')
    return redirect(url_for('finance_mgr.invoices'))

# ============= PAYMENT CRUD OPERATIONS =============
@app.route('/finance/manager/payments/<int:payment_id>/view', methods=['GET'], endpoint='finance_mgr.view_payment')
@role_required([Roles.HQ_FINANCE, Roles.SUPER_HQ])
def view_payment(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    return jsonify({
        'id': payment.id,
        'payment_number': payment.payment_number,
        'payment_date': payment.payment_date.strftime('%Y-%m-%d'),
        'amount': payment.amount,
        'payment_method': payment.payment_method,
        'reference_number': payment.reference_number or '',
        'payee_name': payment.payee_name,
        'status': payment.status,
        'notes': payment.notes or ''
    })

@app.route('/finance/manager/payments/<int:payment_id>/delete', methods=['POST', 'DELETE'], endpoint='finance_mgr.delete_payment')
@role_required([Roles.HQ_FINANCE, Roles.SUPER_HQ])
def delete_payment(payment_id):
    try:
        payment = Payment.query.get_or_404(payment_id)
        db.session.delete(payment)
        db.session.commit()
        if request.is_json:
            return jsonify({'status': 'success', 'message': 'Payment deleted successfully'})
        flash('Payment deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({'status': 'error', 'message': str(e)}), 400
        flash(f'Error deleting payment: {str(e)}', 'error')
    return redirect(url_for('finance_mgr.payments'))

# ============= ACCOUNTS RECEIVABLE CRUD OPERATIONS =============
@app.route('/finance/manager/receivables/<int:receivable_id>/edit', methods=['POST'], endpoint='finance_mgr.edit_receivable')
@role_required([Roles.HQ_FINANCE, Roles.SUPER_HQ])
def edit_receivable(receivable_id):
    try:
        receivable = AccountsReceivable.query.get_or_404(receivable_id)
        data = request.form
        
        receivable.customer_name = data.get('customer_name', receivable.customer_name)
        receivable.amount_due = float(data.get('amount_due', receivable.amount_due))
        receivable.amount_paid = float(data.get('amount_paid', receivable.amount_paid))
        receivable.due_date = datetime.strptime(data.get('due_date'), '%Y-%m-%d').date()
        receivable.status = data.get('status', receivable.status)
        receivable.notes = data.get('notes')
        
        db.session.commit()
        flash('Receivable updated successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating receivable: {str(e)}', 'error')
    return redirect(url_for('finance_mgr.receivables'))

@app.route('/finance/manager/receivables/<int:receivable_id>/delete', methods=['POST', 'DELETE'], endpoint='finance_mgr.delete_receivable')
@role_required([Roles.HQ_FINANCE, Roles.SUPER_HQ])
def delete_receivable(receivable_id):
    try:
        receivable = AccountsReceivable.query.get_or_404(receivable_id)
        db.session.delete(receivable)
        db.session.commit()
        if request.is_json:
            return jsonify({'status': 'success', 'message': 'Receivable deleted successfully'})
        flash('Receivable deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({'status': 'error', 'message': str(e)}), 400
        flash(f'Error deleting receivable: {str(e)}', 'error')
    return redirect(url_for('finance_mgr.receivables'))

# ============= ACCOUNTS PAYABLE CRUD OPERATIONS =============
@app.route('/finance/manager/payables/<int:payable_id>/view', methods=['GET'], endpoint='finance_mgr.view_payable')
@role_required([Roles.HQ_FINANCE, Roles.SUPER_HQ])
def view_payable(payable_id):
    payable = AccountsPayable.query.get_or_404(payable_id)
    return jsonify({
        'id': payable.id,
        'vendor_name': payable.vendor_name,
        'invoice_number': payable.invoice_number,
        'amount_due': payable.amount_due,
        'amount_paid': payable.amount_paid,
        'due_date': payable.due_date.strftime('%Y-%m-%d'),
        'status': payable.status,
        'description': payable.description or ''
    })

@app.route('/finance/manager/payables/<int:payable_id>/delete', methods=['POST', 'DELETE'], endpoint='finance_mgr.delete_payable')
@role_required([Roles.HQ_FINANCE, Roles.SUPER_HQ])
def delete_payable(payable_id):
    try:
        payable = AccountsPayable.query.get_or_404(payable_id)
        db.session.delete(payable)
        db.session.commit()
        if request.is_json:
            return jsonify({'status': 'success', 'message': 'Payable deleted successfully'})
        flash('Payable deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({'status': 'error', 'message': str(e)}), 400
        flash(f'Error deleting payable: {str(e)}', 'error')
    return redirect(url_for('finance_mgr.payables'))

# ============= FINANCIAL TRANSACTION CRUD OPERATIONS =============
@app.route('/finance/manager/transactions/<int:transaction_id>/view', methods=['GET'], endpoint='finance_mgr.view_transaction')
@role_required([Roles.HQ_FINANCE, Roles.SUPER_HQ])
def view_transaction(transaction_id):
    transaction = FinancialTransaction.query.get_or_404(transaction_id)
    return jsonify({
        'id': transaction.id,
        'transaction_number': transaction.transaction_number,
        'transaction_date': transaction.transaction_date.strftime('%Y-%m-%d'),
        'transaction_type': transaction.transaction_type,
        'account': transaction.account,
        'debit_amount': transaction.debit_amount,
        'credit_amount': transaction.credit_amount,
        'description': transaction.description or '',
        'reference': transaction.reference or ''
    })

@app.route('/finance/manager/transactions/<int:transaction_id>/delete', methods=['POST', 'DELETE'], endpoint='finance_mgr.delete_transaction')
@role_required([Roles.HQ_FINANCE, Roles.SUPER_HQ])
def delete_transaction(transaction_id):
    try:
        transaction = FinancialTransaction.query.get_or_404(transaction_id)
        db.session.delete(transaction)
        db.session.commit()
        if request.is_json:
            return jsonify({'status': 'success', 'message': 'Transaction deleted successfully'})
        flash('Transaction deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({'status': 'error', 'message': str(e)}), 400
        flash(f'Error deleting transaction: {str(e)}', 'error')
    return redirect(url_for('finance_mgr.transactions'))

# ============= EXPENSE CRUD OPERATIONS =============
@app.route('/finance/expenses/<int:expense_id>/view', methods=['GET'], endpoint='finance.view_expense')
@role_required([Roles.HQ_FINANCE, Roles.SUPER_HQ])
def view_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    return jsonify({
        'id': expense.id,
        'description': expense.description,
        'amount': expense.amount,
        'category': expense.category,
        'date': expense.date.strftime('%Y-%m-%d'),
        'status': expense.status
    })

@app.route('/finance/expenses/<int:expense_id>/delete', methods=['POST', 'DELETE'], endpoint='finance.delete_expense')
@role_required([Roles.HQ_FINANCE, Roles.SUPER_HQ])
def delete_expense(expense_id):
    try:
        expense = Expense.query.get_or_404(expense_id)
        db.session.delete(expense)
        db.session.commit()
        if request.is_json:
            return jsonify({'status': 'success', 'message': 'Expense deleted successfully'})
        flash('Expense deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({'status': 'error', 'message': str(e)}), 400
        flash(f'Error deleting expense: {str(e)}', 'error')
    return redirect(url_for('finance.expenses'))

# ============= BANK ACCOUNT CRUD OPERATIONS =============
@app.route('/finance/bank-accounts/create', methods=['POST'], endpoint='finance.create_bank_account')
@role_required([Roles.HQ_FINANCE, Roles.SUPER_HQ])
def create_bank_account():
    try:
        data = request.form
        account = BankAccount(
            account_name=data.get('account_name'),
            account_number=data.get('account_number'),
            bank_name=data.get('bank_name'),
            account_type=data.get('account_type'),
            current_balance=float(data.get('current_balance', 0)),
            currency=data.get('currency', 'NGN')
        )
        db.session.add(account)
        db.session.commit()
        flash('Bank account created successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating bank account: {str(e)}', 'error')
    return redirect(url_for('finance.bank_reconciliation'))

@app.route('/finance/bank-accounts/<int:account_id>/delete', methods=['POST', 'DELETE'], endpoint='finance.delete_bank_account')
@role_required([Roles.HQ_FINANCE, Roles.SUPER_HQ])
def delete_bank_account(account_id):
    try:
        account = BankAccount.query.get_or_404(account_id)
        db.session.delete(account)
        db.session.commit()
        flash('Bank account deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting bank account: {str(e)}', 'error')
    return redirect(url_for('finance.bank_reconciliation'))

@app.route('/finance/bank-transactions/create', methods=['POST'], endpoint='finance.create_bank_transaction')
@role_required([Roles.HQ_FINANCE, Roles.SUPER_HQ])
def create_bank_transaction():
    try:
        data = request.form
        transaction = BankTransaction(
            account_id=int(data.get('account_id')),
            transaction_date=datetime.strptime(data.get('transaction_date'), '%Y-%m-%d').date(),
            description=data.get('description'),
            transaction_type=data.get('transaction_type'),
            amount=float(data.get('amount')),
            reference=data.get('reference')
        )
        db.session.add(transaction)
        
        # Update account balance
        account = BankAccount.query.get(transaction.account_id)
        if transaction.transaction_type == 'credit':
            account.current_balance += transaction.amount
        else:
            account.current_balance -= transaction.amount
        
        db.session.commit()
        flash('Bank transaction recorded successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating transaction: {str(e)}', 'error')
    return redirect(url_for('finance.bank_reconciliation'))

@app.route('/finance/bank-transactions/<int:transaction_id>/delete', methods=['POST', 'DELETE'], endpoint='finance.delete_bank_transaction')
@role_required([Roles.HQ_FINANCE, Roles.SUPER_HQ])
def delete_bank_transaction(transaction_id):
    try:
        transaction = BankTransaction.query.get_or_404(transaction_id)
        
        # Reverse account balance
        account = BankAccount.query.get(transaction.account_id)
        if transaction.transaction_type == 'credit':
            account.current_balance -= transaction.amount
        else:
            account.current_balance += transaction.amount
        
        db.session.delete(transaction)
        db.session.commit()
        flash('Bank transaction deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting transaction: {str(e)}', 'error')
    return redirect(url_for('finance.bank_reconciliation'))
"""

print("=" * 80)
print("FINANCE MODULE - CRUD ENDPOINTS TO ADD")
print("=" * 80)
print("\nAdd the following code to app.py after the existing finance manager routes:")
print(ENDPOINTS_TO_ADD)
print("\n" + "=" * 80)
print("These endpoints provide full CRUD operations for all finance modules")
print("=" * 80)
