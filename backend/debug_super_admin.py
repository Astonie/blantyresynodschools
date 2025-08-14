#!/usr/bin/env python3

from app.db.session import SessionLocal
from sqlalchemy import text

def debug_super_admin_check():
    user_id = 1  # From the token
    
    db = SessionLocal()
    try:
        # Check in any tenant that has this user as Super Administrator
        tenants = db.execute(text("SELECT slug FROM tenants ORDER BY id")).scalars().all()
        print(f"Found {len(tenants)} tenants: {list(tenants)}")
        
        for tenant_slug in tenants:
            try:
                print(f"\nChecking tenant: {tenant_slug}")
                db.execute(text(f'SET LOCAL search_path TO "{tenant_slug}", public'))
                
                # Check if users table exists
                users_exist = db.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = :schema 
                        AND table_name = 'users'
                    )
                """), {"schema": tenant_slug}).scalar()
                
                if not users_exist:
                    print(f"  Users table does not exist in {tenant_slug}")
                    continue
                
                # Check if user exists
                user_exists = db.execute(text("SELECT id FROM users WHERE id = :user_id"), {"user_id": user_id}).scalar()
                if not user_exists:
                    print(f"  User {user_id} does not exist in {tenant_slug}")
                    continue
                
                print(f"  User {user_id} exists in {tenant_slug}")
                
                # Check if user has Super Administrator role
                super_admin_check = db.execute(
                    text("""
                        SELECT COUNT(*) FROM user_roles ur
                        JOIN roles r ON ur.role_id = r.id
                        WHERE ur.user_id = :user_id AND r.name = 'Super Administrator'
                    """),
                    {"user_id": user_id}
                ).scalar()
                
                print(f"  Super Admin check result: {super_admin_check}")
                
                if super_admin_check > 0:
                    print(f"  ✓ User {user_id} is Super Administrator in {tenant_slug}")
                    return True
                else:
                    print(f"  ✗ User {user_id} is NOT Super Administrator in {tenant_slug}")
                    
            except Exception as e:
                print(f"  Error checking {tenant_slug}: {e}")
                continue
        
        print("\n❌ User is not Super Administrator in any tenant")
        return False
        
    finally:
        db.close()

if __name__ == "__main__":
    debug_super_admin_check()
