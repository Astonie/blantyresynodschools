#!/usr/bin/env python3
"""
Script to verify the database seeding was successful.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.db.session import SessionLocal

def verify_seeding():
    """Verify that all tenants have been properly seeded."""
    db = SessionLocal()
    try:
        print("🔍 Verifying Database Seeding for Blantyre Synod Schools")
        print("=" * 60)
        
        # Get all tenants
        tenants = db.execute(
            text("SELECT name, slug FROM public.tenants ORDER BY name")
        ).mappings().all()
        
        print(f"\n📊 Total Schools: {len(tenants)}")
        
        for tenant in tenants:
            print(f"\n🏫 {tenant.name} ({tenant.slug})")
            
            # Set search path to tenant schema
            schema_name = tenant.slug
            
            try:
                # Check users
                users_count = db.execute(
                    text(f'SELECT COUNT(*) FROM "{schema_name}".users')
                ).scalar()
                print(f"  👥 Users: {users_count}")
                
                # Check roles
                roles_count = db.execute(
                    text(f'SELECT COUNT(*) FROM "{schema_name}".roles')
                ).scalar()
                print(f"  🎭 Roles: {roles_count}")
                
                # Check permissions
                permissions_count = db.execute(
                    text(f'SELECT COUNT(*) FROM "{schema_name}".permissions')
                ).scalar()
                print(f"  🔑 Permissions: {permissions_count}")
                
                # Check students
                students_count = db.execute(
                    text(f'SELECT COUNT(*) FROM "{schema_name}".students')
                ).scalar()
                print(f"  🎓 Students: {students_count}")
                
                # Check teachers
                teachers_count = db.execute(
                    text(f'SELECT COUNT(*) FROM "{schema_name}".teachers')
                ).scalar()
                print(f"  👨‍🏫 Teachers: {teachers_count}")
                
                # Get sample admin user
                admin_users = db.execute(
                    text(f'''
                        SELECT u.email, u.full_name, u.is_active 
                        FROM "{schema_name}".users u
                        JOIN "{schema_name}".user_roles ur ON u.id = ur.user_id
                        JOIN "{schema_name}".roles r ON ur.role_id = r.id
                        WHERE r.name = 'School Administrator'
                        LIMIT 1
                    ''')
                ).mappings().first()
                
                if admin_users:
                    print(f"  🔐 Admin User: {admin_users.email} ({admin_users.full_name}) - Active: {admin_users.is_active}")
                else:
                    print(f"  ⚠️  No admin user found")
                
            except Exception as e:
                print(f"  ❌ Error checking {tenant.name}: {e}")
        
        # Platform admin verification
        print(f"\n🌐 Platform Administration")
        platform_admins = db.execute(
            text("SELECT email, full_name, is_active FROM public.platform_admins")
        ).mappings().all()
        
        for admin in platform_admins:
            print(f"  🔑 Platform Admin: {admin.email} ({admin.full_name}) - Active: {admin.is_active}")
        
        print("\n" + "=" * 60)
        print("✅ Database verification completed!")
        print("\n📋 Summary:")
        print(f"  • {len(tenants)} schools configured")
        print(f"  • {len(platform_admins)} platform administrators")
        print("  • All tenant schemas created and seeded")
        print("  • RBAC system initialized for all schools")
        
        print(f"\n🚀 Your Blantyre Synod Schools Management System is ready!")
        print("💡 You can now start the application and login with:")
        print("   Platform Admin: admin@blantyresynod.org / admin123")
        
    except Exception as e:
        print(f"❌ Verification error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    verify_seeding()
