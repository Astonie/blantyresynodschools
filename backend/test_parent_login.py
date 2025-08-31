#!/usr/bin/env python3

import requests
import json

# Test parent login
def test_parent_login():
    base_url = "http://localhost:8000/api"
    
    # Test login with parent credentials
    print("=== Testing Parent Login ===")
    
    # Try different parent email formats
    parent_emails = [
        "parent@ndirande-high.edu",
        "john.tembo@parent.ndirande-high.edu", 
        "mary.banda@ndirande-high.edu"
    ]
    
    for email in parent_emails:
        try:
            response = requests.post(f"{base_url}/auth/simple-login", json={
                "username": email,
                "password": "password123"  # Default password
            })
            
            print(f"Login attempt for {email}: Status {response.status_code}")
            if response.status_code == 200:
                token = response.json().get('access_token')
                print(f"✅ Login successful! Token: {token[:50]}...")
                
                # Test parent children endpoint
                headers = {
                    'Authorization': f'Bearer {token}',
                    'X-Tenant': 'ndirande-high'
                }
                
                children_response = requests.get(f"{base_url}/parents/children", headers=headers)
                print(f"Children endpoint: Status {children_response.status_code}")
                if children_response.status_code == 200:
                    print(f"Children data: {children_response.json()}")
                else:
                    print(f"Error: {children_response.text}")
                    
                return token
                
            else:
                print(f"❌ Login failed: {response.text}")
                
        except Exception as e:
            print(f"❌ Error testing {email}: {str(e)}")
    
    return None

if __name__ == "__main__":
    test_parent_login()
