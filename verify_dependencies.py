#!/usr/bin/env python3
"""
Dependency verification script for ChamaLink
Checks all critical dependencies and their availability
"""

import sys
import importlib
import subprocess
import os

def check_dependency(module_name, import_path=None, description=""):
    """Check if a dependency is available"""
    try:
        if import_path:
            importlib.import_module(import_path)
        else:
            importlib.import_module(module_name)
        return True, "✅ Available"
    except ImportError as e:
        return False, f"❌ Missing: {str(e)}"

def main():
    print("🔍 ChamaLink Dependency Verification")
    print("=" * 50)
    
    # Critical dependencies that cause import errors
    critical_deps = [
        ("Flask", "flask", "Web framework"),
        ("reportlab", "reportlab.lib.pagesizes", "PDF generation"),
        ("python-dateutil", "dateutil.relativedelta", "Date calculations"),
        ("africastalking", "africastalking", "SMS service"),
        ("qrcode", "qrcode", "QR code generation"),
        ("Pillow", "PIL", "Image processing"),
        ("psycopg2", "psycopg2", "PostgreSQL adapter"),
        ("gunicorn", "gunicorn", "WSGI server"),
        ("pyotp", "pyotp", "2FA authentication"),
        ("requests", "requests", "HTTP client"),
    ]
    
    print("🧪 Testing Critical Dependencies:")
    print("-" * 30)
    
    all_good = True
    for name, import_path, desc in critical_deps:
        available, status = check_dependency(name, import_path, desc)
        print(f"{status} {name:<20} - {desc}")
        if not available:
            all_good = False
    
    print("\n📋 Python Environment Info:")
    print("-" * 30)
    print(f"Python Version: {sys.version}")
    print(f"Python Executable: {sys.executable}")
    print(f"Platform: {sys.platform}")
    
    # Check pip installed packages
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', 'list'], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"\n📦 Installed Packages: {len(result.stdout.splitlines())} total")
            
            # Look for our critical packages
            installed_lines = result.stdout.lower()
            for name, _, _ in critical_deps:
                if name.lower().replace('-', '_') in installed_lines or name.lower() in installed_lines:
                    print(f"✅ {name} found in pip list")
                else:
                    print(f"❌ {name} NOT found in pip list")
        else:
            print("❌ Could not get pip list")
    except Exception as e:
        print(f"❌ Error checking pip: {e}")
    
    print("\n" + "=" * 50)
    if all_good:
        print("🎉 All critical dependencies are available!")
        print("✅ Application should start successfully")
    else:
        print("⚠️  Some dependencies are missing!")
        print("🔧 Check the error messages above")
    
    return all_good

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
