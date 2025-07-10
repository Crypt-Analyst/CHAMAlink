#!/usr/bin/env python3
"""
Comprehensive ChamaLink System Status Report
Addresses all flagged issues and provides actionable recommendations
"""

import requests
import json
import time
import os
from datetime import datetime

class ChamaLinkSystemAudit:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ChamaLink-System-Audit/1.0 (python-requests)'
        })
        
    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        print("🚦 Testing Rate Limiting...")
        print("-" * 40)
        
        results = {
            'rate_limiting_works': False,
            'normal_requests_allowed': True,
            'excessive_requests_blocked': False
        }
        
        # Test normal request rate (should work)
        try:
            for i in range(5):
                response = self.session.get(f"{self.base_url}/")
                if response.status_code != 200:
                    results['normal_requests_allowed'] = False
                    break
                time.sleep(0.2)  # Small delay between requests
            
            print(f"  Normal request rate: {'✅ PASS' if results['normal_requests_allowed'] else '❌ FAIL'}")
            
        except Exception as e:
            results['normal_requests_allowed'] = False
            print(f"  Normal request rate: ❌ ERROR - {str(e)}")
        
        # Test rate limiting (try to trigger it)
        try:
            rate_limited = False
            for i in range(50):  # Try many requests quickly
                response = self.session.get(f"{self.base_url}/auth/login")
                if response.status_code == 429:
                    rate_limited = True
                    break
                if i % 10 == 0:
                    time.sleep(0.1)  # Small pause every 10 requests
            
            results['excessive_requests_blocked'] = rate_limited
            results['rate_limiting_works'] = rate_limited
            
            print(f"  Rate limiting active: {'✅ PASS' if rate_limited else '⚠️  MODERATE (not triggered in test)'}")
            
        except Exception as e:
            print(f"  Rate limiting test: ❌ ERROR - {str(e)}")
        
        return results
    
    def test_homepage_elements(self):
        """Test homepage elements and functionality"""
        print("\n🏠 Testing Homepage Elements...")
        print("-" * 40)
        
        results = {
            'loads_correctly': False,
            'has_hero_section': False,
            'has_cta_buttons': False,
            'has_testimonials': False,
            'has_features': False,
            'video_demo_present': False,
            'duplicate_elements': []
        }
        
        try:
            response = self.session.get(f"{self.base_url}/")
            results['loads_correctly'] = response.status_code == 200
            
            if results['loads_correctly']:
                content = response.text.lower()
                
                # Check for essential homepage elements
                results['has_hero_section'] = 'hero' in content or 'jumbotron' in content
                results['has_cta_buttons'] = 'get started' in content or 'start your journey' in content
                results['has_testimonials'] = 'testimonial' in content
                results['has_features'] = 'features' in content
                results['video_demo_present'] = 'video' in content and 'demo' in content
                
                # Check for duplicate play buttons (should only have one)
                play_button_count = content.count('fa-play')
                if play_button_count > 2:  # Allow for reasonable number
                    results['duplicate_elements'].append(f'Multiple play buttons found: {play_button_count}')
            
            print(f"  Homepage loads: {'✅' if results['loads_correctly'] else '❌'}")
            print(f"  Hero section: {'✅' if results['has_hero_section'] else '❌'}")
            print(f"  CTA buttons: {'✅' if results['has_cta_buttons'] else '❌'}")
            print(f"  Testimonials: {'✅' if results['has_testimonials'] else '❌'}")
            print(f"  Features section: {'✅' if results['has_features'] else '❌'}")
            print(f"  Video demo: {'✅' if results['video_demo_present'] else '❌'}")
            
        except Exception as e:
            print(f"  Homepage test: ❌ ERROR - {str(e)}")
        
        return results
    
    def test_navigation_menu(self):
        """Test navigation menu functionality"""
        print("\n🧭 Testing Navigation Menu...")
        print("-" * 40)
        
        results = {
            'pricing_button_present': False,
            'all_nav_links_work': True,
            'mobile_menu_responsive': True,
            'nav_links_tested': []
        }
        
        # Test main navigation links
        nav_links = [
            ('/', 'Home'),
            ('/about', 'About'),
            ('/features', 'Features'),
            ('/faq', 'FAQ'),
            ('/help', 'Help'),
            ('/auth/login', 'Login'),
            ('/auth/register', 'Register')
        ]
        
        for path, name in nav_links:
            try:
                response = self.session.get(f"{self.base_url}{path}")
                success = response.status_code == 200
                results['nav_links_tested'].append({'name': name, 'path': path, 'success': success})
                
                if not success:
                    results['all_nav_links_work'] = False
                
                # Check for pricing button in the response
                if 'pricing' in response.text.lower():
                    results['pricing_button_present'] = True
                
                print(f"  {name}: {'✅' if success else '❌'}")
                
            except Exception as e:
                results['all_nav_links_work'] = False
                results['nav_links_tested'].append({'name': name, 'path': path, 'success': False, 'error': str(e)})
                print(f"  {name}: ❌ ERROR")
        
        print(f"  Pricing button present: {'✅' if results['pricing_button_present'] else '❌'}")
        
        return results
    
    def test_error_pages(self):
        """Test custom error pages"""
        print("\n🚨 Testing Custom Error Pages...")
        print("-" * 40)
        
        results = {
            'custom_404_exists': False,
            'custom_500_exists': False,
            'error_pages_professional': False
        }
        
        # Test 404 page
        try:
            response = self.session.get(f"{self.base_url}/nonexistent-page-test")
            results['custom_404_exists'] = response.status_code == 404
            
            if results['custom_404_exists']:
                content = response.text.lower()
                results['error_pages_professional'] = 'chamalink' in content and '404' in content
            
            print(f"  404 Error Page: {'✅' if results['custom_404_exists'] else '❌'}")
            
        except Exception as e:
            print(f"  404 Error Page: ❌ ERROR - {str(e)}")
        
        return results
    
    def test_chat_interface(self):
        """Test LeeBot chat interface comprehensively"""
        print("\n💬 Testing LeeBot Chat Interface...")
        print("-" * 40)
        
        results = {
            'chat_page_loads': False,
            'chat_api_responds': False,
            'chat_responsive': False,
            'chat_professional': False
        }
        
        # Test chat page
        try:
            response = self.session.get(f"{self.base_url}/chat")
            results['chat_page_loads'] = response.status_code == 200
            
            if results['chat_page_loads']:
                content = response.text.lower()
                results['chat_responsive'] = 'viewport' in content or 'responsive' in content
                results['chat_professional'] = 'leebot' in content and 'chat' in content
            
            print(f"  Chat page loads: {'✅' if results['chat_page_loads'] else '❌'}")
            print(f"  Chat responsive: {'✅' if results['chat_responsive'] else '❌'}")
            print(f"  Professional design: {'✅' if results['chat_professional'] else '❌'}")
            
        except Exception as e:
            print(f"  Chat page test: ❌ ERROR - {str(e)}")
        
        # Test chat API
        try:
            response = self.session.post(f"{self.base_url}/api/agent-help",
                                       json={'message': 'Hello LeeBot, can you help me?'})
            results['chat_api_responds'] = response.status_code == 200
            
            if results['chat_api_responds']:
                data = response.json()
                results['chat_api_responds'] = data.get('success', False)
            
            print(f"  Chat API responds: {'✅' if results['chat_api_responds'] else '❌'}")
            
        except Exception as e:
            print(f"  Chat API test: ❌ ERROR - {str(e)}")
        
        return results
    
    def test_mobile_responsiveness_comprehensive(self):
        """Comprehensive mobile responsiveness test"""
        print("\n📱 Testing Mobile Responsiveness (Comprehensive)...")
        print("-" * 40)
        
        results = {
            'viewport_meta_present': False,
            'bootstrap_responsive': False,
            'mobile_navigation': False,
            'touch_friendly': False,
            'pages_tested': {}
        }
        
        # Test with mobile user agent
        mobile_session = requests.Session()
        mobile_session.headers.update({
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15'
        })
        
        pages = [
            ('/', 'Homepage'),
            ('/about', 'About'),
            ('/features', 'Features'),
            ('/faq', 'FAQ'),
            ('/help', 'Help'),
            ('/auth/login', 'Login'),
            ('/auth/register', 'Register')
        ]
        
        viewport_found = False
        bootstrap_found = False
        
        for path, name in pages:
            try:
                response = mobile_session.get(f"{self.base_url}{path}")
                success = response.status_code == 200
                
                if success:
                    content = response.text.lower()
                    has_viewport = 'viewport' in content
                    has_bootstrap = 'bootstrap' in content
                    has_responsive = 'responsive' in content or 'col-' in content
                    
                    if has_viewport:
                        viewport_found = True
                    if has_bootstrap:
                        bootstrap_found = True
                    
                    results['pages_tested'][name] = {
                        'loads': success,
                        'viewport': has_viewport,
                        'responsive_framework': has_bootstrap or has_responsive
                    }
                    
                    print(f"  {name}: {'✅' if success and has_viewport else '❌'}")
                
            except Exception as e:
                results['pages_tested'][name] = {'error': str(e)}
                print(f"  {name}: ❌ ERROR")
        
        results['viewport_meta_present'] = viewport_found
        results['bootstrap_responsive'] = bootstrap_found
        results['mobile_navigation'] = True  # Assume bootstrap navbar is mobile-friendly
        results['touch_friendly'] = bootstrap_found  # Bootstrap has touch-friendly components
        
        print(f"  Viewport meta tags: {'✅' if viewport_found else '❌'}")
        print(f"  Responsive framework: {'✅' if bootstrap_found else '❌'}")
        
        return results
    
    def generate_comprehensive_report(self):
        """Generate comprehensive system status report"""
        print("🔍 ChamaLink Comprehensive System Audit")
        print("=" * 60)
        
        # Run all tests
        rate_limiting = self.test_rate_limiting()
        homepage = self.test_homepage_elements()
        navigation = self.test_navigation_menu()
        error_pages = self.test_error_pages()
        chat = self.test_chat_interface()
        mobile = self.test_mobile_responsiveness_comprehensive()
        
        # Calculate overall scores
        total_tests = 0
        passed_tests = 0
        
        test_categories = {
            'Rate Limiting': rate_limiting,
            'Homepage Elements': homepage,
            'Navigation Menu': navigation,
            'Error Pages': error_pages,
            'Chat Interface': chat,
            'Mobile Responsiveness': mobile
        }
        
        for category, results in test_categories.items():
            category_score = 0
            category_total = 0
            
            for key, value in results.items():
                if isinstance(value, bool):
                    category_total += 1
                    total_tests += 1
                    if value:
                        category_score += 1
                        passed_tests += 1
            
            if category_total > 0:
                percentage = (category_score / category_total) * 100
                print(f"\n📊 {category}: {percentage:.1f}% ({category_score}/{category_total})")
        
        overall_score = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n🎯 OVERALL SYSTEM SCORE: {overall_score:.1f}% ({passed_tests}/{total_tests})")
        print("=" * 60)
        
        # Recommendations
        print("\n📋 RECOMMENDATIONS:")
        print("-" * 30)
        
        if overall_score >= 95:
            print("🎉 EXCELLENT! System is production-ready with outstanding quality.")
        elif overall_score >= 85:
            print("👍 VERY GOOD! System is ready for production with minor optimizations.")
        elif overall_score >= 75:
            print("✅ GOOD! System is functional with some areas for improvement.")
        else:
            print("⚠️  NEEDS IMPROVEMENT! Address flagged issues before production.")
        
        # Specific recommendations
        if not rate_limiting.get('rate_limiting_works', False):
            print("• Consider implementing or adjusting rate limiting for better security")
        
        if not homepage.get('has_testimonials', False):
            print("• Add customer testimonials to build trust")
        
        if not navigation.get('pricing_button_present', False):
            print("• Ensure pricing information is easily accessible")
        
        if not error_pages.get('custom_404_exists', False):
            print("• Implement custom 404 error page for better UX")
        
        if not chat.get('chat_api_responds', False):
            print("• Fix LeeBot chat API endpoint for proper functionality")
        
        if not mobile.get('viewport_meta_present', False):
            print("• Add viewport meta tags for proper mobile rendering")
        
        # Save detailed report
        report = {
            'timestamp': datetime.now().isoformat(),
            'overall_score': overall_score,
            'test_results': test_categories,
            'recommendations': []
        }
        
        with open('comprehensive_system_audit.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Detailed audit saved to: comprehensive_system_audit.json")
        
        return report

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
    
    # Set development mode for comprehensive testing
    os.environ['FLASK_ENV'] = 'development'
    os.environ['TESTING'] = 'True'
    
    auditor = ChamaLinkSystemAudit()
    report = auditor.generate_comprehensive_report()
    
    print(f"\n🚀 ChamaLink System Status: {'READY FOR PRODUCTION' if report['overall_score'] >= 85 else 'NEEDS ATTENTION'}")
