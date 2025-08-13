#!/usr/bin/env python3
"""
Test script for authentication endpoints
"""
import os
import sys
import requests
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
import threading
import time

def test_auth_endpoints():
    """Test the authentication endpoints"""
    app = create_app('development')
    
    # Start the Flask app in a separate thread
    def run_app():
        app.run(host='127.0.0.1', port=5001, debug=False, use_reloader=False)
    
    server_thread = threading.Thread(target=run_app, daemon=True)
    server_thread.start()
    
    # Wait for server to start
    time.sleep(2)
    
    base_url = 'http://127.0.0.1:5001/api'
    
    try:
        print("Testing authentication endpoints...")
        
        # Test 1: Register a new user
        print("\n1. Testing user registration...")
        register_data = {
            'user_id': 'test_auth_user',
            'email': 'testauth@example.com',
            'password': 'TestPassword123!'
        }
        
        response = requests.post(f'{base_url}/auth/register', json=register_data)
        print(f"Registration status: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            access_token = data['access_token']
            print(f"✓ User registered successfully")
            print(f"✓ Access token received: {access_token[:20]}...")
        else:
            print(f"❌ Registration failed: {response.text}")
            return
        
        # Test 2: Test authenticated endpoint
        print("\n2. Testing authenticated endpoint...")
        headers = {'Authorization': f'Bearer {access_token}'}
        
        response = requests.get(f'{base_url}/auth/me', headers=headers)
        print(f"Auth me status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Authenticated user: {data['user']['user_id']}")
        else:
            print(f"❌ Auth me failed: {response.text}")
            return
        
        # Test 3: Test subjects endpoint with authentication
        print("\n3. Testing subjects endpoint with authentication...")
        response = requests.get(f'{base_url}/subjects', headers=headers)
        print(f"Subjects status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Subjects retrieved: {len(data['subjects'])} subjects")
        else:
            print(f"❌ Subjects failed: {response.text}")
            return
        
        # Test 4: Test logout
        print("\n4. Testing logout...")
        response = requests.post(f'{base_url}/auth/logout', headers=headers)
        print(f"Logout status: {response.status_code}")
        
        if response.status_code == 200:
            print("✓ Logout successful")
        else:
            print(f"❌ Logout failed: {response.text}")
        
        # Test 5: Test using token after logout (should fail)
        print("\n5. Testing token after logout...")
        response = requests.get(f'{base_url}/auth/me', headers=headers)
        print(f"Auth me after logout status: {response.status_code}")
        
        if response.status_code == 401:
            print("✓ Token correctly invalidated after logout")
        else:
            print(f"❌ Token should be invalid: {response.text}")
        
        print("\n✅ All authentication endpoint tests passed!")
        
    except Exception as e:
        print(f"\n❌ Authentication endpoint test failed: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    test_auth_endpoints()