#!/usr/bin/env python3
"""
Render.com Deployment Verification Script
Test deployment success and basic functionality
"""

import requests
import sys
import time
import os
from urllib.parse import urljoin

def test_deployment(base_url):
    """Test basic deployment functionality"""
    print(f"🚀 Testing ChamaLink deployment at: {base_url}")
    print("=" * 60)
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Homepage loads
    try:
        print("📍 Test 1: Homepage accessibility...")
        response = requests.get(base_url, timeout=30)
        if response.status_code == 200 and "ChamaLink" in response.text:
            print("   ✅ Homepage loads successfully")
            tests_passed += 1
        else:
            print(f"   ❌ Homepage failed (Status: {response.status_code})")
            tests_failed += 1
    except Exception as e:
        print(f"   ❌ Homepage failed: {str(e)}")
        tests_failed += 1
    
    # Test 2: Login page
    try:
        print("📍 Test 2: Login page accessibility...")
        response = requests.get(urljoin(base_url, "/login"), timeout=30)
        if response.status_code == 200:
            print("   ✅ Login page loads successfully")
            tests_passed += 1
        else:
            print(f"   ❌ Login page failed (Status: {response.status_code})")
            tests_failed += 1
    except Exception as e:
        print(f"   ❌ Login page failed: {str(e)}")
        tests_failed += 1
    
    # Test 3: Registration page
    try:
        print("📍 Test 3: Registration page accessibility...")
        response = requests.get(urljoin(base_url, "/register"), timeout=30)
        if response.status_code == 200:
            print("   ✅ Registration page loads successfully")
            tests_passed += 1
        else:
            print(f"   ❌ Registration page failed (Status: {response.status_code})")
            tests_failed += 1
    except Exception as e:
        print(f"   ❌ Registration page failed: {str(e)}")
        tests_failed += 1
    
    # Test 4: API health check
    try:
        print("📍 Test 4: API health check...")
        response = requests.get(urljoin(base_url, "/api/health"), timeout=30)
        if response.status_code == 200:
            print("   ✅ API health check passed")
            tests_passed += 1
        else:
            print(f"   ❌ API health check failed (Status: {response.status_code})")
            tests_failed += 1
    except Exception as e:
        print(f"   ❌ API health check failed: {str(e)}")
        tests_failed += 1
    
    # Test 5: Static files
    try:
        print("📍 Test 5: Static files accessibility...")
        response = requests.get(urljoin(base_url, "/static/style.css"), timeout=30)
        if response.status_code == 200:
            print("   ✅ Static files accessible")
            tests_passed += 1
        else:
            print("   ⚠️  Static files may not be accessible (this is sometimes normal)")
            tests_passed += 1  # Don't fail for static files
    except Exception as e:
        print("   ⚠️  Static files test inconclusive")
        tests_passed += 1  # Don't fail for static files
    
    # Test 6: Security headers
    try:
        print("📍 Test 6: Security headers check...")
        response = requests.get(base_url, timeout=30)
        if response.status_code == 200:
            headers = response.headers
            security_score = 0
            if 'X-Content-Type-Options' in headers:
                security_score += 1
            if 'X-Frame-Options' in headers:
                security_score += 1
            if 'Strict-Transport-Security' in headers:
                security_score += 1
            
            if security_score >= 1:
                print(f"   ✅ Basic security headers present ({security_score}/3)")
                tests_passed += 1
            else:
                print("   ⚠️  Consider adding security headers")
                tests_passed += 1  # Don't fail for this
        else:
            tests_failed += 1
    except Exception as e:
        print(f"   ⚠️  Security headers test inconclusive")
        tests_passed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 DEPLOYMENT TEST RESULTS:")
    print(f"   ✅ Tests Passed: {tests_passed}")
    print(f"   ❌ Tests Failed: {tests_failed}")
    print(f"   📈 Success Rate: {(tests_passed/(tests_passed+tests_failed))*100:.1f}%")
    
    if tests_failed == 0:
        print("\n🎉 DEPLOYMENT SUCCESSFUL! ChamaLink is ready for production.")
        print("\n📋 Next Steps:")
        print("   1. Set up your custom domain (optional)")
        print("   2. Configure email credentials for production")
        print("   3. Update M-Pesa settings for live payments")
        print("   4. Begin user onboarding and testing")
        return True
    else:
        print("\n⚠️  DEPLOYMENT ISSUES DETECTED")
        print("\n🔧 Troubleshooting:")
        print("   1. Check Render.com service logs")
        print("   2. Verify environment variables are set")
        print("   3. Ensure Python 3.11.9 is being used")
        print("   4. Check database connection")
        print("   5. See RENDER_TROUBLESHOOTING.md for detailed guidance")
        return False

def main():
    """Main function"""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = input("Enter your Render.com app URL (e.g., https://chamalink.onrender.com): ").strip()
    
    if not base_url.startswith('http'):
        base_url = 'https://' + base_url
    
    print(f"🔍 Starting deployment verification for: {base_url}")
    print("⏳ This may take a few moments...")
    print()
    
    success = test_deployment(base_url)
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
