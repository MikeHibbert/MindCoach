#!/usr/bin/env python3
"""
Simple script to top up user tokens for testing
"""

import requests
import json
import sys

def topup_tokens(user_id, amount, api_base_url="http://localhost:5000/api"):
    """Top up tokens for a user"""
    
    url = f"{api_base_url}/users/{user_id}/tokens/topup"
    
    payload = {
        "amount": amount
    }
    
    try:
        print(f"Topping up {amount} tokens for user: {user_id}")
        print(f"API URL: {url}")
        
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Success!")
            print(f"Previous balance: {data['previous_balance']} tokens")
            print(f"Tokens added: {data['tokens_added']} tokens")
            print(f"New balance: {data['new_balance']} tokens")
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error message: {error_data.get('error', {}).get('message', 'Unknown error')}")
            except:
                print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to the API server.")
        print("Make sure the backend server is running on http://localhost:5000")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def get_current_balance(user_id, api_base_url="http://localhost:5000/api"):
    """Get current token balance for a user"""
    
    url = f"{api_base_url}/users/{user_id}/tokens"
    
    try:
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            return data['tokens']
        else:
            print(f"❌ Error getting balance: {response.status_code}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to the API server.")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

if __name__ == "__main__":
    # Default values
    user_id = "test_user"  # You can change this to your actual user ID
    amount = 200
    
    # Check if user provided arguments
    if len(sys.argv) > 1:
        user_id = sys.argv[1]
    if len(sys.argv) > 2:
        try:
            amount = int(sys.argv[2])
        except ValueError:
            print("❌ Error: Amount must be a number")
            sys.exit(1)
    
    print("🪙 Token Top-up Tool")
    print("=" * 30)
    
    # Get current balance
    print("Getting current balance...")
    current_balance = get_current_balance(user_id)
    if current_balance is not None:
        print(f"Current balance: {current_balance} tokens")
    
    # Top up tokens
    success = topup_tokens(user_id, amount)
    
    if success:
        print("\n🎉 Token top-up completed successfully!")
        print(f"You can now use your {amount} additional tokens in the app.")
    else:
        print("\n❌ Token top-up failed. Please check the error messages above.")
        sys.exit(1)