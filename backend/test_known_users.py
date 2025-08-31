#!/usr/bin/env python3

import requests
import json

def test_known_credentials():
    """Test the credentials we know worked before"""
    base_url = "http://localhost:8000/api"
    
    # Test credentials that worked earlier in our session
    test_users = [
        ("mary.phiri@ndirande-high.edu", "teacher123"),
        ("admin@ndirande-high.edu", "admin123"),
        ("user@ndirande-high.edu", "password123")
    ]
    
    for email, password in test_users:
        print(f"\n=== Testing {email} ===")
        
        try:
            response = requests.post(f"{base_url}/auth/simple-login", json={
                "username": email,
                "password": password
            })
            
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                token = response.json().get('access_token')
                print(f"✅ Login successful!")
                
                # Test auth/me
                headers = {
                    'Authorization': f'Bearer {token}',
                    'X-Tenant': 'ndirande-high'
                }
                
                me_response = requests.get(f"{base_url}/auth/me", headers=headers)
                if me_response.status_code == 200:
                    user_info = me_response.json()
                    print(f"User info: {json.dumps(user_info, indent=2)}")
                else:
                    print(f"Auth/me failed: {me_response.text}")
                    
            else:
                print(f"❌ Failed: {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_known_credentials()
