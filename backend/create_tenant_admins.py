#!/usr/bin/env python3
"""
Check if tenant-specific admin users exist and create them if needed
"""
import sys
sys.path.append('/app')

from app.db.session import SessionLocal
from sqlalchemy import text
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def check_tenant_admin_users():
    print('🔍 CHECKING TENANT-SPECIFIC ADMIN USERS')
    print('=' * 50)
    
    db = SessionLocal()
    try:
        # Get all tenant slugs
        tenants = db.execute(text('SELECT slug FROM public.tenants')).scalars().all()
        print(f'   📊 Found {len(tenants)} tenants: {tenants}')
        
        for tenant_slug in tenants:
            schema_name = tenant_slug.replace('-', '_')
            print(f'\n🏫 Checking {tenant_slug} ({schema_name}):')
            
            db.execute(text(f'SET search_path TO "{schema_name}"'))
            
            # Check if admin user exists for this tenant
            admin_email = f'admin@{tenant_slug}.edu'
            admin_user = db.execute(text('SELECT id, email, full_name FROM users WHERE email = :email'), {'email': admin_email}).first()
            
            if admin_user:
                print(f'   ✅ Admin user exists: {admin_user.email}')
                
                # Check roles
                roles = db.execute(text("""
                    SELECT r.name FROM roles r
                    JOIN user_roles ur ON r.id = ur.role_id
                    WHERE ur.user_id = :uid
                """), {'uid': admin_user.id}).scalars().all()
                print(f'   📋 Roles: {roles}')
                
            else:
                print(f'   ❌ Admin user missing: {admin_email}')
                print(f'   🔧 Creating admin user...')
                
                # Create admin user
                hashed_password = pwd_context.hash('admin123')
                
                db.execute(text("""
                    INSERT INTO users (email, full_name, hashed_password, is_active)
                    VALUES (:email, :name, :pwd, :active)
                """), {
                    'email': admin_email,
                    'name': f'{tenant_slug.replace("-", " ").title()} Administrator',
                    'pwd': hashed_password,
                    'active': True
                })
                
                # Get the created user ID
                admin_user_id = db.execute(text('SELECT id FROM users WHERE email = :email'), {'email': admin_email}).scalar()
                
                # Assign Administrator role (ID 3 based on earlier output)
                db.execute(text("""
                    INSERT INTO user_roles (user_id, role_id)
                    VALUES (:uid, :rid)
                """), {'uid': admin_user_id, 'rid': 3})
                
                print(f'   ✅ Created admin user with Administrator role')
        
        db.commit()
        print('\n💾 All changes committed')
        
        # Test login with one of the admins
        print('\n🧪 Testing login with ndirande-high admin...')
        ndirande_admin = 'admin@ndirande-high.edu'
        
        # Set to ndirande_high schema
        db.execute(text('SET search_path TO "ndirande_high"'))
        
        admin_check = db.execute(text('SELECT id, email FROM users WHERE email = :email'), {'email': ndirande_admin}).first()
        if admin_check:
            print(f'   ✅ Admin user ready for login: {admin_check.email}')
            
            # Check permissions
            perms = db.execute(text("""
                SELECT p.name FROM permissions p
                JOIN role_permissions rp ON p.id = rp.permission_id
                JOIN user_roles ur ON rp.role_id = ur.role_id
                WHERE ur.user_id = :uid
                ORDER BY p.name
            """), {'uid': admin_check.id}).scalars().all()
            
            attendance_perms = [p for p in perms if 'attendance' in p.lower()]
            print(f'   📋 Total permissions: {len(perms)}')
            print(f'   📋 Attendance permissions: {attendance_perms}')
        else:
            print(f'   ❌ Still no admin user found')
            
    finally:
        db.close()

if __name__ == "__main__":
    check_tenant_admin_users()
