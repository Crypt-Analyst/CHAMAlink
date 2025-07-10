#!/usr/bin/env python3
"""
Comprehensive UX Audit for ChamaLink
Tests every page and identifies missing elements for a polished user experience
"""

import requests
import time
from urllib.parse import urljoin

BASE_URL = "http://127.0.0.1:5000"

def audit_page(url, page_name, expected_elements=None, should_have_content=True):
    """Audit a single page for UX issues"""
    print(f"\n🔍 Auditing: {page_name}")
    print(f"   URL: {url}")
    
    issues = []
    recommendations = []
    
    try:
        response = requests.get(url, timeout=10)
        content = response.text.lower()
        
        if response.status_code != 200:
            issues.append(f"❌ HTTP {response.status_code} - Page not accessible")
            return issues, recommendations
        
        # Check for basic HTML structure
        if not content:
            issues.append("❌ Empty page content")
            return issues, recommendations
            
        # Check for common UX elements
        ux_checks = {
            'Professional Title': 'chamalink' in content or 'title' in content,
            'Navigation Menu': 'nav' in content or 'menu' in content,
            'Call-to-Action': any(cta in content for cta in ['btn', 'button', 'get started', 'sign up', 'login']),
            'Footer': 'footer' in content or 'copyright' in content,
            'Responsive Design': 'bootstrap' in content or 'responsive' in content or 'col-' in content,
        }
        
        for check, passed in ux_checks.items():
            if not passed:
                issues.append(f"⚠️ Missing: {check}")
        
        # Content quality checks
        if should_have_content:
            content_checks = {
                'Professional Copy': len(content) > 1000,  # Reasonable amount of content
                'Clear Headlines': any(tag in content for tag in ['<h1', '<h2', '<h3']),
                'Visual Elements': any(element in content for element in ['<img', 'fa-', 'icon']),
                'Contact Information': any(contact in content for contact in ['email', 'phone', 'contact']),
            }
            
            for check, passed in content_checks.items():
                if not passed:
                    recommendations.append(f"📝 Improve: {check}")
        
        # Page-specific checks
        if expected_elements:
            for element in expected_elements:
                if element.lower() not in content:
                    issues.append(f"❌ Missing expected element: {element}")
        
        # Security checks
        security_checks = {
            'CSRF Protection': 'csrf' in content,
            'Secure Forms': 'method="post"' in content and 'csrf' in content if 'form' in content else True,
        }
        
        for check, passed in security_checks.items():
            if not passed:
                recommendations.append(f"🔒 Security: {check}")
        
        # Performance hints
        if 'placeholder' in content and 'via.placeholder' in content:
            recommendations.append("🎨 Replace placeholder images with real ones")
        
        if len(content) > 50000:  # Very large page
            recommendations.append("⚡ Consider page size optimization")
            
    except requests.exceptions.RequestException as e:
        issues.append(f"❌ Connection Error: {str(e)}")
    except Exception as e:
        issues.append(f"❌ Unexpected Error: {str(e)}")
    
    return issues, recommendations

def comprehensive_audit():
    """Run comprehensive audit of all pages"""
    print("🎯 ChamaLink Comprehensive UX Audit")
    print("=" * 50)
    
    # Define pages to audit
    pages = [
        # Public Pages
        (f"{BASE_URL}/", "Homepage", ["chamalink", "get started", "features"], True),
        (f"{BASE_URL}/about", "About Page", ["mission", "vision", "team"], True),
        (f"{BASE_URL}/features", "Features Page", ["financial", "management", "mobile"], True),
        (f"{BASE_URL}/contact", "Contact Page", ["email", "phone", "address"], True),
        (f"{BASE_URL}/plans/pricing", "Pricing Page", ["enterprise", "kes", "price"], True),
        (f"{BASE_URL}/terms", "Terms of Service", ["terms", "service", "agreement"], True),
        (f"{BASE_URL}/privacy", "Privacy Policy", ["privacy", "data", "policy"], True),
        
        # Auth Pages
        (f"{BASE_URL}/auth/register", "Registration", ["username", "email", "password"], False),
        (f"{BASE_URL}/auth/login", "Login", ["email", "password", "remember"], False),
        (f"{BASE_URL}/auth/forgot-password", "Forgot Password", ["email", "reset"], False),
        
        # Protected Pages (will likely redirect)
        (f"{BASE_URL}/dashboard", "Dashboard", None, False),
        (f"{BASE_URL}/founder-dashboard", "Founder Dashboard", None, False),
    ]
    
    total_issues = 0
    total_recommendations = 0
    critical_issues = []
    
    for url, page_name, expected_elements, should_have_content in pages:
        issues, recommendations = audit_page(url, page_name, expected_elements, should_have_content)
        
        if issues:
            total_issues += len(issues)
            for issue in issues:
                print(f"   {issue}")
                if "❌" in issue:
                    critical_issues.append(f"{page_name}: {issue}")
        else:
            print("   ✅ No major issues found")
        
        if recommendations:
            total_recommendations += len(recommendations)
            for rec in recommendations:
                print(f"   {rec}")
        
        time.sleep(0.5)  # Be nice to the server
    
    # Summary Report
    print("\n" + "=" * 50)
    print("📊 AUDIT SUMMARY")
    print("=" * 50)
    print(f"🔴 Total Issues Found: {total_issues}")
    print(f"💡 Total Recommendations: {total_recommendations}")
    
    if critical_issues:
        print(f"\n🚨 CRITICAL ISSUES TO FIX:")
        for issue in critical_issues[:10]:  # Show top 10
            print(f"   • {issue}")
    
    # Prioritized recommendations
    print(f"\n🎯 TOP PRIORITY FIXES:")
    priority_fixes = [
        "1. 🎨 Create professional logo and branding",
        "2. 📷 Replace placeholder images with real screenshots",
        "3. ✍️ Write compelling copy for About and Features pages",
        "4. 📱 Test and improve mobile responsiveness",
        "5. 🔗 Add customer testimonials and social proof",
        "6. 📧 Set up proper email templates and notifications",
        "7. 🎭 Add loading states and better error messages",
        "8. 🏠 Improve dashboard empty states and onboarding",
        "9. 📊 Add real analytics and monitoring",
        "10. 🚀 Prepare production deployment checklist"
    ]
    
    for fix in priority_fixes:
        print(f"   {fix}")
    
    # Overall score
    max_possible_score = len(pages) * 5  # 5 points per page
    deductions = total_issues * 2 + total_recommendations * 0.5
    score = max(0, max_possible_score - deductions)
    percentage = (score / max_possible_score) * 100
    
    print(f"\n⭐ OVERALL UX SCORE: {percentage:.1f}% ({score:.1f}/{max_possible_score})")
    
    if percentage >= 90:
        print("🌟 EXCELLENT - Ready for launch!")
    elif percentage >= 80:
        print("✅ GOOD - Minor polish needed")
    elif percentage >= 70:
        print("⚠️ FAIR - Significant improvements needed")
    else:
        print("🔴 NEEDS WORK - Major improvements required")

if __name__ == "__main__":
    comprehensive_audit()
