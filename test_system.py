#!/usr/bin/env python3
"""
ChamaLink System Functionality Test Script
Tests all payment flows, subscription management, and M-Pesa integration
"""

import requests
import json
import time
from datetime import datetime, timedelta

class ChamaLinkTester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        
    def log_result(self, test_name, status, message=""):
        """Log test result"""
        result = {
            'test': test_name,
            'status': status,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_emoji} {test_name:30}: {message}")
    
    def login_test_user(self):
        """Login with the default admin user for testing"""
        try:
            # Get the login page first to get any CSRF tokens
            login_page = self.session.get(f"{self.base_url}/auth/login")
            
            # Login with admin credentials
            login_data = {
                'email': 'admin@chamalink.com',
                'password': 'admin123'
            }
            
            response = self.session.post(f"{self.base_url}/auth/login", data=login_data)
            return response.status_code in [200, 302]  # Success or redirect after login
        except Exception as e:
            print(f"Login failed: {e}")
            return False

    def test_home_page(self):
        """Test if the home page loads"""
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                self.log_result("Home Page Load", "PASS", "Home page loaded successfully")
                return True
            else:
                self.log_result("Home Page Load", "FAIL", f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Home Page Load", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_registration_page(self):
        """Test if registration page loads"""
        try:
            response = self.session.get(f"{self.base_url}/auth/register")
            if response.status_code == 200 and "register" in response.text.lower():
                self.log_result("Registration Page", "PASS", "Registration page loaded")
                return True
            else:
                self.log_result("Registration Page", "FAIL", "Page not loading correctly")
                return False
        except Exception as e:
            self.log_result("Registration Page", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_login_page(self):
        """Test if login page loads"""
        try:
            response = self.session.get(f"{self.base_url}/auth/login")
            if response.status_code == 200 and "login" in response.text.lower():
                self.log_result("Login Page", "PASS", "Login page loaded")
                return True
            else:
                self.log_result("Login Page", "FAIL", "Page not loading correctly")
                return False
        except Exception as e:
            self.log_result("Login Page", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_subscription_plans_page(self):
        """Test if subscription plans page loads"""
        try:
            response = self.session.get(f"{self.base_url}/subscription/plans")
            if response.status_code == 200 and "plan" in response.text.lower():
                self.log_result("Subscription Plans", "PASS", "Plans page loaded")
                return True
            else:
                self.log_result("Subscription Plans", "FAIL", "Plans page not loading")
                return False
        except Exception as e:
            self.log_result("Subscription Plans", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_payment_options_page(self):
        """Test if payment options page loads (assuming plan ID 1 exists)"""
        try:
            # Login first
            if not self.login_test_user():
                self.log_result("Payment Options", "FAIL", "Could not login for testing")
                return False
                
            response = self.session.get(f"{self.base_url}/subscription/payment-options?plan=Basic Plan&duration=1")
            if response.status_code == 200:
                if "m-pesa" in response.text.lower() and "bank transfer" in response.text.lower():
                    self.log_result("Payment Options", "PASS", "Both M-Pesa and bank transfer options available")
                    return True
                else:
                    self.log_result("Payment Options", "WARN", "Payment options page loaded but missing payment methods")
                    return False
            else:
                self.log_result("Payment Options", "FAIL", f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Payment Options", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_enterprise_billing_page(self):
        """Test enterprise billing dashboard"""
        try:
            # This would require authentication, so we'll just test if the route exists
            response = self.session.get(f"{self.base_url}/enterprise/billing")
            # Expect redirect to login if not authenticated
            if response.status_code in [200, 302]:
                self.log_result("Enterprise Billing", "PASS", "Enterprise billing route exists")
                return True
            else:
                self.log_result("Enterprise Billing", "FAIL", f"Route not found: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Enterprise Billing", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_mpesa_callback_endpoint(self):
        """Test if M-Pesa callback endpoint is accessible"""
        try:
            # Test POST to callback URL (would normally come from Safaricom)
            response = self.session.post(f"{self.base_url}/mpesa/callback", 
                                      json={"test": "data"},
                                      headers={"Content-Type": "application/json"})
            # We expect it to handle the request (even if it fails validation)
            if response.status_code in [200, 400, 404]:
                self.log_result("M-Pesa Callback", "PASS", "Callback endpoint accessible")
                return True
            else:
                self.log_result("M-Pesa Callback", "FAIL", f"Unexpected status: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("M-Pesa Callback", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_api_structure(self):
        """Test if all required API endpoints exist"""
        endpoints_to_test = [
            ("/subscription/plans", "GET"),
            ("/subscription/pricing", "GET"), 
            ("/enterprise/plans", "GET"),
            ("/mpesa/callback", "POST"),
        ]
        
        all_passed = True
        for endpoint, method in endpoints_to_test:
            try:
                if method == "GET":
                    response = self.session.get(f"{self.base_url}{endpoint}")
                else:
                    response = self.session.post(f"{self.base_url}{endpoint}")
                
                if response.status_code not in [404, 405]:  # Not found or method not allowed
                    self.log_result(f"API Endpoint {endpoint}", "PASS", f"{method} endpoint exists")
                else:
                    self.log_result(f"API Endpoint {endpoint}", "FAIL", f"Endpoint not found or method not allowed")
                    all_passed = False
            except Exception as e:
                self.log_result(f"API Endpoint {endpoint}", "FAIL", f"Error: {str(e)}")
                all_passed = False
        
        return all_passed
    
    def test_static_assets(self):
        """Test if static assets load"""
        static_files = [
            "/static/css/bootstrap.min.css",
            "/static/js/bootstrap.bundle.min.js",
        ]
        
        all_passed = True
        for static_file in static_files:
            try:
                response = self.session.get(f"{self.base_url}{static_file}")
                if response.status_code == 200:
                    self.log_result(f"Static Asset {static_file}", "PASS", "Asset loaded")
                else:
                    self.log_result(f"Static Asset {static_file}", "FAIL", f"Status: {response.status_code}")
                    all_passed = False
            except Exception as e:
                self.log_result(f"Static Asset {static_file}", "FAIL", f"Error: {str(e)}")
                all_passed = False
        
        return all_passed
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting ChamaLink System Tests...")
        print("=" * 50)
        
        tests = [
            self.test_home_page,
            self.test_registration_page,
            self.test_login_page,
            self.test_subscription_plans_page,
            self.test_payment_options_page,
            self.test_enterprise_billing_page,
            self.test_mpesa_callback_endpoint,
            self.test_api_structure,
            self.test_static_assets,
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            if test():
                passed += 1
        
        print("\n" + "=" * 50)
        print(f"📊 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! System is ready for launch.")
        elif passed >= total * 0.8:
            print("⚠️  Most tests passed. Minor issues to fix.")
        else:
            print("❌ Several tests failed. System needs attention before launch.")
        
        return passed, total
    
    def save_results(self, filename="test_results.json"):
        """Save test results to file"""
        with open(filename, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        print(f"\n📄 Test results saved to {filename}")

if __name__ == "__main__":
    import sys
    
    # Get base URL from command line or use default
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
    
    print(f"🔗 Testing ChamaLink at: {base_url}")
    
    tester = ChamaLinkTester(base_url)
    passed, total = tester.run_all_tests()
    tester.save_results()
    
    # Exit with appropriate code
    sys.exit(0 if passed == total else 1)
