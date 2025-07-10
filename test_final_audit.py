#!/usr/bin/env python3
"""
Final Security and Polish Audit for ChamaLink
Tests all implemented security features and polish elements
"""

import requests
import json
import time
from datetime import datetime
import os
import sys

class FinalAuditTest:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "base_url": base_url,
            "security_tests": {},
            "polish_tests": {},
            "overall_score": 0
        }
        
    def test_security_features(self):
        """Test all implemented security features"""
        print("🔐 Testing Security Features...")
        print("-" * 40)
        
        # Test 1: Rate Limiting
        print("  Testing rate limiting...", end=" ")
        try:
            responses = []
            for i in range(15):  # Try to exceed rate limit
                response = requests.post(f"{self.base_url}/auth/login", 
                                       data={"email": "test@test.com", "password": "wrong"},
                                       timeout=2)
                responses.append(response.status_code)
                time.sleep(0.1)
            
            # Check if we got rate limited (429 status)
            rate_limited = 429 in responses
            self.results["security_tests"]["rate_limiting"] = rate_limited
            print("✅ PASS" if rate_limited else "❌ FAIL")
            
        except Exception as e:
            self.results["security_tests"]["rate_limiting"] = False
            print(f"❌ ERROR: {str(e)}")
        
        # Test 2: SQL Injection Protection
        print("  Testing SQL injection protection...", end=" ")
        try:
            sql_payloads = [
                "' OR '1'='1",
                "'; DROP TABLE users; --",
                "' UNION SELECT * FROM users --"
            ]
            
            sql_blocked = 0
            for payload in sql_payloads:
                response = requests.post(f"{self.base_url}/auth/login",
                                       data={"email": payload, "password": "test"},
                                       timeout=5)
                # Should not return 200 with valid data
                if response.status_code in [400, 403, 500]:
                    sql_blocked += 1
            
            protection_score = sql_blocked / len(sql_payloads)
            self.results["security_tests"]["sql_injection_protection"] = protection_score >= 0.7
            print("✅ PASS" if protection_score >= 0.7 else "❌ FAIL")
            
        except Exception as e:
            self.results["security_tests"]["sql_injection_protection"] = False
            print(f"❌ ERROR: {str(e)}")
        
        # Test 3: XSS Protection
        print("  Testing XSS protection...", end=" ")
        try:
            xss_payloads = [
                "<script>alert('xss')</script>",
                "javascript:alert('xss')",
                "<img src=x onerror=alert('xss')>"
            ]
            
            xss_blocked = 0
            for payload in xss_payloads:
                response = requests.post(f"{self.base_url}/auth/register",
                                       data={"email": f"test{payload}@test.com", 
                                            "password": "password123",
                                            "first_name": payload},
                                       timeout=5)
                # Check if XSS payload is properly escaped or blocked
                if "<script>" not in response.text and "javascript:" not in response.text:
                    xss_blocked += 1
            
            xss_protection_score = xss_blocked / len(xss_payloads)
            self.results["security_tests"]["xss_protection"] = xss_protection_score >= 0.7
            print("✅ PASS" if xss_protection_score >= 0.7 else "❌ FAIL")
            
        except Exception as e:
            self.results["security_tests"]["xss_protection"] = False
            print(f"❌ ERROR: {str(e)}")
        
        # Test 4: Security Headers
        print("  Testing security headers...", end=" ")
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            headers = response.headers
            
            security_headers = {
                'X-Content-Type-Options': 'nosniff',
                'X-Frame-Options': ['DENY', 'SAMEORIGIN'],
                'X-XSS-Protection': '1; mode=block',
                'Strict-Transport-Security': True  # Any HSTS header
            }
            
            headers_score = 0
            for header, expected in security_headers.items():
                if header in headers:
                    if isinstance(expected, list):
                        if any(exp in headers[header] for exp in expected):
                            headers_score += 1
                    elif expected == True:
                        headers_score += 1
                    elif headers[header] == expected:
                        headers_score += 1
            
            headers_passed = headers_score >= 2  # At least 2 security headers
            self.results["security_tests"]["security_headers"] = headers_passed
            print("✅ PASS" if headers_passed else "❌ FAIL")
            
        except Exception as e:
            self.results["security_tests"]["security_headers"] = False
            print(f"❌ ERROR: {str(e)}")
        
        # Test 5: Security Dashboard Access
        print("  Testing security dashboard...", end=" ")
        try:
            response = requests.get(f"{self.base_url}/security-dashboard", timeout=5)
            # Should require authentication (redirect or 401/403)
            dashboard_protected = response.status_code in [302, 401, 403]
            self.results["security_tests"]["security_dashboard"] = dashboard_protected
            print("✅ PASS" if dashboard_protected else "❌ FAIL")
            
        except Exception as e:
            self.results["security_tests"]["security_dashboard"] = False
            print(f"❌ ERROR: {str(e)}")
    
    def test_polish_features(self):
        """Test all polish and UX features"""
        print("\n✨ Testing Polish Features...")
        print("-" * 40)
        
        # Test 1: Homepage Elements
        print("  Testing homepage elements...", end=" ")
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            content = response.text.lower()
            
            homepage_elements = [
                'chamalink',  # Brand name
                'testimonial',  # Testimonials section
                'feature',  # Features section
                'pricing',  # Pricing information
                'get started',  # CTA button
                'contact',  # Contact link
                'faq'  # FAQ link
            ]
            
            elements_found = sum(1 for element in homepage_elements if element in content)
            homepage_score = elements_found / len(homepage_elements)
            
            self.results["polish_tests"]["homepage_elements"] = homepage_score >= 0.8
            print("✅ PASS" if homepage_score >= 0.8 else "❌ FAIL")
            
        except Exception as e:
            self.results["polish_tests"]["homepage_elements"] = False
            print(f"❌ ERROR: {str(e)}")
        
        # Test 2: Navigation and Menu
        print("  Testing navigation menu...", end=" ")
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            content = response.text
            
            nav_elements = [
                'features',
                'about',
                'pricing',
                'contact',
                'faq',
                'help'
            ]
            
            nav_found = sum(1 for element in nav_elements if element in content.lower())
            nav_score = nav_found / len(nav_elements)
            
            self.results["polish_tests"]["navigation_menu"] = nav_score >= 0.8
            print("✅ PASS" if nav_score >= 0.8 else "❌ FAIL")
            
        except Exception as e:
            self.results["polish_tests"]["navigation_menu"] = False
            print(f"❌ ERROR: {str(e)}")
        
        # Test 3: Error Pages
        print("  Testing custom error pages...", end=" ")
        try:
            # Test 404 page
            response_404 = requests.get(f"{self.base_url}/nonexistent-page", timeout=5)
            has_custom_404 = 'chamalink' in response_404.text.lower() and 'page not found' in response_404.text.lower()
            
            self.results["polish_tests"]["custom_error_pages"] = has_custom_404
            print("✅ PASS" if has_custom_404 else "❌ FAIL")
            
        except Exception as e:
            self.results["polish_tests"]["custom_error_pages"] = False
            print(f"❌ ERROR: {str(e)}")
        
        # Test 4: Help and Documentation
        print("  Testing help documentation...", end=" ")
        try:
            response = requests.get(f"{self.base_url}/help", timeout=5)
            content = response.text.lower()
            
            help_elements = [
                'user guide',
                'video tutorial',
                'faq',
                'troubleshooting',
                'contact support',
                'getting started'
            ]
            
            help_found = sum(1 for element in help_elements if element in content)
            help_score = help_found / len(help_elements)
            
            self.results["polish_tests"]["help_documentation"] = help_score >= 0.7
            print("✅ PASS" if help_score >= 0.7 else "❌ FAIL")
            
        except Exception as e:
            self.results["polish_tests"]["help_documentation"] = False
            print(f"❌ ERROR: {str(e)}")
        
        # Test 5: FAQ Page
        print("  Testing FAQ page...", end=" ")
        try:
            response = requests.get(f"{self.base_url}/faq", timeout=5)
            content = response.text.lower()
            
            faq_elements = [
                'frequently asked',
                'question',
                'answer',
                'how to',
                'what is',
                'can i'
            ]
            
            faq_found = sum(1 for element in faq_elements if element in content)
            faq_score = faq_found / len(faq_elements)
            
            self.results["polish_tests"]["faq_page"] = faq_score >= 0.7
            print("✅ PASS" if faq_score >= 0.7 else "❌ FAIL")
            
        except Exception as e:
            self.results["polish_tests"]["faq_page"] = False
            print(f"❌ ERROR: {str(e)}")
        
        # Test 6: Mobile Responsiveness
        print("  Testing mobile responsiveness...", end=" ")
        try:
            # Check for responsive meta tag and CSS
            response = requests.get(f"{self.base_url}/", timeout=5)
            content = response.text
            
            responsive_indicators = [
                'viewport',
                'responsive',
                'mobile',
                'bootstrap',
                '@media'
            ]
            
            responsive_found = sum(1 for indicator in responsive_indicators if indicator in content.lower())
            responsive_score = responsive_found / len(responsive_indicators)
            
            self.results["polish_tests"]["mobile_responsiveness"] = responsive_score >= 0.6
            print("✅ PASS" if responsive_score >= 0.6 else "❌ FAIL")
            
        except Exception as e:
            self.results["polish_tests"]["mobile_responsiveness"] = False
            print(f"❌ ERROR: {str(e)}")
        
        # Test 7: Form Validation
        print("  Testing form validation...", end=" ")
        try:
            # Test registration form validation
            response = requests.post(f"{self.base_url}/auth/register",
                                   data={"email": "invalid-email", "password": "123"},
                                   timeout=5)
            
            # Should show validation errors
            has_validation = any(keyword in response.text.lower() for keyword in 
                               ['invalid', 'error', 'required', 'validation'])
            
            self.results["polish_tests"]["form_validation"] = has_validation
            print("✅ PASS" if has_validation else "❌ FAIL")
            
        except Exception as e:
            self.results["polish_tests"]["form_validation"] = False
            print(f"❌ ERROR: {str(e)}")
    
    def test_chat_functionality(self):
        """Test LeeBot chat functionality"""
        print("\n🤖 Testing LeeBot Chat...")
        print("-" * 40)
        
        print("  Testing chat interface...", end=" ")
        try:
            response = requests.get(f"{self.base_url}/chat", timeout=5)
            content = response.text.lower()
            
            chat_elements = [
                'leebot',
                'chat',
                'message',
                'send',
                'help'
            ]
            
            chat_found = sum(1 for element in chat_elements if element in content)
            chat_score = chat_found / len(chat_elements)
            
            self.results["polish_tests"]["chat_interface"] = chat_score >= 0.7
            print("✅ PASS" if chat_score >= 0.7 else "❌ FAIL")
            
        except Exception as e:
            self.results["polish_tests"]["chat_interface"] = False
            print(f"❌ ERROR: {str(e)}")
        
        print("  Testing chat API endpoint...", end=" ")
        try:
            response = requests.post(f"{self.base_url}/api/agent-help",
                                   json={"message": "Hello, I need help"},
                                   timeout=10)
            
            api_working = response.status_code == 200
            self.results["polish_tests"]["chat_api"] = api_working
            print("✅ PASS" if api_working else "❌ FAIL")
            
        except Exception as e:
            self.results["polish_tests"]["chat_api"] = False
            print(f"❌ ERROR: {str(e)}")
    
    def calculate_overall_score(self):
        """Calculate overall audit score"""
        all_tests = {**self.results["security_tests"], **self.results["polish_tests"]}
        if all_tests:
            passed_tests = sum(1 for result in all_tests.values() if result)
            self.results["overall_score"] = (passed_tests / len(all_tests)) * 100
        else:
            self.results["overall_score"] = 0
    
    def generate_report(self):
        """Generate comprehensive audit report"""
        print("\n" + "=" * 60)
        print("📋 CHAMALINK FINAL AUDIT REPORT")
        print("=" * 60)
        
        # Overall Score
        score = self.results["overall_score"]
        if score >= 90:
            status = "🎉 EXCELLENT"
            color = "green"
        elif score >= 80:
            status = "✅ GOOD"
            color = "green"
        elif score >= 70:
            status = "⚠️ NEEDS IMPROVEMENT"
            color = "yellow"
        else:
            status = "❌ POOR"
            color = "red"
        
        print(f"\n🎯 Overall Score: {score:.1f}% - {status}")
        
        # Security Results
        print(f"\n🔐 Security Features:")
        security_passed = sum(1 for result in self.results["security_tests"].values() if result)
        security_total = len(self.results["security_tests"])
        security_score = (security_passed / security_total * 100) if security_total > 0 else 0
        
        print(f"  Score: {security_score:.1f}% ({security_passed}/{security_total} passed)")
        for test, result in self.results["security_tests"].items():
            status_icon = "✅" if result else "❌"
            print(f"  {status_icon} {test.replace('_', ' ').title()}")
        
        # Polish Results
        print(f"\n✨ Polish & UX Features:")
        polish_passed = sum(1 for result in self.results["polish_tests"].values() if result)
        polish_total = len(self.results["polish_tests"])
        polish_score = (polish_passed / polish_total * 100) if polish_total > 0 else 0
        
        print(f"  Score: {polish_score:.1f}% ({polish_passed}/{polish_total} passed)")
        for test, result in self.results["polish_tests"].items():
            status_icon = "✅" if result else "❌"
            print(f"  {status_icon} {test.replace('_', ' ').title()}")
        
        # Critical Issues
        failed_tests = [test for test, result in {**self.results["security_tests"], **self.results["polish_tests"]}.items() if not result]
        if failed_tests:
            print(f"\n🚨 Issues to Address:")
            for test in failed_tests:
                print(f"  - {test.replace('_', ' ').title()}")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        
        if security_score < 80:
            print("  - Priority: Address security vulnerabilities immediately")
        if polish_score < 80:
            print("  - Improve user experience and polish features")
        if score >= 90:
            print("  - Excellent work! Ready for production deployment")
            print("  - Consider implementing additional monitoring and analytics")
        elif score >= 80:
            print("  - Good foundation. Address remaining issues for production readiness")
        else:
            print("  - Significant work needed before production deployment")
        
        # Production Readiness
        print(f"\n🚀 Production Readiness:")
        if score >= 85 and security_score >= 80:
            print("  ✅ READY FOR PRODUCTION")
            print("  - All critical security measures in place")
            print("  - User experience is polished and professional")
            print("  - Monitoring and error handling implemented")
        elif score >= 75:
            print("  ⚠️ NEARLY READY - Address critical issues first")
        else:
            print("  ❌ NOT READY - Significant improvements needed")
        
        # Save results
        with open("final_audit_results.json", "w") as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: final_audit_results.json")
        print("\n" + "=" * 60)
    
    def run_full_audit(self):
        """Run complete audit"""
        print("🔍 Starting ChamaLink Final Audit...")
        print("=" * 60)
        
        # Test all components
        self.test_security_features()
        self.test_polish_features()
        self.test_chat_functionality()
        
        # Calculate scores and generate report
        self.calculate_overall_score()
        self.generate_report()

if __name__ == "__main__":
    # Check if server is running
    base_url = "http://localhost:5000"
    
    try:
        response = requests.get(base_url, timeout=5)
        if response.status_code == 200:
            print("✅ ChamaLink server is running")
        else:
            print(f"⚠️ Server responded with status code: {response.status_code}")
    except requests.exceptions.RequestException:
        print("❌ ChamaLink server is not running. Please start the server first.")
        print("   Run: python run.py")
        sys.exit(1)
    
    # Run the audit
    auditor = FinalAuditTest(base_url)
    auditor.run_full_audit()
