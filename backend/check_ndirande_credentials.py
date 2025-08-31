#!/usr/bin/env python3
"""
Check credentials for Ndirande High School
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.db.session import SessionLocal

def check_ndirande_credentials():
    """Check the login credentials for Ndirande High School."""
    db = SessionLocal()
    try:
        print("🔍 Checking Ndirande High School Login Credentials")
        print("=" * 50)
        
        # Get all users from Ndirande High School
        users = db.execute(
            text('''
                SELECT 
                    u.email, 
                    u.full_name, 
                    u.is_active,
                    r.name as role_name
                FROM "ndirande-high".users u
                JOIN "ndirande-high".user_roles ur ON u.id = ur.user_id
                JOIN "ndirande-high".roles r ON ur.role_id = r.id
                ORDER BY u.email
            ''')
        ).mappings().all()
        
        print(f"\n👥 Available Users for Ndirande High School:")
        print("-" * 50)
        
        for user in users:
            status = "✅ Active" if user.is_active else "❌ Inactive"
            print(f"📧 Email: {user.email}")
            print(f"👤 Name: {user.full_name}")
            print(f"🎭 Role: {user.role_name}")
            print(f"📊 Status: {status}")
            print("-" * 30)
        
        print(f"\n🏫 Tenant Slug: ndirande-high")
        print(f"🔑 Default Passwords (as seeded):")
        print(f"   • Principal: principal123")
        print(f"   • Teacher: teacher123") 
        print(f"   • Finance: finance123")
        print(f"   • Student: student123")
        print(f"   • Parent: parent123")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_ndirande_credentials()
