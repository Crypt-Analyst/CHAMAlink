#!/usr/bin/env python3
"""
Quick Feature Verification for ChamaLink
Tests core functionality and polish features
"""

import requests
import json
from datetime import datetime

def test_core_features():
    """Test the core features we've implemented"""
    base_url = "http://localhost:5000"
    results = {}
    
    print("🔍 Testing ChamaLink Core Features...")
    print("=" * 50)
    
    # Test 1: Homepage loads
    print("1. Testing homepage...", end=" ")
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            content = response.text.lower()
            has_key_elements = all(keyword in content for keyword in ['chamalink', 'chama', 'management'])
            results['homepage'] = has_key_elements
            print("✅ PASS" if has_key_elements else "❌ FAIL")
        else:
            results['homepage'] = False
            print(f"❌ FAIL (Status: {response.status_code})")
    except Exception as e:
        results['homepage'] = False
        print(f"❌ ERROR: {str(e)}")
    
    # Test 2: Navigation pages
    pages_to_test = [
        ('Features', '/features'),
        ('About', '/about'),
        ('FAQ', '/faq'),
        ('Help', '/help'),
        ('Contact', '/contact'),
        ('Pricing', '/pricing')
    ]
    
    for page_name, url in pages_to_test:
        print(f"2. Testing {page_name} page...", end=" ")
        try:
            response = requests.get(f"{base_url}{url}", timeout=5)
            success = response.status_code == 200
            results[f'{page_name.lower()}_page'] = success
            print("✅ PASS" if success else f"❌ FAIL (Status: {response.status_code})")
        except Exception as e:
            results[f'{page_name.lower()}_page'] = False
            print(f"❌ ERROR: {str(e)}")
    
    # Test 3: Authentication pages
    auth_pages = [
        ('Login', '/auth/login'),
        ('Register', '/auth/register')
    ]
    
    for page_name, url in auth_pages:
        print(f"3. Testing {page_name} page...", end=" ")
        try:
            response = requests.get(f"{base_url}{url}", timeout=5)
            success = response.status_code == 200
            results[f'{page_name.lower()}_page'] = success
            print("✅ PASS" if success else f"❌ FAIL (Status: {response.status_code})")
        except Exception as e:
            results[f'{page_name.lower()}_page'] = False
            print(f"❌ ERROR: {str(e)}")
    
    # Test 4: Error page handling
    print("4. Testing 404 error page...", end=" ")
    try:
        response = requests.get(f"{base_url}/nonexistent-page", timeout=5)
        if response.status_code == 404:
            content = response.text.lower()
            has_custom_404 = 'page not found' in content and 'chamalink' in content
            results['custom_404'] = has_custom_404
            print("✅ PASS" if has_custom_404 else "❌ FAIL")
        else:
            results['custom_404'] = False
            print(f"❌ FAIL (Expected 404, got {response.status_code})")
    except Exception as e:
        results['custom_404'] = False
        print(f"❌ ERROR: {str(e)}")
    
    # Test 5: Security dashboard (should require auth)
    print("5. Testing security dashboard protection...", end=" ")
    try:
        response = requests.get(f"{base_url}/security-dashboard", timeout=5)
        # Should redirect to login or return 401/403
        protected = response.status_code in [302, 401, 403]
        results['security_dashboard_protected'] = protected
        print("✅ PASS" if protected else "❌ FAIL")
    except Exception as e:
        results['security_dashboard_protected'] = False
        print(f"❌ ERROR: {str(e)}")
    
    # Test 6: Chat interface
    print("6. Testing chat interface...", end=" ")
    try:
        response = requests.get(f"{base_url}/chat", timeout=5)
        success = response.status_code == 200
        if success:
            content = response.text.lower()
            has_chat_elements = any(keyword in content for keyword in ['chat', 'leebot', 'message'])
            results['chat_interface'] = has_chat_elements
            print("✅ PASS" if has_chat_elements else "❌ FAIL")
        else:
            results['chat_interface'] = False
            print(f"❌ FAIL (Status: {response.status_code})")
    except Exception as e:
        results['chat_interface'] = False
        print(f"❌ ERROR: {str(e)}")
    
    # Calculate overall score
    passed_tests = sum(1 for result in results.values() if result)
    total_tests = len(results)
    score = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    
    print("\n" + "=" * 50)
    print("📊 VERIFICATION RESULTS")
    print("=" * 50)
    print(f"Overall Score: {score:.1f}% ({passed_tests}/{total_tests} tests passed)")
    
    if score >= 90:
        status = "🎉 EXCELLENT"
    elif score >= 80:
        status = "✅ VERY GOOD"
    elif score >= 70:
        status = "👍 GOOD"
    elif score >= 60:
        status = "⚠️ FAIR"
    else:
        status = "❌ NEEDS WORK"
    
    print(f"Status: {status}")
    
    # Show individual results
    print(f"\n📋 Detailed Results:")
    for test, result in results.items():
        status_icon = "✅" if result else "❌"
        print(f"  {status_icon} {test.replace('_', ' ').title()}")
    
    # Recommendations
    failed_tests = [test for test, result in results.items() if not result]
    if failed_tests:
        print(f"\n🔧 Areas to improve:")
        for test in failed_tests:
            print(f"  - {test.replace('_', ' ').title()}")
    
    if score >= 80:
        print(f"\n🚀 Great work! The platform is {score:.1f}% functional and ready for users.")
    else:
        print(f"\n⚠️ Some features need attention. Current functionality: {score:.1f}%")
    
    return results, score

if __name__ == "__main__":
    results, score = test_core_features()
    
    # Save results
    with open("verification_results.json", "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "score": score,
            "results": results
        }, f, indent=2)
    
    print(f"\n💾 Results saved to: verification_results.json")
