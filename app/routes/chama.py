from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from app.models import (
    Chama, User, Transaction, Event, 
    ChamaMembershipRequest, Notification, ManualPaymentVerification, RegistrationFeePayment
)
from app.models.chama import chama_members as chama_members_table  # Import the table with alias
from app.utils.permissions import chama_member_required, chama_admin_required, user_can_access_chama, get_user_chama_role
from app.utils.mpesa import initiate_stk_push
from app import db
from datetime import datetime, date
from sqlalchemy import desc, and_, or_, func

chama_bp = Blueprint('chama', __name__, url_prefix='/chama')

@chama_bp.route('/my-chamas')
@login_required
def my_chamas():
    """List all chamas the current user is a member of"""
    try:
        # Get all chamas where the user is a member
        user_chamas = db.session.query(Chama).join(
            chama_members_table, Chama.id == chama_members_table.c.chama_id
        ).filter(
            chama_members_table.c.user_id == current_user.id
        ).all()
        
        # Get membership details for each chama
        chama_details = []
        for chama in user_chamas:
            # Get user's role in this chama
            membership = db.session.query(chama_members_table).filter_by(
                user_id=current_user.id,
                chama_id=chama.id
            ).first()
            
            # Get basic stats
            member_count = db.session.query(chama_members_table).filter_by(chama_id=chama.id).count()
            
            # Get total contributions for this chama
            total_contributions = db.session.query(func.sum(Transaction.amount)).filter(
                Transaction.chama_id == chama.id,
                Transaction.transaction_type == 'contribution'
            ).scalar() or 0
            
            chama_details.append({
                'chama': chama,
                'role': membership.role if membership else 'member',
                'member_count': member_count,
                'total_contributions': total_contributions,
                'joined_date': membership.joined_at if membership else None
            })
        
        return render_template('chama/my_chamas.html', chama_details=chama_details)
        
    except Exception as e:
        current_app.logger.error(f"Error loading user chamas: {e}")
        import traceback
        traceback.print_exc()
        flash(f'Error loading your chamas: {str(e)}', 'error')
        return redirect(url_for('main.dashboard'))

@chama_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_chama():
    """Create a new chama"""
    if request.method == 'GET':
        return render_template('chama/create.html')
    
    try:
        data = request.get_json() if request.is_json else request.form
        
        # Validate required fields
        if not data.get('name') or not data.get('name').strip():
            error_msg = 'Chama name is required'
            if request.is_json:
                return jsonify({'success': False, 'message': error_msg}), 400
            else:
                flash(error_msg, 'error')
                return render_template('chama/create.html')
        
        if not data.get('monthly_contribution'):
            error_msg = 'Monthly contribution is required'
            if request.is_json:
                return jsonify({'success': False, 'message': error_msg}), 400
            else:
                flash(error_msg, 'error')
                return render_template('chama/create.html')
        
        # Validate contribution amount
        try:
            contribution = float(data['monthly_contribution'])
            if contribution <= 0:
                error_msg = 'Monthly contribution must be greater than 0'
                if request.is_json:
                    return jsonify({'success': False, 'message': error_msg}), 400
                else:
                    flash(error_msg, 'error')
                    return render_template('chama/create.html')
        except ValueError:
            error_msg = 'Invalid contribution amount'
            if request.is_json:
                return jsonify({'success': False, 'message': error_msg}), 400
            else:
                flash(error_msg, 'error')
                return render_template('chama/create.html')
        
        # Check for duplicate chama names (case insensitive)
        existing_chama = Chama.query.filter(
            db.func.lower(Chama.name) == data['name'].strip().lower()
        ).first()
        
        if existing_chama:
            error_msg = 'A chama with this name already exists. Please choose a different name.'
            if request.is_json:
                return jsonify({'success': False, 'message': error_msg}), 400
            else:
                flash(error_msg, 'error')
                return render_template('chama/create.html')
        
        # Create new chama
        chama = Chama(
            name=data['name'].strip(),
            description=data.get('description', '').strip(),
            goal=data.get('goal', '').strip(),
            monthly_contribution=contribution,
            meeting_day=data.get('meeting_day', ''),
            creator_id=current_user.id
        )
        
        db.session.add(chama)
        db.session.flush()  # Get the chama ID
        
        # Add creator as both creator and chairperson (default leadership)
        from datetime import timedelta
        term_end = datetime.utcnow() + timedelta(days=365)  # 1 year term
        
        db.session.execute(
            db.text("INSERT INTO chama_members (user_id, chama_id, role, joined_at, elected_at, term_end_date) VALUES (:user_id, :chama_id, :role, :joined_at, :elected_at, :term_end_date)"),
            {
                'user_id': current_user.id,
                'chama_id': chama.id,
                'role': 'creator',  # Creator has permanent admin access
                'joined_at': datetime.utcnow(),
                'elected_at': datetime.utcnow(),
                'term_end_date': None  # Creator role is permanent
            }
        )
        
        # Also assign as chairperson initially (can be changed via elections)
        db.session.execute(
            db.text("INSERT INTO chama_members (user_id, chama_id, role, joined_at, elected_at, term_end_date) VALUES (:user_id, :chama_id, :role, :joined_at, :elected_at, :term_end_date)"),
            {
                'user_id': current_user.id,
                'chama_id': chama.id,
                'role': 'chairperson',
                'joined_at': datetime.utcnow(),
                'elected_at': datetime.utcnow(),
                'term_end_date': term_end
            }
        )
        
        db.session.commit()
        
        if request.is_json:
            return jsonify({'success': True, 'message': 'Chama created successfully!', 'chama_id': chama.id})
        else:
            flash('Chama created successfully!', 'success')
            return redirect(url_for('chama.chama_detail', chama_id=chama.id))
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating chama: {e}")
        import traceback
        traceback.print_exc()
        error_msg = f'An error occurred while creating the chama: {str(e)}'
        if request.is_json:
            return jsonify({'success': False, 'message': error_msg}), 500
        else:
            flash(error_msg, 'error')
            return render_template('chama/create.html')

@chama_bp.route('/<int:chama_id>')
@login_required
def chama_detail(chama_id):
    """View detailed information about a specific chama"""
    try:
        chama = Chama.query.get_or_404(chama_id)
        
        current_app.logger.info(f"Accessing chama details: chama_id={chama_id}, user_id={current_user.id}")
        
        # Check if user is a member of this chama or is super admin
        from app.utils.permissions import user_can_access_chama
        if not getattr(current_user, 'is_super_admin', False) and not user_can_access_chama(current_user.id, chama_id):
            flash('You do not have permission to access this chama.', 'error')
            return redirect(url_for('main.dashboard'))
        
        # Get chama statistics with proper error handling
        try:
            total_contributions = db.session.query(db.func.sum(Transaction.amount)).filter(
                Transaction.chama_id == chama_id,
                Transaction.type == 'contribution'
            ).scalar() or 0
        except Exception as e:
            current_app.logger.warning(f"Error getting contributions: {e}")
            total_contributions = 0
        
        try:
            total_loans = db.session.query(db.func.sum(Transaction.amount)).filter(
                Transaction.chama_id == chama_id,
                Transaction.type == 'loan'
            ).scalar() or 0
        except Exception as e:
            current_app.logger.warning(f"Error getting loans: {e}")
            total_loans = 0
        
        # Get recent transactions for this chama
        try:
            recent_transactions = Transaction.query.filter(
                Transaction.chama_id == chama_id
            ).order_by(desc(Transaction.created_at)).limit(10).all()
        except Exception as e:
            current_app.logger.warning(f"Error getting transactions: {e}")
            recent_transactions = []
        
        # Get upcoming events for this chama
        try:
            upcoming_events = Event.query.filter(
                Event.chama_id == chama_id,
                Event.event_date >= date.today()
            ).order_by(Event.event_date).limit(5).all()
        except Exception as e:
            current_app.logger.warning(f"Error getting events: {e}")
            upcoming_events = []
        
        # Get user's role in this chama
        try:
            user_role = get_user_chama_role(current_user.id, chama_id)
            current_app.logger.info(f"🎭 ROLE DEBUG: get_user_chama_role returned: '{user_role}' for user {current_user.id} in chama {chama_id}")
            
            # Also check if user is the creator directly from the chama model
            is_creator = (chama.creator_id == current_user.id)
            current_app.logger.info(f"🏗️ CREATOR DEBUG: chama.creator_id={chama.creator_id}, current_user.id={current_user.id}, is_creator={is_creator}")
            
            # If the function didn't return 'creator' but user is the creator, override it
            if is_creator and user_role != 'creator':
                current_app.logger.warning(f"⚠️ ROLE MISMATCH! User is creator but get_user_chama_role returned: '{user_role}'. Overriding to 'creator'.")
                user_role = 'creator'
            
            current_app.logger.info(f"🎯 FINAL ROLE: '{user_role}' will be passed to template")
                
        except Exception as e:
            current_app.logger.error(f"❌ ERROR getting user role: {e}")
            # Check if user is creator as fallback
            if chama.creator_id == current_user.id:
                current_app.logger.info(f"🎭 FALLBACK: Setting role to 'creator' for chama creator")
                user_role = 'creator'
            else:
                user_role = 'member'  # Default role
        
        current_app.logger.info(f"Successfully loaded chama details: {chama.name}")
        
        return render_template('chama/detail.html',
                             chama=chama,
                             total_contributions=total_contributions,
                             total_loans=total_loans,
                             recent_transactions=recent_transactions,
                             upcoming_events=upcoming_events,
                             user_role=user_role)
                             
    except Exception as e:
        current_app.logger.error(f"Error accessing chama details: {e}")
        import traceback
        traceback.print_exc()
        flash(f'Error accessing chama details: {str(e)}', 'error')
        return redirect(url_for('main.dashboard'))

@chama_bp.route('/<int:chama_id>/dashboard')
@login_required
@chama_member_required
def chama_dashboard(chama_id):
    """Comprehensive chama dashboard with role-based access"""
    try:
        # Get the specific chama by ID - this ensures we're working with the correct chama
        chama = Chama.query.get_or_404(chama_id)
        
        # Log for debugging - confirm we're accessing the right chama
        current_app.logger.info(f"🎯 Loading dashboard for Chama ID: {chama_id}, Name: '{chama.name}', User: {current_user.username}")
        
        # Verify user has access to THIS specific chama
        user_role = get_user_chama_role(current_user.id, chama_id)
        if not user_role:
            current_app.logger.warning(f"❌ User {current_user.username} denied access to chama {chama.name} (ID: {chama_id})")
            flash(f'You do not have access to {chama.name}', 'error')
            return redirect(url_for('main.dashboard'))
        
        current_app.logger.info(f"✅ User role in {chama.name}: {user_role}")
        
        # Get all members with their roles and contribution totals FOR THIS CHAMA ONLY
        members_data = []
        try:
            members_with_roles = db.session.query(
                User, chama_members_table.c.role, chama_members_table.c.joined_at
            ).join(chama_members_table, User.id == chama_members_table.c.user_id).filter(
                chama_members_table.c.chama_id == chama_id  # CRITICAL: Filter by THIS chama_id
            ).all()
            
            current_app.logger.info(f"📊 Found {len(members_with_roles)} members in {chama.name}")
            
            for user, role, joined_at in members_with_roles:
                # Calculate total contributions for this member IN THIS CHAMA ONLY
                total_contributions = db.session.query(func.sum(Transaction.amount)).filter(
                    Transaction.user_id == user.id,
                    Transaction.chama_id == chama_id,  # CRITICAL: Filter by THIS chama_id
                    Transaction.type == 'contribution'
                ).scalar() or 0
                
                members_data.append({
                    'user': user,
                    'role': role,
                    'joined_at': joined_at,
                    'total_contributions': float(total_contributions),
                    'can_edit': user_role in ['admin', 'creator'] or user.id == current_user.id
                })
        except Exception as e:
            current_app.logger.error(f"Error fetching members for {chama.name}: {str(e)}")
            members_data = []
        
        # Get transactions based on role FOR THIS CHAMA ONLY
        transactions = []
        try:
            if user_role in ['admin', 'creator']:
                # Admins see all transactions FOR THIS CHAMA ONLY
                transactions = Transaction.query.filter_by(chama_id=chama_id).order_by(desc(Transaction.created_date)).limit(20).all()
                current_app.logger.info(f"📋 Admin {current_user.username} viewing {len(transactions)} transactions for {chama.name}")
            else:
                # Members see only their transactions IN THIS CHAMA ONLY
                transactions = Transaction.query.filter(
                    Transaction.chama_id == chama_id,  # CRITICAL: Filter by THIS chama_id
                    Transaction.user_id == current_user.id
                ).order_by(desc(Transaction.created_date)).limit(20).all()
                current_app.logger.info(f"📋 Member {current_user.username} viewing {len(transactions)} own transactions for {chama.name}")
        except Exception as e:
            current_app.logger.error(f"Error fetching transactions for {chama.name}: {str(e)}")
        
        # Get pending requests FOR THIS CHAMA ONLY (admin only)
        pending_requests = []
        if user_role in ['admin', 'creator']:
            try:
                pending_requests = ChamaMembershipRequest.query.filter_by(
                    chama_id=chama_id,  # CRITICAL: Filter by THIS chama_id
                    status='pending',
                    request_type='join'
                ).all()
                current_app.logger.info(f"📩 Found {len(pending_requests)} pending requests for {chama.name}")
            except Exception as e:
                current_app.logger.error(f"Error fetching pending requests for {chama.name}: {str(e)}")
        
        # Calculate statistics FOR THIS CHAMA ONLY
        stats = {
            'total_members': len(members_data),
            'total_balance': float(chama.total_balance or 0),
            'monthly_contributions': 0,
            'pending_requests': len(pending_requests)
        }
        
        # Calculate monthly contributions FOR THIS CHAMA ONLY
        try:
            from datetime import datetime
            start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            monthly_contributions = db.session.query(func.sum(Transaction.amount)).filter(
                Transaction.chama_id == chama_id,  # CRITICAL: Filter by THIS chama_id
                Transaction.type == 'contribution',
                Transaction.created_date >= start_of_month
            ).scalar() or 0
            stats['monthly_contributions'] = float(monthly_contributions)
        except Exception as e:
            current_app.logger.error(f"Error calculating monthly contributions for {chama.name}: {str(e)}")
        
        current_app.logger.info(f"✅ Successfully loaded dashboard for {chama.name} - Balance: {stats['total_balance']}, Members: {stats['total_members']}")
        
        return render_template('chama/dashboard.html',
                             chama=chama,  # The specific chama object
                             user_role=user_role,
                             members_data=members_data,
                             transactions=transactions,
                             pending_requests=pending_requests,
                             stats=stats)
                             
    except Exception as e:
        current_app.logger.error(f"Error in chama_dashboard for chama_id {chama_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        flash('Error loading chama dashboard. Please try again.', 'error')
        return redirect(url_for('main.dashboard'))
        
        # Get pending requests (admin only)
        pending_requests = []
        if user_role in ['admin', 'creator']:
            try:
                pending_requests = ChamaMembershipRequest.query.filter_by(
                    chama_id=chama_id,
                    status='pending',
                    request_type='join'
                ).all()
            except Exception as e:
                current_app.logger.error(f"Error fetching pending requests: {str(e)}")
        
        # Calculate statistics
        stats = {
            'total_members': len(members_data),
            'total_balance': float(chama.total_balance or 0),
            'monthly_contributions': 0,
            'pending_requests': len(pending_requests)
        }
        
        # Calculate monthly contributions
        try:
            from datetime import datetime
            start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            monthly_contributions = db.session.query(func.sum(Transaction.amount)).filter(
                Transaction.chama_id == chama_id,
                Transaction.type == 'contribution',
                Transaction.created_date >= start_of_month
            ).scalar() or 0
            stats['monthly_contributions'] = float(monthly_contributions)
        except Exception as e:
            current_app.logger.error(f"Error calculating monthly contributions: {str(e)}")
        
        return render_template('chama/dashboard.html',
                             chama=chama,
                             user_role=user_role,
                             members_data=members_data,
                             transactions=transactions,
                             pending_requests=pending_requests,
                             stats=stats)
                             
    except Exception as e:
        current_app.logger.error(f"Error in chama_dashboard: {str(e)}")
        flash('Error loading chama dashboard. Please try again.', 'error')
        return redirect(url_for('main.dashboard'))

@chama_bp.route('/<int:chama_id>/members')
@login_required
@chama_member_required
def chama_members_list(chama_id):
    """View chama members (only accessible to chama members)"""
    chama = Chama.query.get_or_404(chama_id)
    
    # Get members with their roles
    members_with_roles = db.session.query(
        User, chama_members_table.c.role, chama_members_table.c.joined_at
    ).join(chama_members_table, User.id == chama_members_table.c.user_id).filter(
        chama_members_table.c.chama_id == chama_id
    ).all()
    
    user_role = get_user_chama_role(current_user.id, chama_id)
    
    return render_template('chama/members.html',
                         chama=chama,
                         members_with_roles=members_with_roles,
                         user_role=user_role)

@chama_bp.route('/<int:chama_id>/contribute', methods=['POST'])
@login_required
@chama_member_required
def contribute(chama_id):
    """Make a contribution to a specific chama"""
    try:
        data = request.get_json()
        amount = float(data.get('amount', 0))
        
        if amount <= 0:
            return jsonify({'success': False, 'message': 'Amount must be greater than 0'}), 400
        
        # Get the SPECIFIC chama first to verify it exists and ensure correct targeting
        chama = Chama.query.get(chama_id)
        if not chama:
            current_app.logger.warning(f"❌ Contribution attempt to non-existent chama ID: {chama_id}")
            return jsonify({'success': False, 'message': 'Chama not found'}), 404
        
        # Log the contribution for verification
        current_app.logger.info(f"💰 {current_user.username} contributing {amount} to '{chama.name}' (ID: {chama_id})")
        
        # Create contribution transaction - EXPLICITLY linked to this chama_id
        transaction = Transaction(
            type='contribution',
            amount=amount,
            description=f'{data.get("description", f"Contribution to {chama.name}")}',
            user_id=current_user.id,
            chama_id=chama_id  # CRITICAL: Ensure transaction is linked to correct chama
        )
        
        # Update the balance of THIS SPECIFIC chama
        old_balance = chama.total_balance or 0
        chama.total_balance = old_balance + amount
        
        # Verify the transaction is created correctly
        if transaction.chama_id != chama_id:
            raise ValueError(f"Transaction chama_id mismatch: expected {chama_id}, got {transaction.chama_id}")
        
        # Add transaction and commit
        db.session.add(transaction)
        db.session.commit()
        
        current_app.logger.info(f"✅ Contribution successful: {amount} to '{chama.name}', new balance: {chama.total_balance}")
        
        return jsonify({
            'success': True, 
            'message': f'Contribution of KES {amount:,.2f} recorded successfully for {chama.name}!',
            'chama_name': chama.name,
            'new_balance': float(chama.total_balance)
        })
    
    except ValueError as e:
        db.session.rollback()
        current_app.logger.error(f"❌ Invalid contribution data for chama {chama_id}: {e}")
        return jsonify({'success': False, 'message': 'Invalid amount format'}), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"❌ Contribution error for chama {chama_id}: {e}")
        return jsonify({'success': False, 'message': 'An error occurred while recording your contribution. Please try again.'}), 500

@chama_bp.route('/<int:chama_id>/update', methods=['POST'])
@login_required
def update_chama_details(chama_id):
    """Update chama details (admin/creator only)"""
    try:
        chama = Chama.query.get_or_404(chama_id)
        
        # Check permissions
        user_role = get_user_chama_role(current_user.id, chama_id)
        if user_role not in ['admin', 'creator']:
            return jsonify({'success': False, 'message': 'Access denied. Only admins can update chama details.'}), 403
        
        data = request.get_json()
        
        # Update chama fields
        if 'name' in data and data['name']:
            chama.name = data['name']
        
        if 'description' in data:
            chama.description = data['description']
        
        if 'goal' in data:
            chama.goal = data['goal']
        
        if 'monthly_contribution' in data:
            chama.monthly_contribution = float(data['monthly_contribution']) or 0.0
        
        if 'registration_fee' in data:
            chama.registration_fee = float(data['registration_fee']) or 0.0
        
        if 'meeting_day' in data:
            chama.meeting_day = data['meeting_day'] if data['meeting_day'] else None
        
        if 'meeting_time' in data:
            if data['meeting_time']:
                from datetime import datetime
                time_obj = datetime.strptime(data['meeting_time'], '%H:%M').time()
                chama.meeting_time = time_obj
            else:
                chama.meeting_time = None
        
        chama.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        current_app.logger.info(f"✅ Chama {chama.name} updated by {current_user.username}")
        
        return jsonify({
            'success': True, 
            'message': f'{chama.name} details updated successfully!'
        })
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"❌ Error updating chama {chama_id}: {e}")
        return jsonify({'success': False, 'message': 'An error occurred while updating chama details. Please try again.'}), 500

@chama_bp.route('/<int:chama_id>/invite', methods=['POST'])
@login_required
@chama_admin_required
def invite_member(chama_id):
    """Invite a new member to the chama (admin only)"""
    try:
        # Check member limits first
        from app.models.enterprise import EnterpriseUserSubscription, EnterpriseBillingType
        from app.utils.enterprise_limits import update_member_count
        
        subscription = EnterpriseUserSubscription.query.filter_by(
            user_id=current_user.id,
            is_active=True
        ).first()
        
        # Check if user can add more members based on their enterprise subscription
        if subscription:
            if subscription.plan.billing_type == EnterpriseBillingType.PER_MEMBER:
                if subscription.current_members >= subscription.paid_member_limit:
                    return jsonify({
                        'success': False,
                        'message': f'Member limit reached! You have paid for {subscription.paid_member_limit} members. Please upgrade your payment to add more members.',
                        'upgrade_required': True,
                        'current_members': subscription.current_members,
                        'paid_limit': subscription.paid_member_limit,
                        'cost_per_member': subscription.plan.price_per_member
                    }), 403
            else:
                chama = Chama.query.get(chama_id)
                if len(chama.members) >= subscription.plan.max_members_per_chama:
                    return jsonify({
                        'success': False,
                        'message': f'Member limit reached! Your plan allows {subscription.plan.max_members_per_chama} members. Please upgrade your plan.',
                        'upgrade_required': True
                    }), 403
        
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'success': False, 'message': 'Email is required'}), 400
        
        # Check if user exists
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        # Check if user is already a member
        chama = Chama.query.get(chama_id)
        if any(member.id == user.id for member in chama.members):
            return jsonify({'success': False, 'message': 'User is already a member'}), 400
        
        # Add user to chama
        chama.members.append(user)
        
        # Update member count for enterprise subscription
        if subscription:
            update_member_count(current_user.id, 1)
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'{user.username} has been added to the chama!'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@chama_bp.route('/<int:chama_id>/remove_member', methods=['POST'])
@login_required
@chama_admin_required
def remove_member(chama_id):
    """Remove a member from the chama (admin only)"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'success': False, 'message': 'User ID is required'}), 400
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        chama = Chama.query.get(chama_id)
        if not any(member.id == user.id for member in chama.members):
            return jsonify({'success': False, 'message': 'User is not a member'}), 400
        
        # Cannot remove the creator
        if user.id == chama.creator_id:
            return jsonify({'success': False, 'message': 'Cannot remove the chama creator'}), 400
        
        # Remove user from chama
        chama.members.remove(user)
        
        # Update member count for enterprise subscription
        from app.utils.enterprise_limits import update_member_count
        from app.models.enterprise import EnterpriseUserSubscription
        
        subscription = EnterpriseUserSubscription.query.filter_by(
            user_id=current_user.id,
            is_active=True
        ).first()
        
        if subscription:
            update_member_count(current_user.id, -1)
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'{user.username} has been removed from the chama!'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@chama_bp.route('/<int:chama_id>/transactions')
@login_required
@chama_member_required
def chama_transactions(chama_id):
    """View all transactions for a chama"""
    chama = Chama.query.get_or_404(chama_id)
    
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Get transactions with pagination
    transactions = Transaction.query.filter(
        Transaction.chama_id == chama_id
    ).order_by(desc(Transaction.created_at)).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('chama/transactions.html',
                         chama=chama,
                         transactions=transactions)

@chama_bp.route('/<int:chama_id>/pay-registration-fee', methods=['POST'])
@login_required
@chama_member_required
def pay_registration_fee(chama_id):
    """Pay registration fee for a chama"""
    try:
        data = request.get_json()
        phone = data.get('phone')
        
        if not phone:
            return jsonify({'success': False, 'message': 'Phone number is required'}), 400
        
        chama = Chama.query.get_or_404(chama_id)
        
        if chama.registration_fee <= 0:
            return jsonify({'success': False, 'message': 'No registration fee required for this chama'}), 400
        
        # Check if user has already paid registration fee
        existing_payment = RegistrationFeePayment.query.filter(
            RegistrationFeePayment.user_id == current_user.id,
            RegistrationFeePayment.chama_id == chama_id,
            RegistrationFeePayment.payment_status == 'completed'
        ).first()
        
        if existing_payment:
            return jsonify({'success': False, 'message': 'Registration fee already paid'}), 400
        
        # Create payment record
        payment = RegistrationFeePayment(
            user_id=current_user.id,
            chama_id=chama_id,
            amount=chama.registration_fee,
            payment_status='pending'
        )
        
        db.session.add(payment)
        db.session.commit()
        
        # Initiate M-Pesa STK push
        response = initiate_stk_push(
            phone_number=phone,
            amount=chama.registration_fee,
            account_reference=f"REG-{chama.id}-{current_user.id}",
            transaction_desc=f"Registration fee for {chama.name}"
        )
        
        if response.get('success'):
            return jsonify({
                'success': True,
                'message': 'Registration fee payment initiated. Please complete the payment on your phone.',
                'checkout_request_id': response.get('checkout_request_id')
            })
        else:
            # Update payment status to failed
            payment.payment_status = 'failed'
            db.session.commit()
            return jsonify({'success': False, 'message': 'Failed to initiate payment'}), 400
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@chama_bp.route('/search')
@login_required
def search_chamas():
    """Search for chamas to join"""
    try:
        query = request.args.get('q', '').strip()
        chamas = []
        
        if query:
            # Search for chamas by name (using ilike for case-insensitive search)
            chamas = Chama.query.filter(
                Chama.name.ilike(f'%{query}%'),
                Chama.status == 'active'
            ).all()
        else:
            # Show all active chamas when no search query
            chamas = Chama.query.filter(Chama.status == 'active').limit(50).all()
        
        # Filter out chamas user is already a member of
        try:
            user_chamas = current_user.get_chamas()
            user_chama_ids = [chama.id for chama in user_chamas]
            chamas = [chama for chama in chamas if chama.id not in user_chama_ids]
        except Exception as e:
            current_app.logger.error(f"Error filtering user chamas: {e}")
            # If there's an issue with user chamas, just show all chamas
        
        return render_template('chama/search.html', chamas=chamas, query=query)
        
    except Exception as e:
        current_app.logger.error(f"Error searching chamas: {e}")
        flash(f'Search is currently unavailable. Please try again later.', 'error')
        return render_template('chama/search.html', chamas=[], query='')

@chama_bp.route('/<int:chama_id>/request-join', methods=['POST'])
@login_required
def request_join_chama(chama_id):
    """Request to join a chama"""
    try:
        chama = Chama.query.get_or_404(chama_id)
        
        # Check if user is already a member
        if any(member.id == current_user.id for member in chama.members):
            return jsonify({'success': False, 'message': 'You are already a member of this chama'}), 400
        
        # Check if there's already a pending request
        existing_request = ChamaMembershipRequest.query.filter(
            ChamaMembershipRequest.user_id == current_user.id,
            ChamaMembershipRequest.chama_id == chama_id,
            ChamaMembershipRequest.status == 'pending'
        ).first()
        
        if existing_request:
            return jsonify({'success': False, 'message': 'You already have a pending request for this chama'}), 400
        
        # Create join request
        request_obj = ChamaMembershipRequest(
            user_id=current_user.id,
            chama_id=chama_id,
            request_type='join',
            status='pending'
        )
        
        db.session.add(request_obj)
        db.session.commit()
        
        # Send notification to admins
        admins = chama.admins
        for admin in admins:
            notification = Notification(
                user_id=admin.id,
                chama_id=chama_id,
                type='membership_request',
                title='New Join Request',
                message=f'{current_user.username} wants to join {chama.name}',
                related_id=request_obj.id
            )
            db.session.add(notification)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Join request sent successfully! Admins will review your request.'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@chama_bp.route('/membership-requests/<int:request_id>/approve', methods=['POST'])
@login_required
def approve_membership_request(request_id):
    """Approve a membership request (Admin only)"""
    try:
        membership_request = ChamaMembershipRequest.query.get_or_404(request_id)
        
        # Check if current user is admin/creator of the chama
        user_role = get_user_chama_role(current_user.id, membership_request.chama_id)
        if user_role not in ['admin', 'creator']:
            return jsonify({'success': False, 'message': 'You do not have permission to approve requests'}), 403
        
        # Add user to chama
        db.session.execute(
            db.text("INSERT INTO chama_members (user_id, chama_id, role, joined_at) VALUES (:user_id, :chama_id, :role, :joined_at)"),
            {
                'user_id': membership_request.user_id,
                'chama_id': membership_request.chama_id,
                'role': 'member',
                'joined_at': datetime.utcnow()
            }
        )
        
        # Update request status
        membership_request.status = 'approved'
        membership_request.approved_at = datetime.utcnow()
        membership_request.approved_by = current_user.id
        
        # Send notification to the user
        from app.models.notification import Notification
        notification = Notification(
            user_id=membership_request.user_id,
            chama_id=membership_request.chama_id,
            title='Join Request Approved',
            message=f'Your request to join {membership_request.chama.name} has been approved! Welcome to the chama.',
            type='membership_approved',
            related_id=membership_request.id
        )
        db.session.add(notification)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{membership_request.user.username} has been added to the chama'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error approving membership request: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@chama_bp.route('/membership-requests/<int:request_id>/reject', methods=['POST'])
@login_required
def reject_membership_request(request_id):
    """Reject a membership request (Admin only)"""
    try:
        membership_request = ChamaMembershipRequest.query.get_or_404(request_id)
        
        # Check if current user is admin/creator of the chama
        user_role = get_user_chama_role(current_user.id, membership_request.chama_id)
        if user_role not in ['admin', 'creator']:
            return jsonify({'success': False, 'message': 'You do not have permission to reject requests'}), 403
        
        # Update request status
        membership_request.status = 'rejected'
        membership_request.approved_at = datetime.utcnow()
        membership_request.approved_by = current_user.id
        
        # Send notification to the user
        from app.models.notification import Notification
        notification = Notification(
            user_id=membership_request.user_id,
            chama_id=membership_request.chama_id,
            title='Join Request Declined',
            message=f'Your request to join {membership_request.chama.name} has been declined.',
            type='membership_rejected',
            related_id=membership_request.id
        )
        db.session.add(notification)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Membership request has been rejected'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error rejecting membership request: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
def remove_chama_member(chama_id, member_id):
    """Remove a member from chama (admin only)"""
    try:
        chama = Chama.query.get_or_404(chama_id)
        
        # Check if current user is admin
        if not chama.is_admin(current_user.id):
            return jsonify({'success': False, 'message': 'Only admins can remove members'}), 403
        
        # Check if admin can remove this member
        if not chama.can_remove_member(current_user.id, member_id):
            return jsonify({'success': False, 'message': 'Cannot remove this member'}), 403
        
        # Get member to remove
        member = User.query.get_or_404(member_id)
        
        # Remove member
        success, message = chama.remove_member(member_id)
        
        if success:
            # Update member count for enterprise subscription
            from app.utils.enterprise_limits import update_member_count
            from app.models.enterprise import EnterpriseUserSubscription
            
            subscription = EnterpriseUserSubscription.query.filter_by(
                user_id=current_user.id,
                is_active=True
            ).first()
            
            if subscription:
                update_member_count(current_user.id, -1)
            
            # Send notification to removed member
            notification = Notification(
                user_id=member_id,
                chama_id=chama_id,
                type='membership_removed',
                title='Removed from Chama',
                message=f'You have been removed from {chama.name} by {current_user.username}'
            )
            db.session.add(notification)
            db.session.commit()
            
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@chama_bp.route('/<int:chama_id>/members/<int:member_id>/make-admin', methods=['POST'])
@login_required
def make_chama_admin(chama_id, member_id):
    """Make a member an admin (creator only)"""
    try:
        chama = Chama.query.get_or_404(chama_id)
        
        # Only creator can make new admins
        if current_user.id != chama.creator_id:
            return jsonify({'success': False, 'message': 'Only the chama creator can make new admins'}), 403
        
        # Update member role to admin
        stmt = chama_members_table.update().where(
            chama_members_table.c.user_id == member_id,
            chama_members_table.c.chama_id == chama_id
        ).values(role='admin')
        
        result = db.session.execute(stmt)
        
        if result.rowcount > 0:
            # Send notification to new admin
            member = User.query.get(member_id)
            notification = Notification(
                user_id=member_id,
                chama_id=chama_id,
                type='admin_promotion',
                title='Promoted to Admin',
                message=f'You have been promoted to admin in {chama.name} by {current_user.username}'
            )
            db.session.add(notification)
            db.session.commit()
            
            return jsonify({'success': True, 'message': f'{member.username} is now an admin'})
        else:
            return jsonify({'success': False, 'message': 'Member not found'}), 404
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@chama_bp.route('/<int:chama_id>/verify-payment', methods=['GET', 'POST'])
@login_required
@chama_member_required
def verify_payment(chama_id):
    """Manual payment verification using M-Pesa message"""
    chama = Chama.query.get_or_404(chama_id)
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            mpesa_message = data.get('mpesa_message', '').strip()
            payment_type = data.get('payment_type')
            amount = float(data.get('amount', 0))
            
            if not mpesa_message or not payment_type or amount <= 0:
                return jsonify({'success': False, 'message': 'All fields are required'}), 400
            
            # Extract transaction ID from M-Pesa message (simple regex)
            import re
            transaction_id_match = re.search(r'[A-Z0-9]{10}', mpesa_message)
            transaction_id = transaction_id_match.group() if transaction_id_match else None
            
            # Create verification record
            verification = ManualPaymentVerification(
                user_id=current_user.id,
                chama_id=chama_id,
                payment_type=payment_type,
                amount=amount,
                mpesa_message=mpesa_message,
                transaction_id=transaction_id,
                verification_status='pending'
            )
            
            db.session.add(verification)
            
            # Send notification to admins
            admins = chama.admins
            for admin in admins:
                notification = Notification(
                    user_id=admin.id,
                    chama_id=chama_id,
                    type='payment_verification',
                    title='Payment Verification Required',
                    message=f'{current_user.username} submitted payment verification for {payment_type} (Amount: {amount})',
                    related_id=verification.id
                )
                db.session.add(notification)
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Payment verification submitted. Admins will verify shortly.'
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500
    
    return render_template('chama/verify_payment.html', chama=chama)

@chama_bp.route('/<int:chama_id>/payment-verifications')
@login_required
@chama_admin_required
def payment_verifications(chama_id):
    """View pending payment verifications (admin only)"""
    chama = Chama.query.get_or_404(chama_id)
    
    verifications = ManualPaymentVerification.query.filter(
        ManualPaymentVerification.chama_id == chama_id
    ).order_by(ManualPaymentVerification.created_at.desc()).all()
    
    user_role = get_user_chama_role(current_user.id, chama_id)
    
    return render_template('chama/payment_verifications.html',
                         chama=chama,
                         verifications=verifications,
                         user_role=user_role)

@chama_bp.route('/verify-payment/<int:verification_id>/approve', methods=['POST'])
@login_required
def approve_payment_verification(verification_id):
    """Approve a payment verification (admin only)"""
    try:
        verification = ManualPaymentVerification.query.get_or_404(verification_id)
        chama = verification.chama
        
        # Check if current user is admin
        if not chama.is_admin(current_user.id):
            return jsonify({'success': False, 'message': 'Only admins can approve payments'}), 403
        
        data = request.get_json()
        notes = data.get('notes', '')
        
        # Update verification
        verification.verification_status = 'verified'
        verification.verified_by = current_user.id
        verification.verified_at = datetime.utcnow()
        verification.verification_notes = notes
        
        # Process the payment based on type
        if verification.payment_type == 'contribution':
            # Create transaction record
            transaction = Transaction(
                type='contribution',
                amount=verification.amount,
                description=f"Manual verification - {verification.transaction_id}",
                user_id=verification.user_id,
                chama_id=chama.id
            )
            db.session.add(transaction)
            
            # Update chama balance
            chama.total_balance += verification.amount
            
        elif verification.payment_type == 'registration_fee':
            # Create registration fee payment record
            payment = RegistrationFeePayment(
                user_id=verification.user_id,
                chama_id=chama.id,
                amount=verification.amount,
                mpesa_receipt_number=verification.transaction_id,
                payment_status='completed',
                payment_date=datetime.utcnow()
            )
            db.session.add(payment)
        
        # Send notification to user
        notification = Notification(
            user_id=verification.user_id,
            chama_id=chama.id,
            type='payment_approved',
            title='Payment Verified',
            message=f'Your {verification.payment_type} payment of {verification.amount} has been verified and approved by {current_user.username}',
            related_id=verification.id
        )
        db.session.add(notification)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Payment verification approved successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@chama_bp.route('/verify-payment/<int:verification_id>/reject', methods=['POST'])
@login_required
def reject_payment_verification(verification_id):
    """Reject a payment verification (admin only)"""
    try:
        verification = ManualPaymentVerification.query.get_or_404(verification_id)
        chama = verification.chama
        
        # Check if current user is admin
        if not chama.is_admin(current_user.id):
            return jsonify({'success': False, 'message': 'Only admins can reject payments'}), 403
        
        data = request.get_json()
        notes = data.get('notes', '')
        
        if not notes.strip():
            return jsonify({'success': False, 'message': 'Please provide a reason for rejection'}), 400
        
        # Update verification
        verification.verification_status = 'rejected'
        verification.verified_by = current_user.id
        verification.verified_at = datetime.utcnow()
        verification.verification_notes = notes
        
        # Send notification to user
        notification = Notification(
            user_id=verification.user_id,
            chama_id=chama.id,
            type='payment_rejected',
            title='Payment Verification Rejected',
            message=f'Your {verification.payment_type} payment verification has been rejected. Reason: {notes}' if notes else f'Your {verification.payment_type} payment verification has been rejected',
            related_id=verification.id
        )
        db.session.add(notification)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Payment verification rejected successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@chama_bp.route('/<int:chama_id>/appoint-role', methods=['POST'])
@login_required
@chama_admin_required
def appoint_role(chama_id):
    """Appoint secretary or treasurer role to a member"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        new_role = data.get('role')
        
        if not user_id or not new_role:
            return jsonify({'success': False, 'message': 'User ID and role are required'}), 400
        
        if new_role not in ['secretary', 'treasurer', 'admin', 'member']:
            return jsonify({'success': False, 'message': 'Invalid role'}), 400
        
        # Check if user is a member of the chama
        membership = db.session.query(chama_members_table).filter(
            chama_members_table.c.user_id == user_id,
            chama_members_table.c.chama_id == chama_id
        ).first()
        
        if not membership:
            return jsonify({'success': False, 'message': 'User is not a member of this chama'}), 404
        
        # Update the role
        db.session.execute(
            chama_members_table.update().where(
                and_(
                    chama_members_table.c.user_id == user_id,
                    chama_members_table.c.chama_id == chama_id
                )
            ).values(role=new_role)
        )
        
        # Create notification for the appointed user
        user = User.query.get(user_id)
        chama = Chama.query.get(chama_id)
        
        from app.models.notification import Notification
        notification = Notification(
            user_id=user_id,
            chama_id=chama_id,
            title=f"🎉 Role Appointment in {chama.name}",
            message=f"You have been appointed as {new_role.title()} in {chama.name}. You now have access to {new_role}-specific features.",
            type='system'
        )
        db.session.add(notification)
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'{user.username} has been appointed as {new_role.title()}'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@chama_bp.route('/<int:chama_id>/download/members')
@login_required
@chama_admin_required
def download_members(chama_id):
    """Download members list as CSV"""
    import csv
    import io
    from flask import make_response
    
    chama = Chama.query.get_or_404(chama_id)
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['Name', 'Email', 'Role', 'Joined Date', 'Phone'])
    
    # Get members with roles
    members_data = chama.get_members_with_roles()
    for member_data in members_data:
        user = member_data['user']
        writer.writerow([
            user.username,
            user.email,
            member_data['role'].title(),
            member_data['joined_at'].strftime('%Y-%m-%d') if member_data['joined_at'] else 'N/A',
            getattr(user, 'phone', 'N/A')
        ])
    
    output.seek(0)
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename={chama.name}_members.csv'
    
    return response

@chama_bp.route('/<int:chama_id>/download/transactions')
@login_required
@chama_admin_required
def download_transactions(chama_id):
    """Download transactions as CSV"""
    import csv
    import io
    from flask import make_response
    
    chama = Chama.query.get_or_404(chama_id)
    
    # Get all transactions for this chama
    transactions = Transaction.query.filter_by(chama_id=chama_id).order_by(desc(Transaction.created_at)).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['Date', 'Type', 'Amount', 'Member', 'Description', 'Status'])
    
    for transaction in transactions:
        writer.writerow([
            transaction.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            transaction.type.title(),
            transaction.amount,
            transaction.user.username,
            transaction.description or 'N/A',
            transaction.status or 'completed'
        ])
    
    output.seek(0)
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename={chama.name}_transactions.csv'
    
    return response

@chama_bp.route('/<int:chama_id>/download/financial-report')
@login_required
@chama_member_required
def download_financial_report(chama_id):
    """Download comprehensive financial report as PDF"""
    import io
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from flask import send_file
    
    chama = Chama.query.get_or_404(chama_id)
    user_role = current_user.get_chama_role(chama_id)
    
    # Only admins and treasurers can download full financial reports
    if user_role not in ['creator', 'admin', 'treasurer']:
        flash('Access denied. Only admins and treasurers can download financial reports.', 'error')
        return redirect(url_for('chama.chama_detail', chama_id=chama_id))
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title = Paragraph(f"<b>Financial Report - {chama.name}</b>", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 20))
    
    # Summary statistics
    total_contributions = db.session.query(db.func.sum(Transaction.amount)).filter(
        Transaction.chama_id == chama_id,
        Transaction.type == 'contribution'
    ).scalar() or 0
    
    total_loans = db.session.query(db.func.sum(Transaction.amount)).filter(
        Transaction.chama_id == chama_id,
        Transaction.type == 'loan'
    ).scalar() or 0
    
    summary_data = [
        ['Financial Summary', ''],
        ['Total Balance', f'KES {chama.total_balance:,.2f}'],
        ['Total Contributions', f'KES {total_contributions:,.2f}'],
        ['Total Loans', f'KES {total_loans:,.2f}'],
        ['Monthly Target', f'KES {chama.monthly_contribution:,.2f}'],
        ['Number of Members', str(chama.member_count)]
    ]
    
    summary_table = Table(summary_data, colWidths=[200, 200])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 30))
    
    # Recent transactions
    recent_transactions = Transaction.query.filter(
        Transaction.chama_id == chama_id
    ).order_by(desc(Transaction.created_at)).limit(20).all()
    
    if recent_transactions:
        elements.append(Paragraph("<b>Recent Transactions</b>", styles['Heading2']))
        elements.append(Spacer(1, 10))
        
        transaction_data = [['Date', 'Type', 'Amount', 'Member']]
        for transaction in recent_transactions:
            transaction_data.append([
                transaction.created_at.strftime('%Y-%m-%d'),
                transaction.type.title(),
                f'KES {transaction.amount:,.2f}',
                transaction.user.username
            ])
        
        transaction_table = Table(transaction_data, colWidths=[100, 80, 100, 120])
        transaction_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(transaction_table)
    
    doc.build(elements)
    buffer.seek(0)
    
    filename = f"{chama.name}_financial_report_{datetime.now().strftime('%Y%m%d')}.pdf"
    return send_file(buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')

def get_user_chama_role(user_id, chama_id):
    """Get the role of a user in a specific chama"""
    try:
        membership = db.session.query(chama_members_table).filter(
            chama_members_table.c.user_id == user_id,
            chama_members_table.c.chama_id == chama_id
        ).first()
        
        if membership:
            current_app.logger.info(f"Found membership for user {user_id} in chama {chama_id}: role={membership.role}")
            return membership.role
        else:
            current_app.logger.warning(f"No membership found for user {user_id} in chama {chama_id}")
            return None
    except Exception as e:
        current_app.logger.error(f"Error getting user role for user {user_id} in chama {chama_id}: {str(e)}")
        return None
