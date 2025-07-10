#!/usr/bin/env python3
"""
Comprehensive ChamaLink Application Audit Script
Checks every page and identifies missing elements, broken links, and UX issues
"""

import requests
import time
from urllib.parse import urljoin

BASE_URL = "http://127.0.0.1:5000"

def test_page(url, expected_elements=None, should_redirect=False):
    """Test a single page and check for issues"""
    try:
        response = requests.get(url, allow_redirects=True)
        
        print(f"\n🔍 Testing: {url}")
        print(f"Status: {response.status_code}")
        
        if should_redirect and response.status_code == 200:
            print("⚠️  Expected redirect but got 200")
        
        if response.status_code == 200:
            content = response.text.lower()
            
            # Check for common issues
            issues = []
            
            if 'error' in content and 'traceback' in content:
                issues.append("❌ Python error/traceback visible")
            
            if 'lorem ipsum' in content:
                issues.append("⚠️  Contains placeholder text")
            
            if 'todo' in content or 'fixme' in content:
                issues.append("⚠️  Contains TODO/FIXME comments")
            
            if '</html>' not in content:
                issues.append("❌ Incomplete HTML structure")
            
            if 'bootstrap' not in content and 'style' not in content:
                issues.append("⚠️  No styling detected")
            
            if expected_elements:
                for element in expected_elements:
                    if element.lower() not in content:
                        issues.append(f"❌ Missing: {element}")
            
            # Check for broken image references
            if 'img src' in content and '404' in content:
                issues.append("⚠️  Potential broken images")
            
            if issues:
                for issue in issues:
                    print(f"  {issue}")
            else:
                print("  ✅ No obvious issues detected")
                
        elif response.status_code == 302:
            print(f"  🔄 Redirects to: {response.headers.get('Location', 'Unknown')}")
        else:
            print(f"  ❌ HTTP {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print(f"  ❌ Connection failed - Flask app not running?")
    except Exception as e:
        print(f"  ❌ Error: {e}")

def audit_application():
    """Comprehensive application audit"""
    
    print("🔍 CHAMALINK APPLICATION AUDIT")
    print("=" * 60)
    
    # Public pages (should work without login)
    public_pages = [
        {
            'url': f'{BASE_URL}/',
            'elements': ['chamalink', 'get started', 'modern chama'],
            'redirect': False
        },
        {
            'url': f'{BASE_URL}/auth/register',
            'elements': ['register', 'username', 'email', 'password'],
            'redirect': False
        },
        {
            'url': f'{BASE_URL}/auth/login',
            'elements': ['login', 'email', 'password', 'remember'],
            'redirect': False
        },
        {
            'url': f'{BASE_URL}/about',
            'elements': ['about', 'chamalink'],
            'redirect': False
        },
        {
            'url': f'{BASE_URL}/features',
            'elements': ['features'],
            'redirect': False
        },
        {
            'url': f'{BASE_URL}/pricing',
            'elements': ['pricing', 'plans'],
            'redirect': False
        },
        {
            'url': f'{BASE_URL}/contact',
            'elements': ['contact'],
            'redirect': False
        },
        {
            'url': f'{BASE_URL}/terms',
            'elements': ['terms'],
            'redirect': False
        },
        {
            'url': f'{BASE_URL}/privacy',
            'elements': ['privacy'],
            'redirect': False
        }
    ]
    
    # Protected pages (should redirect to login)
    protected_pages = [
        f'{BASE_URL}/dashboard',
        f'{BASE_URL}/founder-dashboard',
        f'{BASE_URL}/profile',
        f'{BASE_URL}/reports',
        f'{BASE_URL}/help',
        f'{BASE_URL}/meetings'
    ]
    
    print("\n📄 TESTING PUBLIC PAGES")
    print("-" * 30)
    
    for page in public_pages:
        test_page(page['url'], page['elements'], page['redirect'])
    
    print("\n🔒 TESTING PROTECTED PAGES (should redirect)")
    print("-" * 45)
    
    for url in protected_pages:
        test_page(url, should_redirect=True)
    
    print("\n" + "=" * 60)
    print("📋 AUDIT SUMMARY")
    print("Check the output above for:")
    print("- ❌ Critical issues (errors, broken pages)")
    print("- ⚠️  Warnings (placeholder text, missing elements)")
    print("- ✅ Working pages")
    print("\nNext steps: Fix any ❌ issues, review ⚠️  warnings")

if __name__ == "__main__":
    audit_application()
