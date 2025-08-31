"""
Test the full dependency chain of the parents/children endpoint
"""
from app.db.session import SessionLocal
from sqlalchemy import text
from app.core.config import settings
from jose import jwt
import datetime

def test_auth_chain():
    # Test the token we got earlier
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxNyIsImlhdCI6MTc1NjYzMDE5OSwiZXhwIjoxNzU2NjMzNzk5fQ.8ujzSWnqKT4hFfGXcBPU-XFLxmtytjXj3XewMn0Ewr0"
    
    try:
        # Decode token (same logic as get_current_user_id)
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id = int(payload.get("sub"))
        print(f"✅ Token decoded successfully, user_id: {user_id}")
        
        # Check expiration
        exp = payload.get("exp")
        if exp:
            exp_time = datetime.datetime.fromtimestamp(exp)
            current_time = datetime.datetime.utcnow()
            print(f"Token expires at: {exp_time}")
            print(f"Current time: {current_time}")
            print(f"Token expired? {current_time > exp_time}")
        
    except Exception as e:
        print(f"❌ Token decode error: {e}")
        return None
        
    return user_id

def test_role_check(user_id):
    session = SessionLocal()
    try:
        session.execute(text("SET search_path TO ndirande_high, public"))
        
        # Same query as require_roles
        rows = session.execute(
            text("""
                SELECT r.name FROM roles r
                JOIN user_roles ur ON ur.role_id = r.id
                WHERE ur.user_id = :uid
            """),
            {"uid": user_id},
        ).scalars().all()
        
        print(f"User roles: {rows}")
        required_roles = {"Parent"}
        user_roles = set(rows)
        has_permission = bool(user_roles.intersection(required_roles))
        print(f"Required roles: {required_roles}")
        print(f"User has permission: {has_permission}")
        
        return has_permission
        
    finally:
        session.close()

def test_children_query(user_id):
    session = SessionLocal()
    try:
        session.execute(text("SET search_path TO ndirande_high, public"))
        
        children = session.execute(text("""
            SELECT s.id, s.first_name, s.last_name, s.admission_no, c.name as class_name
            FROM parent_students ps
            JOIN students s ON ps.student_id = s.id
            LEFT JOIN classes c ON s.class_name = c.name
            WHERE ps.parent_user_id = :parent_id
            ORDER BY s.first_name, s.last_name
        """), {"parent_id": user_id}).mappings().all()
        
        print(f"Children found: {len(list(children))}")
        return len(list(children)) > 0
        
    finally:
        session.close()

if __name__ == "__main__":
    print("🔍 Testing full parents/children endpoint chain...")
    
    user_id = test_auth_chain()
    if user_id:
        print(f"\n1. ✅ Authentication successful")
        
        if test_role_check(user_id):
            print(f"2. ✅ Role check passed")
            
            if test_children_query(user_id):
                print(f"3. ✅ Children query successful")
                print(f"\n🎉 All checks passed! The endpoint should work.")
            else:
                print(f"3. ❌ No children found in query")
        else:
            print(f"2. ❌ Role check failed")
    else:
        print(f"1. ❌ Authentication failed")
