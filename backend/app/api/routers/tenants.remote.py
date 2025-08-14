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

class TenantUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None

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
            SELECT t.id, t.name, t.slug, t.schema_name, t.created_at, t.updated_at
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
                INSERT INTO public.tenants(name, slug, schema_name)
                VALUES (:name, :slug, :schema_name)
                RETURNING id, name, slug, schema_name, created_at, updated_at
                """
            ),
            {
                "name": tenant_data.name,
                "slug": tenant_data.slug,
                "schema_name": tenant_data.slug,
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

        # Only allow name update for now
        if tenant_data.name is None:
            raise HTTPException(status_code=400, detail="No updatable fields provided")

        db.execute(
            text("UPDATE public.tenants SET name = :name, updated_at = CURRENT_TIMESTAMP WHERE id = :id"),
            {"id": tenant_id, "name": tenant_data.name},
        )

        # Refresh
        updated = db.execute(
            text("SELECT id, name, slug, schema_name, created_at, updated_at FROM public.tenants WHERE id = :id"),
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


