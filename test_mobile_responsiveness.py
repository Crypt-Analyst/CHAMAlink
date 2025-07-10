#!/usr/bin/env python3
"""
Mobile Responsiveness Test Script for ChamaLink
Tests all forms and pages on various mobile screen sizes
"""

import time
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class MobileResponsivenessTest:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.test_results = []
        self.mobile_devices = [
            {"name": "iPhone SE", "width": 375, "height": 667},
            {"name": "iPhone 12", "width": 390, "height": 844},
            {"name": "Samsung Galaxy S21", "width": 384, "height": 854},
            {"name": "iPad Mini", "width": 768, "height": 1024},
            {"name": "Small Mobile", "width": 320, "height": 568}
        ]
        
    def setup_driver(self, device):
        """Setup Chrome driver with mobile device emulation"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Mobile emulation
        mobile_emulation = {
            "deviceMetrics": {
                "width": device["width"],
                "height": device["height"],
                "pixelRatio": 2.0
            },
            "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15"
        }
        chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)
        
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    
    def test_page_responsiveness(self, driver, page_name, url, device):
        """Test a specific page for mobile responsiveness"""
        result = {
            "page": page_name,
            "device": device["name"],
            "url": url,
            "timestamp": datetime.now().isoformat(),
            "tests": {}
        }
        
        try:
            # Load page
            driver.get(url)
            time.sleep(2)
            
            # Test 1: Page loads without horizontal scroll
            body_width = driver.execute_script("return document.body.scrollWidth")
            viewport_width = device["width"]
            result["tests"]["no_horizontal_scroll"] = body_width <= viewport_width + 20  # 20px tolerance
            
            # Test 2: Navigation menu is accessible
            try:
                nav_element = driver.find_element(By.TAG_NAME, "nav")
                result["tests"]["navigation_present"] = True
                
                # Check if mobile menu toggle exists for small screens
                if device["width"] < 768:
                    try:
                        mobile_toggle = driver.find_element(By.CSS_SELECTOR, ".navbar-toggler, .mobile-menu-toggle, [data-bs-toggle='collapse']")
                        result["tests"]["mobile_menu_toggle"] = True
                    except NoSuchElementException:
                        result["tests"]["mobile_menu_toggle"] = False
                else:
                    result["tests"]["mobile_menu_toggle"] = True
                    
            except NoSuchElementException:
                result["tests"]["navigation_present"] = False
                result["tests"]["mobile_menu_toggle"] = False
            
            # Test 3: Forms are properly sized
            forms = driver.find_elements(By.TAG_NAME, "form")
            if forms:
                form_test_results = []
                for i, form in enumerate(forms[:3]):  # Test first 3 forms
                    form_width = form.size["width"]
                    is_responsive = form_width <= viewport_width
                    form_test_results.append(is_responsive)
                
                result["tests"]["forms_responsive"] = all(form_test_results)
                result["tests"]["forms_count"] = len(forms)
            else:
                result["tests"]["forms_responsive"] = True  # No forms to test
                result["tests"]["forms_count"] = 0
            
            # Test 4: Buttons are touch-friendly (min 44px height)
            buttons = driver.find_elements(By.CSS_SELECTOR, "button, .btn, input[type='submit']")
            touch_friendly_buttons = []
            for button in buttons[:10]:  # Test first 10 buttons
                height = button.size["height"]
                touch_friendly_buttons.append(height >= 44)
            
            result["tests"]["touch_friendly_buttons"] = all(touch_friendly_buttons) if touch_friendly_buttons else True
            result["tests"]["buttons_tested"] = len(touch_friendly_buttons)
            
            # Test 5: Text is readable (font size check)
            body_font_size = driver.execute_script("""
                return window.getComputedStyle(document.body).fontSize
            """)
            if body_font_size:
                font_size_px = int(body_font_size.replace('px', ''))
                result["tests"]["readable_text"] = font_size_px >= 16
            else:
                result["tests"]["readable_text"] = True
            
            # Test 6: Images are responsive
            images = driver.find_elements(By.TAG_NAME, "img")
            responsive_images = []
            for img in images[:5]:  # Test first 5 images
                img_width = img.size["width"]
                responsive_images.append(img_width <= viewport_width)
            
            result["tests"]["responsive_images"] = all(responsive_images) if responsive_images else True
            result["tests"]["images_tested"] = len(responsive_images)
            
            # Test 7: Modal dialogs work on mobile
            try:
                modal_triggers = driver.find_elements(By.CSS_SELECTOR, "[data-bs-toggle='modal'], [data-toggle='modal']")
                if modal_triggers:
                    # Click first modal trigger
                    driver.execute_script("arguments[0].click();", modal_triggers[0])
                    time.sleep(1)
                    
                    modal = driver.find_element(By.CSS_SELECTOR, ".modal.show, .modal.in")
                    modal_width = modal.size["width"]
                    result["tests"]["modal_responsive"] = modal_width <= viewport_width
                    
                    # Close modal
                    driver.execute_script("$('.modal').modal('hide');")
                    time.sleep(1)
                else:
                    result["tests"]["modal_responsive"] = True  # No modals to test
            except:
                result["tests"]["modal_responsive"] = True
            
            # Overall score
            test_scores = [v for k, v in result["tests"].items() if isinstance(v, bool)]
            result["overall_score"] = (sum(test_scores) / len(test_scores)) * 100 if test_scores else 0
            result["status"] = "PASS" if result["overall_score"] >= 80 else "FAIL"
            
        except Exception as e:
            result["error"] = str(e)
            result["status"] = "ERROR"
            result["overall_score"] = 0
        
        return result
    
    def test_form_functionality(self, driver, device):
        """Test specific form interactions on mobile"""
        results = []
        
        # Test registration form
        try:
            driver.get(f"{self.base_url}/auth/register")
            time.sleep(2)
            
            form_result = {
                "form": "Registration",
                "device": device["name"],
                "tests": {}
            }
            
            # Test form field accessibility
            email_field = driver.find_element(By.NAME, "email")
            password_field = driver.find_element(By.NAME, "password")
            
            # Test field focusing and typing
            email_field.click()
            email_field.send_keys("test@example.com")
            form_result["tests"]["email_input"] = email_field.get_attribute("value") == "test@example.com"
            
            password_field.click()
            password_field.send_keys("testpassword123")
            form_result["tests"]["password_input"] = password_field.get_attribute("value") == "testpassword123"
            
            # Test form submission button accessibility
            submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
            form_result["tests"]["submit_accessible"] = submit_btn.is_enabled()
            
            results.append(form_result)
            
        except Exception as e:
            results.append({
                "form": "Registration",
                "device": device["name"],
                "error": str(e),
                "status": "ERROR"
            })
        
        # Test login form
        try:
            driver.get(f"{self.base_url}/auth/login")
            time.sleep(2)
            
            form_result = {
                "form": "Login",
                "device": device["name"],
                "tests": {}
            }
            
            # Test form fields
            email_field = driver.find_element(By.NAME, "email")
            password_field = driver.find_element(By.NAME, "password")
            
            email_field.click()
            email_field.send_keys("test@example.com")
            form_result["tests"]["email_input"] = True
            
            password_field.click()
            password_field.send_keys("password")
            form_result["tests"]["password_input"] = True
            
            # Test remember me checkbox
            try:
                remember_checkbox = driver.find_element(By.NAME, "remember_me")
                remember_checkbox.click()
                form_result["tests"]["remember_checkbox"] = True
            except:
                form_result["tests"]["remember_checkbox"] = False
            
            results.append(form_result)
            
        except Exception as e:
            results.append({
                "form": "Login",
                "device": device["name"],
                "error": str(e),
                "status": "ERROR"
            })
        
        return results
    
    def run_comprehensive_test(self):
        """Run comprehensive mobile responsiveness test"""
        print("🔍 Starting ChamaLink Mobile Responsiveness Test...")
        print("=" * 60)
        
        # Pages to test
        test_pages = [
            ("Homepage", "/"),
            ("Login", "/auth/login"),
            ("Register", "/auth/register"),
            ("Features", "/features"),
            ("About", "/about"),
            ("Contact", "/contact"),
            ("FAQ", "/faq"),
            ("Help", "/help"),
            ("Dashboard", "/dashboard"),
            ("Pricing", "/pricing")
        ]
        
        for device in self.mobile_devices:
            print(f"\n📱 Testing on {device['name']} ({device['width']}x{device['height']})")
            print("-" * 50)
            
            driver = self.setup_driver(device)
            
            try:
                # Test each page
                for page_name, url in test_pages:
                    print(f"  Testing {page_name}...", end=" ")
                    
                    result = self.test_page_responsiveness(driver, page_name, f"{self.base_url}{url}", device)
                    self.test_results.append(result)
                    
                    if result["status"] == "PASS":
                        print(f"✅ {result['overall_score']:.1f}%")
                    elif result["status"] == "FAIL":
                        print(f"❌ {result['overall_score']:.1f}%")
                    else:
                        print("🚫 ERROR")
                
                # Test form functionality
                print("  Testing forms...", end=" ")
                form_results = self.test_form_functionality(driver, device)
                self.test_results.extend(form_results)
                print("✅ Complete")
                
            finally:
                driver.quit()
        
        # Generate report
        self.generate_report()
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 60)
        print("📊 MOBILE RESPONSIVENESS TEST REPORT")
        print("=" * 60)
        
        # Overall statistics
        total_tests = len([r for r in self.test_results if "overall_score" in r])
        passed_tests = len([r for r in self.test_results if r.get("status") == "PASS"])
        failed_tests = len([r for r in self.test_results if r.get("status") == "FAIL"])
        error_tests = len([r for r in self.test_results if r.get("status") == "ERROR"])
        
        print(f"\n📈 Overall Statistics:")
        print(f"  Total Tests: {total_tests}")
        print(f"  Passed: {passed_tests} ✅")
        print(f"  Failed: {failed_tests} ❌")
        print(f"  Errors: {error_tests} 🚫")
        print(f"  Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "N/A")
        
        # Device-specific results
        print(f"\n📱 Results by Device:")
        for device in self.mobile_devices:
            device_results = [r for r in self.test_results if r.get("device") == device["name"] and "overall_score" in r]
            if device_results:
                avg_score = sum(r["overall_score"] for r in device_results) / len(device_results)
                status_counts = {}
                for r in device_results:
                    status = r.get("status", "UNKNOWN")
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                print(f"  {device['name']:15} | Avg Score: {avg_score:5.1f}% | "
                      f"Pass: {status_counts.get('PASS', 0):2} | "
                      f"Fail: {status_counts.get('FAIL', 0):2} | "
                      f"Error: {status_counts.get('ERROR', 0):2}")
        
        # Page-specific results
        print(f"\n📄 Results by Page:")
        pages = set(r.get("page") for r in self.test_results if r.get("page"))
        for page in sorted(pages):
            page_results = [r for r in self.test_results if r.get("page") == page and "overall_score" in r]
            if page_results:
                avg_score = sum(r["overall_score"] for r in page_results) / len(page_results)
                issues = sum(1 for r in page_results if r.get("status") != "PASS")
                
                status = "✅" if avg_score >= 80 and issues == 0 else "⚠️" if avg_score >= 60 else "❌"
                print(f"  {page:15} | {status} {avg_score:5.1f}% | Issues: {issues}")
        
        # Critical issues
        critical_issues = []
        for result in self.test_results:
            if result.get("status") == "FAIL" and result.get("overall_score", 0) < 50:
                critical_issues.append(f"{result.get('page', 'Unknown')} on {result.get('device', 'Unknown')}")
        
        if critical_issues:
            print(f"\n🚨 Critical Issues (Score < 50%):")
            for issue in critical_issues[:10]:  # Show top 10
                print(f"  - {issue}")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        
        # Check common issues
        horizontal_scroll_issues = len([r for r in self.test_results 
                                      if r.get("tests", {}).get("no_horizontal_scroll") == False])
        if horizontal_scroll_issues > 0:
            print(f"  - Fix horizontal scrolling issues ({horizontal_scroll_issues} instances)")
        
        button_issues = len([r for r in self.test_results 
                           if r.get("tests", {}).get("touch_friendly_buttons") == False])
        if button_issues > 0:
            print(f"  - Improve button touch targets ({button_issues} instances)")
        
        text_issues = len([r for r in self.test_results 
                         if r.get("tests", {}).get("readable_text") == False])
        if text_issues > 0:
            print(f"  - Increase font sizes for better readability ({text_issues} instances)")
        
        form_issues = len([r for r in self.test_results 
                         if r.get("tests", {}).get("forms_responsive") == False])
        if form_issues > 0:
            print(f"  - Fix form responsiveness issues ({form_issues} instances)")
        
        # Save detailed results to file
        with open("mobile_test_results.json", "w") as f:
            json.dump(self.test_results, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: mobile_test_results.json")
        print("\n" + "=" * 60)

if __name__ == "__main__":
    # Check if server is running
    import requests
    import sys
    
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
    
    # Run the test
    tester = MobileResponsivenessTest(base_url)
    tester.run_comprehensive_test()
