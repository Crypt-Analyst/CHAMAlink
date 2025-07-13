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
        # QuickBooks OAuth parameters
        client_id = "your_quickbooks_client_id"
        redirect_uri = url_for('integrations.quickbooks_callback', _external=True)
        scope = "com.intuit.quickbooks.accounting"
        state = "security_token"  # Should be randomly generated
        
        oauth_url = (
            f"https://appcenter.intuit.com/connect/oauth2?"
            f"client_id={client_id}&"
            f"scope={scope}&"
            f"redirect_uri={redirect_uri}&"
            f"response_type=code&"
            f"access_type=offline&"
            f"state={state}"
        )
        
        return redirect(oauth_url)
        
    except Exception as e:
        flash(f'Error initiating QuickBooks connection: {str(e)}', 'error')
        return redirect(url_for('integrations.dashboard'))

@integrations_bp.route('/accounting/quickbooks/callback')
@login_required
@admin_required
def quickbooks_callback():
    """Handle QuickBooks OAuth callback"""
    try:
        code = request.args.get('code')
        state = request.args.get('state')
        
        if not code:
            flash('QuickBooks authorization failed', 'error')
            return redirect(url_for('integrations.dashboard'))
        
        # Exchange code for access token
        # In production, make actual OAuth token exchange
        
        flash('Successfully connected to QuickBooks!', 'success')
        return redirect(url_for('integrations.dashboard'))
        
    except Exception as e:
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

def sync_quickbooks_data():
    """Sync data with QuickBooks"""
    # Get all chamas for current user
    chamas = Chama.query.all()  # In production, filter by user access
    
    sync_results = []
    for chama in chamas:
        # Create customer in QuickBooks
        customer_data = {
            "FullyQualifiedName": chama.name,
            "CompanyName": chama.name,
            "DisplayName": chama.name
        }
        
        # In production, make actual QuickBooks API calls
        sync_results.append({
            'chama_id': chama.id,
            'chama_name': chama.name,
            'status': 'synced',
            'quickbooks_id': f"qb_{chama.id}"
        })
    
    return {
        'provider': 'QuickBooks',
        'synced_chamas': len(sync_results),
        'results': sync_results,
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
