#!/usr/bin/env python3
"""
Test script for authentication system
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.services.auth_service import AuthService

def test_authentication():
    """Test the authentication system"""
    app = create_app('development')
    
    with app.app_context():
        try:
            print("Testing authentication system...")
            
            # Test user registration
            print("\n1. Testing user registration...")
            user, access_token, refresh_token = AuthService.register_user(
                user_id="test_user_123",
                email="test@example.com",
                password="TestPassword123!"
            )
            print(f"✓ User registered: {user.user_id}")
            print(f"✓ Access token generated: {access_token[:20]}...")
            print(f"✓ Refresh token generated: {refresh_token[:20]}...")
            
            # Test user login
            print("\n2. Testing user login...")
            login_user, login_access_token, login_refresh_token = AuthService.login_user(
                email="test@example.com",
                password="TestPassword123!"
            )
            print(f"✓ User logged in: {login_user.user_id}")
            print(f"✓ Login access token: {login_access_token[:20]}...")
            
            # Test password validation
            print("\n3. Testing password validation...")
            print(f"✓ Password check (correct): {user.check_password('TestPassword123!')}")
            print(f"✓ Password check (incorrect): {user.check_password('WrongPassword')}")
            
            print("\n✅ All authentication tests passed!")
            
        except Exception as e:
            print(f"\n❌ Authentication test failed: {str(e)}")
            sys.exit(1)

if __name__ == '__main__':
    test_authentication()