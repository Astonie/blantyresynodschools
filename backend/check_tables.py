#!/usr/bin/env python3

from app.db.session import SessionLocal
from sqlalchemy import text

def check_tables():
    db = SessionLocal()
    try:
        # Check what tables exist in public schema
        tables = db.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)).scalars().all()
        
        print("Tables in public schema:")
        for table in tables:
            print(f"  - {table}")
            
        # Check if tenants table exists
        tenants_exist = db.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'tenants'
            )
        """)).scalar()
        
        print(f"\nTenants table exists: {tenants_exist}")
        
        if tenants_exist:
            # Get tenant data
            tenants = db.execute(text("SELECT id, name, slug FROM tenants ORDER BY id")).mappings().all()
            print(f"\nFound {len(tenants)} tenants:")
            for tenant in tenants:
                print(f"  - {tenant.name} ({tenant.slug})")
        
    finally:
        db.close()

if __name__ == "__main__":
    check_tables()
