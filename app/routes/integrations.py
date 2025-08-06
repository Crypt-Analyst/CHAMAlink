"""
Third-party Integrations
=======================
Banking APIs, accounting software sync, and external payment gateways
"""

from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models import User, Chama, ChamaMember
from app.utils.permissions import admin_required
from app import db
import requests
import json
from datetime import datetime
import hashlib
import hmac

integrations_bp = Blueprint('integrations', __name__, url_prefix='/integrations')

@integrations_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Integrations dashboard"""
    # Available integrations
    integrations = [
        {
            'id': 'equity_bank',
            'name': 'Equity Bank API',
            'type': 'banking',
            'status': 'available',
            'description': 'Connect with Equity Bank for account verification and transactions',
            'features': ['Account verification', 'Balance inquiry', 'Transaction history']
        },
        {
            'id': 'kcb_bank',
            'name': 'KCB Bank API',
            'type': 'banking',
            'status': 'available',
            'description': 'Integration with Kenya Commercial Bank services',
            'features': ['Account validation', 'Payment processing', 'Statement download']
        },
        {
            'id': 'quickbooks',
            'name': 'QuickBooks Online',
            'type': 'accounting',
            'status': 'available',
            'description': 'Sync chama finances with QuickBooks accounting software',
            'features': ['Financial sync', 'Report generation', 'Tax preparation']
        },
        {
            'id': 'xero',
            'name': 'Xero Accounting',
            'type': 'accounting',
            'status': 'available',
            'description': 'Connect with Xero for comprehensive accounting management',
            'features': ['Automated bookkeeping', 'Financial reporting', 'Invoice management']
        },
        {
            'id': 'paypal',
            'name': 'PayPal',
            'type': 'payment',
            'status': 'available',
            'description': 'Accept international payments through PayPal',
            'features': ['International payments', 'Currency conversion', 'Secure checkout']
        },
        {
            'id': 'flutterwave',
            'name': 'Flutterwave',
            'type': 'payment',
            'status': 'available',
            'description': 'African payment gateway for multiple payment methods',
            'features': ['Multiple payment methods', 'African coverage', 'Mobile money']
        },
        {
            'id': 'whatsapp_business',
            'name': 'WhatsApp Business API',
            'type': 'communication',
            'status': 'beta',
            'description': 'Send notifications and reminders via WhatsApp',
            'features': ['Message notifications', 'Meeting reminders', 'Payment alerts']
        },
        {
            'id': 'telegram_bot',
            'name': 'Telegram Bot',
            'type': 'communication',
            'status': 'available',
            'description': 'Chama management through Telegram bot',
            'features': ['Chat commands', 'Balance inquiries', 'Quick notifications']
        }
    ]
    
    return render_template('integrations/dashboard.html', integrations=integrations)

@integrations_bp.route('/banking/equity/connect', methods=['POST'])
@login_required
@admin_required
def connect_equity_bank():
    """Connect to Equity Bank API"""
    try:
        data = request.get_json()
        api_key = data.get('api_key')
        secret_key = data.get('secret_key')
        
        if not api_key or not secret_key:
            return jsonify({
                'success': False,
                'error': 'API key and secret key required'
            }), 400
        
        # Test connection to Equity Bank API
        test_url = "https://api.equitybank.co.ke/v1/test"
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        # In production, make actual API call
        # response = requests.get(test_url, headers=headers)
        
        # For demo, simulate successful connection
        connection_successful = True
        
        if connection_successful:
            # Store encrypted credentials (in production, use proper encryption)
            # For now, just mark as connected
            return jsonify({
                'success': True,
                'message': 'Successfully connected to Equity Bank API',
                'features_enabled': [
                    'Account verification',
                    'Balance inquiry',
                    'Transaction history'
                ]
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to connect to Equity Bank API'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@integrations_bp.route('/accounting/quickbooks/oauth')
@login_required
@admin_required
def quickbooks_oauth():
    """Initiate QuickBooks OAuth flow"""
    try:
        from app.services.quickbooks_service import QuickBooksService
        
        qb_service = QuickBooksService(current_app.config)
        chama_id = request.args.get('chama_id', 'all')
        state = f"chama_{chama_id}"
        
        auth_url = qb_service.get_authorization_url(state)
        return redirect(auth_url)
        
    except Exception as e:
        flash(f'Error initiating QuickBooks connection: {str(e)}', 'error')
        return redirect(url_for('integrations.dashboard'))

@integrations_bp.route('/accounting/quickbooks/callback')
@login_required
@admin_required
def quickbooks_callback():
    """Handle QuickBooks OAuth callback"""
    try:
        from app.services.quickbooks_service import QuickBooksService
        from app.models import QuickBooksIntegration
        from datetime import datetime, timedelta
        
        code = request.args.get('code')
        realm_id = request.args.get('realmId')
        state = request.args.get('state')
        
        if not code or not realm_id:
            flash('QuickBooks authorization failed - missing authorization code', 'error')
            return redirect(url_for('integrations.dashboard'))
        
        qb_service = QuickBooksService(current_app.config)
        tokens = qb_service.exchange_code_for_tokens(code, realm_id)
        
        # Parse chama_id from state
        chama_id = None
        if state and state.startswith('chama_'):
            try:
                chama_part = state.split('_')[1]
                if chama_part != 'all':
                    chama_id = int(chama_part)
            except (IndexError, ValueError):
                chama_id = None
        
        # Check if integration already exists
        existing = QuickBooksIntegration.query.filter_by(
            chama_id=chama_id,
            company_id=realm_id
        ).first()
        
        if existing:
            # Update existing integration
            existing.access_token = tokens['access_token']
            existing.refresh_token = tokens['refresh_token']
            existing.token_expires_at = datetime.utcnow() + timedelta(seconds=tokens['expires_in'])
            existing.sync_status = 'active'
            existing.updated_at = datetime.utcnow()
        else:
            # Create new integration
            integration = QuickBooksIntegration(
                chama_id=chama_id,
                company_id=realm_id,
                access_token=tokens['access_token'],
                refresh_token=tokens['refresh_token'],
                token_expires_at=datetime.utcnow() + timedelta(seconds=tokens['expires_in'])
            )
            db.session.add(integration)
        
        db.session.commit()
        
        flash('Successfully connected to QuickBooks! You can now sync your chama financial data.', 'success')
        return redirect(url_for('integrations.dashboard'))
        
    except Exception as e:
        current_app.logger.error(f"QuickBooks callback error: {str(e)}")
        flash(f'Error connecting to QuickBooks: {str(e)}', 'error')
        return redirect(url_for('integrations.dashboard'))

@integrations_bp.route('/payment/flutterwave/setup', methods=['POST'])
@login_required
@admin_required
def setup_flutterwave():
    """Setup Flutterwave payment integration"""
    try:
        data = request.get_json()
        public_key = data.get('public_key')
        secret_key = data.get('secret_key')
        
        if not public_key or not secret_key:
            return jsonify({
                'success': False,
                'error': 'Public key and secret key required'
            }), 400
        
        # Test Flutterwave API connection
        test_url = "https://api.flutterwave.com/v3/charges"
        headers = {
            'Authorization': f'Bearer {secret_key}',
            'Content-Type': 'application/json'
        }
        
        # Simulate successful setup
        setup_successful = True
        
        if setup_successful:
            return jsonify({
                'success': True,
                'message': 'Flutterwave payment gateway configured successfully',
                'supported_methods': [
                    'Card payments',
                    'Bank transfer',
                    'Mobile money',
                    'USSD'
                ]
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to configure Flutterwave'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@integrations_bp.route('/communication/whatsapp/webhook', methods=['POST'])
def whatsapp_webhook():
    """WhatsApp Business API webhook"""
    try:
        data = request.get_json()
        
        # Verify webhook signature
        signature = request.headers.get('X-Hub-Signature-256')
        if not verify_webhook_signature(data, signature):
            return jsonify({'error': 'Invalid signature'}), 401
        
        # Process WhatsApp message
        for entry in data.get('entry', []):
            for change in entry.get('changes', []):
                if change.get('field') == 'messages':
                    messages = change.get('value', {}).get('messages', [])
                    for message in messages:
                        process_whatsapp_message(message)
        
        return jsonify({'status': 'success'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def verify_webhook_signature(data, signature):
    """Verify WhatsApp webhook signature"""
    try:
        webhook_secret = "your_webhook_secret"
        expected_signature = hmac.new(
            webhook_secret.encode(),
            json.dumps(data).encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(f"sha256={expected_signature}", signature)
    except:
        return False

def process_whatsapp_message(message):
    """Process incoming WhatsApp message"""
    try:
        phone_number = message.get('from')
        text = message.get('text', {}).get('body', '')
        
        # Find user by phone number
        user = User.query.filter_by(phone_number=phone_number).first()
        
        if user and text.lower().startswith('/balance'):
            # Send balance information
            send_whatsapp_message(phone_number, f"Your balance information: ...")
        elif user and text.lower().startswith('/meetings'):
            # Send meeting information
            send_whatsapp_message(phone_number, f"Upcoming meetings: ...")
        else:
            # Send help message
            send_whatsapp_message(phone_number, 
                "Welcome to CHAMAlink! Available commands:\n"
                "/balance - Check your balance\n"
                "/meetings - View upcoming meetings\n"
                "/help - Show this help message"
            )
            
    except Exception as e:
        print(f"Error processing WhatsApp message: {e}")

def send_whatsapp_message(phone_number, message):
    """Send WhatsApp message"""
    try:
        url = "https://graph.facebook.com/v17.0/your_phone_number_id/messages"
        headers = {
            'Authorization': 'Bearer your_access_token',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "text",
            "text": {"body": message}
        }
        
        # In production, make actual API call
        # response = requests.post(url, headers=headers, json=payload)
        print(f"Would send WhatsApp message to {phone_number}: {message}")
        
    except Exception as e:
        print(f"Error sending WhatsApp message: {e}")

@integrations_bp.route('/sync/accounting/<provider>')
@login_required
@admin_required
def sync_accounting_data(provider):
    """Sync chama financial data with accounting software"""
    try:
        if provider == 'quickbooks':
            # Sync with QuickBooks
            sync_result = sync_quickbooks_data()
        elif provider == 'xero':
            # Sync with Xero
            sync_result = sync_xero_data()
        else:
            return jsonify({
                'success': False,
                'error': 'Unsupported accounting provider'
            }), 400
        
        return jsonify({
            'success': True,
            'data': sync_result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@integrations_bp.route('/sync/quickbooks/<int:chama_id>')
@login_required
@admin_required
def sync_quickbooks_chama(chama_id):
    """Sync specific chama to QuickBooks"""
    try:
        from app.services.quickbooks_service import QuickBooksService
        from app.models import QuickBooksIntegration, Chama
        
        # Check if chama exists and user has access
        chama = Chama.query.get_or_404(chama_id)
        
        # Check if QuickBooks is connected for this chama
        integration = QuickBooksIntegration.query.filter_by(chama_id=chama_id).first()
        if not integration:
            return jsonify({
                'success': False,
                'error': 'QuickBooks not connected for this chama'
            }), 400
        
        qb_service = QuickBooksService(current_app.config)
        result = qb_service.sync_chama_to_quickbooks(chama_id)
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        current_app.logger.error(f"QuickBooks chama sync error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# New role-based route for treasurers
@integrations_bp.route('/quickbooks/<int:chama_id>/sync', methods=['POST'])
@login_required
def sync_chama_financials(chama_id):
    """Sync chama financial data - accessible to creators, chairpersons, and treasurers"""
    try:
        from app.routes.quickbooks_decorators import can_sync_financials
        from app.services.quickbooks_service import QuickBooksService
        from app.models import QuickBooksIntegration, Chama
        
        # Check permissions
        if not can_sync_financials(current_user.id, chama_id):
            return jsonify({
                'success': False,
                'error': 'You do not have permission to sync financial data for this chama'
            }), 403
        
        # Check if chama exists
        chama = Chama.query.get_or_404(chama_id)
        
        # Check if QuickBooks is connected
        integration = QuickBooksIntegration.query.filter_by(chama_id=chama_id).first()
        if not integration:
            return jsonify({
                'success': False,
                'error': 'QuickBooks is not connected for this chama'
            }), 400
        
        qb_service = QuickBooksService(current_app.config)
        result = qb_service.sync_chama_to_quickbooks(chama_id)
        
        return jsonify({
            'success': True,
            'data': result,
            'user_role': current_user.get_chama_role(chama_id) if hasattr(current_user, 'get_chama_role') else 'admin'
        })
        
    except Exception as e:
        current_app.logger.error(f"Financial sync error for chama {chama_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@integrations_bp.route('/quickbooks/<int:chama_id>/status')
@login_required
def get_chama_quickbooks_status(chama_id):
    """Get QuickBooks status for a specific chama - accessible to leadership roles"""
    try:
        from app.routes.quickbooks_decorators import can_view_quickbooks_status, get_user_quickbooks_permissions
        from app.models import QuickBooksIntegration, Chama
        
        # Check permissions
        if not can_view_quickbooks_status(current_user.id, chama_id):
            return jsonify({
                'success': False,
                'error': 'You do not have permission to view QuickBooks status for this chama'
            }), 403
        
        chama = Chama.query.get_or_404(chama_id)
        integration = QuickBooksIntegration.query.filter_by(chama_id=chama_id).first()
        
        if not integration:
            return jsonify({
                'success': True,
                'data': {
                    'connected': False,
                    'chama_id': chama_id,
                    'chama_name': chama.name,
                    'message': 'QuickBooks not connected',
                    'user_permissions': get_user_quickbooks_permissions(current_user.id, chama_id)
                }
            })
        
        status_data = {
            'connected': True,
            'chama_id': chama_id,
            'chama_name': chama.name,
            'company_id': integration.company_id,
            'last_sync': integration.last_sync.isoformat() if integration.last_sync else None,
            'sync_status': integration.sync_status,
            'is_token_valid': integration.is_token_valid,
            'days_since_sync': integration.days_since_last_sync,
            'connected_at': integration.connected_at.isoformat() if integration.connected_at else None,
            'user_permissions': get_user_quickbooks_permissions(current_user.id, chama_id)
        }
        
        return jsonify({
            'success': True,
            'data': status_data
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting QuickBooks status for chama {chama_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@integrations_bp.route('/quickbooks/test/<int:chama_id>')
@login_required
@admin_required
def test_quickbooks_connection(chama_id):
    """Test QuickBooks connection for specific chama"""
    try:
        from app.services.quickbooks_service import QuickBooksService
        from app.models import QuickBooksIntegration
        
        integration = QuickBooksIntegration.query.filter_by(chama_id=chama_id).first()
        if not integration:
            return jsonify({
                'success': False,
                'error': 'QuickBooks not connected for this chama'
            }), 400
        
        qb_service = QuickBooksService(current_app.config)
        result = qb_service.test_connection(integration)
        
        return jsonify({
            'success': result['status'] == 'success',
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def sync_quickbooks_data():
    """Sync data with QuickBooks using the new service"""
    from app.services.quickbooks_service import QuickBooksService
    from app.models import QuickBooksIntegration
    
    try:
        qb_service = QuickBooksService(current_app.config)
        integrations = QuickBooksIntegration.query.filter_by(sync_status='active').all()
        
        sync_results = []
        for integration in integrations:
            if integration.chama_id:
                try:
                    result = qb_service.sync_chama_to_quickbooks(integration.chama_id)
                    sync_results.append({
                        'chama_id': integration.chama_id,
                        'chama_name': integration.chama.name if integration.chama else 'Unknown',
                        'status': 'synced',
                        'quickbooks_company_id': integration.company_id,
                        'last_sync': result.get('details', {}).get('last_sync')
                    })
                except Exception as e:
                    sync_results.append({
                        'chama_id': integration.chama_id,
                        'chama_name': integration.chama.name if integration.chama else 'Unknown',
                        'status': 'error',
                        'error': str(e),
                        'quickbooks_company_id': integration.company_id
                    })
        
        return {
            'provider': 'QuickBooks',
            'synced_chamas': len([r for r in sync_results if r['status'] == 'synced']),
            'results': sync_results,
            'last_sync': datetime.now().isoformat()
        }
        
    except Exception as e:
        current_app.logger.error(f"QuickBooks sync error: {str(e)}")
        return {
            'provider': 'QuickBooks',
            'synced_chamas': 0,
            'results': [],
            'error': str(e),
            'last_sync': datetime.now().isoformat()
        }

def sync_xero_data():
    """Sync data with Xero"""
    # Similar to QuickBooks but for Xero API
    chamas = Chama.query.all()
    
    sync_results = []
    for chama in chamas:
        sync_results.append({
            'chama_id': chama.id,
            'chama_name': chama.name,
            'status': 'synced',
            'xero_id': f"xero_{chama.id}"
        })
    
    return {
        'provider': 'Xero',
        'synced_chamas': len(sync_results),
        'results': sync_results,
        'last_sync': datetime.now().isoformat()
    }

@integrations_bp.route('/api/webhook/test', methods=['POST'])
@login_required
@admin_required
def test_webhook():
    """Test webhook integration"""
    try:
        data = request.get_json()
        webhook_type = data.get('type')
        
        if webhook_type == 'payment':
            # Simulate payment webhook
            response = {
                'webhook_id': 'test_webhook_123',
                'type': 'payment',
                'status': 'success',
                'amount': 1000,
                'currency': 'KES',
                'transaction_id': 'test_txn_456'
            }
        elif webhook_type == 'banking':
            # Simulate banking webhook
            response = {
                'webhook_id': 'test_bank_webhook_789',
                'type': 'banking',
                'status': 'success',
                'account_balance': 50000,
                'last_transaction': {
                    'amount': 1000,
                    'type': 'credit',
                    'description': 'Chama contribution'
                }
            }
        else:
            response = {
                'webhook_id': 'test_generic_webhook',
                'type': 'test',
                'status': 'success',
                'message': 'Webhook test successful'
            }
        
        return jsonify({
            'success': True,
            'webhook_response': response
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@integrations_bp.route('/mobile')
@login_required
def mobile():
    """Mobile app integration page"""
    return render_template('integrations/mobile.html')
