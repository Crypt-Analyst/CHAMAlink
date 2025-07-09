import requests
import base64
import json
from datetime import datetime
import os
from flask import current_app

class MpesaAPI:
    def __init__(self):
        self.consumer_key = os.getenv('MPESA_CONSUMER_KEY')
        self.consumer_secret = os.getenv('MPESA_CONSUMER_SECRET')
        self.business_short_code = os.getenv('MPESA_BUSINESS_SHORT_CODE', '174379')
        self.passkey = os.getenv('MPESA_PASSKEY')
        self.callback_url = os.getenv('MPESA_CALLBACK_URL', 'https://chamalink.com/api/mpesa/callback')
        self.environment = os.getenv('MPESA_ENVIRONMENT', 'sandbox')  # sandbox or production
        
        # Subscription payments go to till 5625121
        self.subscription_till = '5625121'
        
        if self.environment == 'sandbox':
            self.base_url = 'https://sandbox.safaricom.co.ke'
        else:
            self.base_url = 'https://api.safaricom.co.ke'
    
    def get_access_token(self):
        """Get OAuth access token from M-Pesa"""
        url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
        
        # Create base64 encoded string
        credentials = f"{self.consumer_key}:{self.consumer_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            'Authorization': f'Basic {encoded_credentials}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json().get('access_token')
        except Exception as e:
            current_app.logger.error(f"M-Pesa access token error: {e}")
            return None
    
    def generate_password(self):
        """Generate password for STK push"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password_string = f"{self.business_short_code}{self.passkey}{timestamp}"
        password = base64.b64encode(password_string.encode()).decode()
        return password, timestamp
    
    def stk_push(self, phone_number, amount, account_reference, transaction_desc):
        """Initiate STK push payment"""
        access_token = self.get_access_token()
        if not access_token:
            return {'success': False, 'message': 'Failed to get access token'}
        
        password, timestamp = self.generate_password()
        
        # Format phone number (remove + and ensure it starts with 254)
        if phone_number.startswith('+'):
            phone_number = phone_number[1:]
        if phone_number.startswith('0'):
            phone_number = '254' + phone_number[1:]
        if not phone_number.startswith('254'):
            phone_number = '254' + phone_number
        
        url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'BusinessShortCode': self.business_short_code,
            'Password': password,
            'Timestamp': timestamp,
            'TransactionType': 'CustomerPayBillOnline',
            'Amount': int(amount),
            'PartyA': phone_number,
            'PartyB': self.business_short_code,
            'PhoneNumber': phone_number,
            'CallBackURL': self.callback_url,
            'AccountReference': account_reference,
            'TransactionDesc': transaction_desc
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            
            return {
                'success': True,
                'checkout_request_id': result.get('CheckoutRequestID'),
                'merchant_request_id': result.get('MerchantRequestID'),
                'response_code': result.get('ResponseCode'),
                'response_description': result.get('ResponseDescription'),
                'customer_message': result.get('CustomerMessage')
            }
        except Exception as e:
            current_app.logger.error(f"M-Pesa STK push error: {e}")
            return {
                'success': False,
                'message': f'Payment initiation failed: {str(e)}'
            }
    
    def stk_push_subscription(self, phone_number, amount, account_reference, transaction_desc):
        """Initiate STK push payment for subscription (to till 5625121)"""
        access_token = self.get_access_token()
        if not access_token:
            return {'success': False, 'message': 'Failed to get access token'}
        
        # For subscription payments, we use CustomerBuyGoodsOnline to till number
        password, timestamp = self.generate_password()
        
        # Format phone number (remove + and ensure it starts with 254)
        if phone_number.startswith('+'):
            phone_number = phone_number[1:]
        if phone_number.startswith('0'):
            phone_number = '254' + phone_number[1:]
        if not phone_number.startswith('254'):
            phone_number = '254' + phone_number
        
        url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'BusinessShortCode': self.business_short_code,
            'Password': password,
            'Timestamp': timestamp,
            'TransactionType': 'CustomerBuyGoodsOnline',  # Changed for till payments
            'Amount': int(amount),
            'PartyA': phone_number,
            'PartyB': self.subscription_till,  # Till number for subscriptions
            'PhoneNumber': phone_number,
            'CallBackURL': self.callback_url,
            'AccountReference': account_reference,
            'TransactionDesc': transaction_desc
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            
            return {
                'success': True,
                'checkout_request_id': result.get('CheckoutRequestID'),
                'merchant_request_id': result.get('MerchantRequestID'),
                'response_code': result.get('ResponseCode'),
                'response_description': result.get('ResponseDescription'),
                'customer_message': result.get('CustomerMessage')
            }
        except Exception as e:
            current_app.logger.error(f"M-Pesa subscription STK push error: {e}")
            return {
                'success': False,
                'message': f'Subscription payment initiation failed: {str(e)}'
            }
    
    def query_transaction_status(self, checkout_request_id):
        """Query the status of an STK push transaction"""
        access_token = self.get_access_token()
        if not access_token:
            return {'success': False, 'message': 'Failed to get access token'}
        
        password, timestamp = self.generate_password()
        
        url = f"{self.base_url}/mpesa/stkpushquery/v1/query"
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'BusinessShortCode': self.business_short_code,
            'Password': password,
            'Timestamp': timestamp,
            'CheckoutRequestID': checkout_request_id
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            current_app.logger.error(f"M-Pesa query error: {e}")
            return {'success': False, 'message': str(e)}

# Initialize M-Pesa API
mpesa_api = MpesaAPI()

# Helper function for easy import
def initiate_stk_push(phone_number, amount, account_reference, transaction_desc):
    """Helper function to initiate STK push payment"""
    return mpesa_api.stk_push(phone_number, amount, account_reference, transaction_desc)

def initiate_subscription_payment(phone_number, amount, account_reference, transaction_desc):
    """Helper function to initiate subscription payment to till 5625121"""
    return mpesa_api.stk_push_subscription(phone_number, amount, account_reference, transaction_desc)

def query_stk_push_status(checkout_request_id):
    """Helper function to query STK push status"""
    return mpesa_api.query_transaction_status(checkout_request_id)
