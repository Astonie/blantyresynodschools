from typing import Callable, Iterable, Optional
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.tenancy.deps import get_tenant_db
from app.api.deps import get_current_user_id

# Enhanced audit logging function
def log_audit_event(
    db: Session,
    user_id: int,
    action: str,
    resource_type: str,
    resource_id: Optional[int] = None,
    old_values: Optional[dict] = None,
    new_values: Optional[dict] = None,
    request: Optional[Request] = None
):
    """Log security-relevant events for audit trail"""
    try:
        ip_address = None
        user_agent = None
        
        if request:
            # Get client IP (handle proxies)
            ip_address = request.headers.get('X-Forwarded-For', '').split(',')[0].strip()
            if not ip_address:
                ip_address = request.headers.get('X-Real-IP', '')
            if not ip_address:
                ip_address = request.client.host if request.client else None
            
            user_agent = request.headers.get('User-Agent', '')[:500]  # Truncate
        
        # Get current tenant schema
        tenant_schema = db.execute(text("SELECT current_schema()")).scalar()
        
        db.execute(text("""
            INSERT INTO audit_logs 
            (user_id, action, resource_type, resource_id, old_values, new_values, 
             ip_address, user_agent, tenant_schema)
            VALUES (:user_id, :action, :resource_type, :resource_id, :old_values, 
                    :new_values, :ip_address, :user_agent, :tenant_schema)
        """), {
            "user_id": user_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "old_values": old_values,
            "new_values": new_values,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "tenant_schema": tenant_schema
        })
        db.commit()
    except Exception as e:
        print(f"Audit logging failed: {e}")
        # Don't fail the main operation if audit logging fails
        pass

# Enhanced permission checking with data-level security
def require_permissions_with_context(required: Iterable[str], resource_type: str = None) -> Callable:
    """Enhanced permission checker with context-aware security"""
    required_set = set(r.strip() for r in required)

    def dependency(
        request: Request,
        db: Session = Depends(get_tenant_db),
        user_id: int = Depends(get_current_user_id),
    ) -> dict:
        # Get user roles and permissions
        user_data = db.execute(text("""
            SELECT u.id, u.email,
                   STRING_AGG(DISTINCT r.name, ',') as roles,
                   STRING_AGG(DISTINCT p.name, ',') as permissions
            FROM users u
            LEFT JOIN user_roles ur ON u.id = ur.user_id
            LEFT JOIN roles r ON ur.role_id = r.id
            LEFT JOIN role_permissions rp ON r.id = rp.role_id
            LEFT JOIN permissions p ON rp.permission_id = p.id
            WHERE u.id = :uid
            GROUP BY u.id, u.email
        """), {"uid": user_id}).mappings().first()
        
        if not user_data:
            log_audit_event(db, user_id, "PERMISSION_DENIED", "authentication", 
                          request=request)
            raise HTTPException(status_code=403, detail="User not found")
        
        user_permissions = set(user_data.permissions.split(',')) if user_data.permissions else set()
        user_roles = set(user_data.roles.split(',')) if user_data.roles else set()
        
        # Check if user has required permissions
        has_permission = bool(user_permissions.intersection(required_set))
        
        # Enhanced context-aware security checks
        security_context = {
            "user_id": user_id,
            "user_email": user_data.email,
            "roles": user_roles,
            "permissions": user_permissions,
            "can_access_all": False,
            "restricted_to_own": False,
            "restricted_to_children": False
        }
        
        # Role-specific access restrictions
        if "Parent" in user_roles:
            # Parents should only access parent-specific endpoints or their children's data
            if not any(perm.endswith('.children') for perm in user_permissions):
                security_context["restricted_to_children"] = True
            
            # Log parent access attempts
            log_audit_event(db, user_id, "PARENT_ACCESS_ATTEMPT", 
                          resource_type or "unknown", request=request)
        
        elif "Student" in user_roles:
            # Students should only access their own data
            security_context["restricted_to_own"] = True
            
            # Log student access attempts
            log_audit_event(db, user_id, "STUDENT_ACCESS_ATTEMPT", 
                          resource_type or "unknown", request=request)
        
        elif any(role in ["Administrator", "Super Administrator"] for role in user_roles):
            security_context["can_access_all"] = True
        
        # Check permission match
        if not has_permission and not security_context["can_access_all"]:
            log_audit_event(db, user_id, "PERMISSION_DENIED", resource_type or "unknown",
                          new_values={"required": list(required_set), "user_permissions": list(user_permissions)},
                          request=request)
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Log successful access
        log_audit_event(db, user_id, "ACCESS_GRANTED", resource_type or "unknown",
                      new_values={"permissions": list(required_set)}, request=request)
        
        return security_context

    return dependency

# Parent-specific access control
def require_parent_access_to_children() -> Callable:
    """Ensure parents can only access their own children's data"""
    def dependency(
        request: Request,
        db: Session = Depends(get_tenant_db),
        user_id: int = Depends(get_current_user_id),
    ) -> list:
        # Check if user is a parent
        user_roles = db.execute(text("""
            SELECT r.name FROM roles r
            JOIN user_roles ur ON r.id = ur.role_id
            WHERE ur.user_id = :uid
        """), {"uid": user_id}).scalars().all()
        
        if "Parent" not in user_roles:
            log_audit_event(db, user_id, "PARENT_ACCESS_DENIED", "parent_endpoint", 
                          request=request)
            raise HTTPException(status_code=403, detail="Parent access required")
        
        # Get children IDs for this parent
        children_ids = db.execute(text("""
            SELECT student_id FROM parent_students
            WHERE parent_user_id = :parent_id
        """), {"parent_id": user_id}).scalars().all()
        
        log_audit_event(db, user_id, "PARENT_ACCESS_GRANTED", "children_data",
                      new_values={"children_count": len(children_ids)}, request=request)
        
        return children_ids

    return dependency

# Student self-access control
def require_student_self_access() -> Callable:
    """Ensure students can only access their own data"""
    def dependency(
        request: Request,
        db: Session = Depends(get_tenant_db),
        user_id: int = Depends(get_current_user_id),
    ) -> int:
        # Check if user is a student
        user_roles = db.execute(text("""
            SELECT r.name FROM roles r
            JOIN user_roles ur ON r.id = ur.role_id
            WHERE ur.user_id = :uid
        """), {"uid": user_id}).scalars().all()
        
        if "Student" not in user_roles:
            log_audit_event(db, user_id, "STUDENT_ACCESS_DENIED", "student_endpoint", 
                          request=request)
            raise HTTPException(status_code=403, detail="Student access required")
        
        # Get student record ID
        student_record = db.execute(text("""
            SELECT id FROM students WHERE user_id = :user_id
        """), {"user_id": user_id}).scalar()
        
        if not student_record:
            log_audit_event(db, user_id, "STUDENT_RECORD_NOT_FOUND", "student_data", 
                          request=request)
            raise HTTPException(status_code=404, detail="Student record not found")
        
        log_audit_event(db, user_id, "STUDENT_SELF_ACCESS", "own_data",
                      new_values={"student_id": student_record}, request=request)
        
        return student_record

    return dependency

# Enhanced role checker with audit logging
def require_roles_with_audit(required: Iterable[str]) -> Callable:
    """Role checker with comprehensive audit logging"""
    required_set = set(r.strip() for r in required)

    def dependency(
        request: Request,
        db: Session = Depends(get_tenant_db),
        user_id: int = Depends(get_current_user_id),
    ) -> None:
        user_roles = db.execute(text("""
            SELECT r.name FROM roles r
            JOIN user_roles ur ON ur.role_id = r.id
            WHERE ur.user_id = :uid
        """), {"uid": user_id}).scalars().all()
        
        user_roles_set = set(user_roles)
        
        if not user_roles_set.intersection(required_set):
            log_audit_event(db, user_id, "ROLE_ACCESS_DENIED", "role_protected_endpoint",
                          new_values={"required_roles": list(required_set), "user_roles": user_roles},
                          request=request)
            raise HTTPException(status_code=403, detail="Insufficient role")
        
        log_audit_event(db, user_id, "ROLE_ACCESS_GRANTED", "role_protected_endpoint",
                      new_values={"required_roles": list(required_set), "user_roles": user_roles},
                      request=request)

    return dependency
