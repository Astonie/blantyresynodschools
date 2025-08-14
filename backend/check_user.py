#!/usr/bin/env python3

from app.db.session import SessionLocal
from sqlalchemy import text

def check_admin_user():
    db = SessionLocal()
    try:
        # Check in standrews tenant
        db.execute(text('SET search_path TO standrews, public'))
        result = db.execute(text("SELECT id, email, full_name FROM users WHERE email = 'admin@blantyresynod.org'")).first()
        if result:
            print(f"User ID: {result[0]}, Email: {result[1]}, Name: {result[2]}")
            
            # Check if user has Super Administrator role
            role_result = db.execute(text("""
                SELECT r.name FROM roles r
                JOIN user_roles ur ON ur.role_id = r.id
                WHERE ur.user_id = :user_id AND r.name = 'Super Administrator'
            """), {"user_id": result[0]}).first()
            
            if role_result:
                print(f"User has role: {role_result[0]}")
            else:
                print("User does not have Super Administrator role")
        else:
            print("User not found")
    finally:
        db.close()

if __name__ == "__main__":
    check_admin_user()
