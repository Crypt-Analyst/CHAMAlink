#!/usr/bin/env python3
"""
Test script for founder dashboard functionality
Tests all the newly implemented buttons and routes
"""

import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_founder_endpoints():
    """Test all founder dashboard endpoints"""
    
    # You'll need to be logged in as a super admin for these to work
    session = requests.Session()
    
    print("🧪 Testing Founder Dashboard Endpoints")
    print("=" * 50)
    
    # Test endpoints
    endpoints = [
        {
            "name": "New Feature",
            "url": f"{BASE_URL}/founder-dashboard/new-feature",
            "data": {
                "name": "Test Feature",
                "description": "This is a test feature",
                "priority": "medium"
            }
        },
        {
            "name": "Platform Notice",
            "url": f"{BASE_URL}/founder-dashboard/platform-notice",
            "data": {
                "title": "Test Notice",
                "message": "This is a test platform notice",
                "priority": "info",
                "send_email": False
            }
        },
        {
            "name": "Generate Report",
            "url": f"{BASE_URL}/founder-dashboard/generate-report",
            "data": {
                "report_type": "User Activity Report",
                "date_range": "30",
                "export_format": "pdf"
            }
        },
        {
            "name": "Create Promotion",
            "url": f"{BASE_URL}/founder-dashboard/create-promotion",
            "data": {
                "name": "Test Promotion",
                "discount_type": "percentage",
                "discount_value": "20",
                "start_date": "2025-07-10",
                "end_date": "2025-07-20"
            }
        },
        {
            "name": "Maintenance Mode",
            "url": f"{BASE_URL}/founder-dashboard/maintenance-mode",
            "data": {
                "enable": True,
                "message": "Test maintenance mode"
            }
        },
        {
            "name": "Emergency Broadcast",
            "url": f"{BASE_URL}/founder-dashboard/emergency-broadcast",
            "data": {
                "message": "Test emergency broadcast",
                "send_sms": False,
                "send_email": True
            }
        }
    ]
    
    for endpoint in endpoints:
        print(f"\n🔍 Testing: {endpoint['name']}")
        print(f"URL: {endpoint['url']}")
        
        try:
            response = session.post(
                endpoint['url'],
                json=endpoint['data'],
                headers={'Content-Type': 'application/json'}
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Success: {result.get('message', 'No message')}")
            elif response.status_code == 403:
                print("⚠️  Access denied (need to be logged in as super admin)")
            else:
                print(f"❌ Error: {response.status_code}")
                try:
                    error = response.json()
                    print(f"Error message: {error.get('message', 'Unknown error')}")
                except:
                    print(f"Response: {response.text}")
                    
        except requests.exceptions.ConnectionError:
            print("❌ Connection error - Flask app not running?")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 Test completed!")
    print("\nNote: Some endpoints may return 403 (Access denied)")
    print("This is expected if you're not logged in as super admin")

if __name__ == "__main__":
    test_founder_endpoints()
