from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user

lending_bp = Blueprint('lending', __name__, url_prefix='/lending')

@lending_bp.route('/')
@login_required
def lending_dashboard():
    """Lending dashboard: view and manage loans."""
    # TODO: Query loans for current user
    return render_template('lending/dashboard.html', loans=[])

@lending_bp.route('/request', methods=['GET', 'POST'])
@login_required
def request_loan():
    """Request a new loan from group members."""
    if request.method == 'POST':
        # TODO: Save loan request
        flash('Loan request submitted.', 'success')
        return redirect(url_for('lending.lending_dashboard'))
    return render_template('lending/request.html')

@lending_bp.route('/approve/<int:loan_id>')
@login_required
def approve_loan(loan_id):
    """Approve a member loan request."""
    # TODO: Approve loan in DB
    flash('Loan approved.', 'success')
    return redirect(url_for('lending.lending_dashboard'))

@lending_bp.route('/repay/<int:loan_id>', methods=['POST'])
@login_required
def repay_loan(loan_id):
    """Repay a loan."""
    # TODO: Process repayment
    flash('Loan repayment successful.', 'success')
    return redirect(url_for('lending.lending_dashboard'))
