from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from pydantic import BaseModel

from app.tenancy.deps import get_tenant_db
from app.api.deps import require_permissions, get_current_user_id

router = APIRouter()

# Pydantic models for API requests/responses
class UserCreate(BaseModel):
    email: str
    full_name: str
    password: str
    is_active: bool = True

class UserUpdate(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None

class UserRead(BaseModel):
    id: int
    email: str
    full_name: str
    is_active: bool
    created_at: str
    updated_at: str
    roles: List[str]

class RoleCreate(BaseModel):
    name: str
    description: Optional[str] = None

class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class RoleRead(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_at: str
    updated_at: str
    permissions: List[str]
    user_count: int

class PermissionRead(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_at: str

class UserRoleAssignment(BaseModel):
    user_id: int
    role_id: int

class RolePermissionAssignment(BaseModel):
    role_id: int
    permission_id: int

# User Management Endpoints
@router.get("/users", response_model=List[UserRead], dependencies=[Depends(require_permissions(["settings.manage"]))])
def list_users(
    db: Session = Depends(get_tenant_db),
    user_id: int = Depends(get_current_user_id),
    q: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    status: Optional[str] = Query(None)
):
    """List all users with their roles and permissions."""
    # Check if user is a Super Administrator
    super_admin_check = db.execute(
        text("""
            SELECT COUNT(*) FROM user_roles ur
            JOIN roles r ON ur.role_id = r.id
            WHERE ur.user_id = :user_id AND r.name = 'Super Administrator'
        """),
        {"user_id": user_id}
    ).scalar()
    
    if super_admin_check == 0:
        raise HTTPException(
            status_code=403, 
            detail="Access denied. Only Super Administrators can access user management."
        )
    
    query = """
        SELECT u.id, u.email, u.full_name, u.is_active, u.created_at, u.updated_at,
               STRING_AGG(r.name, ', ') as roles
        FROM users u
        LEFT JOIN user_roles ur ON u.id = ur.user_id
        LEFT JOIN roles r ON ur.role_id = r.id
        WHERE 1=1
    """
    params = {}
    
    if q:
        query += " AND (LOWER(u.email) LIKE :q OR LOWER(u.full_name) LIKE :q)"
        params["q"] = f"%{q.lower()}%"
    
    if role:
        query += " AND r.name = :role"
        params["role"] = role
    
    if status:
        if status == "active":
            query += " AND u.is_active = true"
        elif status == "inactive":
            query += " AND u.is_active = false"
    
    query += " GROUP BY u.id, u.email, u.full_name, u.is_active, u.created_at, u.updated_at"
    query += " ORDER BY u.created_at DESC"
    
    rows = db.execute(text(query), params).mappings().all()
    
    # Convert to UserRead format
    users = []
    for row in rows:
        roles_list = row.roles.split(', ') if row.roles else []
        users.append(UserRead(
            id=row.id,
            email=row.email,
            full_name=row.full_name or "Unknown User",  # Provide default if None
            is_active=row.is_active,
            created_at=str(row.created_at),
            updated_at=str(row.updated_at),
            roles=roles_list
        ))
    
    return users

@router.post("/users", response_model=UserRead, dependencies=[Depends(require_permissions(["settings.manage"]))])
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_tenant_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """Create a new user."""
    # Check if user is a Super Administrator
    super_admin_check = db.execute(
        text("""
            SELECT COUNT(*) FROM user_roles ur
            JOIN roles r ON ur.role_id = r.id
            WHERE ur.user_id = :user_id AND r.name = 'Super Administrator'
        """),
        {"user_id": current_user_id}
    ).scalar()
    
    if super_admin_check == 0:
        raise HTTPException(
            status_code=403, 
            detail="Access denied. Only Super Administrators can create users."
        )
    
    from app.services.security import hash_password
    
    # Check if user already exists
    existing = db.execute(text("SELECT id FROM users WHERE email = :email"), {"email": user_data.email}).scalar()
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    # Create user
    hashed_password = hash_password(user_data.password)
    result = db.execute(
        text("""
            INSERT INTO users(email, full_name, hashed_password, is_active)
            VALUES (:email, :full_name, :password, :is_active)
            RETURNING id, email, full_name, is_active, created_at, updated_at
        """),
        {
            "email": user_data.email,
            "full_name": user_data.full_name,
            "password": hashed_password,
            "is_active": user_data.is_active
        }
    )
    
    new_user = result.mappings().first()
    db.commit()
    
    return UserRead(
        id=new_user.id,
        email=new_user.email,
        full_name=new_user.full_name,
        is_active=new_user.is_active,
        created_at=str(new_user.created_at),
        updated_at=str(new_user.updated_at),
        roles=[]
    )

@router.put("/users/{user_id}", response_model=UserRead, dependencies=[Depends(require_permissions(["settings.manage"]))])
def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_tenant_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """Update an existing user."""
    # Check if user exists
    existing = db.execute(text("SELECT id FROM users WHERE id = :id"), {"id": user_id}).scalar()
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if user is a Super Administrator
    super_admin_check = db.execute(
        text("""
            SELECT COUNT(*) FROM user_roles ur
            JOIN roles r ON ur.role_id = r.id
            WHERE ur.user_id = :user_id AND r.name = 'Super Administrator'
        """),
        {"user_id": current_user_id}
    ).scalar()
    
    if super_admin_check == 0:
        raise HTTPException(
            status_code=403, 
            detail="Access denied. Only Super Administrators can update users."
        )

    # Build update query
    update_fields = []
    params = {"id": user_id}
    
    if user_data.email is not None:
        # Check if email is already taken by another user
        email_exists = db.execute(
            text("SELECT id FROM users WHERE email = :email AND id != :id"),
            {"email": user_data.email, "id": user_id}
        ).scalar()
        if email_exists:
            raise HTTPException(status_code=400, detail="Email already taken by another user")
        
        update_fields.append("email = :email")
        params["email"] = user_data.email
    
    if user_data.full_name is not None:
        update_fields.append("full_name = :full_name")
        params["full_name"] = user_data.full_name
    
    if user_data.is_active is not None:
        update_fields.append("is_active = :is_active")
        params["is_active"] = user_data.is_active
    
    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    update_fields.append("updated_at = CURRENT_TIMESTAMP")
    query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = :id"
    
    db.execute(text(query), params)
    
    # Get updated user
    updated_user = db.execute(
        text("SELECT id, email, full_name, is_active, created_at, updated_at FROM users WHERE id = :id"),
        {"id": user_id}
    ).mappings().first()
    
    # Get user roles
    roles = db.execute(
        text("SELECT r.name FROM roles r JOIN user_roles ur ON r.id = ur.role_id WHERE ur.user_id = :user_id"),
        {"user_id": user_id}
    ).scalars().all()
    
    db.commit()
    
    return UserRead(
        id=updated_user.id,
        email=updated_user.email,
        full_name=updated_user.full_name,
        is_active=updated_user.is_active,
        created_at=str(updated_user.created_at),
        updated_at=str(updated_user.updated_at),
        roles=list(roles)
    )

@router.delete("/users/{user_id}", dependencies=[Depends(require_permissions(["settings.manage"]))])
def delete_user(
    user_id: int,
    db: Session = Depends(get_tenant_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """Delete a user."""
    # Prevent self-deletion
    if user_id == current_user_id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    # Check if user exists
    existing = db.execute(text("SELECT id FROM users WHERE id = :id"), {"id": user_id}).scalar()
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if user is a Super Administrator
    super_admin_check = db.execute(
        text("""
            SELECT COUNT(*) FROM user_roles ur
            JOIN roles r ON ur.role_id = r.id
            WHERE ur.user_id = :user_id AND r.name = 'Super Administrator'
        """),
        {"user_id": current_user_id}
    ).scalar()
    
    if super_admin_check == 0:
        raise HTTPException(
            status_code=403, 
            detail="Access denied. Only Super Administrators can delete users."
        )

    # Delete user roles first
    db.execute(text("DELETE FROM user_roles WHERE user_id = :id"), {"id": user_id})
    
    # Delete user
    db.execute(text("DELETE FROM users WHERE id = :id"), {"id": user_id})
    db.commit()
    
    return {"message": "User deleted successfully"}

# Role Management Endpoints
@router.get("/roles", response_model=List[RoleRead], dependencies=[Depends(require_permissions(["settings.manage"]))])
def list_roles(
    db: Session = Depends(get_tenant_db),
    user_id: int = Depends(get_current_user_id)
):
    """List all roles with their permissions and user counts."""
    # Check if user is a Super Administrator
    super_admin_check = db.execute(
        text("""
            SELECT COUNT(*) FROM user_roles ur
            JOIN roles r ON ur.role_id = r.id
            WHERE ur.user_id = :user_id AND r.name = 'Super Administrator'
        """),
        {"user_id": user_id}
    ).scalar()
    
    if super_admin_check == 0:
        raise HTTPException(
            status_code=403, 
            detail="Access denied. Only Super Administrators can access role management."
        )
    
    query = """
        SELECT r.id, r.name, r.description, r.created_at, r.updated_at,
               STRING_AGG(p.name, ', ') as permissions,
               COUNT(DISTINCT ur.user_id) as user_count
        FROM roles r
        LEFT JOIN role_permissions rp ON r.id = rp.role_id
        LEFT JOIN permissions p ON rp.permission_id = p.id
        LEFT JOIN user_roles ur ON r.id = ur.role_id
        GROUP BY r.id, r.name, r.description, r.created_at, r.updated_at
        ORDER BY r.name
    """
    
    rows = db.execute(text(query)).mappings().all()
    
    roles = []
    for row in rows:
        permissions_list = row.permissions.split(', ') if row.permissions else []
        roles.append(RoleRead(
            id=row.id,
            name=row.name,
            description=row.description,
            created_at=str(row.created_at),
            updated_at=str(row.updated_at),
            permissions=permissions_list,
            user_count=row.user_count
        ))
    
    return roles

@router.post("/roles", response_model=RoleRead, dependencies=[Depends(require_permissions(["settings.manage"]))])
def create_role(
    role_data: RoleCreate,
    db: Session = Depends(get_tenant_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """Create a new role."""
    # Check if user is a Super Administrator
    super_admin_check = db.execute(
        text("""
            SELECT COUNT(*) FROM user_roles ur
            JOIN roles r ON ur.role_id = r.id
            WHERE ur.user_id = :user_id AND r.name = 'Super Administrator'
        """),
        {"user_id": current_user_id}
    ).scalar()
    
    if super_admin_check == 0:
        raise HTTPException(
            status_code=403, 
            detail="Access denied. Only Super Administrators can create roles."
        )
    
    # Check if role already exists
    existing = db.execute(text("SELECT id FROM roles WHERE name = :name"), {"name": role_data.name}).scalar()
    if existing:
        raise HTTPException(status_code=400, detail="Role with this name already exists")
    
    # Create role
    result = db.execute(
        text("""
            INSERT INTO roles(name, description)
            VALUES (:name, :description)
            RETURNING id, name, description, created_at, updated_at
        """),
        {
            "name": role_data.name,
            "description": role_data.description
        }
    )
    
    new_role = result.mappings().first()
    db.commit()
    
    return RoleRead(
        id=new_role.id,
        name=new_role.name,
        description=new_role.description,
        created_at=str(new_role.created_at),
        updated_at=str(new_role.updated_at),
        permissions=[],
        user_count=0
    )

@router.put("/roles/{role_id}", response_model=RoleRead, dependencies=[Depends(require_permissions(["settings.manage"]))])
def update_role(
    role_id: int,
    role_data: RoleUpdate,
    db: Session = Depends(get_tenant_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """Update an existing role."""
    # Check if role exists
    existing = db.execute(text("SELECT id FROM roles WHERE id = :id"), {"id": role_id}).scalar()
    if not existing:
        raise HTTPException(status_code=404, detail="Role not found")
    
    # Build update query
    update_fields = []
    params = {"id": role_id}
    
    if role_data.name is not None:
        # Check if name is already taken by another role
        name_exists = db.execute(
            text("SELECT id FROM roles WHERE name = :name AND id != :id"),
            {"name": role_data.name, "id": role_id}
        ).scalar()
        if name_exists:
            raise HTTPException(status_code=400, detail="Role name already taken")
        
        update_fields.append("name = :name")
        params["name"] = role_data.name
    
    if role_data.description is not None:
        update_fields.append("description = :description")
        params["description"] = role_data.description
    
    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    update_fields.append("updated_at = CURRENT_TIMESTAMP")
    query = f"UPDATE roles SET {', '.join(update_fields)} WHERE id = :id"
    
    db.execute(text(query), params)
    
    # Get updated role
    updated_role = db.execute(
        text("SELECT id, name, description, created_at, updated_at FROM roles WHERE id = :id"),
        {"id": role_id}
    ).mappings().first()
    
    # Get role permissions
    permissions = db.execute(
        text("SELECT p.name FROM permissions p JOIN role_permissions rp ON p.id = rp.permission_id WHERE rp.role_id = :role_id"),
        {"role_id": role_id}
    ).scalars().all()
    
    # Get user count
    user_count = db.execute(
        text("SELECT COUNT(*) FROM user_roles WHERE role_id = :role_id"),
        {"role_id": role_id}
    ).scalar()
    
    db.commit()
    
    return RoleRead(
        id=updated_role.id,
        name=updated_role.name,
        description=updated_role.description,
        created_at=str(updated_role.created_at),
        updated_at=str(updated_role.updated_at),
        permissions=list(permissions),
        user_count=user_count
    )

@router.delete("/roles/{role_id}", dependencies=[Depends(require_permissions(["settings.manage"]))])
def delete_role(
    role_id: int,
    db: Session = Depends(get_tenant_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """Delete a role."""
    # Check if role exists
    existing = db.execute(text("SELECT id FROM roles WHERE id = :id"), {"id": role_id}).scalar()
    if not existing:
        raise HTTPException(status_code=404, detail="Role not found")
    
    # Check if role is assigned to any users
    user_count = db.execute(
        text("SELECT COUNT(*) FROM user_roles WHERE role_id = :id"),
        {"id": role_id}
    ).scalar()
    
    if user_count > 0:
        raise HTTPException(status_code=400, detail=f"Cannot delete role. It is assigned to {user_count} user(s)")
    
    # Delete role permissions first
    db.execute(text("DELETE FROM role_permissions WHERE role_id = :id"), {"id": role_id})
    
    # Delete role
    db.execute(text("DELETE FROM roles WHERE id = :id"), {"id": role_id})
    db.commit()
    
    return {"message": "Role deleted successfully"}

# Permission Management Endpoints
@router.get("/permissions", response_model=List[PermissionRead], dependencies=[Depends(require_permissions(["settings.manage"]))])
def list_permissions(
    db: Session = Depends(get_tenant_db),
    user_id: int = Depends(get_current_user_id)
):
    """List all available permissions."""
    # Check if user is a Super Administrator
    super_admin_check = db.execute(
        text("""
            SELECT COUNT(*) FROM user_roles ur
            JOIN roles r ON ur.role_id = r.id
            WHERE ur.user_id = :user_id AND r.name = 'Super Administrator'
        """),
        {"user_id": user_id}
    ).scalar()
    
    if super_admin_check == 0:
        raise HTTPException(
            status_code=403, 
            detail="Access denied. Only Super Administrators can access permission management."
        )
    
    query = """
        SELECT id, name, description, created_at
        FROM permissions
        ORDER BY name
    """
    
    rows = db.execute(text(query)).mappings().all()
    
    permissions = []
    for row in rows:
        permissions.append(PermissionRead(
            id=row.id,
            name=row.name,
            description=row.description,
            created_at=str(row.created_at)
        ))
    
    return permissions

# User-Role Assignment Endpoints
@router.post("/users/{user_id}/roles", dependencies=[Depends(require_permissions(["settings.manage"]))])
def assign_role_to_user(
    user_id: int,
    assignment: UserRoleAssignment,
    db: Session = Depends(get_tenant_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """Assign a role to a user."""
    # Check if user exists
    user_exists = db.execute(text("SELECT id FROM users WHERE id = :id"), {"id": user_id}).scalar()
    if not user_exists:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if role exists
    role_exists = db.execute(text("SELECT id FROM roles WHERE id = :id"), {"id": assignment.role_id}).scalar()
    if not role_exists:
        raise HTTPException(status_code=404, detail="Role not found")
    
    # Check if assignment already exists
    existing = db.execute(
        text("SELECT id FROM user_roles WHERE user_id = :user_id AND role_id = :role_id"),
        {"user_id": user_id, "role_id": assignment.role_id}
    ).scalar()
    
    if existing:
        raise HTTPException(status_code=400, detail="User already has this role")
    
    # Create assignment
    db.execute(
        text("INSERT INTO user_roles(user_id, role_id) VALUES (:user_id, :role_id)"),
        {"user_id": user_id, "role_id": assignment.role_id}
    )
    
    db.commit()
    return {"message": "Role assigned successfully"}

@router.delete("/users/{user_id}/roles/{role_id}", dependencies=[Depends(require_permissions(["settings.manage"]))])
def remove_role_from_user(
    user_id: int,
    role_id: int,
    db: Session = Depends(get_tenant_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """Remove a role from a user."""
    # Check if assignment exists
    existing = db.execute(
        text("SELECT id FROM user_roles WHERE user_id = :user_id AND role_id = :role_id"),
        {"user_id": user_id, "role_id": role_id}
    ).scalar()
    
    if not existing:
        raise HTTPException(status_code=404, detail="Role assignment not found")
    
    # Remove assignment
    db.execute(
        text("DELETE FROM user_roles WHERE user_id = :user_id AND role_id = :role_id"),
        {"user_id": user_id, "role_id": role_id}
    )
    
    db.commit()
    return {"message": "Role removed successfully"}

# Role-Permission Assignment Endpoints
@router.post("/roles/{role_id}/permissions", dependencies=[Depends(require_permissions(["settings.manage"]))])
def assign_permission_to_role(
    role_id: int,
    assignment: RolePermissionAssignment,
    db: Session = Depends(get_tenant_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """Assign a permission to a role."""
    # Check if role exists
    role_exists = db.execute(text("SELECT id FROM roles WHERE id = :id"), {"id": role_id}).scalar()
    if not role_exists:
        raise HTTPException(status_code=404, detail="Role not found")
    
    # Check if permission exists
    permission_exists = db.execute(text("SELECT id FROM permissions WHERE id = :id"), {"id": assignment.permission_id}).scalar()
    if not permission_exists:
        raise HTTPException(status_code=404, detail="Permission not found")
    
    # Check if assignment already exists
    existing = db.execute(
        text("SELECT id FROM role_permissions WHERE role_id = :role_id AND permission_id = :permission_id"),
        {"role_id": role_id, "permission_id": assignment.permission_id}
    ).scalar()
    
    if existing:
        raise HTTPException(status_code=400, detail="Role already has this permission")
    
    # Create assignment
    db.execute(
        text("INSERT INTO role_permissions(role_id, permission_id) VALUES (:role_id, :permission_id)"),
        {"role_id": role_id, "permission_id": assignment.permission_id}
    )
    
    db.commit()
    return {"message": "Permission assigned successfully"}

@router.delete("/roles/{role_id}/permissions/{permission_id}", dependencies=[Depends(require_permissions(["settings.manage"]))])
def remove_permission_from_role(
    role_id: int,
    permission_id: int,
    db: Session = Depends(get_tenant_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """Remove a permission from a role."""
    # Check if assignment exists
    existing = db.execute(
        text("SELECT id FROM role_permissions WHERE role_id = :role_id AND permission_id = :permission_id"),
        {"role_id": role_id, "permission_id": permission_id}
    ).scalar()
    
    if not existing:
        raise HTTPException(status_code=404, detail="Permission assignment not found")
    
    # Remove assignment
    db.execute(
        text("DELETE FROM role_permissions WHERE role_id = :role_id AND permission_id = :permission_id"),
        {"role_id": role_id, "permission_id": permission_id}
    )
    
    db.commit()
    return {"message": "Permission removed successfully"}

# System Information Endpoint
@router.get("/system-info", dependencies=[Depends(require_permissions(["settings.manage"]))])
def get_system_info(
    db: Session = Depends(get_tenant_db),
    user_id: int = Depends(get_current_user_id)
):
    """Get system statistics and information."""
    # Check if user is a Super Administrator
    super_admin_check = db.execute(
        text("""
            SELECT COUNT(*) FROM user_roles ur
            JOIN roles r ON ur.role_id = r.id
            WHERE ur.user_id = :user_id AND r.name = 'Super Administrator'
        """),
        {"user_id": user_id}
    ).scalar()
    
    if super_admin_check == 0:
        raise HTTPException(
            status_code=403, 
            detail="Access denied. Only Super Administrators can access system information."
        )
    
    # Count users
    user_count = db.execute(text("SELECT COUNT(*) FROM users")).scalar()
    active_users = db.execute(text("SELECT COUNT(*) FROM users WHERE is_active = true")).scalar()
    
    # Count roles
    role_count = db.execute(text("SELECT COUNT(*) FROM roles")).scalar()
    
    # Count permissions
    permission_count = db.execute(text("SELECT COUNT(*) FROM permissions")).scalar()
    
    # Get recent activity (last 5 users created)
    recent_users = db.execute(
        text("SELECT email, full_name, created_at FROM users ORDER BY created_at DESC LIMIT 5")
    ).mappings().all()
    
    return {
        "statistics": {
            "total_users": user_count,
            "active_users": active_users,
            "total_roles": role_count,
            "total_permissions": permission_count
        },
        "recent_users": [
            {
                "email": user.email,
                "full_name": user.full_name,
                "created_at": str(user.created_at)
            }
            for user in recent_users
        ]
    }


# Super Admin Endpoints
@router.get("/super-admin/users", response_model=List[UserRead])
def super_admin_list_users(
    tenant: str = Query(..., description="Tenant slug"),
    q: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    status: Optional[str] = Query(None)
):
    """List all users in a specific tenant for super admin."""
    from app.db.session import SessionLocal
    
    db = SessionLocal()
    try:
        # Set search path to the specified tenant
        db.execute(text(f'SET LOCAL search_path TO "{tenant}", public'))
        
        query = """
            SELECT u.id, u.email, u.full_name, u.is_active, u.created_at, u.updated_at,
                   STRING_AGG(r.name, ', ') as roles
            FROM users u
            LEFT JOIN user_roles ur ON u.id = ur.user_id
            LEFT JOIN roles r ON ur.role_id = r.id
            WHERE 1=1
        """
        params = {}
        
        if q:
            query += " AND (LOWER(u.email) LIKE :q OR LOWER(u.full_name) LIKE :q)"
            params["q"] = f"%{q.lower()}%"
        
        if role:
            query += " AND r.name = :role"
            params["role"] = role
        
        if status:
            if status == "active":
                query += " AND u.is_active = true"
            elif status == "inactive":
                query += " AND u.is_active = false"
        
        query += " GROUP BY u.id, u.email, u.full_name, u.is_active, u.created_at, u.updated_at"
        query += " ORDER BY u.created_at DESC"
        
        rows = db.execute(text(query), params).mappings().all()
        
        # Convert to UserRead format
        users = []
        for row in rows:
            roles_list = row.roles.split(', ') if row.roles else []
            users.append(UserRead(
                id=row.id,
                email=row.email,
                full_name=row.full_name or "Unknown User",
                is_active=row.is_active,
                created_at=str(row.created_at),
                updated_at=str(row.updated_at),
                roles=roles_list
            ))
        
        return users
    finally:
        db.close()


@router.get("/super-admin/roles", response_model=List[RoleRead])
def super_admin_list_roles(
    tenant: str = Query(..., description="Tenant slug")
):
    """List all roles in a specific tenant for super admin."""
    from app.db.session import SessionLocal
    
    db = SessionLocal()
    try:
        # Set search path to the specified tenant
        db.execute(text(f'SET LOCAL search_path TO "{tenant}", public'))
        
        query = """
            SELECT r.id, r.name, r.description, r.created_at, r.updated_at,
                   STRING_AGG(p.name, ', ') as permissions,
                   COUNT(DISTINCT ur.user_id) as user_count
            FROM roles r
            LEFT JOIN role_permissions rp ON r.id = rp.role_id
            LEFT JOIN permissions p ON rp.permission_id = p.id
            LEFT JOIN user_roles ur ON r.id = ur.role_id
            GROUP BY r.id, r.name, r.description, r.created_at, r.updated_at
            ORDER BY r.name
        """
        
        rows = db.execute(text(query)).mappings().all()
        
        roles = []
        for row in rows:
            permissions_list = row.permissions.split(', ') if row.permissions else []
            roles.append(RoleRead(
                id=row.id,
                name=row.name,
                description=row.description,
                created_at=str(row.created_at),
                updated_at=str(row.updated_at),
                permissions=permissions_list,
                user_count=row.user_count
            ))
        
        return roles
    finally:
        db.close()


@router.get("/super-admin/permissions", response_model=List[PermissionRead])
def super_admin_list_permissions(
    tenant: str = Query(..., description="Tenant slug")
):
    """List all permissions in a specific tenant for super admin."""
    from app.db.session import SessionLocal
    
    db = SessionLocal()
    try:
        # Set search path to the specified tenant
        db.execute(text(f'SET LOCAL search_path TO "{tenant}", public'))
        
        query = """
            SELECT id, name, description, created_at
            FROM permissions
            ORDER BY name
        """
        
        rows = db.execute(text(query)).mappings().all()
        
        permissions = []
        for row in rows:
            permissions.append(PermissionRead(
                id=row.id,
                name=row.name,
                description=row.description,
                created_at=str(row.created_at)
            ))
        
        return permissions
    finally:
        db.close()


@router.get("/super-admin/system-info")
def super_admin_system_info():
    """Get system statistics across all tenants for super admin."""
    from app.db.session import SessionLocal
    
    db = SessionLocal()
    try:
        tenants = db.execute(text("SELECT id, name, slug FROM tenants ORDER BY id")).mappings().all()
        
        total_stats = {
            "total_users": 0,
            "active_users": 0,
            "total_roles": 0,
            "total_permissions": 0,
            "total_tenants": len(tenants)
        }
        
        tenant_details = []
        
        for tenant in tenants:
            # Set search path to this tenant
            db.execute(text(f'SET LOCAL search_path TO "{tenant.slug}", public'))
            
            # Get tenant statistics
            user_count = db.execute(text("SELECT COUNT(*) FROM users")).scalar() or 0
            active_users = db.execute(text("SELECT COUNT(*) FROM users WHERE is_active = true")).scalar() or 0
            role_count = db.execute(text("SELECT COUNT(*) FROM roles")).scalar() or 0
            permission_count = db.execute(text("SELECT COUNT(*) FROM permissions")).scalar() or 0
            
            total_stats["total_users"] += user_count
            total_stats["active_users"] += active_users
            total_stats["total_roles"] += role_count
            total_stats["total_permissions"] += permission_count
            
            tenant_details.append({
                "id": tenant.id,
                "name": tenant.name,
                "slug": tenant.slug,
                "users": user_count,
                "active_users": active_users,
                "roles": role_count,
                "permissions": permission_count
            })
        
        return {
            "statistics": total_stats,
            "tenants": tenant_details
        }
    finally:
        db.close()


# Tenant-Specific Settings Endpoints (for regular users)
@router.get("/tenant/users", response_model=List[UserRead], dependencies=[Depends(require_permissions(["settings.manage"]))])
def list_tenant_users(
    db: Session = Depends(get_tenant_db),
    user_id: int = Depends(get_current_user_id),
    q: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    status: Optional[str] = Query(None)
):
    """List users in the current tenant (for regular users)."""
    query = """
        SELECT u.id, u.email, u.full_name, u.is_active, u.created_at, u.updated_at,
               STRING_AGG(r.name, ', ') as roles
        FROM users u
        LEFT JOIN user_roles ur ON u.id = ur.user_id
        LEFT JOIN roles r ON ur.role_id = r.id
        WHERE 1=1
    """
    params = {}
    
    if q:
        query += " AND (LOWER(u.email) LIKE :q OR LOWER(u.full_name) LIKE :q)"
        params["q"] = f"%{q.lower()}%"
    
    if role:
        query += " AND r.name = :role"
        params["role"] = role
    
    if status:
        if status == "active":
            query += " AND u.is_active = true"
        elif status == "inactive":
            query += " AND u.is_active = false"
    
    query += " GROUP BY u.id, u.email, u.full_name, u.is_active, u.created_at, u.updated_at"
    query += " ORDER BY u.created_at DESC"
    
    rows = db.execute(text(query), params).mappings().all()
    
    # Convert to UserRead format
    users = []
    for row in rows:
        roles_list = row.roles.split(', ') if row.roles else []
        users.append(UserRead(
            id=row.id,
            email=row.email,
            full_name=row.full_name or "Unknown User",
            is_active=row.is_active,
            created_at=str(row.created_at),
            updated_at=str(row.updated_at),
            roles=roles_list
        ))
    
    return users


@router.get("/tenant/roles", response_model=List[RoleRead], dependencies=[Depends(require_permissions(["settings.manage"]))])
def list_tenant_roles(
    db: Session = Depends(get_tenant_db),
    user_id: int = Depends(get_current_user_id)
):
    """List roles in the current tenant (for regular users)."""
    query = """
        SELECT r.id, r.name, r.description, r.created_at, r.updated_at,
               STRING_AGG(p.name, ', ') as permissions,
               COUNT(DISTINCT ur.user_id) as user_count
        FROM roles r
        LEFT JOIN role_permissions rp ON r.id = rp.role_id
        LEFT JOIN permissions p ON rp.permission_id = p.id
        LEFT JOIN user_roles ur ON r.id = ur.role_id
        GROUP BY r.id, r.name, r.description, r.created_at, r.updated_at
        ORDER BY r.name
    """
    
    rows = db.execute(text(query)).mappings().all()
    
    roles = []
    for row in rows:
        permissions_list = row.permissions.split(', ') if row.permissions else []
        roles.append(RoleRead(
            id=row.id,
            name=row.name,
            description=row.description,
            created_at=str(row.created_at),
            updated_at=str(row.updated_at),
            permissions=permissions_list,
            user_count=row.user_count
        ))
    
    return roles


@router.get("/tenant/permissions", response_model=List[PermissionRead], dependencies=[Depends(require_permissions(["settings.manage"]))])
def list_tenant_permissions(
    db: Session = Depends(get_tenant_db),
    user_id: int = Depends(get_current_user_id)
):
    """List permissions in the current tenant (for regular users)."""
    query = """
        SELECT id, name, description, created_at
        FROM permissions
        ORDER BY name
    """
    
    rows = db.execute(text(query)).mappings().all()
    
    permissions = []
    for row in rows:
        permissions.append(PermissionRead(
            id=row.id,
            name=row.name,
            description=row.description,
            created_at=str(row.created_at)
        ))
    
    return permissions


@router.get("/tenant/system-info", dependencies=[Depends(require_permissions(["settings.manage"]))])
def get_tenant_system_info(
    db: Session = Depends(get_tenant_db),
    user_id: int = Depends(get_current_user_id)
):
    """Get tenant-specific system statistics and information."""
    # Count users in current tenant
    user_count = db.execute(text("SELECT COUNT(*) FROM users")).scalar()
    active_users = db.execute(text("SELECT COUNT(*) FROM users WHERE is_active = true")).scalar()
    
    # Count roles in current tenant
    role_count = db.execute(text("SELECT COUNT(*) FROM roles")).scalar()
    
    # Count permissions in current tenant
    permission_count = db.execute(text("SELECT COUNT(*) FROM permissions")).scalar()
    
    # Get recent activity (last 5 users created)
    recent_users = db.execute(
        text("SELECT email, full_name, created_at FROM users ORDER BY created_at DESC LIMIT 5")
    ).mappings().all()
    
    return {
        "statistics": {
            "total_users": user_count,
            "active_users": active_users,
            "total_roles": role_count,
            "total_permissions": permission_count
        },
        "recent_users": [
            {
                "email": user.email,
                "full_name": user.full_name,
                "created_at": str(user.created_at)
            }
            for user in recent_users
        ]
    }

