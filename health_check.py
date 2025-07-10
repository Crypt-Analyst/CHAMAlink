#!/usr/bin/env python3
"""
Quick ChamaLink System Status Check
Verifies core functionality is working
"""

import requests
import json

def quick_health_check():
    """Quick system health check"""
    base_url = "http://localhost:5000"
    
    print("🔍 ChamaLink Quick Health Check")
    print("=" * 40)
    
    # Test core pages
    tests = [
        ("Homepage", "/"),
        ("Login", "/auth/login"),
        ("Features", "/features"),
        ("Chat", "/chat"),
        ("API Status", "/api/agent-help")
    ]
    
    results = {}
    
    for name, path in tests:
        try:
            response = requests.get(f"{base_url}{path}", timeout=5)
            status = "✅ OK" if response.status_code == 200 else f"❌ {response.status_code}"
            results[name] = response.status_code == 200
            print(f"  {name}: {status}")
        except Exception as e:
            results[name] = False
            print(f"  {name}: ❌ ERROR")
    
    # Test chat API
    try:
        response = requests.post(f"{base_url}/api/agent-help", 
                               json={"message": "health check"}, 
                               timeout=5)
        chat_status = "✅ OK" if response.status_code == 200 else f"❌ {response.status_code}"
        results["Chat API"] = response.status_code == 200
        print(f"  Chat API: {chat_status}")
    except Exception as e:
        results["Chat API"] = False
        print(f"  Chat API: ❌ ERROR")
    
    # Calculate score
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    score = (passed / total) * 100
    
    print(f"\n🎯 Health Score: {score:.1f}% ({passed}/{total})")
    
    if score >= 85:
        print("🚀 System Status: EXCELLENT - Ready for production!")
    elif score >= 70:
        print("👍 System Status: GOOD - Minor issues may exist")
    else:
        print("⚠️  System Status: NEEDS ATTENTION")
    
    return results

if __name__ == "__main__":
    quick_health_check()
