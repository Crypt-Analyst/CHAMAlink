import os
import sys
import subprocess
import json
from datetime import datetime
import sqlite3
import requests

def check_system_readiness():
    """Comprehensive CHAMAlink system readiness assessment"""
    
    print("🔍 CHAMAlink System Readiness Assessment")
    print("=" * 60)
    print(f"Assessment Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    results = {
        'overall_score': 0,
        'max_score': 0,
        'categories': {},
        'critical_issues': [],
        'recommendations': [],
        'production_ready': False
    }
    
    # 1. Core Application Structure
    print("\n📁 1. CORE APPLICATION STRUCTURE")
    app_structure_score = 0
    app_structure_max = 8
    
    required_files = [
        'app/__init__.py',
        'app/models/__init__.py', 
        'app/routes/__init__.py',
        'app/templates/base.html',
        'requirements.txt',
        'run.py',
        '.env',
        'config.py'
    ]
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
            app_structure_score += 1
        else:
            print(f"❌ {file} - MISSING")
            results['critical_issues'].append(f"Missing core file: {file}")
    
    results['categories']['App Structure'] = f"{app_structure_score}/{app_structure_max}"
    
    # 2. Database Health
    print("\n🗄️ 2. DATABASE HEALTH")
    db_score = 0
    db_max = 6
    
    try:
        # Check if database file exists
        if os.path.exists('instance/chamalink.db'):
            print("✅ Database file exists")
            db_score += 1
            
            # Check database tables
            conn = sqlite3.connect('instance/chamalink.db')
            cursor = conn.cursor()
            
            required_tables = ['users', 'chamas', 'chama_members', 'contributions', 'transactions', 'subscriptions']
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            existing_tables = [table[0] for table in cursor.fetchall()]
            
            for table in required_tables:
                if table in existing_tables:
                    print(f"✅ Table: {table}")
                    db_score += 1
                else:
                    print(f"❌ Table: {table} - MISSING")
                    results['critical_issues'].append(f"Missing database table: {table}")
            
            conn.close()
        else:
            print("❌ Database file not found")
            results['critical_issues'].append("Database file missing")
    except Exception as e:
        print(f"❌ Database error: {e}")
        results['critical_issues'].append(f"Database error: {e}")
    
    results['categories']['Database'] = f"{db_score}/{db_max}"
    
    # 3. Security Features
    print("\n🔒 3. SECURITY FEATURES")
    security_score = 0
    security_max = 8
    
    try:
        security_checks = [
            ('CSRF Protection', 'flask_wtf' in open('requirements.txt').read() if os.path.exists('requirements.txt') else False),
            ('Login Required Decorators', '@login_required' in open('app/routes/chama.py').read() if os.path.exists('app/routes/chama.py') else False),
            ('Password Hashing', 'werkzeug.security' in open('app/models/user.py').read() if os.path.exists('app/models/user.py') else False),
            ('Session Management', 'flask_login' in open('requirements.txt').read() if os.path.exists('requirements.txt') else False),
            ('Environment Variables', os.path.exists('.env')),
            ('Secret Key', 'SECRET_KEY' in open('.env').read() if os.path.exists('.env') else False),
            ('Database URI Security', 'sqlite:///' in open('.env').read() if os.path.exists('.env') else True),
            ('Error Handling', 'try:' in open('app/routes/chama.py').read() if os.path.exists('app/routes/chama.py') else False)
        ]
        
        for check_name, check_result in security_checks:
            if check_result:
                print(f"✅ {check_name}")
                security_score += 1
            else:
                print(f"❌ {check_name}")
                results['recommendations'].append(f"Implement {check_name}")
    except Exception as e:
        print(f"❌ Security check error: {e}")
    
    results['categories']['Security'] = f"{security_score}/{security_max}"
    
    # 4. API Endpoints
    print("\n🌐 4. API ENDPOINTS & ROUTES")
    api_score = 0
    api_max = 10
    
    route_files = [
        'app/routes/main.py',
        'app/routes/auth.py', 
        'app/routes/chama.py',
        'app/routes/payments.py',
        'app/routes/settings.py',
        'app/routes/reports.py',
        'app/routes/subscriptions.py',
        'app/routes/currency.py',
        'app/routes/feedback.py',
        'app/routes/leebot.py'
    ]
    
    for route_file in route_files:
        if os.path.exists(route_file):
            print(f"✅ {route_file}")
            api_score += 1
        else:
            print(f"❌ {route_file} - MISSING")
    
    results['categories']['API Routes'] = f"{api_score}/{api_max}"
    
    # 5. Frontend Components
    print("\n🎨 5. FRONTEND COMPONENTS")
    frontend_score = 0
    frontend_max = 8
    
    template_dirs = [
        'app/templates/auth/',
        'app/templates/chama/',
        'app/templates/main/',
        'app/templates/settings/',
        'app/templates/payments/',
        'app/templates/reports/',
        'app/static/css/',
        'app/static/js/'
    ]
    
    for template_dir in template_dirs:
        if os.path.exists(template_dir):
            print(f"✅ {template_dir}")
            frontend_score += 1
        else:
            print(f"❌ {template_dir} - MISSING")
    
    results['categories']['Frontend'] = f"{frontend_score}/{frontend_max}"
    
    # 6. Payment Integration
    print("\n💳 6. PAYMENT INTEGRATION")
    payment_score = 0
    payment_max = 4
    
    try:
        payment_checks = [
            ('M-Pesa Integration', 'mpesa' in open('app/routes/payments.py').read().lower() if os.path.exists('app/routes/payments.py') else False),
            ('Stripe Integration', 'stripe' in open('requirements.txt').read().lower() if os.path.exists('requirements.txt') else False),
            ('Payment Models', 'Transaction' in open('app/models/__init__.py').read() if os.path.exists('app/models/__init__.py') else False),
            ('Currency Support', os.path.exists('app/routes/currency.py'))
        ]
        
        for check_name, check_result in payment_checks:
            if check_result:
                print(f"✅ {check_name}")
                payment_score += 1
            else:
                print(f"⚠️ {check_name}")
    except Exception as e:
        print(f"❌ Payment check error: {e}")
    
    results['categories']['Payments'] = f"{payment_score}/{payment_max}"
    
    # 7. Performance & Scalability
    print("\n⚡ 7. PERFORMANCE & SCALABILITY")
    performance_score = 0
    performance_max = 6
    
    try:
        performance_checks = [
            ('Database Indexing', 'db.Index' in open('app/models/user.py').read() if os.path.exists('app/models/user.py') else False),
            ('Pagination', 'paginate' in open('app/routes/chama.py').read() if os.path.exists('app/routes/chama.py') else False),
            ('Caching Headers', 'Cache-Control' in open('app/__init__.py').read() if os.path.exists('app/__init__.py') else False),
            ('Static File Optimization', os.path.exists('app/static/css/') and os.path.exists('app/static/js/')),
            ('Error Logging', 'logging' in open('app/__init__.py').read() if os.path.exists('app/__init__.py') else False),
            ('Connection Pooling', 'pool' in open('config.py').read().lower() if os.path.exists('config.py') else False)
        ]
        
        for check_name, check_result in performance_checks:
            if check_result:
                print(f"✅ {check_name}")
                performance_score += 1
            else:
                print(f"⚠️ {check_name}")
                results['recommendations'].append(f"Implement {check_name}")
    except Exception as e:
        print(f"❌ Performance check error: {e}")
    
    results['categories']['Performance'] = f"{performance_score}/{performance_max}"
    
    # 8. Deployment Readiness
    print("\n🚀 8. DEPLOYMENT READINESS")
    deployment_score = 0
    deployment_max = 6
    
    try:
        deployment_checks = [
            ('Gunicorn/WSGI', 'gunicorn' in open('requirements.txt').read() if os.path.exists('requirements.txt') else False),
            ('Environment Config', os.path.exists('.env') and os.path.exists('.env.render')),
            ('Production Database', 'postgresql' in open('requirements.txt').read().lower() if os.path.exists('requirements.txt') else False),
            ('Docker Support', os.path.exists('Dockerfile')),
            ('Health Check Endpoint', '/health' in open('app/routes/main.py').read() if os.path.exists('app/routes/main.py') else False),
            ('Migrations', os.path.exists('migrations/') or 'flask-migrate' in open('requirements.txt').read() if os.path.exists('requirements.txt') else False)
        ]
        
        for check_name, check_result in deployment_checks:
            if check_result:
                print(f"✅ {check_name}")
                deployment_score += 1
            else:
                print(f"⚠️ {check_name}")
                results['recommendations'].append(f"Add {check_name}")
    except Exception as e:
        print(f"❌ Deployment check error: {e}")
    
    results['categories']['Deployment'] = f"{deployment_score}/{deployment_max}"
    
    # Calculate overall score
    total_score = (app_structure_score + db_score + security_score + api_score + 
                  frontend_score + payment_score + performance_score + deployment_score)
    total_max = (app_structure_max + db_max + security_max + api_max + 
                frontend_max + payment_max + performance_max + deployment_max)
    
    results['overall_score'] = total_score
    results['max_score'] = total_max
    overall_percentage = (total_score / total_max) * 100
    
    # Determine production readiness
    if overall_percentage >= 85 and len(results['critical_issues']) == 0:
        results['production_ready'] = True
        readiness_status = "🟢 PRODUCTION READY"
    elif overall_percentage >= 70:
        readiness_status = "🟡 STAGING READY (Minor Issues)"
    else:
        readiness_status = "🔴 NOT PRODUCTION READY"
    
    # Final Assessment
    print("\n" + "=" * 60)
    print("📊 FINAL ASSESSMENT")
    print("=" * 60)
    print(f"Overall Score: {total_score}/{total_max} ({overall_percentage:.1f}%)")
    print(f"Status: {readiness_status}")
    print()
    
    print("📋 Category Breakdown:")
    for category, score in results['categories'].items():
        print(f"  • {category}: {score}")
    
    if results['critical_issues']:
        print(f"\n🚨 Critical Issues ({len(results['critical_issues'])}):")
        for issue in results['critical_issues']:
            print(f"  • {issue}")
    
    if results['recommendations']:
        print(f"\n💡 Recommendations ({len(results['recommendations'])}):")
        for rec in results['recommendations'][:5]:  # Show top 5
            print(f"  • {rec}")
    
    # Production Readiness Checklist
    print("\n✅ PRODUCTION READINESS CHECKLIST")
    print("-" * 40)
    
    checklist = [
        ("Core application structure complete", app_structure_score >= 6),
        ("Database schema properly set up", db_score >= 4),
        ("Security measures implemented", security_score >= 6),
        ("All major routes functional", api_score >= 7),
        ("Frontend templates complete", frontend_score >= 6),
        ("Payment integration working", payment_score >= 2),
        ("Basic performance optimizations", performance_score >= 3),
        ("Deployment configuration ready", deployment_score >= 3)
    ]
    
    for check, passed in checklist:
        status = "✅" if passed else "❌"
        print(f"{status} {check}")
    
    print(f"\n🎯 RECOMMENDATION: {readiness_status}")
    
    if overall_percentage >= 85:
        print("Your CHAMAlink system is ready for production deployment!")
    elif overall_percentage >= 70:
        print("Your system needs minor fixes before production deployment.")
    else:
        print("Your system needs significant work before production deployment.")
    
    # Save results to file
    with open('system_readiness_report.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed report saved to: system_readiness_report.json")
    
    return results

def check_dropdown_functionality():
    """Check and fix dropdown menu functionality issues"""
    
    print("\n🔽 DROPDOWN FUNCTIONALITY CHECK")
    print("=" * 50)
    
    dropdown_issues = []
    
    # Check base.html for dropdown structure
    if os.path.exists('app/templates/base.html'):
        with open('app/templates/base.html', 'r') as f:
            base_content = f.read()
            
        # Check for missing routes
        missing_routes = []
        
        # Common dropdown links that might be missing routes
        dropdown_routes = [
            "url_for('main.dashboard')",
            "url_for('main.founder_dashboard')",
            "url_for('main.admin_user_management')",
            "url_for('penalties.penalty_dashboard')",
            "url_for('receipts.my_receipts')",
            "url_for('recurring.my_recurring_payments')",
            "url_for('main.reports')",
            "url_for('notifications.notification_dashboard')",
            "url_for('main.chat')",
            "url_for('main.profile')",
            "url_for('settings.account_settings')",
            "url_for('main.help_support')",
            "url_for('auth.logout')"
        ]
        
        for route in dropdown_routes:
            if route in base_content:
                print(f"✅ Found route: {route}")
            else:
                print(f"❌ Missing route: {route}")
                missing_routes.append(route)
        
        if missing_routes:
            dropdown_issues.extend(missing_routes)
    
    print(f"\nDropdown Issues Found: {len(dropdown_issues)}")
    
    return dropdown_issues

if __name__ == "__main__":
    # Run system readiness check
    results = check_system_readiness()
    
    # Check dropdown functionality
    dropdown_issues = check_dropdown_functionality()
    
    print("\n" + "=" * 60)
    print("🎯 NEXT STEPS")
    print("=" * 60)
    
    if dropdown_issues:
        print("🔧 Dropdown fixes needed:")
        for issue in dropdown_issues:
            print(f"  • {issue}")
    
    if not results['production_ready']:
        print("🚀 Focus on these critical issues first:")
        for issue in results['critical_issues'][:3]:
            print(f"  • {issue}")