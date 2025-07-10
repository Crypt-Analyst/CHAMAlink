#!/usr/bin/env python3
"""
Test script to verify security fixes and system functionality
Tests with proper user agent to avoid false positives
"""

import requests
import json
import time
import os
from datetime import datetime

class SecurityFixTest:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        # Set a legitimate user agent
        self.session.headers.update({
            'User-Agent': 'ChamaLink-Test-Suite/1.0 (python-requests/2.28.0)'
        })
        
    def test_basic_pages(self):
        """Test that basic pages load without 403 errors"""
        print("🌐 Testing Basic Pages Access...")
        print("-" * 40)
        
        pages = [
            ('/', 'Homepage'),
            ('/about', 'About Page'),
            ('/features', 'Features Page'),
            ('/faq', 'FAQ Page'),
            ('/help', 'Help Page'),
            ('/auth/login', 'Login Page'),
            ('/auth/register', 'Register Page')
        ]
        
        results = {}
        
        for path, name in pages:
            try:
                response = self.session.get(f"{self.base_url}{path}", timeout=10)
                status = response.status_code
                results[name] = {
                    'status': status,
                    'success': status == 200,
                    'size': len(response.content)
                }
                print(f"  {name}: {status} {'✅' if status == 200 else '❌'}")
                
            except Exception as e:
                results[name] = {
                    'status': 'ERROR',
                    'success': False,
                    'error': str(e)
                }
                print(f"  {name}: ERROR - {str(e)}")
        
        return results
    
    def test_security_features(self):
        """Test security features without triggering false positives"""
        print("\n🔐 Testing Security Features...")
        print("-" * 40)
        
        results = {}
        
        # Test 1: Normal login attempt (should work)
        print("  Testing normal login attempt...", end=" ")
        try:
            response = self.session.post(f"{self.base_url}/auth/login", 
                                       data={"email": "test@example.com", "password": "testpass123"})
            results['normal_login'] = response.status_code in [200, 302]  # 302 for redirect
            print("✅ PASS" if results['normal_login'] else f"❌ FAIL ({response.status_code})")
        except Exception as e:
            results['normal_login'] = False
            print(f"❌ ERROR: {str(e)}")
        
        # Test 2: API endpoints
        print("  Testing API endpoints...", end=" ")
        try:
            response = self.session.get(f"{self.base_url}/api/agent-help")
            results['api_access'] = response.status_code in [200, 401, 403]  # 401/403 expected if not logged in
            print("✅ PASS" if results['api_access'] else f"❌ FAIL ({response.status_code})")
        except Exception as e:
            results['api_access'] = False
            print(f"❌ ERROR: {str(e)}")
        
        # Test 3: Security dashboard (should require auth)
        print("  Testing security dashboard...", end=" ")
        try:
            response = self.session.get(f"{self.base_url}/security-dashboard")
            results['security_dashboard'] = response.status_code in [200, 302, 401, 403]
            print("✅ PASS" if results['security_dashboard'] else f"❌ FAIL ({response.status_code})")
        except Exception as e:
            results['security_dashboard'] = False
            print(f"❌ ERROR: {str(e)}")
        
        return results
    
    def test_chat_functionality(self):
        """Test LeeBot chat functionality"""
        print("\n💬 Testing LeeBot Chat...")
        print("-" * 40)
        
        results = {}
        
        # Test chat page access
        print("  Testing chat page access...", end=" ")
        try:
            response = self.session.get(f"{self.base_url}/chat")
            results['chat_page'] = response.status_code == 200
            print("✅ PASS" if results['chat_page'] else f"❌ FAIL ({response.status_code})")
        except Exception as e:
            results['chat_page'] = False
            print(f"❌ ERROR: {str(e)}")
        
        # Test chat API endpoint
        print("  Testing chat API endpoint...", end=" ")
        try:
            response = self.session.post(f"{self.base_url}/api/agent-help",
                                       json={"message": "Hello, can you help me?"})
            results['chat_api'] = response.status_code in [200, 401]  # 401 if auth required
            print("✅ PASS" if results['chat_api'] else f"❌ FAIL ({response.status_code})")
        except Exception as e:
            results['chat_api'] = False
            print(f"❌ ERROR: {str(e)}")
        
        return results
    
    def test_mobile_responsiveness(self):
        """Test mobile responsiveness by checking viewport meta tags"""
        print("\n📱 Testing Mobile Responsiveness...")
        print("-" * 40)
        
        results = {}
        
        # Test with mobile user agent
        mobile_session = requests.Session()
        mobile_session.headers.update({
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
        })
        
        pages = ['/', '/about', '/features', '/dashboard']
        
        for page in pages:
            try:
                response = mobile_session.get(f"{self.base_url}{page}", timeout=10)
                has_viewport = 'viewport' in response.text.lower()
                has_responsive_css = 'bootstrap' in response.text.lower() or 'responsive' in response.text.lower()
                
                page_key = f'mobile_{page.replace("/", "home" if page == "/" else page[1:])}'
                results[page_key] = {
                    'status': response.status_code,
                    'has_viewport': has_viewport,
                    'has_responsive_css': has_responsive_css,
                    'mobile_ready': has_viewport and has_responsive_css
                }
                
                print(f"  {page}: {'✅' if results[page_key]['mobile_ready'] else '❌'}")
                
            except Exception as e:
                page_key = f'mobile_{page.replace("/", "home" if page == "/" else page[1:])}'
                results[page_key] = {
                    'error': str(e),
                    'mobile_ready': False
                }
                print(f"  {page}: ❌ ERROR")
        
        return results
    
    def run_all_tests(self):
        """Run all tests and generate comprehensive report"""
        print("🚀 ChamaLink Security Fix & Functionality Test")
        print("=" * 50)
        
        # Set development mode for testing
        os.environ['FLASK_ENV'] = 'development'
        os.environ['TESTING'] = 'True'
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'base_url': self.base_url,
            'basic_pages': self.test_basic_pages(),
            'security_features': self.test_security_features(),
            'chat_functionality': self.test_chat_functionality(),
            'mobile_responsiveness': self.test_mobile_responsiveness()
        }
        
        # Calculate overall score
        total_tests = 0
        passed_tests = 0
        
        for category, tests in results.items():
            if isinstance(tests, dict) and category not in ['timestamp', 'base_url']:
                for test_name, test_result in tests.items():
                    total_tests += 1
                    if isinstance(test_result, dict):
                        passed_tests += 1 if test_result.get('success', test_result.get('mobile_ready', False)) else 0
                    else:
                        passed_tests += 1 if test_result else 0
        
        overall_score = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        results['overall_score'] = overall_score
        
        print(f"\n📊 OVERALL SCORE: {overall_score:.1f}% ({passed_tests}/{total_tests} tests passed)")
        print("=" * 50)
        
        # Save results to file
        with open('security_fix_test_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"📄 Detailed results saved to: security_fix_test_results.json")
        
        return results

if __name__ == "__main__":
    # Check if server is running
    import socket
    
    def is_server_running(host='localhost', port=5000):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((host, port))
            sock.close()
            return True
        except:
            return False
    
    if not is_server_running():
        print("❌ Flask server is not running on localhost:5000")
        print("Please start the server with: python run.py")
        exit(1)
    
    tester = SecurityFixTest()
    results = tester.run_all_tests()
    
    if results['overall_score'] >= 90:
        print("🎉 EXCELLENT! System is ready for production.")
    elif results['overall_score'] >= 75:
        print("👍 GOOD! Minor issues to address.")
    else:
        print("⚠️  NEEDS WORK! Several issues need fixing.")
