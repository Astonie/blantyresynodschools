from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.schemas.auth import LoginRequest, Token
from app.services.security import create_access_token, verify_password
from app.tenancy.deps import get_tenant_db
from app.api.deps import get_current_user_id


router = APIRouter()


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_tenant_db)):
    user_row = db.execute(text("SELECT id, email, hashed_password, is_active FROM users WHERE email=:e"), {"e": payload.username}).first()
    if not user_row:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not verify_password(payload.password, user_row.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user_row.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")

    token = create_access_token(subject=str(user_row.id))
    return Token(access_token=token)


@router.post("/super-admin/login", response_model=Token)
def super_admin_login(payload: LoginRequest):
    """Platform-level Super Admin login (no tenant context)."""
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        user_row = db.execute(
            text("SELECT id, email, hashed_password, is_active FROM public.platform_admins WHERE email = :email"),
            {"email": payload.username}
        ).first()

        if not user_row:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        if not verify_password(payload.password, user_row.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        if not user_row.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")

        # Create platform token with super admin privileges; no tenant claim
        token = create_access_token(
            subject=str(user_row.id),
            extra={"super_admin": True}
        )
        return Token(access_token=token)
    finally:
        db.close()


@router.get("/me")
def me(db: Session = Depends(get_tenant_db), user_id: int = Depends(get_current_user_id)):
    user = db.execute(text("SELECT id, email, full_name, is_active FROM users WHERE id=:id"), {"id": user_id}).mappings().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    roles = db.execute(
        text(
            """
            SELECT r.name FROM roles r
            JOIN user_roles ur ON ur.role_id = r.id
            WHERE ur.user_id = :uid
            """
        ),
        {"uid": user_id},
    ).scalars().all()
    permissions = db.execute(
        text(
            """
            SELECT DISTINCT p.name
            FROM permissions p
            JOIN role_permissions rp ON rp.permission_id = p.id
            JOIN user_roles ur ON ur.role_id = rp.role_id
            WHERE ur.user_id = :uid
            """
        ),
        {"uid": user_id},
    ).scalars().all()
    data = dict(user)
    data.update({"roles": roles, "permissions": permissions})
    return data


@router.get("/super-admin/me")
def super_admin_me(user_id: int = Depends(get_current_user_id)):
    """Get platform super admin profile (public schema)."""
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        user = db.execute(
            text("SELECT id, email, full_name, is_active, created_at, updated_at FROM public.platform_admins WHERE id = :id"),
            {"id": user_id}
        ).mappings().first()
        if not user:
            raise HTTPException(status_code=404, detail="Super Administrator not found")

        data = dict(user)
        data.update({
            "roles": ["Super Administrator"],
            "permissions": ["tenants.manage", "settings.manage"],
            "super_admin": True
        })
        return data
    finally:
        db.close()


@router.get("/super-admin/tenants")
def get_all_tenants():
    """Get all tenants for super admin."""
    from app.db.session import SessionLocal
    
    db = SessionLocal()
    try:
        tenants = db.execute(text("SELECT id, name, slug FROM tenants ORDER BY id")).mappings().all()
        return [{"id": t.id, "name": t.name, "slug": t.slug} for t in tenants]
    finally:
        db.close()


