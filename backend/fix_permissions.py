#!/usr/bin/env python3
"""
Check and fix user role and permission assignments
"""
import sys
sys.path.append('/app')

from app.db.session import SessionLocal
from sqlalchemy import text

def diagnose_and_fix_permissions():
    print('🔍 DIAGNOSING USER PERMISSIONS SYSTEM')
    print('=' * 50)
    
    db = SessionLocal()
    try:
        # Use ndirande_high as test schema
        db.execute(text('SET search_path TO "ndirande_high"'))
        
        print('\n1️⃣ Checking users...')
        users = db.execute(text('SELECT id, email, full_name FROM users')).fetchall()
        print(f'   📊 Found {len(users)} users:')
        for user_id, email, full_name in users:
            print(f'      ID {user_id}: {email} ({full_name})')
        
        print('\n2️⃣ Checking roles...')
        roles = db.execute(text('SELECT id, name, description FROM roles')).fetchall()
        print(f'   📊 Found {len(roles)} roles:')
        for role_id, name, desc in roles:
            print(f'      ID {role_id}: {name} - {desc or "No description"}')
        
        print('\n3️⃣ Checking user-role assignments...')
        user_roles = db.execute(text("""
            SELECT u.email, r.name as role_name
            FROM user_roles ur
            JOIN users u ON ur.user_id = u.id
            JOIN roles r ON ur.role_id = r.id
            ORDER BY u.email
        """)).fetchall()
        print(f'   📊 Found {len(user_roles)} user-role assignments:')
        for email, role_name in user_roles:
            print(f'      {email} → {role_name}')
            
        print('\n4️⃣ Checking role-permission assignments...')
        role_perms = db.execute(text("""
            SELECT r.name as role_name, COUNT(rp.permission_id) as perm_count
            FROM roles r
            LEFT JOIN role_permissions rp ON r.id = rp.role_id
            GROUP BY r.id, r.name
            ORDER BY r.name
        """)).fetchall()
        print(f'   📊 Role-permission counts:')
        for role_name, perm_count in role_perms:
            print(f'      {role_name}: {perm_count} permissions')
        
        print('\n5️⃣ Checking specific admin permissions...')
        admin_user = db.execute(text("SELECT id FROM users WHERE email = 'admin@ndirande-high.edu'")).scalar()
        if admin_user:
            # Check if admin has roles assigned
            admin_roles = db.execute(text("""
                SELECT r.name FROM roles r
                JOIN user_roles ur ON r.id = ur.role_id
                WHERE ur.user_id = :uid
            """), {"uid": admin_user}).scalars().all()
            
            print(f'   📋 Admin roles: {admin_roles}')
            
            if not admin_roles:
                print('   🚨 PROBLEM: Admin has no roles assigned!')
                print('   🔧 Attempting to fix by assigning Administrator role...')
                
                # Find Administrator role
                admin_role_id = db.execute(text("SELECT id FROM roles WHERE name = 'Administrator'")).scalar()
                if admin_role_id:
                    # Assign admin role to admin user
                    db.execute(text("""
                        INSERT INTO user_roles (user_id, role_id) 
                        VALUES (:uid, :rid)
                        ON CONFLICT (user_id, role_id) DO NOTHING
                    """), {"uid": admin_user, "rid": admin_role_id})
                    
                    print('   ✅ Administrator role assigned to admin user')
                    
                    # Check if Administrator role has permissions
                    admin_role_perms = db.execute(text("""
                        SELECT COUNT(*) FROM role_permissions WHERE role_id = :rid
                    """), {"rid": admin_role_id}).scalar()
                    
                    print(f'   📊 Administrator role has {admin_role_perms} permissions')
                    
                    if admin_role_perms == 0:
                        print('   🚨 PROBLEM: Administrator role has no permissions!')
                        print('   🔧 Need to assign permissions to Administrator role...')
                        
                        # Get all permissions
                        all_perms = db.execute(text('SELECT id FROM permissions')).scalars().all()
                        
                        # Assign all permissions to Administrator role
                        for perm_id in all_perms:
                            db.execute(text("""
                                INSERT INTO role_permissions (role_id, permission_id)
                                VALUES (:rid, :pid)
                                ON CONFLICT (role_id, permission_id) DO NOTHING
                            """), {"rid": admin_role_id, "pid": perm_id})
                        
                        print(f'   ✅ Assigned {len(all_perms)} permissions to Administrator role')
                        
                    db.commit()
                    print('   💾 Changes committed')
                else:
                    print('   ❌ Administrator role not found!')
        else:
            print('   ❌ Admin user not found!')
            
    finally:
        db.close()

if __name__ == "__main__":
    diagnose_and_fix_permissions()
