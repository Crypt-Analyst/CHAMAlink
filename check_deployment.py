#!/usr/bin/env python3
"""
ChamaLink Deployment Health Check Script
Monitors deployment status and validates core functionality
"""

import requests
import time
import sys
from urllib.parse import urljoin

# Deployment URLs
RENDER_URL = "https://chamalink.onrender.com"
HEALTH_ENDPOINTS = [
    "/",
    "/auth/login",
    "/auth/register",
    "/dashboard"
]

def check_deployment_health():
    """Check if the deployment is healthy"""
    print("🔍 ChamaLink Deployment Health Check")
    print("=" * 50)
    
    overall_status = True
    
    for endpoint in HEALTH_ENDPOINTS:
        url = urljoin(RENDER_URL, endpoint)
        print(f"📍 Checking: {url}")
        
        try:
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                print(f"✅ {endpoint}: OK ({response.status_code})")
            elif response.status_code in [301, 302, 403]:
                print(f"⚠️  {endpoint}: Redirect/Auth ({response.status_code})")
            else:
                print(f"❌ {endpoint}: Error ({response.status_code})")
                overall_status = False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ {endpoint}: Connection Error - {str(e)}")
            overall_status = False
        
        time.sleep(1)  # Be nice to the server
    
    print("=" * 50)
    if overall_status:
        print("🎉 Deployment Status: HEALTHY")
        print("✅ ChamaLink is ready for production!")
    else:
        print("⚠️  Deployment Status: ISSUES DETECTED")
        print("🔧 Please check the Render.com deployment logs")
    
    return overall_status

def check_sms_service():
    """Check if SMS service is properly configured"""
    print("\n📱 SMS Service Configuration Check")
    print("=" * 30)
    
    try:
        # Try to import the SMS service
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))
        
        from app.utils.sms_service import SMSService
        sms = SMSService()
        
        if sms.sms is not None:
            print("✅ SMS Service: Configured and ready")
        else:
            print("⚠️  SMS Service: Not configured (optional)")
            
    except ImportError as e:
        print(f"❌ SMS Service: Import error - {str(e)}")
    except Exception as e:
        print(f"⚠️  SMS Service: {str(e)}")

if __name__ == "__main__":
    print("🚀 Starting ChamaLink Deployment Health Check...")
    print(f"🌐 Target URL: {RENDER_URL}")
    print()
    
    # Check deployment health
    deployment_healthy = check_deployment_health()
    
    # Check SMS service (optional)
    check_sms_service()
    
    print("\n" + "=" * 50)
    print("📊 Final Status Summary:")
    print(f"🌐 Deployment: {'HEALTHY' if deployment_healthy else 'NEEDS ATTENTION'}")
    print("📱 SMS Service: Check above for details")
    print("=" * 50)
    
    # Exit with appropriate code
    sys.exit(0 if deployment_healthy else 1)
