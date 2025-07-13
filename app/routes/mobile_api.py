"""
Mobile App Integration API
========================
REST API endpoints for mobile app integration
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_login import current_user
from app.models import User, Chama, ChamaMember
from app import db
from werkzeug.security import check_password_hash
from datetime import timedelta
import json

mobile_api = Blueprint('mobile_api', __name__, url_prefix='/api/mobile')

@mobile_api.route('/auth/login', methods=['POST'])
def mobile_login():
    """Mobile app login endpoint"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        device_id = data.get('device_id')
        
        if not email or not password:
            return jsonify({
                'success': False,
                'error': 'Email and password required'
            }), 400
        
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
                        'preferred_currency': user.preferred_currency
                    },
                    'access_token': access_token,
                    'token_type': 'Bearer'
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid credentials'
            }), 401
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

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
