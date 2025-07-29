"""
Mobile App Integration API
========================
REST API endpoints for mobile app integration with standardized responses

Standard Response Format:
{
    "success": true/false,
    "status": "success"/"error", 
    "status_code": 200,
    "message": "Success message",
    "timestamp": "2025-07-29T17:22:00Z",
    "data": { ... }
}
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_login import current_user
from app.models import User, Chama, ChamaMember
from app import db
from app.utils.api_response import APIResponse, APIValidator, handle_api_exceptions, StatusCode
from werkzeug.security import check_password_hash
from datetime import timedelta
import json

mobile_api = Blueprint('mobile_api', __name__, url_prefix='/api/mobile')

@mobile_api.route('/health', methods=['GET'])
def api_health():
    """API health check with standardized response"""
    return APIResponse.success(
        data={
            'status': 'healthy',
            'version': '1.0.0',
            'api_name': 'CHAMAlink Mobile API',
            'features': [
                'authentication',
                'user_management', 
                'chama_management',
                'transactions',
                'analytics'
            ]
        },
        message="API is healthy and operational"
    )

@mobile_api.route('/auth/login', methods=['POST'])
@handle_api_exceptions
def mobile_login():
    """Mobile app login endpoint with standardized responses"""
    data = request.get_json()
    
    # Validate required fields
    errors = APIValidator.validate_required_fields(data, ['email', 'password'])
    if errors:
        return APIResponse.validation_error(errors)
    
    email = data.get('email')
    password = data.get('password')
    device_id = data.get('device_id')
    
    # Validate email format
    if not APIValidator.validate_email(email):
        return APIResponse.validation_error(['Invalid email format'])
    
    user = User.query.filter_by(email=email).first()
    
    if user and check_password_hash(user.password_hash, password):
        # Create JWT token for mobile
        access_token = create_access_token(
            identity=user.id,
            expires_delta=timedelta(days=30)
        )
        
        # Update device info if provided
        if device_id:
            user.mobile_device_id = device_id
            db.session.commit()
        
        return APIResponse.success(
            data={
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'phone_number': user.phone_number,
                    'country_code': user.country_code,
                    'preferred_currency': user.preferred_currency
                },
                'access_token': access_token,
                'token_type': 'Bearer',
                'expires_in': 30 * 24 * 60 * 60  # 30 days in seconds
            },
            message="Login successful"
        )
    else:
        return APIResponse.unauthorized("Invalid credentials")

@mobile_api.route('/user/profile', methods=['GET'])
@jwt_required()
def get_mobile_profile():
    """Get user profile for mobile app"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        # Get user's chamas
        memberships = ChamaMember.query.filter_by(user_id=user.id).all()
        chamas = []
        
        for membership in memberships:
            chama = membership.chama
            chamas.append({
                'id': chama.id,
                'name': chama.name,
                'description': chama.description,
                'role': membership.role,
                'status': chama.status,
                'member_count': len(chama.members),
                'contribution_amount': float(chama.contribution_amount or 0),
                'currency': chama.currency or 'KES'
            })
        
        return jsonify({
            'success': True,
            'data': {
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'phone_number': user.phone_number,
                    'country_code': user.country_code,
                    'country_name': user.country_name,
                    'preferred_currency': user.preferred_currency,
                    'is_email_verified': user.is_email_verified
                },
                'chamas': chamas,
                'stats': {
                    'total_chamas': len(chamas),
                    'active_memberships': len([c for c in chamas if c['status'] == 'active'])
                }
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@mobile_api.route('/chamas', methods=['GET'])
@jwt_required()
def get_mobile_chamas():
    """Get user's chamas for mobile app"""
    try:
        user_id = get_jwt_identity()
        memberships = ChamaMember.query.filter_by(user_id=user_id).all()
        
        chamas = []
        for membership in memberships:
            chama = membership.chama
            
            # Calculate basic stats
            total_members = len(chama.members)
            contribution_amount = float(chama.contribution_amount or 0)
            
            chamas.append({
                'id': chama.id,
                'name': chama.name,
                'description': chama.description,
                'category': chama.category,
                'status': chama.status,
                'role': membership.role,
                'contribution_amount': contribution_amount,
                'contribution_frequency': chama.contribution_frequency,
                'currency': chama.currency or 'KES',
                'member_count': total_members,
                'meeting_day': chama.meeting_day,
                'meeting_time': chama.meeting_time.strftime('%H:%M') if chama.meeting_time else None,
                'next_meeting_date': chama.next_meeting_date.isoformat() if chama.next_meeting_date else None,
                'created_at': chama.created_at.isoformat(),
                'stats': {
                    'total_contributions': contribution_amount * total_members,  # Simplified
                    'total_members': total_members,
                    'active_loans': 0  # Would query loan table
                }
            })
        
        return jsonify({
            'success': True,
            'data': {
                'chamas': chamas,
                'total_count': len(chamas)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@mobile_api.route('/chama/<int:chama_id>', methods=['GET'])
@jwt_required()
def get_mobile_chama_details(chama_id):
    """Get detailed chama information for mobile app"""
    try:
        user_id = get_jwt_identity()
        membership = ChamaMember.query.filter_by(
            user_id=user_id, 
            chama_id=chama_id
        ).first()
        
        if not membership:
            return jsonify({
                'success': False,
                'error': 'Not a member of this chama'
            }), 403
        
        chama = membership.chama
        
        # Get all members
        members = []
        for member in chama.members:
            members.append({
                'id': member.user.id,
                'name': f"{member.user.first_name} {member.user.last_name}",
                'role': member.role,
                'phone_number': member.user.phone_number,
                'joined_at': member.joined_at.isoformat() if member.joined_at else None
            })
        
        return jsonify({
            'success': True,
            'data': {
                'chama': {
                    'id': chama.id,
                    'name': chama.name,
                    'description': chama.description,
                    'category': chama.category,
                    'status': chama.status,
                    'contribution_amount': float(chama.contribution_amount or 0),
                    'contribution_frequency': chama.contribution_frequency,
                    'currency': chama.currency or 'KES',
                    'meeting_day': chama.meeting_day,
                    'meeting_time': chama.meeting_time.strftime('%H:%M') if chama.meeting_time else None,
                    'meeting_location': chama.meeting_location,
                    'next_meeting_date': chama.next_meeting_date.isoformat() if chama.next_meeting_date else None,
                    'terms_and_conditions': chama.terms_and_conditions,
                    'created_at': chama.created_at.isoformat(),
                    'member_count': len(chama.members)
                },
                'members': members,
                'user_role': membership.role,
                'permissions': {
                    'can_edit': membership.role in ['admin', 'chairman'],
                    'can_manage_members': membership.role in ['admin', 'chairman', 'secretary'],
                    'can_manage_finances': membership.role in ['admin', 'treasurer'],
                    'can_view_reports': True
                }
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@mobile_api.route('/notifications', methods=['GET'])
@jwt_required()
def get_mobile_notifications():
    """Get notifications for mobile app"""
    try:
        user_id = get_jwt_identity()
        
        # This would integrate with the notification system
        # For now, returning sample notifications
        notifications = [
            {
                'id': 1,
                'title': 'Meeting Reminder',
                'message': 'Your chama meeting is tomorrow at 2:00 PM',
                'type': 'meeting',
                'created_at': '2025-07-12T10:00:00Z',
                'is_read': False
            },
            {
                'id': 2,
                'title': 'Contribution Due',
                'message': 'Your monthly contribution of KES 1,000 is due in 3 days',
                'type': 'payment',
                'created_at': '2025-07-11T15:30:00Z',
                'is_read': False
            }
        ]
        
        return jsonify({
            'success': True,
            'data': {
                'notifications': notifications,
                'unread_count': len([n for n in notifications if not n['is_read']])
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@mobile_api.route('/sync', methods=['POST'])
@jwt_required()
def mobile_sync():
    """Sync mobile app data with server"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Handle offline data sync
        offline_actions = data.get('offline_actions', [])
        sync_results = []
        
        for action in offline_actions:
            try:
                # Process offline action
                action_type = action.get('type')
                action_data = action.get('data')
                
                if action_type == 'update_profile':
                    user = User.query.get(user_id)
                    if user:
                        user.first_name = action_data.get('first_name', user.first_name)
                        user.last_name = action_data.get('last_name', user.last_name)
                        db.session.commit()
                
                sync_results.append({
                    'action_id': action.get('id'),
                    'status': 'success'
                })
                
            except Exception as e:
                sync_results.append({
                    'action_id': action.get('id'),
                    'status': 'error',
                    'error': str(e)
                })
        
        # Return latest data for sync
        return jsonify({
            'success': True,
            'data': {
                'sync_results': sync_results,
                'server_timestamp': '2025-07-12T15:30:00Z',
                'sync_status': 'complete'
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@mobile_api.route('/register-device', methods=['POST'])
@jwt_required()
def register_mobile_device():
    """Register mobile device for push notifications"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        device_token = data.get('device_token')
        device_type = data.get('device_type')  # 'ios' or 'android'
        
        if not device_token:
            return jsonify({
                'success': False,
                'error': 'Device token required'
            }), 400
        
        user = User.query.get(user_id)
        if user:
            # Store device token for push notifications
            user.mobile_device_token = device_token
            user.mobile_device_type = device_type
            db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Device registered for push notifications'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@mobile_api.route('/app-config', methods=['GET'])
def get_mobile_app_config():
    """Get mobile app configuration"""
    try:
        config = {
            'api_version': '1.0',
            'minimum_app_version': '1.0.0',
            'features': {
                'push_notifications': True,
                'offline_mode': True,
                'biometric_auth': True,
                'dark_mode': True
            },
            'endpoints': {
                'mpesa_callback': '/api/mobile/mpesa/callback',
                'support_chat': '/api/mobile/support/chat'
            },
            'currencies': ['KES', 'USD', 'EUR', 'TZS', 'UGX', 'GBP'],
            'supported_countries': [
                {'code': 'KE', 'name': 'Kenya', 'currency': 'KES'},
                {'code': 'TZ', 'name': 'Tanzania', 'currency': 'TZS'},
                {'code': 'UG', 'name': 'Uganda', 'currency': 'UGX'}
            ]
        }
        
        return jsonify({
            'success': True,
            'data': config
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@mobile_api.route('/transactions', methods=['GET'])
@jwt_required()
def get_transactions():
    """Get user's transactions for mobile app"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        # Get transactions from user's chamas
        transactions = []
        for membership in user.chama_memberships:
            chama = membership.chama
            # This would typically fetch from a Transaction model
            # For now, return mock data structure
            transactions.extend([
                {
                    'id': f'txn_{chama.id}_001',
                    'chama_id': chama.id,
                    'chama_name': chama.name,
                    'type': 'contribution',
                    'amount': 5000,
                    'currency': 'KSH',
                    'date': '2025-07-29T10:00:00Z',
                    'status': 'completed',
                    'description': 'Monthly contribution'
                },
                {
                    'id': f'txn_{chama.id}_002',
                    'chama_id': chama.id,
                    'chama_name': chama.name,
                    'type': 'withdrawal',
                    'amount': 2000,
                    'currency': 'KSH',
                    'date': '2025-07-25T14:30:00Z',
                    'status': 'pending',
                    'description': 'Emergency withdrawal request'
                }
            ])
        
        # Sort by date (newest first)
        transactions.sort(key=lambda x: x['date'], reverse=True)
        
        return jsonify({
            'success': True,
            'data': {
                'transactions': transactions,
                'total_count': len(transactions),
                'summary': {
                    'total_contributions': sum(t['amount'] for t in transactions if t['type'] == 'contribution'),
                    'total_withdrawals': sum(t['amount'] for t in transactions if t['type'] == 'withdrawal'),
                    'pending_count': sum(1 for t in transactions if t['status'] == 'pending')
                }
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@mobile_api.route('/transactions/<int:chama_id>', methods=['GET'])
@jwt_required()
def get_chama_transactions(chama_id):
    """Get transactions for a specific chama"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        # Check if user is member of this chama
        membership = ChamaMember.query.filter_by(
            user_id=user_id,
            chama_id=chama_id
        ).first()
        
        if not membership:
            return jsonify({
                'success': False,
                'error': 'Access denied'
            }), 403
        
        chama = Chama.query.get(chama_id)
        if not chama:
            return jsonify({
                'success': False,
                'error': 'Chama not found'
            }), 404
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        transaction_type = request.args.get('type')  # 'contribution', 'withdrawal', etc.
        
        # Mock transactions for this chama
        all_transactions = [
            {
                'id': f'txn_{chama_id}_{i:03d}',
                'chama_id': chama_id,
                'chama_name': chama.name,
                'type': 'contribution' if i % 3 != 0 else 'withdrawal',
                'amount': 5000 if i % 3 != 0 else 2000,
                'currency': 'KSH',
                'date': f'2025-07-{29-i:02d}T{10+i%12:02d}:00:00Z',
                'status': 'completed' if i % 4 != 0 else 'pending',
                'description': f'Transaction #{i:03d}',
                'member_name': user.username,
                'reference': f'REF{chama_id}{i:06d}'
            } for i in range(1, 101)  # 100 mock transactions
        ]
        
        # Filter by type if specified
        if transaction_type:
            all_transactions = [t for t in all_transactions if t['type'] == transaction_type]
        
        # Pagination
        start = (page - 1) * per_page
        end = start + per_page
        transactions = all_transactions[start:end]
        
        return jsonify({
            'success': True,
            'data': {
                'transactions': transactions,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': len(all_transactions),
                    'pages': (len(all_transactions) + per_page - 1) // per_page
                },
                'summary': {
                    'total_contributions': sum(t['amount'] for t in all_transactions if t['type'] == 'contribution'),
                    'total_withdrawals': sum(t['amount'] for t in all_transactions if t['type'] == 'withdrawal'),
                    'balance': sum(t['amount'] if t['type'] == 'contribution' else -t['amount'] for t in all_transactions if t['status'] == 'completed')
                }
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
