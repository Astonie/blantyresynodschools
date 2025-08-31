#!/usr/bin/env python3

import subprocess
import tempfile
import os

def create_parents_via_docker():
    """Create parent users by executing SQL directly in the backend container"""
    
    sql_commands = [
        'SET search_path TO "ndirande_high", public;',
        
        # Create parent users with bcrypt hashed password for "parent123"
        '''INSERT INTO users (email, full_name, hashed_password, is_active, created_at, updated_at)
        VALUES 
            ('mary.tembo@parent.ndirande-high.edu', 'Mary Tembo', '$2b$12$EixZxYaz.hwxg3BTrzQr4.KJOGinzaZPJRfuEBAfgEtXVhDr1rjSC', true, NOW(), NOW()),
            ('john.banda@parent.ndirande-high.edu', 'John Banda Sr.', '$2b$12$EixZxYaz.hwxg3BTrzQr4.KJOGinzaZPJRfuEBAfgEtXVhDr1rjSC', true, NOW(), NOW()),
            ('grace.mwale@parent.ndirande-high.edu', 'Grace Mwale', '$2b$12$EixZxYaz.hwxg3BTrzQr4.KJOGinzaZPJRfuEBAfgEtXVhDr1rjSC', true, NOW(), NOW())
        ON CONFLICT (email) DO NOTHING;''',
        
        # Assign Parent role
        '''DO $$ 
        DECLARE
            parent_role_id INTEGER;
            user_rec RECORD;
        BEGIN
            SELECT id INTO parent_role_id FROM roles WHERE name = 'Parent';
            
            IF parent_role_id IS NOT NULL THEN
                FOR user_rec IN 
                    SELECT id FROM users WHERE email LIKE '%@parent.ndirande-high.edu'
                LOOP
                    INSERT INTO user_roles (user_id, role_id) 
                    VALUES (user_rec.id, parent_role_id) 
                    ON CONFLICT DO NOTHING;
                END LOOP;
            END IF;
        END $$;''',
        
        # Create parent-student relationships
        '''INSERT INTO parent_students (parent_user_id, student_id)
        SELECT u.id, s.id 
        FROM users u, students s 
        WHERE u.email = 'mary.tembo@parent.ndirande-high.edu' 
        AND s.first_name = 'Hope' AND s.last_name = 'Tembo'
        ON CONFLICT DO NOTHING;''',
        
        '''INSERT INTO parent_students (parent_user_id, student_id)
        SELECT u.id, s.id 
        FROM users u, students s 
        WHERE u.email = 'john.banda@parent.ndirande-high.edu' 
        AND s.first_name = 'John' AND s.last_name = 'Banda'
        ON CONFLICT DO NOTHING;''',
        
        '''INSERT INTO parent_students (parent_user_id, student_id)
        SELECT u.id, s.id 
        FROM users u, students s 
        WHERE u.email = 'grace.mwale@parent.ndirande-high.edu' 
        AND s.first_name = 'Joseph' AND s.last_name = 'Mwale'
        ON CONFLICT DO NOTHING;''',
        
        # Show results
        '''SELECT 
            u.email, 
            u.full_name as parent_name,
            s.first_name || ' ' || s.last_name as child_name,
            s.admission_no,
            s.class_name
        FROM users u
        JOIN parent_students ps ON u.id = ps.parent_user_id
        JOIN students s ON ps.student_id = s.id
        WHERE u.email LIKE '%@parent.ndirande-high.edu'
        ORDER BY u.email;'''
    ]
    
    print("=== Creating Parent Users via Docker ===")
    
    try:
        # Create a temporary SQL file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as f:
            for cmd in sql_commands:
                f.write(cmd + '\n\n')
            temp_sql_file = f.name
        
        # Copy SQL file to container
        print("📋 Copying SQL script to container...")
        subprocess.run([
            'docker', 'cp', temp_sql_file, f'ccapsynod-backend:/tmp/create_parents.sql'
        ], check=True)
        
        # Execute SQL using python inside the container
        print("🐍 Executing SQL via Python in container...")
        python_script = '''
import os, sys
sys.path.append('/app')
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Use container's environment variables
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD") 
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")

DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

try:
    # Read and execute SQL file
    with open("/tmp/create_parents.sql", "r") as f:
        sql_content = f.read()
    
    # Split by semicolons and execute each statement
    statements = [stmt.strip() for stmt in sql_content.split(";") if stmt.strip()]
    
    for stmt in statements:
        if stmt.strip():
            session.execute(text(stmt))
    
    session.commit()
    print("✅ Parent users created successfully!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    session.rollback()
finally:
    session.close()
'''
        
        result = subprocess.run([
            'docker', 'exec', 'ccapsynod-backend', 
            'python', '-c', python_script
        ], capture_output=True, text=True, check=True)
        
        print("✅ Command executed successfully!")
        if result.stdout:
            print("Output:", result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
            
        # Clean up
        os.unlink(temp_sql_file)
        subprocess.run(['docker', 'exec', 'ccapsynod-backend', 'rm', '/tmp/create_parents.sql'], capture_output=True)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Docker command failed: {e}")
        print("STDOUT:", e.stdout if e.stdout else "None")
        print("STDERR:", e.stderr if e.stderr else "None")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    create_parents_via_docker()
