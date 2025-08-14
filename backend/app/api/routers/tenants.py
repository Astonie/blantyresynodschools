from pydantic import BaseModel, EmailStr
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.session import get_public_session
from app.tenancy.service import TenantService
from app.services.security import hash_password


router = APIRouter()


@router.get("")
def list_tenants(db: Session = Depends(get_public_session)):
    rows = db.execute(text("SELECT id, name, slug FROM tenants ORDER BY name ASC")).mappings().all()
    return [dict(r) for r in rows]


class OnboardRequest(BaseModel):
    name: str
    slug: str
    admin_email: EmailStr
    admin_password: str


@router.post("/onboard")
def onboard_tenant(payload: OnboardRequest, db: Session = Depends(get_public_session)):
    schema_name = f"t_{payload.slug}"
    svc = TenantService(db)
    existing = svc.get_by_slug(payload.slug)
    if existing:
        raise HTTPException(status_code=400, detail="Tenant already exists")

    tenant = svc.create(name=payload.name, slug=payload.slug, schema_name=schema_name)
    svc.ensure_schema(schema_name)
    
    # Set search path and seed defaults in a single transaction
    db.execute(text(f"SET LOCAL search_path TO \"{schema_name}\", public"))
    svc.seed_defaults()
    
    # create admin user with Administrator role
    db.execute(
        text("INSERT INTO users(email, hashed_password) VALUES (:e, :p) ON CONFLICT DO NOTHING"),
        {"e": payload.admin_email, "p": hash_password(payload.admin_password)},
    )
    admin_user_id = db.execute(text("SELECT id FROM users WHERE email=:e"), {"e": payload.admin_email}).scalar()
    admin_role_id = db.execute(text("SELECT id FROM roles WHERE name='Administrator'")).scalar()
    if admin_user_id and admin_role_id:
        db.execute(
            text("INSERT INTO user_roles(user_id, role_id) VALUES (:u, :r) ON CONFLICT DO NOTHING"),
            {"u": admin_user_id, "r": admin_role_id},
        )
    db.commit()
    return {"id": tenant.id, "name": tenant.name, "slug": tenant.slug}


