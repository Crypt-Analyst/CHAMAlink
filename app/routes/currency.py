from flask import Blueprint, render_template, request, jsonify, session, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models import Chama, ChamaMember, SubscriptionPlan
from app.utils.permissions import chama_member_required
from app import db
import requests
from datetime import datetime, timedelta
import json

currency_bp = Blueprint('currency', __name__, url_prefix='/currency')

# Supported currencies with their configurations
SUPPORTED_CURRENCIES = {
    'KES': {
        'name': 'Kenyan Shilling',
        'symbol': 'KES',
        'format': 'KES {amount:,.0f}',
        'country': 'Kenya',
        'flag': '🇰🇪',
        'payment_methods': ['mpesa', 'bank_transfer', 'cash'],
        'default_plan_prices': {
            'basic': 500,
            'classic': 1200,
            'advanced': 2500,
            'enterprise': 30  # per member
        }
    },
    'USD': {
        'name': 'US Dollar',
        'symbol': '$',
        'format': '${amount:,.2f}',
        'country': 'United States',
        'flag': '🇺🇸',
        'payment_methods': ['stripe', 'paypal', 'bank_transfer'],
        'default_plan_prices': {
            'basic': 5,
            'classic': 12,
            'advanced': 25,
            'enterprise': 0.30  # per member
        }
    },
    'EUR': {
        'name': 'Euro',
        'symbol': '€',
        'format': '€{amount:,.2f}',
        'country': 'European Union',
        'flag': '🇪🇺',
        'payment_methods': ['stripe', 'paypal', 'sepa'],
        'default_plan_prices': {
            'basic': 4.5,
            'classic': 11,
            'advanced': 22,
            'enterprise': 0.25  # per member
        }
    },
    'TZS': {
        'name': 'Tanzanian Shilling',
        'symbol': 'TSh',
        'format': 'TSh {amount:,.0f}',
        'country': 'Tanzania',
        'flag': '🇹🇿',
        'payment_methods': ['mobile_money', 'bank_transfer', 'cash'],
        'default_plan_prices': {
            'basic': 11000,
            'classic': 26000,
            'advanced': 55000,
            'enterprise': 65  # per member
        }
    },
    'UGX': {
        'name': 'Ugandan Shilling',
        'symbol': 'UGX',
        'format': 'UGX {amount:,.0f}',
        'country': 'Uganda',
        'flag': '🇺🇬',
        'payment_methods': ['mobile_money', 'bank_transfer', 'cash'],
        'default_plan_prices': {
            'basic': 18000,
            'classic': 43000,
            'advanced': 90000,
            'enterprise': 110  # per member
        }
    },
    'GBP': {
        'name': 'British Pound',
        'symbol': '£',
        'format': '£{amount:,.2f}',
        'country': 'United Kingdom',
        'flag': '🇬🇧',
        'payment_methods': ['stripe', 'paypal', 'bacs'],
        'default_plan_prices': {
            'basic': 4,
            'classic': 9.5,
            'advanced': 20,
            'enterprise': 0.22  # per member
        }
    }
}

@currency_bp.route('/api/rates')
def get_exchange_rates():
    """Get current exchange rates from external API"""
    try:
        # Use exchangerate-api.com for real exchange rates
        response = requests.get('https://api.exchangerate-api.com/v4/latest/USD', timeout=10)
        if response.status_code == 200:
            data = response.json()
            return jsonify({
                'success': True,
                'rates': data['rates'],
                'base': 'USD',
                'updated': data['date']
            })
        else:
            # Fallback to stored rates
            return get_fallback_rates()
    except Exception as e:
        print(f"Error fetching exchange rates: {e}")
        return get_fallback_rates()

def get_fallback_rates():
    """Fallback exchange rates when API is unavailable"""
    return jsonify({
        'success': True,
        'rates': {
            'KES': 155.0,
            'USD': 1.0,
            'EUR': 0.85,
            'TZS': 2400.0,
            'UGX': 3700.0,
            'GBP': 0.75
        },
        'base': 'USD',
        'updated': datetime.now().strftime('%Y-%m-%d'),
        'fallback': True
    })

@currency_bp.route('/set/<currency_code>')
def set_currency(currency_code):
    """Set user's preferred currency"""
    if currency_code.upper() in SUPPORTED_CURRENCIES:
        session['preferred_currency'] = currency_code.upper()
        if current_user.is_authenticated:
            # Save to user preferences if logged in
            current_user.preferred_currency = currency_code.upper()
            db.session.commit()
        
        flash(f'Currency changed to {SUPPORTED_CURRENCIES[currency_code.upper()]["name"]}', 'success')
    else:
        flash('Currency not supported', 'error')
    
    return redirect(request.referrer or url_for('main.index'))

@currency_bp.route('/convert')
def convert_currency():
    """Convert amount between currencies"""
    try:
        from_currency = request.args.get('from', 'KES').upper()
        to_currency = request.args.get('to', 'USD').upper()
        amount = float(request.args.get('amount', 0))
        
        if from_currency == to_currency:
            return jsonify({
                'success': True,
                'converted_amount': amount,
                'rate': 1.0,
                'from_currency': from_currency,
                'to_currency': to_currency
            })
        
        # Get current rates
        rates_response = get_exchange_rates()
        rates_data = rates_response.get_json()
        
        if rates_data['success']:
            rates = rates_data['rates']
            
            # Convert via USD as base
            if from_currency == 'USD':
                usd_amount = amount
            else:
                usd_amount = amount / rates.get(from_currency, 1)
            
            if to_currency == 'USD':
                converted_amount = usd_amount
                rate = 1 / rates.get(from_currency, 1) if from_currency != 'USD' else 1
            else:
                converted_amount = usd_amount * rates.get(to_currency, 1)
                rate = rates.get(to_currency, 1) / rates.get(from_currency, 1)
            
            return jsonify({
                'success': True,
                'converted_amount': round(converted_amount, 2),
                'rate': round(rate, 4),
                'from_currency': from_currency,
                'to_currency': to_currency,
                'timestamp': rates_data.get('updated')
            })
        else:
            return jsonify({'success': False, 'message': 'Unable to get exchange rates'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@currency_bp.route('/price-calculator')
@login_required
def price_calculator():
    """Show pricing in different currencies for real subscription plans"""
    from app.models.subscription import SubscriptionPlan, SubscriptionPlanPricing
    
    base_currency = request.args.get('base', 'KES').upper()
    target_currencies = request.args.getlist('currencies') or ['USD', 'EUR', 'TZS', 'UGX', 'GBP']
    
    # Get actual subscription plans from database
    plans = SubscriptionPlan.query.filter_by(is_active=True).order_by(SubscriptionPlan.price).all()
    
    # Real pricing structure from CHAMAlink
    real_pricing = {
        'KES': {'Basic': 500, 'Classic': 1200, 'Advanced': 2500, 'Enterprise': 5000},
        'USD': {'Basic': 5, 'Classic': 12, 'Advanced': 25, 'Enterprise': 50},
        'EUR': {'Basic': 4.5, 'Classic': 11, 'Advanced': 22, 'Enterprise': 45},
        'TZS': {'Basic': 11000, 'Classic': 26000, 'Advanced': 55000, 'Enterprise': 115000},
        'UGX': {'Basic': 18000, 'Classic': 43000, 'Advanced': 90000, 'Enterprise': 185000},
        'GBP': {'Basic': 4, 'Classic': 9.5, 'Advanced': 20, 'Enterprise': 42}
    }
    
    # Build plans pricing with real data
    plans_pricing = {}
    currencies_to_show = [base_currency] + [c for c in target_currencies if c != base_currency]
    
    for plan_name in ['Basic', 'Classic', 'Advanced', 'Enterprise']:
        plans_pricing[plan_name] = {}
        
        for currency in currencies_to_show:
            if currency in real_pricing:
                price = real_pricing[currency][plan_name]
                plans_pricing[plan_name][currency] = {
                    'price': price,
                    'formatted': format_currency_amount(price, currency)
                }
    
    # Features for each plan
    plan_features = {
        'Basic': {
            'description': 'Perfect for small chamas',
            'features': ['Up to 20 members', 'Basic reporting', 'SMS notifications', '5 chamas max', 'Community support'],
            'color': 'info'
        },
        'Classic': {
            'description': 'Great for growing chamas',
            'features': ['Up to 100 members', 'Advanced reporting', 'Email & SMS', '20 chamas max', 'Priority support'],
            'color': 'success'
        },
        'Advanced': {
            'description': 'For established chamas',
            'features': ['Up to 500 members', 'Full analytics', 'All notifications', 'Unlimited chamas', 'Phone support'],
            'color': 'warning'
        },
        'Enterprise': {
            'description': 'Large organizations',
            'features': ['Unlimited members', 'Custom features', 'Dedicated support', 'White-label options', 'SLA guarantee'],
            'color': 'primary'
        }
    }
    
    return render_template('currency/price_calculator.html',
                         plans_pricing=plans_pricing,
                         plan_features=plan_features,
                         base_currency=base_currency,
                         currencies_to_show=currencies_to_show,
                         real_pricing=real_pricing)

def get_user_currency():
    """Get user's preferred currency"""
    if current_user.is_authenticated and hasattr(current_user, 'preferred_currency') and current_user.preferred_currency:
        return current_user.preferred_currency
    
    return session.get('preferred_currency', 'KES')

def format_currency_amount(amount, currency_code='KES'):
    """Format amount with currency-specific formatting"""
    if currency_code in SUPPORTED_CURRENCIES:
        config = SUPPORTED_CURRENCIES[currency_code]
        try:
            return config['format'].format(amount=amount)
        except:
            return f"{config['symbol']} {amount:,.2f}"
    
    return f"{currency_code} {amount:,.2f}"

def get_currency_config(currency_code='KES'):
    """Get currency configuration"""
    return SUPPORTED_CURRENCIES.get(currency_code, SUPPORTED_CURRENCIES['KES'])

def get_payment_methods_for_currency(currency_code='KES'):
    """Get available payment methods for a currency"""
    config = get_currency_config(currency_code)
    return config.get('payment_methods', ['bank_transfer'])

# Template context processors
@currency_bp.app_context_processor
def inject_currency_helpers():
    """Make currency functions available in templates"""
    return dict(
        get_user_currency=get_user_currency,
        format_currency_amount=format_currency_amount,
        get_currency_config=get_currency_config,
        get_payment_methods_for_currency=get_payment_methods_for_currency,
        supported_currencies=SUPPORTED_CURRENCIES
    )
