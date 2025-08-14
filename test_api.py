#!/usr/bin/env python3
"""
Quick test to verify the API endpoints work
"""

import requests
import json

def test_api():
    base_url = "http://localhost:5000/api"
    user_id = "test_user"
    
    print("🧪 Testing API endpoints...")
    print("=" * 40)
    
    # Test health check
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ Health check: OK")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return
    
    # Test get tokens
    try:
        response = requests.get(f"{base_url}/users/{user_id}/tokens")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Get tokens: {data['tokens']} tokens")
        else:
            print(f"❌ Get tokens failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Get tokens error: {e}")
    
    # Test token topup
    try:
        payload = {"amount": 200}
        response = requests.post(f"{base_url}/users/{user_id}/tokens/topup", json=payload)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Token topup: Added {data['tokens_added']} tokens")
            print(f"   New balance: {data['new_balance']} tokens")
        else:
            print(f"❌ Token topup failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Token topup error: {e}")
    
    # Test get tokens again to verify
    try:
        response = requests.get(f"{base_url}/users/{user_id}/tokens")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Final balance: {data['tokens']} tokens")
        else:
            print(f"❌ Final balance check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Final balance error: {e}")

if __name__ == "__main__":
    test_api()