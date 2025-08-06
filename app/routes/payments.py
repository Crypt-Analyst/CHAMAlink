from flask import Blueprint, render_template, request, jsonify, make_response, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import (
    Chama, Transaction, Contribution, LoanApplication, 
    Penalty, MpesaTransaction, User
)
from app.models.chama import chama_members as chama_members_table  # Import with alias to avoid conflicts
from app.utils.permissions import chama_member_required
from app import db
from datetime import datetime, timedelta
import csv
import io
from sqlalchemy import func, or_, and_

payments_bp = Blueprint('payments', __name__, url_prefix='/payments')

@payments_bp.route('/chama/<int:chama_id>/comprehensive-history')
@login_required
@chama_member_required
def comprehensive_history(chama_id):
    """Enhanced comprehensive payment history with advanced filtering and analytics"""
    chama = Chama.query.get_or_404(chama_id)
    
    # Check if user is a member
    member = db.session.query(chama_members_table).filter(
        chama_members_table.c.user_id == current_user.id,
        chama_members_table.c.chama_id == chama_id
    ).first()
    
    if not member:
        flash('You are not a member of this chama.', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Get all chama members for filtering (admin/treasurer only)
    members_list = []
    if member.role in ['admin', 'treasurer']:
        # Get all members with their user details
        members_with_users = db.session.query(
            User, chama_members_table.c.role, chama_members_table.c.joined_at
        ).join(chama_members_table, User.id == chama_members_table.c.user_id).filter(
            chama_members_table.c.chama_id == chama_id
        ).all()
        members_list = members_with_users
    
    # Get comprehensive payment data
    all_payments = get_comprehensive_payment_data(chama_id, member)
    
    # Calculate payment summary
    payment_summary = calculate_payment_summary(all_payments)
    
    return render_template('payments/comprehensive_history.html',
                         chama=chama,
                         member=member,
                         all_payments=all_payments,
                         payment_summary=payment_summary,
                         chama_members=members_list)

@payments_bp.route('/chama/<int:chama_id>/payment-analytics')
@login_required
@chama_member_required
def payment_analytics(chama_id):
    """Advanced payment analytics dashboard"""
    chama = Chama.query.get_or_404(chama_id)
    
    # Check if user is a member
    member = db.session.query(chama_members_table).filter(
        chama_members_table.c.user_id == current_user.id,
        chama_members_table.c.chama_id == chama_id
    ).first()
    
    if not member:
        flash('You are not a member of this chama.', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Get analytics data
    analytics_data = generate_payment_analytics(chama_id, member)
    
    return render_template('payments/analytics.html',
                         chama=chama,
                         member=member,
                         analytics=analytics_data)

@payments_bp.route('/chama/<int:chama_id>/export-comprehensive')
@login_required
@chama_member_required
def export_comprehensive_history(chama_id):
    """Export comprehensive payment history as CSV"""
    chama = Chama.query.get_or_404(chama_id)
    
    # Check if user is a member
    member = db.session.query(chama_members_table).filter(
        chama_members_table.c.user_id == current_user.id,
        chama_members_table.c.chama_id == chama_id
    ).first()
    
    if not member:
        flash('You are not a member of this chama.', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Get comprehensive payment data
    all_payments = get_comprehensive_payment_data(chama_id, member)
    
    # Generate CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write headers
    headers = ['Date', 'Time', 'Type', 'Amount', 'Method', 'Status', 
               'Transaction ID', 'Description']
    if member.role in ['admin', 'treasurer']:
        headers.insert(2, 'Member')
    
    writer.writerow(headers)
    
    # Write data
    for payment in all_payments:
        row = [
            payment.created_at.strftime('%Y-%m-%d'),
            payment.created_at.strftime('%H:%M:%S'),
            payment.type.replace('_', ' ').title(),
            f'KES {payment.amount:,.2f}',
            (payment.payment_method or 'Unknown').title(),
            payment.status.title(),
            payment.transaction_id or payment.mpesa_receipt_number or 'N/A',
            payment.description or ''
        ]
        
        if member.role in ['admin', 'treasurer']:
            row.insert(2, payment.user.full_name if payment.user else 'System')
        
        writer.writerow(row)
    
    output.seek(0)
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename={chama.name}_comprehensive_payment_history.csv'
    
    return response

@payments_bp.route('/api/payment-details/<int:payment_id>')
@login_required
def get_payment_details(payment_id):
    """Get detailed payment information"""
    try:
        # Try to find payment in different tables
        payment = None
        payment_type = None
        
        # Check contributions
        payment = Contribution.query.get(payment_id)
        if payment:
            payment_type = 'contribution'
        
        # Check transactions
        if not payment:
            payment = Transaction.query.get(payment_id)
            if payment:
                payment_type = 'transaction'
        
        # Check M-Pesa transactions
        if not payment:
            mpesa_payment = MpesaTransaction.query.get(payment_id)
            if mpesa_payment:
                payment = mpesa_payment
                payment_type = 'mpesa'
        
        if not payment:
            return jsonify({'error': 'Payment not found'}), 404
        
        # Generate HTML for payment details
        html = generate_payment_details_html(payment, payment_type)
        
        return jsonify({'html': html})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_comprehensive_payment_data(chama_id, member):
    """Get all payment-related data for comprehensive tracking"""
    all_payments = []
    
    # Get contributions
    contribution_query = Contribution.query.filter_by(chama_id=chama_id)
    if member.role not in ['admin', 'treasurer']:
        contribution_query = contribution_query.filter_by(user_id=current_user.id)
    
    contributions = contribution_query.order_by(Contribution.created_at.desc()).all()
    
    # Get loan transactions (repayments and disbursements)
    transaction_query = Transaction.query.filter_by(chama_id=chama_id).filter(
        Transaction.type.in_(['loan_repayment', 'loan_disbursement', 'penalty_payment'])
    )
    if member.role not in ['admin', 'treasurer']:
        transaction_query = transaction_query.filter_by(user_id=current_user.id)
    
    transactions = transaction_query.order_by(Transaction.created_at.desc()).all()
    
    # Get M-Pesa transactions
    mpesa_query = MpesaTransaction.query.filter_by(chama_id=chama_id)
    if member.role not in ['admin', 'treasurer']:
        mpesa_query = mpesa_query.filter_by(user_id=current_user.id)
    
    mpesa_transactions = mpesa_query.order_by(MpesaTransaction.created_at.desc()).all()
    
    # Combine all payments
    all_payments.extend(contributions)
    all_payments.extend(transactions)
    
    # Add M-Pesa transactions that don't have corresponding contributions/transactions
    for mpesa in mpesa_transactions:
        if not any(p.transaction_id == mpesa.checkout_request_id for p in all_payments):
            all_payments.append(mpesa)
    
    # Sort by date (most recent first)
    all_payments.sort(key=lambda x: x.created_at, reverse=True)
    
    return all_payments

def calculate_payment_summary(payments):
    """Calculate summary statistics for payments"""
    summary = {
        'total_contributions': 0,
        'total_loan_payments': 0,
        'total_penalties': 0,
        'total_transactions': len(payments),
        'total_amount': 0,
        'completed_payments': 0,
        'pending_payments': 0,
        'failed_payments': 0
    }
    
    for payment in payments:
        # Count by type
        if hasattr(payment, 'type'):
            if payment.type == 'contribution':
                summary['total_contributions'] += payment.amount
            elif payment.type == 'loan_repayment':
                summary['total_loan_payments'] += payment.amount
            elif payment.type == 'penalty_payment':
                summary['total_penalties'] += payment.amount
        
        # Count by status
        if hasattr(payment, 'status'):
            if payment.status == 'completed' or payment.status == 'confirmed':
                summary['completed_payments'] += 1
            elif payment.status == 'pending':
                summary['pending_payments'] += 1
            elif payment.status == 'failed':
                summary['failed_payments'] += 1
        
        # Total amount
        if hasattr(payment, 'amount'):
            summary['total_amount'] += payment.amount
    
    return summary

def generate_payment_analytics(chama_id, member):
    """Generate advanced payment analytics"""
    # Get payment data for the last year
    one_year_ago = datetime.now() - timedelta(days=365)
    
    # Monthly contribution trends
    monthly_contributions = db.session.query(
        func.date_trunc('month', Contribution.created_at).label('month'),
        func.sum(Contribution.amount).label('total'),
        func.count(Contribution.id).label('count')
    ).filter(
        Contribution.chama_id == chama_id,
        Contribution.created_at >= one_year_ago,
        Contribution.status == 'confirmed'
    ).group_by(func.date_trunc('month', Contribution.created_at)).all()
    
    # Payment method distribution
    payment_methods = db.session.query(
        func.coalesce(Transaction.payment_method, 'unknown').label('method'),
        func.count(Transaction.id).label('count'),
        func.sum(Transaction.amount).label('total')
    ).filter(
        Transaction.chama_id == chama_id,
        Transaction.created_at >= one_year_ago
    ).group_by(func.coalesce(Transaction.payment_method, 'unknown')).all()
    
    # Member payment patterns (admin/treasurer only)
    member_patterns = []
    if member.role in ['admin', 'treasurer']:
        member_patterns = db.session.query(
            User.full_name,
            func.count(Contribution.id).label('payment_count'),
            func.sum(Contribution.amount).label('total_amount'),
            func.avg(Contribution.amount).label('avg_amount')
        ).join(Contribution).filter(
            Contribution.chama_id == chama_id,
            Contribution.created_at >= one_year_ago,
            Contribution.status == 'confirmed'
        ).group_by(User.id, User.full_name).all()
    
    # Payment timing analysis
    payment_timing = db.session.query(
        func.extract('hour', Contribution.created_at).label('hour'),
        func.count(Contribution.id).label('count')
    ).filter(
        Contribution.chama_id == chama_id,
        Contribution.created_at >= one_year_ago
    ).group_by(func.extract('hour', Contribution.created_at)).all()
    
    return {
        'monthly_contributions': monthly_contributions,
        'payment_methods': payment_methods,
        'member_patterns': member_patterns,
        'payment_timing': payment_timing
    }

def generate_payment_details_html(payment, payment_type):
    """Generate HTML for payment details modal"""
    html = f"""
    <div class="row">
        <div class="col-md-6">
            <h6>Basic Information</h6>
            <table class="table table-sm">
                <tr>
                    <th>Date:</th>
                    <td>{payment.created_at.strftime('%Y-%m-%d %I:%M %p')}</td>
                </tr>
                <tr>
                    <th>Type:</th>
                    <td><span class="badge bg-primary">{payment.type.replace('_', ' ').title() if hasattr(payment, 'type') else 'Payment'}</span></td>
                </tr>
                <tr>
                    <th>Amount:</th>
                    <td><strong>KES {payment.amount:,.2f}</strong></td>
                </tr>
                <tr>
                    <th>Status:</th>
                    <td><span class="badge bg-{'success' if payment.status == 'completed' or payment.status == 'confirmed' else 'warning' if payment.status == 'pending' else 'danger'}">{payment.status.title()}</span></td>
                </tr>
            </table>
        </div>
        <div class="col-md-6">
            <h6>Transaction Details</h6>
            <table class="table table-sm">
    """
    
    if hasattr(payment, 'transaction_id') and payment.transaction_id:
        html += f"""
                <tr>
                    <th>Transaction ID:</th>
                    <td><code>{payment.transaction_id}</code></td>
                </tr>
        """
    
    if hasattr(payment, 'mpesa_receipt_number') and payment.mpesa_receipt_number:
        html += f"""
                <tr>
                    <th>M-Pesa Receipt:</th>
                    <td><code>{payment.mpesa_receipt_number}</code></td>
                </tr>
        """
    
    if hasattr(payment, 'phone_number') and payment.phone_number:
        html += f"""
                <tr>
                    <th>Phone Number:</th>
                    <td>{payment.phone_number}</td>
                </tr>
        """
    
    if hasattr(payment, 'payment_method') and payment.payment_method:
        html += f"""
                <tr>
                    <th>Payment Method:</th>
                    <td>{payment.payment_method.title()}</td>
                </tr>
        """
    
    if hasattr(payment, 'description') and payment.description:
        html += f"""
                <tr>
                    <th>Description:</th>
                    <td>{payment.description}</td>
                </tr>
        """
    
    html += """
            </table>
        </div>
    </div>
    """
    
    if hasattr(payment, 'user') and payment.user:
        html += f"""
        <div class="row mt-3">
            <div class="col-12">
                <h6>Member Information</h6>
                <table class="table table-sm">
                    <tr>
                        <th>Name:</th>
                        <td>{payment.user.full_name}</td>
                    </tr>
                    <tr>
                        <th>Phone:</th>
                        <td>{payment.user.phone_number}</td>
                    </tr>
                    <tr>
                        <th>Email:</th>
                        <td>{payment.user.email}</td>
                    </tr>
                </table>
            </div>
        </div>
        """
    
    return html
