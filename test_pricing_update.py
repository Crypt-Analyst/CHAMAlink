#!/usr/bin/env python3
"""Test Enterprise plan display on pricing page"""

import requests
import sys
from app import create_app
import threading
import time

def test_pricing_page():
    """Test pricing page with updated Enterprise plan"""
    app = create_app()
    
    def run_app():
        app.run(debug=True, use_reloader=False, port=5002)
    
    # Start the app in a separate thread
    server_thread = threading.Thread(target=run_app)
    server_thread.daemon = True
    server_thread.start()
    
    # Wait for server to start
    time.sleep(2)
    
    try:
        # Test the pricing page (using the correct route)
        response = requests.get('http://localhost:5002/plans/pricing')
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Pricing page loaded successfully!")
            content = response.text
            
            # Check for Enterprise plan content
            checks = [
                ("Enterprise Plan", "Enterprise Plan title"),
                ("SACCOs, NGOs, Government", "Broader organizational scope"),
                ("KES 30", "Per member pricing"),
                ("KES 1000", "Service fee"),
                ("KES 500", "Training fee"),
                ("Custom Pricing", "Custom pricing display"),
                ("Large organizations", "Large organization messaging")
            ]
            
            print("\n🔍 Content Verification:")
            for search_text, description in checks:
                if search_text in content:
                    print(f"✅ {description}: Found")
                else:
                    print(f"❌ {description}: Missing")
                    
        else:
            print(f"❌ Error loading page: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing page: {e}")

if __name__ == '__main__':
    test_pricing_page()
