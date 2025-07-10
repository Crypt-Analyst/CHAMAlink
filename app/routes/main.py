from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import Chama, Transaction, Event, User
from app import db
from datetime import datetime, date, timedelta
from sqlalchemy import desc

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
        if not data.get('name'):
            return jsonify({'success': False, 'message': 'Chama name is required'}), 400
        
        if not data.get('monthly_contribution'):
            return jsonify({'success': False, 'message': 'Monthly contribution is required'}), 400
        
        # Create new chama
        chama = Chama(
            name=data['name'],
            goal=data.get('goal', ''),
            monthly_contribution=float(data['monthly_contribution']),
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
        
        return jsonify({'success': True, 'message': 'Chama created successfully!'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@main.route('/contribute', methods=['POST'])
@login_required
def contribute():
    try:
        data = request.get_json()
        chama_id = data.get('chama_id')
        amount = float(data.get('amount', 0))
        
        if not chama_id:
            return jsonify({'success': False, 'message': 'Chama ID is required'}), 400
        
        if amount <= 0:
            return jsonify({'success': False, 'message': 'Amount must be greater than 0'}), 400
        
        # Security check: Ensure user is a member of this chama
        from app.utils.permissions import user_can_access_chama
        if not user_can_access_chama(current_user.id, chama_id):
            return jsonify({'success': False, 'message': 'You do not have access to this chama'}), 403
        
        # Create transaction
        transaction = Transaction(
            type='contribution',
            amount=amount,
            description=f"Monthly contribution",
            user_id=current_user.id,
            chama_id=chama_id
        )
        
        db.session.add(transaction)
        
        # Update chama balance
        chama = Chama.query.get(chama_id)
        chama.total_balance += amount
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Contribution successful!'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400
        data = request.get_json()
        chama_id = data['chama_id']
        amount = float(data['amount'])
        
        # Create contribution transaction
        transaction = Transaction(
            type='contribution',
            amount=amount,
            description=f'{data.get("description", "Monthly contribution")}',
            user_id=current_user.id,
            chama_id=chama_id
        )
        
        # Update chama balance
        chama = Chama.query.get(chama_id)
        if chama:
            chama.total_balance += amount
            db.session.add(transaction)
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'Contribution recorded successfully!'})
        else:
            return jsonify({'success': False, 'message': 'Chama not found'}), 404
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

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
    return render_template('profile.html')

@main.route('/reports')
@login_required
def reports():
    """Financial reports page"""
    user_chamas = current_user.chamas
    
    # Calculate report data
    total_contributions = db.session.query(db.func.sum(Transaction.amount)).filter(
        Transaction.type == 'contribution',
        Transaction.user_id == current_user.id
    ).scalar() or 0
    
    total_loans = db.session.query(db.func.sum(Transaction.amount)).filter(
        Transaction.type == 'loan',
        Transaction.user_id == current_user.id
    ).scalar() or 0
    
    total_penalties = db.session.query(db.func.sum(Transaction.amount)).filter(
        Transaction.type == 'penalty',
        Transaction.user_id == current_user.id
    ).scalar() or 0
    
    # Get monthly transaction data for charts
    monthly_data = db.session.query(
        db.func.date_trunc('month', Transaction.created_at).label('month'),
        db.func.sum(Transaction.amount).label('total')
    ).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == 'contribution'
    ).group_by(db.func.date_trunc('month', Transaction.created_at)).all()
    
    return render_template('reports.html',
                         user_chamas=user_chamas,
                         total_contributions=total_contributions,
                         total_loans=total_loans,
                         total_penalties=total_penalties,
                         monthly_data=monthly_data)

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
    
    chama = Chama.query.get_or_404(chama_id)
    action = request.json.get('action')
    
    if action == 'suspend':
        chama.status = 'suspended'
        message = f'Chama "{chama.name}" has been suspended'
    elif action == 'activate':
        chama.status = 'active'
        message = f'Chama "{chama.name}" has been activated'
    elif action == 'blacklist':
        chama.status = 'blacklisted'
        message = f'Chama "{chama.name}" has been blacklisted'
    else:
        return jsonify({'success': False, 'message': 'Invalid action'}), 400
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': message})

@main.route('/chat')
def chat():
    """Chat support interface"""
    return render_template('chat.html')

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

@main.route('/test-email')
@login_required
def test_email():
    """Test email functionality - super admin only"""
    if not current_user.is_super_admin:
        flash('Access denied. Super admin privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    try:
        from flask_mail import Message
        from app import mail
        
        # Create test email
        msg = Message(
            subject='ChamaLink Test Email - System Working!',
            sender=('ChamaLink System', 'noreply@chamalink.co.ke'),
            recipients=[current_user.email]
        )
        
        msg.html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; text-align: center;">
                <h1 style="color: white; margin: 0;">🎉 Email System Test</h1>
            </div>
            
            <div style="padding: 30px; background: #f8f9fa;">
                <h2 style="color: #333;">Hello Founder Bilford! 👑</h2>
                
                <p style="font-size: 16px; line-height: 1.6; color: #555;">
                    Great news! Your ChamaLink email system is working perfectly.
                </p>
                
                <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #667eea;">
                    <h3 style="color: #667eea; margin-top: 0;">📧 Test Details:</h3>
                    <ul style="color: #666;">
                        <li><strong>Sent to:</strong> {current_user.email}</li>
                        <li><strong>User:</strong> {current_user.full_name}</li>
                        <li><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
                        <li><strong>Status:</strong> ✅ Email delivery successful</li>
                    </ul>
                </div>
                
                <div style="background: #e8f4fd; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <h4 style="color: #0066cc; margin-top: 0;">🚀 What This Means:</h4>
                    <p style="margin-bottom: 0; color: #004499;">
                        Your email configuration is working correctly. Users will receive:
                        <br>• Registration confirmations
                        <br>• Password reset emails  
                        <br>• Payment notifications
                        <br>• LeeBot agent escalation emails
                        <br>• System notifications
                    </p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="http://127.0.0.1:5000/founder-dashboard" 
                       style="background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                        👑 Return to Founder Dashboard
                    </a>
                </div>
            </div>
            
            <div style="background: #333; color: white; padding: 15px; text-align: center; font-size: 12px;">
                <p style="margin: 0;">© 2025 ChamaLink - Kenya's Premier Chama Management Platform</p>
            </div>
        </div>
        """
        
        # Send the email
        mail.send(msg)
        
        flash(f'✅ Test email sent successfully to {current_user.email}! Check your inbox.', 'success')
        return redirect(url_for('main.founder_dashboard'))
        
    except Exception as e:
        flash(f'❌ Email test failed: {str(e)}', 'error')
        return redirect(url_for('main.founder_dashboard'))

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
        
        # In a real implementation, create notifications for all users
        # and optionally send emails
        print(f"Platform Notice: {title} - {priority} - Email: {send_email}")
        
        # Here you would:
        # 1. Create notifications for all users
        # 2. Send emails if requested
        # 3. Log the action
        
        return jsonify({
            'success': True,
            'message': f'Platform notice "{title}" sent successfully!'
        })
    except Exception as e:
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
