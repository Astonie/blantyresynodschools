#!/usr/bin/env python3

import requests
import json

def test_existing_users():
    """Check what users exist by trying to login as teacher first"""
    base_url = "http://localhost:8000/api"
    
    print("=== Testing Teacher Login (Known Working) ===")
    
    try:
        response = requests.post(f"{base_url}/auth/simple-login", json={
            "username": "mary.phiri@ndirande-high.edu",
            "password": "teacher123"
        })
        
        print(f"Teacher login: Status {response.status_code}")
        if response.status_code == 200:
            token = response.json().get('access_token')
            print(f"✅ Teacher login successful!")
            
            # Test auth/me endpoint
            headers = {
                'Authorization': f'Bearer {token}',
                'X-Tenant': 'ndirande-high'
            }
            
            me_response = requests.get(f"{base_url}/auth/me", headers=headers)
            print(f"Auth/me response: {me_response.json()}")
            
        else:
            print(f"❌ Teacher login failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_existing_users()
