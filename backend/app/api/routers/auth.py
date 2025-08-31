from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.schemas.auth import LoginRequest, Token
from app.services.security import create_access_token, verify_password
from app.tenancy.deps import get_tenant_db
from app.api.deps import get_current_user_id


router = APIRouter()


@router.post("/simple-login", response_model=Token)
def simple_login(payload: LoginRequest):
    """Simplified login that auto-detects tenant from email domain"""
    from app.db.session import SessionLocal
    
    # Extract domain from email to determine tenant
    email_domain = payload.username.split('@')[-1]
    tenant_slug = None
    
    # Map email domains to tenant slugs
    domain_mapping = {
        'parent.ndirande-high.edu': 'ndirande-high',
        'ndirande-high.edu': 'ndirande-high',
        'teacher.ndirande-high.edu': 'ndirande-high',
        'admin.ndirande-high.edu': 'ndirande-high',
    }
    
    # Check if we have a direct mapping
    if email_domain in domain_mapping:
        tenant_slug = domain_mapping[email_domain]
    else:
        # Fallback: try to extract tenant from email pattern
        if 'ndirande' in email_domain.lower():
            tenant_slug = 'ndirande-high'
        else:
            # Try to find tenant by partial matching
            public_db = SessionLocal()
            try:
                # Look for tenant by slug pattern
                domain_parts = email_domain.replace('.edu', '').replace('.', '-').split('-')
                for part in domain_parts:
                    if len(part) > 2:  # Ignore very short parts
                        tenant_row = public_db.execute(
                            text("SELECT slug FROM public.tenants WHERE slug ILIKE :pattern"),
                            {"pattern": f"%{part}%"}
                        ).first()
                        if tenant_row:
                            tenant_slug = tenant_row.slug
                            break
            finally:
                public_db.close()
        
        if not tenant_slug:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Could not determine school from email address. Please contact your administrator."
            )
    
    # Now connect to tenant database and authenticate
    from app.db.session import tenant_session
    from app.tenancy.service import TenantService
    
    # First, get the tenant's schema name
    public_db = SessionLocal()
    try:
        tenant_service = TenantService(public_db)
        tenant = tenant_service.get_by_slug(tenant_slug)
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Invalid school configuration"
            )
        schema_name = tenant.schema_name
    finally:
        public_db.close()
    
    # Now connect to tenant database
    with tenant_session(schema_name) as tenant_db:
        user_row = tenant_db.execute(
            text("SELECT id, email, hashed_password, is_active FROM users WHERE email = :email"),
            {"email": payload.username}
        ).first()
        
        if not user_row:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        if not verify_password(payload.password, user_row.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        if not user_row.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")

        # Create token with tenant context
        token = create_access_token(
            subject=str(user_row.id),
            extra={"tenant": tenant_slug}
        )
        return Token(access_token=token)


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
def me(request: Request, user_id: int = Depends(get_current_user_id)):
    """Get current user info using tenant from JWT token"""
    from app.db.session import SessionLocal, tenant_session
    from jose import jwt
    from app.core.config import settings
    
    # Extract token and get tenant
    auth_header = request.headers.get('authorization', '')
    if not auth_header.lower().startswith('bearer '):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    
    token = auth_header.split(' ', 1)[1]
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        tenant_slug = payload.get("tenant")
        if not tenant_slug:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No tenant in token")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    # Get tenant schema from slug
    public_db = SessionLocal()
    try:
        from app.tenancy.service import TenantService
        tenant_service = TenantService(public_db)
        tenant = tenant_service.get_by_slug(tenant_slug)
        if not tenant:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
        schema_name = tenant.schema_name
    finally:
        public_db.close()
    
    # Now get user data from tenant database
    with tenant_session(schema_name) as tenant_db:
        user = tenant_db.execute(text("SELECT id, email, full_name, is_active FROM users WHERE id=:id"), {"id": user_id}).mappings().first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        roles = tenant_db.execute(
            text(
                """
                SELECT r.name FROM roles r
                JOIN user_roles ur ON ur.role_id = r.id
                WHERE ur.user_id = :uid
                """
            ),
            {"uid": user_id},
        ).scalars().all()
        permissions = tenant_db.execute(
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


