#!/usr/bin/env python3
"""
Script to seed all tenant schemas with necessary tables and data.
This ensures all tenants have the proper RBAC structure.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.db.session import SessionLocal
from app.tenancy.service import TenantService
from app.services.security import hash_password

def seed_all_tenants():
    """Seed all existing tenants with proper schema and data."""
    db = SessionLocal()
    try:
        # Get all tenants
        tenants = db.execute(text("SELECT id, name, slug FROM tenants ORDER BY id")).mappings().all()
        
        print(f"Found {len(tenants)} tenants to seed:")
        for tenant in tenants:
            print(f"  - {tenant.name} ({tenant.slug})")
        
        # Seed each tenant
        for tenant in tenants:
            print(f"\nSeeding tenant: {tenant.name} ({tenant.slug})")
            
            try:
                # Create tenant service instance
                tenant_service = TenantService(db)
                
                # Ensure schema exists
                tenant_service.ensure_schema(tenant.slug)
                
                # Set search path to this tenant
                db.execute(text(f'SET LOCAL search_path TO "{tenant.slug}", public'))
                
                # Check if users table exists
                users_exist = db.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = :schema 
                        AND table_name = 'users'
                    )
                """), {"schema": tenant.slug}).scalar()
                
                if not users_exist:
                    print(f"  Creating schema for {tenant.slug}...")
                    # Create the schema using the tenant service
                    tenant_service.create_schema(tenant.slug)
                
                # Seed defaults (this will create all tables and data)
                print(f"  Seeding default data for {tenant.slug}...")
                tenant_service.seed_defaults()
                
                print(f"  ✓ Successfully seeded {tenant.slug}")
                
            except Exception as e:
                print(f"  ✗ Error seeding {tenant.slug}: {e}")
                continue
        
        print("\n✅ Tenant seeding completed!")
        
    except Exception as e:
        print(f"Error during tenant seeding: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_all_tenants()
