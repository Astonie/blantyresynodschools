#!/usr/bin/env python3
"""
Script to create sample Blantyre Synod schools as tenants and seed their databases.
"""

import sys
import os
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.db.session import SessionLocal
from app.tenancy.service import TenantService

# Sample schools for Blantyre Synod
SAMPLE_SCHOOLS = [
    {
        "name": "Blantyre Secondary School",
        "slug": "blantyre-secondary",
        "description": "Main secondary school in Blantyre serving the central urban area",
        "contact_email": "admin@blantyresecondary.mw",
        "contact_phone": "+265-1-871234",
        "address": "Blantyre City, Malawi",
        "enabled_modules": ["academic", "students", "teachers", "finance", "library", "communications"]
    },
    {
        "name": "Limbe Primary School",
        "slug": "limbe-primary",
        "description": "Primary school in Limbe serving grades 1-8",
        "contact_email": "admin@limbeprimary.mw",
        "contact_phone": "+265-1-872345",
        "address": "Limbe, Blantyre, Malawi",
        "enabled_modules": ["academic", "students", "teachers", "finance", "communications"]
    },
    {
        "name": "Chilomoni Community School",
        "slug": "chilomoni-community",
        "description": "Community school serving Chilomoni township",
        "contact_email": "admin@chilomoni.mw",
        "contact_phone": "+265-1-873456",
        "address": "Chilomoni, Blantyre, Malawi",
        "enabled_modules": ["academic", "students", "teachers", "communications"]
    },
    {
        "name": "Ndirande High School",
        "slug": "ndirande-high",
        "description": "Secondary school serving Ndirande area",
        "contact_email": "admin@ndirandehigh.mw",
        "contact_phone": "+265-1-874567",
        "address": "Ndirande, Blantyre, Malawi",
        "enabled_modules": ["academic", "students", "teachers", "finance", "library"]
    },
    {
        "name": "Machinjiri CCAP School",
        "slug": "machinjiri-ccap",
        "description": "CCAP school in Machinjiri serving primary and secondary students",
        "contact_email": "admin@machinjiriccap.mw",
        "contact_phone": "+265-1-875678",
        "address": "Machinjiri, Blantyre, Malawi",
        "enabled_modules": ["academic", "students", "teachers", "finance", "communications"]
    }
]

def create_sample_schools():
    """Create sample schools as tenants and seed their databases."""
    db = SessionLocal()
    try:
        tenant_service = TenantService(db)
        
        print("🏫 Creating Sample Blantyre Synod Schools...")
        print("=" * 50)
        
        for school_data in SAMPLE_SCHOOLS:
            school_name = school_data["name"]
            school_slug = school_data["slug"]
            
            print(f"\n📚 Creating: {school_name}")
            
            try:
                # Check if tenant already exists
                existing = db.execute(
                    text("SELECT id FROM public.tenants WHERE slug = :slug"),
                    {"slug": school_slug}
                ).scalar()
                
                if existing:
                    print(f"  ⚠️  School already exists: {school_name}")
                    continue
                
                # Insert new tenant
                result = db.execute(
                    text("""
                        INSERT INTO public.tenants 
                        (name, slug, schema_name, description, contact_email, contact_phone, address, enabled_modules, is_active, created_at, updated_at)
                        VALUES (:name, :slug, :schema_name, :description, :contact_email, :contact_phone, :address, :enabled_modules, true, NOW(), NOW())
                        RETURNING id
                    """),
                    {
                        "name": school_data["name"],
                        "slug": school_data["slug"],
                        "schema_name": school_data["slug"].replace("-", "_"),
                        "description": school_data["description"],
                        "contact_email": school_data["contact_email"],
                        "contact_phone": school_data["contact_phone"],
                        "address": school_data["address"],
                        "enabled_modules": json.dumps(school_data["enabled_modules"])
                    }
                )
                tenant_id = result.scalar()
                db.commit()
                
                print(f"  ✅ Tenant created with ID: {tenant_id}")
                
                # Create and seed the school's schema
                print(f"  🔧 Creating database schema...")
                tenant_service.ensure_schema(school_slug)
                
                print(f"  🌱 Seeding default data...")
                tenant_service.seed_defaults()
                
                print(f"  🎉 Successfully set up: {school_name}")
                
            except Exception as e:
                print(f"  ❌ Error creating {school_name}: {e}")
                db.rollback()
                continue
        
        print("\n" + "=" * 50)
        print("🎊 Sample schools creation completed!")
        
        # Show created schools
        tenants = db.execute(
            text("SELECT name, slug, contact_email FROM public.tenants ORDER BY name")
        ).mappings().all()
        
        print(f"\n📋 Total schools in system: {len(tenants)}")
        for tenant in tenants:
            print(f"  • {tenant.name} ({tenant.slug}) - {tenant.contact_email}")
            
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_sample_schools()
