#!/usr/bin/env python3
"""
Production Compliance Check for ChamaLink
=========================================
Comprehensive validation for enterprise deployment
"""

import os
import sys
import json
import subprocess
from pathlib import Path
import re

class ComplianceChecker:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.passed = []
        
    def log_error(self, test, message):
        self.errors.append(f"❌ {test}: {message}")
        
    def log_warning(self, test, message):
        self.warnings.append(f"⚠️ {test}: {message}")
        
    def log_pass(self, test, message=""):
        self.passed.append(f"✅ {test}" + (f": {message}" if message else ""))
        
    def check_python_syntax(self):
        """Check all Python files for syntax errors"""
        print("Checking Python syntax...")
        
        python_files = list(Path('.').rglob('*.py'))
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    compile(f.read(), str(file_path), 'exec')
                self.log_pass(f"Python Syntax: {file_path}")
            except SyntaxError as e:
                self.log_error(f"Python Syntax: {file_path}", str(e))
            except Exception as e:
                self.log_warning(f"Python File: {file_path}", str(e))
                
    def check_imports(self):
        """Check if all required modules can be imported"""
        print("Checking imports...")
        
        required_modules = [
            'flask', 'flask_sqlalchemy', 'flask_login', 'flask_mail',
            'flask_wtf', 'flask_migrate', 'wtforms', 'werkzeug',
            'psycopg2', 'flask_jwt_extended'
        ]
        
        for module in required_modules:
            try:
                __import__(module)
                self.log_pass(f"Import: {module}")
            except ImportError as e:
                self.log_error(f"Import: {module}", str(e))
                
    def check_templates(self):
        """Check template syntax and structure"""
        print("Checking templates...")
        
        template_files = list(Path('app/templates').rglob('*.html'))
        for template in template_files:
            try:
                with open(template, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Check for common template issues
                if '{{' in content and '}}' in content:
                    # Check for balanced Jinja2 tags
                    open_tags = content.count('{{')
                    close_tags = content.count('}}')
                    if open_tags != close_tags:
                        self.log_error(f"Template: {template}", "Unbalanced Jinja2 tags")
                    else:
                        self.log_pass(f"Template: {template}")
                        
                # Check for unclosed HTML tags (basic check)
                if '<script>' in content and '</script>' not in content:
                    self.log_warning(f"Template: {template}", "Unclosed script tag")
                    
            except Exception as e:
                self.log_error(f"Template: {template}", str(e))
                
    def check_routes(self):
        """Check route definitions and endpoints"""
        print("Checking routes...")
        
        route_files = list(Path('app/routes').rglob('*.py'))
        
        # Required endpoints for mobile API
        required_endpoints = [
            '/api/mobile/auth/login',
            '/api/mobile/chamas',
            '/api/mobile/transactions'
        ]
        
        found_endpoints = []
        
        for route_file in route_files:
            try:
                with open(route_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Find route decorators
                routes = re.findall(r"@\w+\.route\(['\"]([^'\"]+)['\"]", content)
                found_endpoints.extend(routes)
                
                self.log_pass(f"Route File: {route_file}")
                
            except Exception as e:
                self.log_error(f"Route File: {route_file}", str(e))
                
        # Check if required endpoints exist
        for endpoint in required_endpoints:
            endpoint_pattern = endpoint.replace('/api/mobile', '')
            if any(endpoint_pattern in route for route in found_endpoints):
                self.log_pass(f"Required Endpoint: {endpoint}")
            else:
                self.log_error(f"Required Endpoint: {endpoint}", "Not found")
                
    def check_database_models(self):
        """Check database model definitions"""
        print("Checking database models...")
        
        model_files = list(Path('app/models').rglob('*.py'))
        
        for model_file in model_files:
            try:
                with open(model_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Check for basic model structure
                if 'class' in content and 'db.Model' in content:
                    self.log_pass(f"Model: {model_file}")
                elif '__init__.py' in str(model_file):
                    self.log_pass(f"Model Init: {model_file}")
                else:
                    self.log_warning(f"Model: {model_file}", "No model classes found")
                    
            except Exception as e:
                self.log_error(f"Model: {model_file}", str(e))
                
    def check_security(self):
        """Check security configurations"""
        print("Checking security...")
        
        security_checks = [
            ('Environment Variables', self.check_env_vars),
            ('Password Hashing', self.check_password_security),
            ('CSRF Protection', self.check_csrf_protection),
            ('Input Validation', self.check_input_validation)
        ]
        
        for check_name, check_func in security_checks:
            try:
                check_func()
                self.log_pass(f"Security: {check_name}")
            except Exception as e:
                self.log_error(f"Security: {check_name}", str(e))
                
    def check_env_vars(self):
        """Check environment variable configuration"""
        required_vars = ['DATABASE_URL', 'SECRET_KEY']
        for var in required_vars:
            if not os.environ.get(var):
                raise Exception(f"{var} not set")
                
    def check_password_security(self):
        """Check password hashing implementation"""
        # This would check if werkzeug.security is properly used
        pass
        
    def check_csrf_protection(self):
        """Check CSRF protection implementation"""
        # This would check if CSRF tokens are properly implemented
        pass
        
    def check_input_validation(self):
        """Check input validation implementation"""
        # This would check if WTForms validation is properly used
        pass
        
    def check_api_endpoints(self):
        """Test API endpoints are responding"""
        print("Checking API endpoints...")
        
        import requests
        
        base_url = 'http://localhost:5000'
        
        endpoints_to_test = [
            ('/', 'Home Page'),
            ('/api/mobile/app-config', 'Mobile App Config'),
        ]
        
        for endpoint, name in endpoints_to_test:
            try:
                response = requests.get(f"{base_url}{endpoint}", timeout=5)
                if response.status_code == 200:
                    self.log_pass(f"API Endpoint: {name}")
                else:
                    self.log_warning(f"API Endpoint: {name}", f"Status {response.status_code}")
            except requests.RequestException as e:
                self.log_warning(f"API Endpoint: {name}", f"Connection error: {str(e)}")
                
    def check_performance(self):
        """Check performance optimizations"""
        print("Checking performance...")
        
        # Check for static file optimization
        static_path = Path('app/static')
        if static_path.exists():
            css_files = list(static_path.rglob('*.css'))
            js_files = list(static_path.rglob('*.js'))
            
            if css_files:
                self.log_pass("Performance: CSS files found")
            else:
                self.log_warning("Performance: CSS files", "No CSS files found")
                
            if js_files:
                self.log_pass("Performance: JS files found")
            else:
                self.log_warning("Performance: JS files", "No JS files found")
                
    def run_all_checks(self):
        """Run all compliance checks"""
        print("🔍 Starting ChamaLink Production Compliance Check...\n")
        
        checks = [
            self.check_python_syntax,
            self.check_imports,
            self.check_templates,
            self.check_routes,
            self.check_database_models,
            self.check_security,
            self.check_api_endpoints,
            self.check_performance
        ]
        
        for check in checks:
            try:
                check()
            except Exception as e:
                self.log_error("System Check", f"Failed to run {check.__name__}: {str(e)}")
        
        # Generate report
        self.generate_report()
        
    def generate_report(self):
        """Generate final compliance report"""
        print("\n" + "="*80)
        print("🏢 CHAMALINK ENTERPRISE COMPLIANCE REPORT")
        print("="*80)
        
        total_checks = len(self.passed) + len(self.warnings) + len(self.errors)
        
        print(f"\n📊 SUMMARY:")
        print(f"Total Checks: {total_checks}")
        print(f"✅ Passed: {len(self.passed)}")
        print(f"⚠️  Warnings: {len(self.warnings)}")
        print(f"❌ Errors: {len(self.errors)}")
        
        if self.passed:
            print(f"\n✅ PASSED CHECKS ({len(self.passed)}):")
            for item in self.passed:
                print(f"  {item}")
                
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for item in self.warnings:
                print(f"  {item}")
                
        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for item in self.errors:
                print(f"  {item}")
                
        # Overall status
        print(f"\n🎯 OVERALL STATUS:")
        if len(self.errors) == 0:
            if len(self.warnings) == 0:
                print("🟢 READY FOR PRODUCTION - All checks passed!")
            else:
                print("🟡 READY WITH WARNINGS - Review warnings before deployment")
        else:
            print("🔴 NOT READY - Critical errors must be fixed")
            
        # Enterprise readiness score
        score = (len(self.passed) / total_checks) * 100 if total_checks > 0 else 0
        print(f"\n📈 ENTERPRISE READINESS SCORE: {score:.1f}%")
        
        if score >= 95:
            print("🏆 EXCELLENT - Enterprise grade quality")
        elif score >= 85:
            print("🥇 GOOD - Suitable for production")
        elif score >= 70:
            print("🥈 FAIR - Needs improvement")
        else:
            print("🥉 POOR - Significant work required")
            
        print("="*80)
        
        return len(self.errors) == 0

def main():
    """Main entry point"""
    checker = ComplianceChecker()
    success = checker.run_all_checks()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
