from app.db.session import SessionLocal
from sqlalchemy import text
from app.services.security import hash_password

db = SessionLocal()
try:
    db.execute(text('SET search_path TO ndirande_high, public'))
    
    # Update the password for Isaac's parent with proper bcrypt hashing
    new_password = "Parent123"
    hashed_password = hash_password(new_password)
    
    # Update the parent password
    result = db.execute(text("""
        UPDATE users 
        SET hashed_password = :password 
        WHERE email = 'parent.isaac.banda@parent.ndirande-high.edu'
    """), {"password": hashed_password})
    
    if result.rowcount > 0:
        print(f"✅ Updated password for parent.isaac.banda@parent.ndirande-high.edu")
        print(f"   New password: {new_password}")
        db.commit()
    else:
        print("❌ Parent not found")
        
finally:
    db.close()
