#!/usr/bin/env python3
"""Test script to specifically test enterprise plans template rendering"""

import requests
import sys
from app import create_app
import threading
import time

def test_enterprise_plans_page():
    """Test if the enterprise plans page renders without errors"""
    app = create_app()
    
    def run_app():
        app.run(debug=True, use_reloader=False, port=5001)
    
    # Start the app in a separate thread
    server_thread = threading.Thread(target=run_app)
    server_thread.daemon = True
    server_thread.start()
    
    # Wait for server to start
    time.sleep(2)
    
    try:
        # Test the enterprise plans page
        response = requests.get('http://localhost:5001/enterprise/plans')
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Enterprise plans page loaded successfully!")
            print(f"Content length: {len(response.content)} bytes")
            
            # Check if the page contains expected content
            content = response.text
            if "Enterprise Plans" in content or "SACCO/NGO" in content:
                print("✅ Page contains expected content")
            else:
                print("⚠️ Page might be missing expected content")
                
        else:
            print(f"❌ Error loading page: {response.status_code}")
            print(response.text[:500])  # First 500 chars of error
            
    except Exception as e:
        print(f"❌ Error testing page: {e}")

if __name__ == '__main__':
    test_enterprise_plans_page()
