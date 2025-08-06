from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from app.models import Chama, Transaction, Event, User
from app import db
from datetime import datetime, date, timedelta
from sqlalchemy import desc, extract

main = Blueprint('main', __name__)

@main.route('/')
def home():
    print("Home route accessed!")  # Debug print
    print("Template path: home.html")  # Debug print
    return render_template('home.html')

@main.route('/test-new-home')
def test_new_home():
    """Test route to force new template rendering"""
    return render_template('home.html')

@main.route('/debug')
def debug():
    """Debug route to check template rendering"""
    return "<h1>Debug Route Works!</h1><p>If you see this, Flask routing is working.</p>"

@main.route('/dashboard')
@login_required
def dashboard():
    # Super admins bypass subscription checks
    if not current_user.is_super_admin:
        # Check subscription status and show warnings if needed
        from app.utils.subscription_utils import check_trial_expiry, ensure_user_has_subscription
        
        # Ensure user has a subscription (create trial if needed)
        subscription = ensure_user_has_subscription(current_user)
        
        # Check if trial is expiring soon
        trial_warning = check_trial_expiry()
        if trial_warning:
            flash(f"Your free trial expires in {trial_warning['days_remaining']} days on {trial_warning['expires_on']}. Upgrade now to continue!", 'warning')
        
        # Check if subscription is expired
        if not subscription.is_active:
            flash('Your subscription has expired. Please upgrade to continue using ChamaLink.', 'danger')
            return redirect(url_for('subscription.plans'))
    
    # Get user's chamas
    user_chamas = current_user.chamas
    
    # Calculate dashboard statistics
    total_chamas = len(user_chamas)
    total_savings = sum(chama.total_balance for chama in user_chamas)
    monthly_contributions = sum(chama.monthly_contribution for chama in user_chamas)
    
    # Calculate average ROI (placeholder calculation)
    avg_roi = 8.5  # This would be calculated based on actual investment performance
    
    # Get recent transactions (last 10)
    recent_transactions = Transaction.query.join(Chama).filter(
        Chama.id.in_([chama.id for chama in user_chamas])
    ).order_by(desc(Transaction.created_at)).limit(10).all()
    
    # Get upcoming events (next 5)
    upcoming_events = Event.query.join(Chama).filter(
        Chama.id.in_([chama.id for chama in user_chamas]),
        Event.event_date >= date.today()
    ).order_by(Event.event_date).limit(5).all()
    
    return render_template('dashboard.html', 
                         user_chamas=user_chamas,
                         total_chamas=total_chamas,
                         total_savings=total_savings,
                         monthly_contributions=monthly_contributions,
                         avg_roi=avg_roi,
                         recent_transactions=recent_transactions,
                         upcoming_events=upcoming_events)

@main.route("/supabase-test")
def supabase_test():
    from app.utils.supabase_client import supabase
    try:
        result = supabase.table("test").insert({"message": "ChamaLink is live 💡"}).execute()
        return f"Inserted: {result.data}"
    except Exception as e:
        return f"Error: {e}"

@main.route('/create_chama', methods=['POST'])
@login_required
def create_chama():
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name') or not data.get('name').strip():
            return jsonify({'success': False, 'message': 'Chama name is required'}), 400
        
        if not data.get('monthly_contribution'):
            return jsonify({'success': False, 'message': 'Monthly contribution is required'}), 400
        
        # Validate contribution amount
        try:
            contribution = float(data['monthly_contribution'])
            if contribution <= 0:
                return jsonify({'success': False, 'message': 'Monthly contribution must be greater than 0'}), 400
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid contribution amount'}), 400
        
        # Check for duplicate chama names (case insensitive)
        existing_chama = Chama.query.filter(
            db.func.lower(Chama.name) == data['name'].strip().lower()
        ).first()
        
        if existing_chama:
            return jsonify({'success': False, 'message': 'A chama with this name already exists. Please choose a different name.'}), 400
        
        # Create new chama
        chama = Chama(
            name=data['name'].strip(),
            goal=data.get('goal', '').strip(),
            monthly_contribution=contribution,
            meeting_day=data.get('meeting_day', ''),
            creator_id=current_user.id
        )
        
        db.session.add(chama)
        db.session.flush()  # Get the chama ID
        
        # Add creator as admin member
        from app.models import chama_members
        membership = chama_members.insert().values(
            user_id=current_user.id,
            chama_id=chama.id,
            role='creator'
        )
        db.session.execute(membership)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Chama created successfully!', 'chama_id': chama.id})
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating chama: {e}")
        return jsonify({'success': False, 'message': 'An error occurred while creating the chama. Please try again.'}), 500

@main.route('/contribute', methods=['POST'])
@login_required
def contribute():
    try:
        data = request.get_json()
        chama_id = data.get('chama_id')
        amount = float(data.get('amount', 0))
        
        current_app.logger.info(f"Contribution attempt by user {current_user.id}: chama_id={chama_id}, amount={amount}")
        
        if not chama_id:
            return jsonify({'success': False, 'message': 'Chama ID is required'}), 400
        
        if amount <= 0:
            return jsonify({'success': False, 'message': 'Amount must be greater than 0'}), 400
        
        # Security check: Ensure user is a member of this chama
        from app.utils.permissions import user_can_access_chama
        if not user_can_access_chama(current_user.id, chama_id):
            return jsonify({'success': False, 'message': 'You do not have access to this chama'}), 403
        
        # Get chama details first
        chama = Chama.query.get(chama_id)
        if not chama:
            return jsonify({'success': False, 'message': 'Chama not found'}), 404
        
        current_app.logger.info(f"Processing contribution to chama: {chama.name}")
        
        # Create contribution transaction
        transaction = Transaction(
            type='contribution',
            amount=amount,
            description=f'{data.get("description", "Monthly contribution")}',
            user_id=current_user.id,
            chama_id=chama_id,
            status='completed'
        )
        
        # Update chama balance if it exists
        if hasattr(chama, 'total_balance'):
            chama.total_balance += amount
        
        # Add transaction to session and commit
        db.session.add(transaction)
        db.session.commit()
        
        current_app.logger.info(f"Contribution recorded successfully: transaction_id={transaction.id}")
        return jsonify({'success': True, 'message': 'Contribution recorded successfully!'})
            
    except ValueError as e:
        db.session.rollback()
        current_app.logger.error(f"Value error in contribution: {e}")
        return jsonify({'success': False, 'message': 'Invalid amount format'}), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Contribution error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'An error occurred while recording your contribution: {str(e)}'}), 500

@main.route('/contribute_mpesa', methods=['POST'])
@login_required
def contribute_mpesa():
    """Initiate M-Pesa payment for contribution"""
    try:
        data = request.get_json()
        chama_id = data.get('chama_id')
        amount = float(data.get('amount', 0))
        phone_number = data.get('phone_number') or current_user.phone_number
        
        current_app.logger.info(f"M-Pesa contribution attempt by user {current_user.id}: chama_id={chama_id}, amount={amount}")
        
        # Validate inputs
        if not chama_id or amount <= 0:
            return jsonify({'success': False, 'message': 'Invalid chama or amount'}), 400
        
        if not phone_number:
            return jsonify({'success': False, 'message': 'Phone number is required for M-Pesa payment'}), 400
        
        # Security check: Ensure user is a member of this chama
        from app.utils.permissions import user_can_access_chama
        if not user_can_access_chama(current_user.id, chama_id):
            return jsonify({'success': False, 'message': 'You do not have access to this chama'}), 403
        
        chama = Chama.query.get(chama_id)
        if not chama:
            return jsonify({'success': False, 'message': 'Chama not found'}), 404
        
        # Import M-Pesa functionality
        from app.utils.mpesa import get_mpesa_api
        
        # Create account reference
        account_reference = f"CHAMA{chama_id}U{current_user.id}"
        transaction_desc = f"Contribution to {chama.name}"
        
        # Initiate M-Pesa STK push
        mpesa_result = get_mpesa_api().stk_push(
            phone_number=phone_number,
            amount=amount,
            account_reference=account_reference,
            transaction_desc=transaction_desc
        )
        
        if mpesa_result.get('success'):
            current_app.logger.info(f"M-Pesa STK push initiated successfully: {mpesa_result.get('checkout_request_id')}")
            return jsonify({
                'success': True,
                'message': 'Payment initiated successfully! Please check your phone for the M-Pesa prompt.',
                'checkout_request_id': mpesa_result.get('checkout_request_id'),
                'customer_message': mpesa_result.get('customer_message')
            })
        else:
            current_app.logger.error(f"M-Pesa STK push failed: {mpesa_result}")
            return jsonify({
                'success': False,
                'message': mpesa_result.get('message', 'Payment initiation failed. Please try again.')
            }), 400
            
    except Exception as e:
        current_app.logger.error(f"M-Pesa contribution error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Payment initiation failed: {str(e)}'}), 500

@main.route('/dashboard_stats')
@login_required
def dashboard_stats():
    """API endpoint to get dashboard statistics"""
    user_chamas = current_user.chamas
    
    stats = {
        'total_chamas': len(user_chamas),
        'total_savings': sum(chama.total_balance for chama in user_chamas),
        'monthly_contributions': sum(chama.monthly_contribution for chama in user_chamas),
        'avg_roi': 8.5  # Placeholder
    }
    
    return jsonify(stats)

# Add missing routes
@main.route('/about')
def about():
    """About ChamaLink page"""
    return render_template('about.html')

@main.route('/features')
def features():
    """Features page"""
    return render_template('features.html')

@main.route('/founder-story')
def founder_story():
    """Founder's story page"""
    return render_template('founder_story.html')

@main.route('/about-founder')
def about_founder():
    """About founder page - detailed founder story"""
    return render_template('about_founder.html')

@main.route('/meetings')
@login_required
def meetings():
    """Online meetings page"""
    return render_template('meetings.html')

@main.route('/help')
@login_required
def help_support():
    """Help & Support page"""
    return render_template('help.html')

@main.route('/profile')
@login_required
def profile():
    """User profile page"""
    try:
        # Get user's chamas
        user_chamas = current_user.get_chamas()
        
        # Get user statistics
        total_contributions = db.session.query(db.func.sum(Transaction.amount)).filter(
            Transaction.type == 'contribution',
            Transaction.user_id == current_user.id
        ).scalar() or 0
        
        return render_template('profile.html', 
                             user_chamas=user_chamas,
                             total_contributions=total_contributions)
    except Exception as e:
        current_app.logger.error(f'Profile error: {str(e)}')
        flash('Error loading profile. Please try again.', 'error')
        return redirect(url_for('main.dashboard'))

@main.route('/reports')
@login_required
def reports():
    """Financial reports page"""
    try:
        # Get user chamas safely
        try:
            user_chamas = current_user.get_chamas() or []
        except Exception as e:
            current_app.logger.warning(f"Error getting user chamas: {e}")
            user_chamas = []
        
        # Calculate report data safely with better error handling
        total_contributions = 0
        total_loans = 0
        total_penalties = 0
        
        try:
            total_contributions = db.session.query(db.func.sum(Transaction.amount)).filter(
                Transaction.type == 'contribution',
                Transaction.user_id == current_user.id
            ).scalar() or 0
        except Exception as e:
            current_app.logger.warning(f"Error calculating contributions: {e}")
        
        try:
            total_loans = db.session.query(db.func.sum(Transaction.amount)).filter(
                Transaction.type == 'loan',
                Transaction.user_id == current_user.id
            ).scalar() or 0
        except Exception as e:
            current_app.logger.warning(f"Error calculating loans: {e}")
        
        try:
            total_penalties = db.session.query(db.func.sum(Transaction.amount)).filter(
                Transaction.type == 'penalty',
                Transaction.user_id == current_user.id
            ).scalar() or 0
        except Exception as e:
            current_app.logger.warning(f"Error calculating penalties: {e}")
        
        # Get monthly transaction data for charts with better error handling
        monthly_data = []
        try:
            monthly_data = db.session.query(
                db.func.to_char(Transaction.created_at, 'YYYY-MM').label('month'),
                db.func.sum(Transaction.amount).label('total')
            ).filter(
                Transaction.user_id == current_user.id,
                Transaction.type == 'contribution'
            ).group_by(db.func.to_char(Transaction.created_at, 'YYYY-MM')).all()
        except Exception as e:
            current_app.logger.warning(f"Monthly data error: {e}")
            monthly_data = []
        
        # Provide default message if no data
        if not user_chamas and total_contributions == 0 and total_loans == 0:
            flash('No financial data available yet. Join or create a chama to see your reports!', 'info')
        
        return render_template('reports.html',
                             user_chamas=user_chamas,
                             total_contributions=float(total_contributions),
                             total_loans=float(total_loans),
                             total_penalties=float(total_penalties),
                             monthly_data=monthly_data,
                             current_date=datetime.now(),
                             seven_days_ago=(datetime.now() - timedelta(days=7)))
    except Exception as e:
        current_app.logger.error(f"Reports route error: {e}")
        flash('Unable to load reports at this time. Please try again later.', 'error')
        return redirect(url_for('main.dashboard'))

@main.route('/terms')
def terms():
    """Terms of Service page"""
    return render_template('terms.html')

@main.route('/privacy')
def privacy():
    """Privacy Policy page"""
    return render_template('privacy.html')

@main.route('/contact')
def contact():
    """Contact page"""
    return render_template('contact.html')

@main.route('/contact', methods=['POST'])
def contact_submit():
    """Handle contact form submission"""
    try:
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')
        
        # In a real app, you'd send this to an email service
        # For now, just flash a success message
        flash('Thank you for your message! We will get back to you soon.', 'success')
        
        return redirect(url_for('main.contact'))
    except Exception as e:
        flash('Error sending message. Please try again.', 'error')
        return redirect(url_for('main.contact'))

@main.route('/api/notification-count')
@login_required
def notification_count():
    """Get unread notification count for badge"""
    count = current_user.get_unread_notifications_count()
    return jsonify({'count': count})

@main.route('/founder-dashboard')
@login_required
def founder_dashboard():
    """Founder admin dashboard - only accessible by super admin"""
    if not current_user.is_super_admin:
        flash('Access denied. Founder privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Get system-wide statistics
    from app.models.subscription import UserSubscription, SubscriptionPayment
    from app.models.enterprise import EnterpriseSubscriptionPayment
    
    # Chama statistics only (no user personal data)
    total_chamas = Chama.query.count()
    active_chamas = Chama.query.filter_by(status='active').count()
    
    # Financial overview
    total_subscription_revenue = db.session.query(db.func.sum(SubscriptionPayment.amount)).filter(
        SubscriptionPayment.payment_status == 'completed'
    ).scalar() or 0
    
    total_enterprise_revenue = db.session.query(db.func.sum(EnterpriseSubscriptionPayment.amount)).filter(
        EnterpriseSubscriptionPayment.status == 'completed'
    ).scalar() or 0
    
    total_revenue = total_subscription_revenue + total_enterprise_revenue
    
    # Admin statistics (aggregated only, no personal data)
    admin_users = User.query.filter_by(is_super_admin=True).count()
    total_users = User.query.count()
    verified_users = User.query.filter_by(is_email_verified=True).count()
    
    # Chamas by status
    pending_chamas = Chama.query.filter_by(status='pending').all()
    flagged_chamas = Chama.query.filter_by(status='flagged').all()
    all_chamas = Chama.query.order_by(Chama.created_at.desc()).limit(20).all()
    
    # System health metrics
    active_chama_percentage = (active_chamas / total_chamas * 100) if total_chamas > 0 else 0
    
    # Payment history (handle missing pricing_id column)
    try:
        recent_payments = SubscriptionPayment.query.filter(
            SubscriptionPayment.payment_status == 'completed'
        ).order_by(SubscriptionPayment.payment_date.desc()).limit(20).all()
    except Exception as e:
        print(f"Error fetching subscription payments: {e}")
        recent_payments = []
    
    return render_template('founder/dashboard.html',
                         total_chamas=total_chamas,
                         active_chamas=active_chamas,
                         total_revenue=total_revenue,
                         admin_users=admin_users,
                         total_users=total_users,
                         verified_users=verified_users,
                         pending_chamas=pending_chamas,
                         flagged_chamas=flagged_chamas,
                         all_chamas=all_chamas,
                         active_chama_percentage=active_chama_percentage,
                         recent_payments=recent_payments)

@main.route('/founder-dashboard/chama/<int:chama_id>/toggle-status', methods=['POST'])
@login_required
def toggle_chama_status(chama_id):
    """Toggle chama status (activate/suspend) - founder only"""
    if not current_user.is_super_admin:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    # Handle both JSON and form data
    if request.is_json:
        data = request.get_json()
        action = data.get('action')
    else:
        action = request.form.get('action')
    
    chama = Chama.query.get_or_404(chama_id)
    
    if action == 'suspend':
        chama.status = 'suspended'
        message = f'Chama "{chama.name}" has been suspended'
    elif action == 'activate':
        chama.status = 'active'
        message = f'Chama "{chama.name}" has been activated'
    elif action == 'blacklist':
        chama.status = 'blacklisted'
        message = f'Chama "{chama.name}" has been blacklisted'
    elif action == 'delete':
        db.session.delete(chama)
        message = f'Chama "{chama.name}" has been deleted'
    else:
        return jsonify({'success': False, 'message': 'Invalid action'}), 400
    
    try:
        db.session.commit()
        return jsonify({'success': True, 'message': message})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error toggling chama status: {e}")
        return jsonify({'success': False, 'message': 'Database error occurred'}), 500

@main.route('/chat')
def chat():
    """Chat support interface"""
    return render_template('chat.html')

@main.route('/demo')
def demo():
    """Demo video page"""
    return render_template('demo.html')

@main.route('/founder-dashboard/export-chamas')
@login_required
def export_all_chamas():
    """Export all chamas data - founder only"""
    if not current_user.is_super_admin:
        flash('Access denied. Founder privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    import csv
    from io import StringIO
    from flask import make_response
    
    # Get all chamas with statistics
    chamas = Chama.query.all()
    
    # Create CSV data
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'ID', 'Name', 'Admin', 'Status', 'Members Count', 'Total Contributions', 
        'Total Loans', 'Created Date', 'Description'
    ])
    
    # Write chama data
    for chama in chamas:
        # Calculate statistics
        total_contributions = db.session.query(db.func.sum(Transaction.amount)).filter(
            Transaction.chama_id == chama.id,
            Transaction.type == 'contribution'
        ).scalar() or 0
        
        total_loans = db.session.query(db.func.sum(Transaction.amount)).filter(
            Transaction.chama_id == chama.id,
            Transaction.type == 'loan'
        ).scalar() or 0
        
        writer.writerow([
            chama.id,
            chama.name,
            chama.creator.full_name if chama.creator else 'N/A',
            chama.status,
            len(chama.members),
            f"KES {total_contributions:,.2f}",
            f"KES {total_loans:,.2f}",
            chama.created_at.strftime('%Y-%m-%d') if chama.created_at else 'N/A',
            chama.description or 'N/A'
        ])
    
    # Create response
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=chamalink_all_chamas_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    return response

# Test email route has been replaced with production system notification feature
# System notifications can be sent from the founder dashboard using /api/system-notification

@main.route('/api/transaction/<int:transaction_id>')
@login_required
def get_transaction_details(transaction_id):
    """Get transaction details for modal display"""
    transaction = Transaction.query.get_or_404(transaction_id)
    
    # Check if user has permission to view this transaction
    if not current_user.is_super_admin:
        # Check if user is member of the chama or the transaction belongs to them
        if transaction.user_id != current_user.id:
            if transaction.chama:
                if not current_user.is_member_of_chama(transaction.chama.id):
                    return jsonify({'success': False, 'message': 'Access denied'}), 403
            else:
                return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    transaction_data = {
        'id': transaction.id,
        'type': transaction.type.title(),
        'amount': f"{transaction.amount:,.2f}",
        'description': transaction.description or 'No description',
        'created_at': transaction.created_at.strftime('%B %d, %Y at %I:%M %p'),
        'chama_name': transaction.chama.name if transaction.chama else None,
        'user_name': transaction.user.full_name if transaction.user else None
    }
    
    return jsonify({
        'success': True,
        'transaction': transaction_data
    })

@main.route('/api/feature-interest', methods=['POST'])
def feature_interest():
    """Handle feature interest submissions"""
    try:
        data = request.get_json()
        
        # Log feature interest (in a real app, store in database)
        print(f"Feature Interest: {data}")
        
        # Here you would typically save to database
        # For now, just return success
        
        return jsonify({
            'success': True,
            'message': 'Thank you for your interest! We\'ll keep you updated.'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Something went wrong. Please try again.'
        }), 400

@main.route('/api/developer')
def api_developer():
    """API Developer portal page"""
    return render_template('api_developer.html')

@main.route('/subscription/upgrade')
def subscription_upgrade():
    """Subscription upgrade page"""
    return render_template('subscription_upgrade.html')

@main.route('/founder-dashboard/new-feature', methods=['POST'])
@login_required
def add_new_feature():
    """Add a new feature to the development roadmap - founder only"""
    if not current_user.is_super_admin:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        data = request.get_json()
        feature_name = data.get('name')
        description = data.get('description')
        priority = data.get('priority', 'medium')
        
        # In a real implementation, save to database
        # For now, just log and return success
        print(f"New Feature Request: {feature_name} - {priority} - {description}")
        
        return jsonify({
            'success': True,
            'message': f'Feature "{feature_name}" added to development roadmap!'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@main.route('/founder-dashboard/platform-notice', methods=['POST'])
@login_required
def send_platform_notice():
    """Send platform-wide notice - founder only"""
    if not current_user.is_super_admin:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        data = request.get_json()
        title = data.get('title')
        message = data.get('message')
        priority = data.get('priority', 'info')
        send_email = data.get('send_email', False)
        
        if not title or not message:
            return jsonify({'success': False, 'message': 'Title and message are required'}), 400
        
        # Import models
        from app.models.user import User
        from app.models.chama import Chama
        from app.models.notification import Notification
        
        # Get all chama creators and their emails
        creators = User.query.join(Chama, User.id == Chama.creator_id).distinct().all()
        
        notification_count = 0
        email_count = 0
        
        # Create in-app notifications for all chama creators
        for creator in creators:
            notification = Notification(
                user_id=creator.id,
                title=f"📢 Platform Notice: {title}",
                message=message,
                type='system'
            )
            db.session.add(notification)
            notification_count += 1
        
        # Send emails if requested
        if send_email:
            from app.utils.email_utils import send_system_email
            for creator in creators:
                try:
                    success, _ = send_system_email(
                        to_email=creator.email,
                        subject=f"📢 Important Notice from ChamaLink: {title}",
                        template='emails/platform_notice.html',
                        user=creator,
                        title=title,
                        message=message,
                        priority=priority
                    )
                    if success:
                        email_count += 1
                except Exception as e:
                    print(f"Failed to send email to {creator.email}: {e}")
        
        # Commit all notifications
        db.session.commit()
        
        result_message = f'Platform notice sent to {notification_count} chama creators'
        if send_email:
            result_message += f' ({email_count} emails sent)'
        
        return jsonify({
            'success': True,
            'message': result_message
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@main.route('/founder-dashboard/generate-report', methods=['POST'])
@login_required
def generate_platform_report():
    """Generate platform reports - founder only"""
    if not current_user.is_super_admin:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        data = request.get_json()
        report_type = data.get('report_type')
        date_range = data.get('date_range', '30')
        export_format = data.get('export_format', 'pdf')
        
        # In a real implementation, generate actual reports
        print(f"Report Request: {report_type} - {date_range} days - {export_format}")
        
        # Here you would:
        # 1. Query data based on report type and date range
        # 2. Generate report in requested format
        # 3. Email to founder or provide download link
        
        return jsonify({
            'success': True,
            'message': f'{report_type} report generated successfully! Check your email.'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@main.route('/founder-dashboard/create-promotion', methods=['POST'])
@login_required
def create_promotion():
    """Create a new promotion - founder only"""
    if not current_user.is_super_admin:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        data = request.get_json()
        name = data.get('name')
        discount_type = data.get('discount_type')
        discount_value = data.get('discount_value')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        # In a real implementation, save promotion to database
        print(f"New Promotion: {name} - {discount_type} - {discount_value}% - {start_date} to {end_date}")
        
        # Here you would:
        # 1. Create promotion record in database
        # 2. Set up automated application of discounts
        # 3. Notify users about the promotion
        
        return jsonify({
            'success': True,
            'message': f'Promotion "{name}" created and activated successfully!'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@main.route('/founder-dashboard/maintenance-mode', methods=['POST'])
@login_required
def toggle_maintenance_mode():
    """Toggle maintenance mode - founder only"""
    if not current_user.is_super_admin:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        data = request.get_json()
        enable = data.get('enable', True)
        message = data.get('message', 'System under maintenance')
        
        # In a real implementation, set maintenance mode flag
        print(f"Maintenance Mode: {'Enabled' if enable else 'Disabled'} - {message}")
        
        # Here you would:
        # 1. Set maintenance flag in configuration
        # 2. Show maintenance page to non-admin users
        # 3. Log the action
        
        action = 'enabled' if enable else 'disabled'
        return jsonify({
            'success': True,
            'message': f'Maintenance mode {action} successfully!'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@main.route('/founder-dashboard/emergency-broadcast', methods=['POST'])
@login_required
def emergency_broadcast():
    """Send emergency broadcast - founder only"""
    if not current_user.is_super_admin:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        data = request.get_json()
        message = data.get('message')
        send_sms = data.get('send_sms', False)
        send_email = data.get('send_email', True)
        
        # In a real implementation, send emergency notifications
        print(f"Emergency Broadcast: {message} - SMS: {send_sms} - Email: {send_email}")
        
        # Here you would:
        # 1. Send immediate notifications to all users
        # 2. Send SMS if requested and configured
        # 3. Send emails
        # 4. Log the emergency action
        
        return jsonify({
            'success': True,
            'message': 'Emergency broadcast sent to all users!'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@main.route('/pricing')
def pricing():
    """Public pricing page with multi-currency support"""
    return render_template('main/pricing_multi_currency.html')

@main.route('/faq')
def faq():
    """Frequently Asked Questions page"""
    return render_template('faq.html')

@main.route('/security-dashboard')
@login_required
def security_dashboard():
    """Security monitoring dashboard - founder only"""
    if not current_user.is_super_admin:
        flash('Access denied. Founder privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Get security statistics
    from app.utils.security_monitor import security_monitor
    
    # Basic stats for initial page load
    threats_blocked = 42  # This would be calculated from security logs
    blocked_ips_count = len(security_monitor.blocked_ips)
    
    return render_template('security_dashboard.html', 
                         threats_blocked=threats_blocked,
                         blocked_ips_count=blocked_ips_count)

@main.route('/admin/user-management')
@login_required
def admin_user_management():
    """Admin interface for user and chama management"""
    if not current_user.is_super_admin:
        flash('Access denied. Super admin privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    try:
        # Get all users
        users = User.query.order_by(User.username).all()
        
        # Get all chamas
        chamas = Chama.query.order_by(Chama.name).all()
        
        # Get user-chama relationships for display
        user_chamas = {}
        for user in users:
            user_chamas[user.id] = user.get_chamas()
        
        return render_template('admin/user_management.html', 
                             users=users, 
                             chamas=chamas,
                             user_chamas=user_chamas)
    except Exception as e:
        current_app.logger.error(f"Error in admin user management: {e}")
        flash('Error loading user management interface.', 'error')
        return redirect(url_for('main.dashboard'))

@main.route('/admin/add-user-to-chama', methods=['POST'])
@login_required  
def admin_add_user_to_chama():
    """Add a user to a chama (Super admin only)"""
    if not current_user.is_super_admin:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        chama_id = data.get('chama_id')
        role = data.get('role', 'member')  # Default to member role
        
        if not user_id or not chama_id:
            return jsonify({'success': False, 'message': 'User ID and Chama ID are required'}), 400
        
        # Validate user and chama exist
        user = User.query.get(user_id)
        chama = Chama.query.get(chama_id)
        
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        if not chama:
            return jsonify({'success': False, 'message': 'Chama not found'}), 404
        
        # Check if user is already a member
        if user.is_member_of_chama(chama_id):
            return jsonify({'success': False, 'message': f'{user.username} is already a member of {chama.name}'}), 400
        
        # Add user to chama
        from app.models.chama import chama_members
        membership = chama_members.insert().values(
            user_id=user_id,
            chama_id=chama_id,
            role=role,
            joined_at=datetime.utcnow()
        )
        db.session.execute(membership)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'{user.username} successfully added to {chama.name} as {role}'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error adding user to chama: {e}")
        return jsonify({'success': False, 'message': 'An error occurred while adding user to chama'}), 500

@main.route('/admin/remove-user-from-chama', methods=['POST'])
@login_required
def admin_remove_user_from_chama():
    """Remove a user from a chama (Super admin only)"""
    if not current_user.is_super_admin:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        chama_id = data.get('chama_id')
        
        if not user_id or not chama_id:
            return jsonify({'success': False, 'message': 'User ID and Chama ID are required'}), 400
        
        # Validate user and chama exist
        user = User.query.get(user_id)
        chama = Chama.query.get(chama_id)
        
        if not user or not chama:
            return jsonify({'success': False, 'message': 'User or Chama not found'}), 404
        
        # Check if user is a member
        if not user.is_member_of_chama(chama_id):
            return jsonify({'success': False, 'message': f'{user.username} is not a member of {chama.name}'}), 400
        
        # Remove user from chama
        from app.models.chama import chama_members
        db.session.execute(
            chama_members.delete().where(
                chama_members.c.user_id == user_id,
                chama_members.c.chama_id == chama_id
            )
        )
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'{user.username} successfully removed from {chama.name}'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error removing user from chama: {e}")
        return jsonify({'success': False, 'message': 'An error occurred while removing user from chama'}), 500

@main.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Test database connection
        db.session.execute(db.text('SELECT 1'))
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'database': 'connected',
            'version': '1.0.0'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }), 500

@main.route('/founder-dashboard/save-note', methods=['POST'])
@login_required
def save_founder_note():
    """Save founder's notepad content"""
    if not current_user.is_super_admin:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        data = request.get_json()
        content = data.get('content', '')
        
        # You can save to database here if needed
        # For now, we'll just acknowledge the save
        current_app.logger.info(f"Founder note saved by {current_user.username}: {len(content)} characters")
        
        return jsonify({
            'success': True, 
            'message': 'Note saved successfully',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error saving founder note: {e}")
        return jsonify({'success': False, 'message': 'Failed to save note'}), 500
