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
    """Super admin login that works across all tenants."""
    from app.db.session import SessionLocal
    
    # Get all tenants
    db = SessionLocal()
    try:
        tenants = db.execute(text("SELECT id, name, slug FROM tenants ORDER BY id")).mappings().all()
        
        # Try to find the super admin user in any tenant
        super_admin_user = None
        super_admin_tenant = None
        
        for tenant in tenants:
            try:
                # Set search path to this tenant
                db.execute(text(f'SET LOCAL search_path TO "{tenant.slug}", public'))
                
                # Check if super admin exists in this tenant
                user_row = db.execute(
                    text("SELECT id, email, hashed_password, is_active FROM users WHERE email = :email"),
                    {"email": payload.username}
                ).first()
                
                if user_row:
                    # Check if this user has Super Administrator role
                    roles = db.execute(
                        text("""
                            SELECT r.name FROM roles r
                            JOIN user_roles ur ON ur.role_id = r.id
                            WHERE ur.user_id = :user_id AND r.name = 'Super Administrator'
                        """),
                        {"user_id": user_row.id}
                    ).scalars().all()
                    
                    if roles:
                        super_admin_user = user_row
                        super_admin_tenant = tenant
                        break
            except Exception as e:
                # If there's an error with this tenant, continue to the next one
                print(f"Error checking tenant {tenant.slug}: {e}")
                continue
        
        if not super_admin_user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials or not a Super Administrator")
        
        if not verify_password(payload.password, super_admin_user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        
        if not super_admin_user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
        
        # Create token with super admin privileges and tenant info
        token = create_access_token(
            subject=str(super_admin_user.id),
            extra={"super_admin": True, "tenant": super_admin_tenant.slug}
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
    """Get super admin user information across all tenants."""
    from app.db.session import SessionLocal
    from app.tenancy.service import TenantService
    
    db = SessionLocal()
    try:
        tenants = db.execute(text("SELECT id, name, slug FROM tenants ORDER BY id")).mappings().all()
        
        # Find the super admin user in any tenant
        super_admin_user = None
        super_admin_tenant = None
        
        for tenant in tenants:
            db.execute(text(f'SET LOCAL search_path TO "{tenant.slug}", public'))
            
            user = db.execute(
                text("SELECT id, email, full_name, is_active FROM users WHERE id = :id"),
                {"id": user_id}
            ).mappings().first()
            
            if user:
                # Check if this user has Super Administrator role
                roles = db.execute(
                    text("""
                        SELECT r.name FROM roles r
                        JOIN user_roles ur ON ur.role_id = r.id
                        WHERE ur.user_id = :user_id AND r.name = 'Super Administrator'
                    """),
                    {"user_id": user_id}
                ).scalars().all()
                
                if roles:
                    super_admin_user = user
                    super_admin_tenant = tenant
                    break
        
        if not super_admin_user:
            raise HTTPException(status_code=404, detail="Super Administrator not found")
        
        # Get all permissions for super admin
        permissions = db.execute(
            text("""
                SELECT DISTINCT p.name
                FROM permissions p
                JOIN role_permissions rp ON rp.permission_id = p.id
                JOIN user_roles ur ON ur.role_id = rp.role_id
                WHERE ur.user_id = :uid
            """),
            {"uid": user_id}
        ).scalars().all()
        
        data = dict(super_admin_user)
        data.update({
            "roles": ["Super Administrator"],
            "permissions": list(permissions),
            "tenant": super_admin_tenant.slug if super_admin_tenant else None,
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


