from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models.chama import Chama, ChamaMember, RecurringPayment, Contribution
from app.models.user import User
from app import db
from datetime import datetime, timedelta
import json

# Optional dateutil import - graceful fallback if not available
try:
    from dateutil.relativedelta import relativedelta
    DATEUTIL_AVAILABLE = True
except ImportError:
    DATEUTIL_AVAILABLE = False
    
    def add_months(date, months):
        """Fallback function to add months to a date"""
        month = date.month - 1 + months
        year = date.year + month // 12
        month = month % 12 + 1
        day = min(date.day, [31,
            29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
            31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month-1])
        return date.replace(year=year, month=month, day=day)
    
    def add_years(date, years):
        """Fallback function to add years to a date"""
        try:
            return date.replace(year=date.year + years)
        except ValueError:  # leap year edge case
            return date.replace(year=date.year + years, day=28)
    
    # Create a simple relativedelta replacement
    class relativedelta:
        def __init__(self, months=0, years=0, days=0):
            self.months = months
            self.years = years
            self.days = days
        
        def __radd__(self, other):
            if isinstance(other, datetime):
                result = other
                if self.years:
                    result = add_years(result, self.years)
                if self.months:
                    result = add_months(result, self.months)
                if self.days:
                    result = result + timedelta(days=self.days)
                return result
            return NotImplemented

recurring_bp = Blueprint('recurring', __name__)

@recurring_bp.route('/chama/<int:chama_id>/recurring-payments')
@login_required
def chama_recurring_payments(chama_id):
    """View recurring payments for a chama"""
    chama = Chama.query.get_or_404(chama_id)
    
    # Check if user is a member
    member = ChamaMember.query.filter_by(
        user_id=current_user.id,
        chama_id=chama_id
    ).first()
    
    if not member:
        flash('You are not a member of this chama.', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Get recurring payments based on role
    if member.role in ['admin', 'treasurer']:
        recurring_payments = RecurringPayment.query.filter_by(chama_id=chama_id).all()
    else:
        recurring_payments = RecurringPayment.query.filter_by(
            chama_id=chama_id,
            user_id=current_user.id
        ).all()
    
    return render_template('recurring/list.html', 
                         chama=chama, 
                         recurring_payments=recurring_payments, 
                         member=member)

@recurring_bp.route('/chama/<int:chama_id>/recurring-payments/create', methods=['GET', 'POST'])
@login_required
def create_recurring_payment(chama_id):
    """Create a new recurring payment"""
    chama = Chama.query.get_or_404(chama_id)
    
    # Check if user is a member
    member = ChamaMember.query.filter_by(
        user_id=current_user.id,
        chama_id=chama_id
    ).first()
    
    if not member:
        flash('You are not a member of this chama.', 'error')
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        try:
            amount = float(request.form['amount'])
            payment_type = request.form['payment_type']
            frequency = request.form['frequency']
            start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
            end_date_str = request.form.get('end_date')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else None
            description = request.form.get('description', '')
            
            # Calculate next payment date
            next_payment_date = start_date
            if frequency == 'weekly':
                next_payment_date = start_date + timedelta(weeks=1)
            elif frequency == 'monthly':
                next_payment_date = start_date + relativedelta(months=1)
            elif frequency == 'quarterly':
                next_payment_date = start_date + relativedelta(months=3)
            elif frequency == 'yearly':
                next_payment_date = start_date + relativedelta(years=1)
            
            recurring_payment = RecurringPayment(
                chama_id=chama_id,
                user_id=current_user.id,
                amount=amount,
                payment_type=payment_type,
                frequency=frequency,
                start_date=start_date,
                end_date=end_date,
                next_payment_date=next_payment_date,
                description=description,
                is_active=True
            )
            
            db.session.add(recurring_payment)
            db.session.commit()
            
            flash('Recurring payment created successfully!', 'success')
            return redirect(url_for('recurring.chama_recurring_payments', chama_id=chama_id))
            
        except ValueError as e:
            flash('Invalid input. Please check your data.', 'error')
        except Exception as e:
            flash(f'Error creating recurring payment: {str(e)}', 'error')
    
    return render_template('recurring/create.html', chama=chama, member=member)

@recurring_bp.route('/recurring-payment/<int:payment_id>/toggle', methods=['POST'])
@login_required
def toggle_recurring_payment(payment_id):
    """Toggle recurring payment active status"""
    recurring_payment = RecurringPayment.query.get_or_404(payment_id)
    
    # Check if user has permission
    if recurring_payment.user_id != current_user.id:
        member = ChamaMember.query.filter_by(
            user_id=current_user.id,
            chama_id=recurring_payment.chama_id
        ).first()
        
        if not member or member.role not in ['admin', 'treasurer']:
            return jsonify({'error': 'Permission denied'}), 403
    
    recurring_payment.is_active = not recurring_payment.is_active
    db.session.commit()
    
    status = 'activated' if recurring_payment.is_active else 'deactivated'
    flash(f'Recurring payment {status} successfully!', 'success')
    
    return jsonify({'success': True, 'is_active': recurring_payment.is_active})

@recurring_bp.route('/recurring-payment/<int:payment_id>/delete', methods=['POST'])
@login_required
def delete_recurring_payment(payment_id):
    """Delete a recurring payment"""
    recurring_payment = RecurringPayment.query.get_or_404(payment_id)
    
    # Check if user has permission
    if recurring_payment.user_id != current_user.id:
        member = ChamaMember.query.filter_by(
            user_id=current_user.id,
            chama_id=recurring_payment.chama_id
        ).first()
        
        if not member or member.role not in ['admin', 'treasurer']:
            return jsonify({'error': 'Permission denied'}), 403
    
    chama_id = recurring_payment.chama_id
    db.session.delete(recurring_payment)
    db.session.commit()
    
    flash('Recurring payment deleted successfully!', 'success')
    return redirect(url_for('recurring.chama_recurring_payments', chama_id=chama_id))

@recurring_bp.route('/recurring-payment/<int:payment_id>/execute', methods=['POST'])
@login_required
def execute_recurring_payment(payment_id):
    """Execute a recurring payment (create contribution)"""
    recurring_payment = RecurringPayment.query.get_or_404(payment_id)
    
    # Check if user has permission
    if recurring_payment.user_id != current_user.id:
        member = ChamaMember.query.filter_by(
            user_id=current_user.id,
            chama_id=recurring_payment.chama_id
        ).first()
        
        if not member or member.role not in ['admin', 'treasurer']:
            return jsonify({'error': 'Permission denied'}), 403
    
    try:
        # Create contribution
        contribution = Contribution(
            chama_id=recurring_payment.chama_id,
            user_id=recurring_payment.user_id,
            amount=recurring_payment.amount,
            type=recurring_payment.payment_type,
            status='pending',
            description=f"Auto-generated from recurring payment: {recurring_payment.description}"
        )
        
        db.session.add(contribution)
        
        # Update next payment date
        if recurring_payment.frequency == 'weekly':
            recurring_payment.next_payment_date = recurring_payment.next_payment_date + timedelta(weeks=1)
        elif recurring_payment.frequency == 'monthly':
            recurring_payment.next_payment_date = recurring_payment.next_payment_date + relativedelta(months=1)
        elif recurring_payment.frequency == 'quarterly':
            recurring_payment.next_payment_date = recurring_payment.next_payment_date + relativedelta(months=3)
        elif recurring_payment.frequency == 'yearly':
            recurring_payment.next_payment_date = recurring_payment.next_payment_date + relativedelta(years=1)
        
        # Check if recurring payment should be deactivated
        if recurring_payment.end_date and recurring_payment.next_payment_date > recurring_payment.end_date:
            recurring_payment.is_active = False
        
        db.session.commit()
        
        flash('Recurring payment executed successfully!', 'success')
        return jsonify({'success': True, 'contribution_id': contribution.id})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error executing payment: {str(e)}'}), 500

@recurring_bp.route('/my-recurring-payments')
@login_required
def my_recurring_payments():
    """View user's recurring payments across all chamas"""
    recurring_payments = RecurringPayment.query.filter_by(user_id=current_user.id).all()
    return render_template('recurring/my_recurring.html', recurring_payments=recurring_payments)

@recurring_bp.route('/api/recurring-payments/due')
@login_required
def get_due_recurring_payments():
    """Get recurring payments that are due"""
    today = datetime.now().date()
    
    due_payments = RecurringPayment.query.filter(
        RecurringPayment.user_id == current_user.id,
        RecurringPayment.is_active == True,
        RecurringPayment.next_payment_date <= today
    ).all()
    
    return jsonify({
        'due_payments': [{
            'id': payment.id,
            'chama_name': payment.chama.name,
            'amount': payment.amount,
            'payment_type': payment.payment_type,
            'next_payment_date': payment.next_payment_date.isoformat(),
            'description': payment.description
        } for payment in due_payments]
    })

@recurring_bp.route('/api/recurring-payments/reminders')
@login_required
def get_payment_reminders():
    """Get upcoming payment reminders"""
    today = datetime.now().date()
    reminder_date = today + timedelta(days=3)  # 3 days ahead
    
    upcoming_payments = RecurringPayment.query.filter(
        RecurringPayment.user_id == current_user.id,
        RecurringPayment.is_active == True,
        RecurringPayment.next_payment_date > today,
        RecurringPayment.next_payment_date <= reminder_date
    ).all()
    
    return jsonify({
        'upcoming_payments': [{
            'id': payment.id,
            'chama_name': payment.chama.name,
            'amount': payment.amount,
            'payment_type': payment.payment_type,
            'next_payment_date': payment.next_payment_date.isoformat(),
            'description': payment.description,
            'days_until_due': (payment.next_payment_date - today).days
        } for payment in upcoming_payments]
    })
