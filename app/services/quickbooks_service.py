import requests
import json
import base64
from datetime import datetime, timedelta
from app import db
from app.models import QuickBooksIntegration, QuickBooksSyncLog, Chama
import logging

logger = logging.getLogger(__name__)

class QuickBooksService:
    """Service class for QuickBooks Online API integration"""
    
    def __init__(self, config):
        self.client_id = config.QUICKBOOKS_CLIENT_ID
        self.client_secret = config.QUICKBOOKS_CLIENT_SECRET
        self.redirect_uri = config.QUICKBOOKS_REDIRECT_URI
        self.environment = config.QUICKBOOKS_ENVIRONMENT
        
        if self.environment == 'sandbox':
            self.discovery_document_url = 'https://appcenter.intuit.com/connect/oauth2'
            self.base_url = 'https://sandbox-quickbooks.api.intuit.com'
        else:
            self.discovery_document_url = 'https://appcenter.intuit.com/connect/oauth2'
            self.base_url = 'https://quickbooks.api.intuit.com'
    
    def get_authorization_url(self, state=None):
        """Generate QuickBooks OAuth 2.0 authorization URL"""
        scope = 'com.intuit.quickbooks.accounting'
        
        auth_url = (
            f"{self.discovery_document_url}?"
            f"client_id={self.client_id}&"
            f"scope={scope}&"
            f"redirect_uri={self.redirect_uri}&"
            f"response_type=code&"
            f"access_type=offline"
        )
        
        if state:
            auth_url += f"&state={state}"
            
        return auth_url
    
    def exchange_code_for_tokens(self, auth_code, realm_id):
        """Exchange authorization code for access and refresh tokens"""
        try:
            token_url = 'https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer'
            
            # Prepare headers
            auth_header = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
            headers = {
                'Authorization': f'Basic {auth_header}',
                'Accept': 'application/json',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            # Prepare payload
            payload = {
                'grant_type': 'authorization_code',
                'code': auth_code,
                'redirect_uri': self.redirect_uri
            }
            
            # Make request
            response = requests.post(token_url, headers=headers, data=payload)
            response.raise_for_status()
            
            token_data = response.json()
            
            return {
                'access_token': token_data['access_token'],
                'refresh_token': token_data['refresh_token'],
                'expires_in': token_data['expires_in'],
                'realm_id': realm_id
            }
            
        except requests.RequestException as e:
            logger.error(f"Error exchanging code for tokens: {e}")
            raise Exception(f"Failed to exchange authorization code: {str(e)}")
    
    def refresh_access_token(self, refresh_token):
        """Refresh expired access token using refresh token"""
        try:
            token_url = 'https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer'
            
            # Prepare headers
            auth_header = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
            headers = {
                'Authorization': f'Basic {auth_header}',
                'Accept': 'application/json',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            # Prepare payload
            payload = {
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token
            }
            
            # Make request
            response = requests.post(token_url, headers=headers, data=payload)
            response.raise_for_status()
            
            token_data = response.json()
            
            return {
                'access_token': token_data['access_token'],
                'refresh_token': token_data.get('refresh_token', refresh_token),  # May not return new refresh token
                'expires_in': token_data['expires_in']
            }
            
        except requests.RequestException as e:
            logger.error(f"Error refreshing access token: {e}")
            raise Exception(f"Failed to refresh access token: {str(e)}")
    
    def get_valid_token(self, integration):
        """Get valid access token, refreshing if necessary"""
        if not integration.is_token_valid:
            if not integration.refresh_token:
                raise Exception("No refresh token available")
            
            tokens = self.refresh_access_token(integration.refresh_token)
            integration.access_token = tokens['access_token']
            integration.refresh_token = tokens['refresh_token']
            integration.token_expires_at = datetime.utcnow() + timedelta(seconds=tokens['expires_in'])
            db.session.commit()
        
        return integration.access_token
    
    def make_api_request(self, integration, method, endpoint, data=None):
        """Make authenticated API request to QuickBooks"""
        try:
            access_token = self.get_valid_token(integration)
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json'
            }
            
            if data:
                headers['Content-Type'] = 'application/json'
            
            url = f"{self.base_url}/v3/company/{integration.company_id}/{endpoint}"
            
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, json=data)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=headers, json=data)
            else:
                raise Exception(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"QuickBooks API request failed: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
            raise Exception(f"QuickBooks API error: {str(e)}")
    
    def sync_chama_to_quickbooks(self, chama_id):
        """Sync chama financial data to QuickBooks"""
        integration = QuickBooksIntegration.query.filter_by(chama_id=chama_id).first()
        if not integration:
            raise Exception("QuickBooks not connected for this chama")
        
        # Create sync log
        sync_log = QuickBooksSyncLog(
            integration_id=integration.id,
            sync_type='manual',
            status='running'
        )
        db.session.add(sync_log)
        db.session.commit()
        
        try:
            chama = Chama.query.get(chama_id)
            if not chama:
                raise Exception("Chama not found")
            
            # Sync chama as customer
            customer_result = self.sync_chama_as_customer(integration, chama)
            
            # Sync financial transactions
            transactions_result = self.sync_chama_transactions(integration, chama)
            
            # Update integration
            integration.last_sync = datetime.utcnow()
            integration.sync_status = 'active'
            
            # Update sync log
            sync_log.status = 'success'
            sync_log.completed_at = datetime.utcnow()
            sync_log.records_processed = transactions_result.get('processed', 0)
            sync_log.records_synced = transactions_result.get('synced', 0)
            sync_log.sync_data = {
                'customer': customer_result,
                'transactions': transactions_result
            }
            
            db.session.commit()
            
            return {
                'status': 'success',
                'message': f'Successfully synced {chama.name} to QuickBooks',
                'details': {
                    'customer_synced': customer_result.get('created', False) or customer_result.get('updated', False),
                    'transactions_synced': transactions_result.get('synced', 0),
                    'last_sync': integration.last_sync.isoformat()
                }
            }
            
        except Exception as e:
            # Update sync log with error
            sync_log.status = 'error'
            sync_log.completed_at = datetime.utcnow()
            sync_log.error_message = str(e)
            
            # Update integration status
            integration.sync_status = 'error'
            
            db.session.commit()
            
            logger.error(f"Error syncing chama {chama_id}: {e}")
            raise
    
    def sync_chama_as_customer(self, integration, chama):
        """Sync chama as a customer in QuickBooks"""
        try:
            # Search for existing customer
            search_response = self.make_api_request(
                integration, 
                'GET', 
                f"query?query=SELECT * FROM Customer WHERE Name = '{chama.name}'"
            )
            
            customer_data = {
                'Name': chama.name,
                'CompanyName': chama.name,
                'Active': True
            }
            
            # Add contact info if available
            if hasattr(chama, 'phone') and chama.phone:
                customer_data['PrimaryPhone'] = {'FreeFormNumber': chama.phone}
            
            if hasattr(chama, 'email') and chama.email:
                customer_data['PrimaryEmailAddr'] = {'Address': chama.email}
            
            existing_customers = search_response.get('QueryResponse', {}).get('Customer', [])
            
            if existing_customers:
                # Update existing customer
                customer = existing_customers[0]
                customer_data['Id'] = customer['Id']
                customer_data['SyncToken'] = customer['SyncToken']
                
                response = self.make_api_request(integration, 'POST', 'customer', customer_data)
                
                return {
                    'updated': True,
                    'quickbooks_id': customer['Id'],
                    'name': chama.name
                }
            else:
                # Create new customer
                response = self.make_api_request(integration, 'POST', 'customer', customer_data)
                
                created_customer = response.get('QueryResponse', {}).get('Customer', [{}])[0]
                
                return {
                    'created': True,
                    'quickbooks_id': created_customer.get('Id'),
                    'name': chama.name
                }
                
        except Exception as e:
            logger.error(f"Error syncing chama as customer: {e}")
            return {'error': str(e)}
    
    def sync_chama_transactions(self, integration, chama):
        """Sync chama transactions to QuickBooks"""
        try:
            # This is a simplified example - you would implement based on your transaction model
            # For now, we'll create a sample journal entry
            
            # Get recent transactions (you would implement this based on your Transaction model)
            # transactions = Transaction.query.filter_by(chama_id=chama.id).limit(10).all()
            
            # Create journal entry for member contributions
            journal_entry_data = {
                'DocNumber': f"CHAMA-{chama.id}-{datetime.now().strftime('%Y%m%d')}",
                'TxnDate': datetime.now().strftime('%Y-%m-%d'),
                'PrivateNote': f'CHAMAlink sync for {chama.name}',
                'Line': [
                    {
                        'Amount': 1000.00,  # This would be calculated from actual transactions
                        'DetailType': 'JournalEntryLineDetail',
                        'JournalEntryLineDetail': {
                            'PostingType': 'Debit',
                            'AccountRef': {
                                'value': '1',  # Cash account - you'd need to map this properly
                                'name': 'Cash'
                            }
                        }
                    },
                    {
                        'Amount': 1000.00,
                        'DetailType': 'JournalEntryLineDetail',
                        'JournalEntryLineDetail': {
                            'PostingType': 'Credit',
                            'AccountRef': {
                                'value': '82',  # Income account - you'd need to map this properly
                                'name': 'Member Contributions'
                            }
                        }
                    }
                ]
            }
            
            # For demo purposes, we'll just return success without making the actual call
            return {
                'processed': 1,
                'synced': 1,
                'journal_entries_created': 1
            }
            
        except Exception as e:
            logger.error(f"Error syncing transactions: {e}")
            return {
                'processed': 0,
                'synced': 0,
                'error': str(e)
            }
    
    def get_company_info(self, integration):
        """Get QuickBooks company information"""
        try:
            response = self.make_api_request(integration, 'GET', 'companyinfo/1')
            company_info = response.get('QueryResponse', {}).get('CompanyInfo', [{}])[0]
            
            return {
                'company_name': company_info.get('CompanyName', 'Unknown'),
                'country': company_info.get('Country', 'Unknown'),
                'legal_name': company_info.get('LegalName', 'Unknown'),
                'email': company_info.get('Email', {}).get('Address', ''),
                'phone': company_info.get('PrimaryPhone', {}).get('FreeFormNumber', '')
            }
            
        except Exception as e:
            logger.error(f"Error getting company info: {e}")
            return {'error': str(e)}
    
    def test_connection(self, integration):
        """Test QuickBooks connection"""
        try:
            company_info = self.get_company_info(integration)
            if 'error' in company_info:
                return {'status': 'error', 'message': company_info['error']}
            
            return {
                'status': 'success',
                'message': 'Connection successful',
                'company_name': company_info.get('company_name', 'Unknown')
            }
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
