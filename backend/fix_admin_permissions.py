#!/usr/bin/env python3
"""
Fix Administrator role permissions to include attendance
"""
import sys
sys.path.append('/app')

from app.db.session import SessionLocal
from sqlalchemy import text

def fix_administrator_permissions():
    print('🔧 FIXING ADMINISTRATOR ROLE PERMISSIONS')
    print('=' * 50)
    
    db = SessionLocal()
    try:
        # Use ndirande_high as test schema
        db.execute(text('SET search_path TO "ndirande_high"'))
        
        print('\n1️⃣ Checking Administrator role permissions...')
        admin_role_id = db.execute(text("SELECT id FROM roles WHERE name = 'Administrator'")).scalar()
        print(f'   📋 Administrator role ID: {admin_role_id}')
        
        # Get current permissions
        current_perms = db.execute(text("""
            SELECT p.name FROM permissions p
            JOIN role_permissions rp ON p.id = rp.permission_id
            WHERE rp.role_id = :rid
            ORDER BY p.name
        """), {'rid': admin_role_id}).scalars().all()
        
        print(f'   📊 Current permissions ({len(current_perms)}):')
        for perm in current_perms:
            print(f'      {perm}')
        
        # Get all available permissions
        all_perms = db.execute(text('SELECT id, name FROM permissions ORDER BY name')).fetchall()
        print(f'\n2️⃣ All available permissions ({len(all_perms)}):')
        
        missing_perms = []
        for perm_id, perm_name in all_perms:
            if perm_name not in current_perms:
                missing_perms.append((perm_id, perm_name))
                
        print(f'\n3️⃣ Missing permissions ({len(missing_perms)}):')
        for perm_id, perm_name in missing_perms:
            print(f'      {perm_name}')
            
        if missing_perms:
            print('\n🔧 Adding missing permissions to Administrator role...')
            for perm_id, perm_name in missing_perms:
                db.execute(text("""
                    INSERT INTO role_permissions (role_id, permission_id)
                    VALUES (:rid, :pid)
                    ON CONFLICT (role_id, permission_id) DO NOTHING
                """), {'rid': admin_role_id, 'pid': perm_id})
                print(f'      ✅ Added: {perm_name}')
                
            db.commit()
            print('\n💾 Changes committed')
            
            # Verify the fix
            print('\n4️⃣ Verifying fix...')
            admin_email = 'admin@ndirande-high.edu'
            admin_id = db.execute(text('SELECT id FROM users WHERE email = :email'), {'email': admin_email}).scalar()
            
            final_perms = db.execute(text("""
                SELECT p.name FROM permissions p
                JOIN role_permissions rp ON p.id = rp.permission_id
                JOIN user_roles ur ON rp.role_id = ur.role_id
                WHERE ur.user_id = :uid
                ORDER BY p.name
            """), {'uid': admin_id}).scalars().all()
            
            attendance_perms = [p for p in final_perms if 'attendance' in p.lower()]
            print(f'   📊 Final permissions: {len(final_perms)}')
            print(f'   ✅ Attendance permissions: {attendance_perms}')
            
        else:
            print('   ✅ Administrator role already has all permissions!')
            
    finally:
        db.close()

if __name__ == "__main__":
    fix_administrator_permissions()
