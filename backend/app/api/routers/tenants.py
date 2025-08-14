from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

from app.tenancy.deps import get_tenant_db
from app.api.deps import get_current_user_id
from app.core.config import settings
from fastapi import Header

router = APIRouter()
security = HTTPBearer()

def get_super_admin_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get Super Admin user from JWT token."""
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id = int(payload.get("sub"))
        
        # Check if user is a platform Super Administrator (public schema)
        from app.db.session import SessionLocal
        db = SessionLocal()
        try:
            exists = db.execute(
                text("SELECT 1 FROM public.platform_admins WHERE id = :id AND is_active = true"),
                {"id": user_id}
            ).scalar()

            if exists:
                return user_id

            raise HTTPException(status_code=403, detail="Access denied. Only platform Super Administrators can access tenant management.")
        finally:
            db.close()
            
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Pydantic models
class TenantCreate(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    is_active: bool = True
    enabled_modules: Optional[list[str]] = None  # e.g. ["students","finance","academic","teachers","communications"]
    branding: Optional[dict] = None

class TenantUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None
    enabled_modules: Optional[list[str]] = None
    branding: Optional[dict] = None

class TenantRead(BaseModel):
    id: int
    name: str
    slug: str
    schema_name: Optional[str] = None
    description: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    enabled_modules: Optional[list[str]] = None
    branding: Optional[dict] = None
    user_count: int
    student_count: int
    teacher_count: int

class TenantStats(BaseModel):
    total_users: int
    active_users: int
    total_students: int
    total_teachers: int
    total_classes: int
    total_subjects: int
    recent_activity: List[dict]

# Public Endpoints
@router.get("/public", response_model=List[dict])
def list_public_tenants():
    """List available tenants for login (public access)."""
    from app.db.session import SessionLocal
    db = SessionLocal()
    try:
        rows = db.execute(
            text("SELECT id, name, slug, is_active FROM public.tenants WHERE is_active = true ORDER BY name")
        ).mappings().all()
        return [{"id": row.id, "name": row.name, "slug": row.slug, "is_active": row.is_active} for row in rows]
    finally:
        db.close()

# Tenant Management Endpoints (Super Admin only)
@router.get("", response_model=List[TenantRead])
def list_tenants(
    user_id: int = Depends(get_super_admin_user),
    q: Optional[str] = Query(None),
    status: Optional[str] = Query(None)
):
    """List all tenants (Super Admin only)."""
    from app.db.session import SessionLocal
    
    db = SessionLocal()
    try:
        query = """
            SELECT t.id, t.name, t.slug, t.schema_name, t.is_active, t.contact_email, t.contact_phone, t.address, t.enabled_modules, t.branding, t.created_at, t.updated_at
            FROM public.tenants t
            WHERE 1=1
        """
        params = {}
        
        if q:
            query += " AND (LOWER(t.name) LIKE :q OR LOWER(t.slug) LIKE :q)"
            params["q"] = f"%{q.lower()}%"
        
        if status:
            if status == "active":
                query += " AND t.is_active = true"
            elif status == "inactive":
                query += " AND t.is_active = false"
        
        query += " ORDER BY t.name"
        
        rows = db.execute(text(query), params).mappings().all()
        
        # Get statistics for each tenant
        tenants = []
        for row in rows:
            # Set search path to this tenant to get stats
            db.execute(text(f'SET LOCAL search_path TO "{row.schema_name}", public'))
            
            try:
                user_count = db.execute(text("SELECT COUNT(*) FROM users")).scalar() or 0
                student_count = db.execute(text("SELECT COUNT(*) FROM students")).scalar() or 0
                teacher_count = db.execute(text("SELECT COUNT(*) FROM teachers")).scalar() or 0
            except:
                user_count = 0
                student_count = 0
                teacher_count = 0
            
            tenants.append(TenantRead(
                id=row.id,
                name=row.name,
                slug=row.slug,
                schema_name=row.schema_name,
                is_active=bool(row.is_active) if row.is_active is not None else True,
                contact_email=row.contact_email,
                contact_phone=row.contact_phone,
                address=row.address,
                enabled_modules=row.enabled_modules,
                branding=row.branding,
                created_at=str(row.created_at) if row.created_at is not None else None,
                updated_at=str(row.updated_at) if row.updated_at is not None else None,
                user_count=user_count,
                student_count=student_count,
                teacher_count=teacher_count
            ))
        
        return tenants
    finally:
        db.close()

@router.post("", response_model=TenantRead)
def create_tenant(
    tenant_data: TenantCreate,
    user_id: int = Depends(get_super_admin_user)
):
    """Create a new tenant (Platform Super Admin only)."""
    from app.db.session import SessionLocal
    db = SessionLocal()
    try:
        # Check if tenant slug already exists
        existing = db.execute(
            text("SELECT id FROM public.tenants WHERE slug = :slug"), 
            {"slug": tenant_data.slug}
        ).scalar()
        if existing:
            raise HTTPException(status_code=400, detail="Tenant with this slug already exists")

        # Insert into public.tenants
        result = db.execute(
            text(
                """
                INSERT INTO public.tenants(name, slug, schema_name, is_active, contact_email, contact_phone, address, enabled_modules, branding)
                VALUES (:name, :slug, :schema_name, :is_active, :contact_email, :contact_phone, :address, :enabled_modules, :branding)
                RETURNING id, name, slug, schema_name, is_active, contact_email, contact_phone, address, enabled_modules, branding, created_at, updated_at
                """
            ),
            {
                "name": tenant_data.name,
                "slug": tenant_data.slug,
                "schema_name": tenant_data.slug,
                "is_active": tenant_data.is_active,
                "contact_email": tenant_data.contact_email,
                "contact_phone": tenant_data.contact_phone,
                "address": tenant_data.address,
                "enabled_modules": (tenant_data.enabled_modules or ["students","finance","academic","teachers","communications"]),
                "branding": (tenant_data.branding or {}),
            },
        )
        new_tenant = result.mappings().first()

        # Create schema and seed defaults for the new tenant
        from app.tenancy.service import TenantService
        tenant_service = TenantService(db)
        tenant_service.create_schema(new_tenant.schema_name)
        db.execute(text(f'SET LOCAL search_path TO "{new_tenant.schema_name}", public'))
        tenant_service.seed_defaults()
        db.commit()

        return TenantRead(
            id=new_tenant.id,
            name=new_tenant.name,
            slug=new_tenant.slug,
            schema_name=new_tenant.schema_name,
            is_active=bool(new_tenant.is_active) if new_tenant.is_active is not None else True,
            contact_email=new_tenant.contact_email,
            contact_phone=new_tenant.contact_phone,
            address=new_tenant.address,
            enabled_modules=new_tenant.enabled_modules,
            branding=new_tenant.branding,
            created_at=str(new_tenant.created_at) if new_tenant.created_at else None,
            updated_at=str(new_tenant.updated_at) if new_tenant.updated_at else None,
            user_count=0,
            student_count=0,
            teacher_count=0,
        )
    finally:
        db.close()

@router.put("/{tenant_id}", response_model=TenantRead)
def update_tenant(
    tenant_id: int,
    tenant_data: TenantUpdate,
    user_id: int = Depends(get_super_admin_user)
):
    """Update a tenant (Platform Super Admin only)."""
    from app.db.session import SessionLocal
    db = SessionLocal()
    try:
        # Check exists
        tenant = db.execute(
            text("SELECT id, name, slug, schema_name, created_at, updated_at FROM public.tenants WHERE id = :id"),
            {"id": tenant_id}
        ).mappings().first()
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")

        # Build update set
        fields = []
        params = {"id": tenant_id}
        if tenant_data.name is not None:
            fields.append("name = :name"); params["name"] = tenant_data.name
        if tenant_data.description is not None:
            fields.append("description = :description"); params["description"] = tenant_data.description
        if tenant_data.contact_email is not None:
            fields.append("contact_email = :contact_email"); params["contact_email"] = tenant_data.contact_email
        if tenant_data.contact_phone is not None:
            fields.append("contact_phone = :contact_phone"); params["contact_phone"] = tenant_data.contact_phone
        if tenant_data.address is not None:
            fields.append("address = :address"); params["address"] = tenant_data.address
        if tenant_data.is_active is not None:
            fields.append("is_active = :is_active"); params["is_active"] = tenant_data.is_active
        if tenant_data.enabled_modules is not None:
            fields.append("enabled_modules = :enabled_modules"); params["enabled_modules"] = tenant_data.enabled_modules
        if tenant_data.branding is not None:
            fields.append("branding = :branding"); params["branding"] = tenant_data.branding
        if not fields:
            raise HTTPException(status_code=400, detail="No updatable fields provided")
        set_sql = ", ".join(fields) + ", updated_at = CURRENT_TIMESTAMP"
        db.execute(text(f"UPDATE public.tenants SET {set_sql} WHERE id = :id"), params)

        # Refresh
        updated = db.execute(
            text("SELECT id, name, slug, schema_name, is_active, contact_email, contact_phone, address, enabled_modules, branding, created_at, updated_at FROM public.tenants WHERE id = :id"),
            {"id": tenant_id}
        ).mappings().first()

        # Stats
        db.execute(text(f'SET LOCAL search_path TO "{updated.schema_name}", public'))
        try:
            user_count = db.execute(text("SELECT COUNT(*) FROM users")).scalar() or 0
            student_count = db.execute(text("SELECT COUNT(*) FROM students")).scalar() or 0
            teacher_count = db.execute(text("SELECT COUNT(*) FROM teachers")).scalar() or 0
        except:
            user_count = 0
            student_count = 0
            teacher_count = 0

        db.commit()
        return TenantRead(
            id=updated.id,
            name=updated.name,
            slug=updated.slug,
            schema_name=updated.schema_name,
            is_active=bool(updated.is_active) if updated.is_active is not None else True,
            contact_email=updated.contact_email,
            contact_phone=updated.contact_phone,
            address=updated.address,
            enabled_modules=updated.enabled_modules,
            branding=updated.branding,
            created_at=str(updated.created_at) if updated.created_at else None,
            updated_at=str(updated.updated_at) if updated.updated_at else None,
            user_count=user_count,
            student_count=student_count,
            teacher_count=teacher_count,
        )
    finally:
        db.close()

@router.delete("/{tenant_id}")
def delete_tenant(
    tenant_id: int,
    user_id: int = Depends(get_super_admin_user)
):
    """Delete a tenant (Platform Super Admin only)."""
    from app.db.session import SessionLocal
    db = SessionLocal()
    try:
        tenant = db.execute(
            text("SELECT id, slug, schema_name FROM public.tenants WHERE id = :id"),
            {"id": tenant_id}
        ).mappings().first()
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")

        db.execute(text(f'SET LOCAL search_path TO "{tenant.schema_name}", public'))
        try:
            user_count = db.execute(text("SELECT COUNT(*) FROM users")).scalar() or 0
            student_count = db.execute(text("SELECT COUNT(*) FROM students")).scalar() or 0
        except:
            user_count = 0
            student_count = 0
        if user_count > 0 or student_count > 0:
            raise HTTPException(status_code=400, detail=f"Cannot delete tenant. It has {user_count} users and {student_count} students.")

        # Drop schema and remove record
        db.execute(text(f'DROP SCHEMA IF EXISTS "{tenant.schema_name}" CASCADE'))
        db.execute(text("DELETE FROM public.tenants WHERE id = :id"), {"id": tenant_id})
        db.commit()
        return {"message": "Tenant deleted successfully"}
    finally:
        db.close()

@router.get("/{tenant_id}/stats", response_model=TenantStats)
def get_tenant_stats(
    tenant_id: int,
    user_id: int = Depends(get_super_admin_user)
):
    """Get detailed statistics for a tenant (Super Admin only)."""
    from app.db.session import SessionLocal
    db = SessionLocal()
    try:
        # Get tenant from public schema
        tenant = db.execute(
            text("SELECT id, slug, schema_name FROM public.tenants WHERE id = :id"), 
            {"id": tenant_id}
        ).mappings().first()

        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")

        # Set search path to this tenant
        db.execute(text(f'SET LOCAL search_path TO "{tenant.schema_name}", public'))

        try:
            total_users = db.execute(text("SELECT COUNT(*) FROM users")).scalar() or 0
            active_users = db.execute(text("SELECT COUNT(*) FROM users WHERE is_active = true")).scalar() or 0
            total_students = db.execute(text("SELECT COUNT(*) FROM students")).scalar() or 0
            total_teachers = db.execute(text("SELECT COUNT(*) FROM teachers")).scalar() or 0
            total_classes = db.execute(text("SELECT COUNT(*) FROM classes")).scalar() or 0
            total_subjects = db.execute(text("SELECT COUNT(*) FROM subjects")).scalar() or 0

            # Get recent activity (last 5 users created)
            recent_users = db.execute(
                text("SELECT email, full_name, created_at FROM users ORDER BY created_at DESC LIMIT 5")
            ).mappings().all()

            recent_activity = [
                {
                    "type": "user_created",
                    "email": user.email,
                    "full_name": user.full_name,
                    "created_at": str(user.created_at)
                }
                for user in recent_users
            ]

        except Exception:
            # If schema doesn't exist or has issues, return zeros
            total_users = 0
            active_users = 0
            total_students = 0
            total_teachers = 0
            total_classes = 0
            total_subjects = 0
            recent_activity = []

        return TenantStats(
            total_users=total_users,
            active_users=active_users,
            total_students=total_students,
            total_teachers=total_teachers,
            total_classes=total_classes,
            total_subjects=total_subjects,
            recent_activity=recent_activity,
        )
    finally:
        db.close()

@router.get("/public/config")
def public_tenant_config(slug: str = Query(..., description="Tenant slug")):
    """Public endpoint to fetch branding and enabled modules by slug (no auth)."""
    from app.db.session import SessionLocal
    db = SessionLocal()
    try:
        row = db.execute(
            text("SELECT name, slug, enabled_modules, branding FROM public.tenants WHERE slug = :slug AND is_active = true"),
            {"slug": slug}
        ).mappings().first()
        if not row:
            raise HTTPException(status_code=404, detail="Tenant not found")
        return {
            "name": row.name,
            "slug": row.slug,
            "enabled_modules": row.enabled_modules or [],
            "branding": row.branding or {}
        }
    finally:
        db.close()

@router.post("/{tenant_id}/reset")
def reset_tenant_data(
    tenant_id: int,
    user_id: int = Depends(get_super_admin_user)
):
    """Reset tenant data (Super Admin only)."""
    from app.db.session import SessionLocal
    db = SessionLocal()
    try:
        tenant = db.execute(
            text("SELECT id, slug, schema_name FROM public.tenants WHERE id = :id"), 
            {"id": tenant_id}
        ).mappings().first()
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")

        from app.tenancy.service import TenantService
        tenant_service = TenantService(db)
        try:
            # Drop and recreate schema
            db.execute(text(f'DROP SCHEMA IF EXISTS "{tenant.schema_name}" CASCADE'))
            tenant_service.create_schema(tenant.schema_name)
            db.execute(text(f'SET LOCAL search_path TO "{tenant.schema_name}", public'))
            tenant_service.seed_defaults()
            db.commit()
            return {"message": "Tenant data reset successfully"}
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to reset tenant data: {str(e)}")
    finally:
        db.close()


