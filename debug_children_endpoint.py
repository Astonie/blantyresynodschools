"""
Test the exact same logic as the parents/children endpoint
"""
from app.db.session import SessionLocal
from app.tenancy.deps import get_tenant_db
from sqlalchemy.orm import Session
from sqlalchemy import text

# Import the exact same query logic
session = SessionLocal()
try:
    session.execute(text("SET search_path TO ndirande_high, public"))
    
    # James Phiri's user ID
    user_id = 17
    
    print(f"🔍 Testing parents/children endpoint logic for user_id: {user_id}")
    
    # Execute the exact same query from the endpoint
    children = session.execute(text("""
        SELECT s.id, s.first_name, s.last_name, s.admission_no, c.name as class_name
        FROM parent_students ps
        JOIN students s ON ps.student_id = s.id
        LEFT JOIN classes c ON s.class_name = c.name
        WHERE ps.parent_user_id = :parent_id
        ORDER BY s.first_name, s.last_name
    """), {"parent_id": user_id}).mappings().all()
    
    print(f"Raw query result: {list(children)}")
    
    if not children:
        print("❌ No children found - this would trigger HTTPException(404)")
    else:
        print(f"✅ Found {len(children)} children:")
        for child in children:
            print(f"  Child dict: {dict(child)}")
            
        # Test creating ChildInfo objects like the endpoint does
        try:
            from pydantic import BaseModel
            
            class ChildInfo(BaseModel):
                id: int
                first_name: str
                last_name: str
                admission_no: str
                class_name: str
            
            child_objects = [ChildInfo(**dict(child)) for child in children]
            print(f"✅ Successfully created {len(child_objects)} ChildInfo objects")
            for child_obj in child_objects:
                print(f"  {child_obj}")
                
        except Exception as e:
            print(f"❌ Error creating ChildInfo objects: {e}")
            
finally:
    session.close()
