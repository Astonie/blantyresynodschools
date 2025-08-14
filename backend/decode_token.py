#!/usr/bin/env python3

from jose import jwt
from app.core.config import settings

def decode_token():
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiaWF0IjoxNzU1MTg1NTc3LCJleHAiOjE3NTUxODkxNzcsInN1cGVyX2FkbWluIjp0cnVlLCJ0ZW5hbnQiOiJzdGFuZHJld3MifQ.7fDaz87xhYSL3-SMzjJ5Xj5WBgg-9G1TsszykgdsqR0"
    
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        print("Token payload:")
        for key, value in payload.items():
            print(f"  {key}: {value}")
        
        user_id = int(payload.get("sub"))
        print(f"\nExtracted user_id: {user_id}")
        
    except Exception as e:
        print(f"Error decoding token: {e}")

if __name__ == "__main__":
    decode_token()
