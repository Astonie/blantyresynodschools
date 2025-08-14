from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.base import PublicBase
from app.db.session import engine, SessionLocal
from app.models import public  # ensure models are imported so metadata is populated
from app.services.security import hash_password


def init_public() -> None:
    # Create public metadata tables using ORM for the public schema
    PublicBase.metadata.create_all(bind=engine)

    # Ensure tenants table exists if defined by ORM; otherwise a fallback DDL could be placed here
    # Create platform-level admin table and seed a default platform owner
    db: Session = SessionLocal()
    try:
        # Add production-ready columns to public.tenants
        db.execute(text("""
            ALTER TABLE IF EXISTS public.tenants
            ADD COLUMN IF NOT EXISTS is_active boolean DEFAULT true,
            ADD COLUMN IF NOT EXISTS description text,
            ADD COLUMN IF NOT EXISTS contact_email varchar(255),
            ADD COLUMN IF NOT EXISTS contact_phone varchar(50),
            ADD COLUMN IF NOT EXISTS address text,
            ADD COLUMN IF NOT EXISTS enabled_modules jsonb DEFAULT '[]'::jsonb,
            ADD COLUMN IF NOT EXISTS branding jsonb DEFAULT '{}'::jsonb
        """))

        # Create platform_admins table in public schema
        db.execute(text(
            """
            CREATE TABLE IF NOT EXISTS public.platform_admins (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                full_name VARCHAR(255) NOT NULL,
                hashed_password VARCHAR(255) NOT NULL,
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        ))

        # Seed default platform owner if missing
        existing = db.execute(
            text("SELECT id FROM public.platform_admins WHERE email = :email"),
            {"email": "admin@blantyresynod.org"}
        ).scalar()

        if not existing:
            db.execute(
                text(
                    """
                    INSERT INTO public.platform_admins (email, full_name, hashed_password, is_active)
                    VALUES (:email, :full_name, :hp, true)
                    """
                ),
                {
                    "email": "admin@blantyresynod.org",
                    "full_name": "Platform Owner",
                    "hp": hash_password("admin123"),
                },
            )
        db.commit()
    finally:
        db.close()


