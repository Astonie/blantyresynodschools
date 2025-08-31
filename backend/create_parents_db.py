#!/usr/bin/env python3
"""
Directly add parent users and relationships via database using the backend container
"""

import subprocess
import json

def create_parent_users_db():
    """Create parent users directly in the database"""
    
    sql_script = '''
SET search_path TO "ndirande_high", public;

-- Create parent users
INSERT INTO users (email, full_name, hashed_password, is_active, created_at, updated_at)
VALUES 
    ('mary.tembo@parent.ndirande-high.edu', 'Mary Tembo', '$2b$12$EixZxYaz.hwxg3BTrzQr4.KJOGinzaZPJRfuEBAfgEtXVhDr1rjSC', true, NOW(), NOW()),
    ('john.banda@parent.ndirande-high.edu', 'John Banda Sr.', '$2b$12$EixZxYaz.hwxg3BTrzQr4.KJOGinzaZPJRfuEBAfgEtXVhDr1rjSC', true, NOW(), NOW()),
    ('grace.mwale@parent.ndirande-high.edu', 'Grace Mwale', '$2b$12$EixZxYaz.hwxg3BTrzQr4.KJOGinzaZPJRfuEBAfgEtXVhDr1rjSC', true, NOW(), NOW())
ON CONFLICT (email) DO NOTHING;

-- Get Parent role ID
DO $$
DECLARE
    parent_role_id INTEGER;
    mary_user_id INTEGER;
    john_user_id INTEGER;
    grace_user_id INTEGER;
BEGIN
    SELECT id INTO parent_role_id FROM roles WHERE name = 'Parent';
    
    IF parent_role_id IS NOT NULL THEN
        -- Assign Parent role to users
        SELECT id INTO mary_user_id FROM users WHERE email = 'mary.tembo@parent.ndirande-high.edu';
        SELECT id INTO john_user_id FROM users WHERE email = 'john.banda@parent.ndirande-high.edu';
        SELECT id INTO grace_user_id FROM users WHERE email = 'grace.mwale@parent.ndirande-high.edu';
        
        IF mary_user_id IS NOT NULL THEN
            INSERT INTO user_roles (user_id, role_id) VALUES (mary_user_id, parent_role_id) ON CONFLICT DO NOTHING;
        END IF;
        
        IF john_user_id IS NOT NULL THEN
            INSERT INTO user_roles (user_id, role_id) VALUES (john_user_id, parent_role_id) ON CONFLICT DO NOTHING;
        END IF;
        
        IF grace_user_id IS NOT NULL THEN
            INSERT INTO user_roles (user_id, role_id) VALUES (grace_user_id, parent_role_id) ON CONFLICT DO NOTHING;
        END IF;
    END IF;
END $$;

-- Create parent-student relationships
INSERT INTO parent_students (parent_user_id, student_id)
SELECT u.id, s.id 
FROM users u, students s 
WHERE u.email = 'mary.tembo@parent.ndirande-high.edu' 
AND s.first_name = 'Hope' AND s.last_name = 'Tembo'
ON CONFLICT DO NOTHING;

INSERT INTO parent_students (parent_user_id, student_id)
SELECT u.id, s.id 
FROM users u, students s 
WHERE u.email = 'john.banda@parent.ndirande-high.edu' 
AND s.first_name = 'John' AND s.last_name = 'Banda'
ON CONFLICT DO NOTHING;

INSERT INTO parent_students (parent_user_id, student_id)
SELECT u.id, s.id 
FROM users u, students s 
WHERE u.email = 'grace.mwale@parent.ndirande-high.edu' 
AND s.first_name = 'Joseph' AND s.last_name = 'Mwale'
ON CONFLICT DO NOTHING;

-- Show created parents and their children
SELECT 
    u.email, 
    u.full_name as parent_name,
    s.first_name || ' ' || s.last_name as child_name,
    s.admission_no,
    s.class_name
FROM users u
JOIN parent_students ps ON u.id = ps.parent_user_id
JOIN students s ON ps.student_id = s.id
WHERE u.email LIKE '%@parent.ndirande-high.edu'
ORDER BY u.email;
'''
    
    print("=== Creating Parent Users in Database ===")
    
    try:
        # Execute SQL in the backend container
        result = subprocess.run([
            'docker', 'exec', '-i', 'ccapsynod-backend', 
            'psql', 'postgresql://admin:admin123@localhost:5432/synod_schools',
            '-c', sql_script
        ], capture_output=True, text=True, check=True)
        
        print("✅ SQL executed successfully!")
        print("Output:")
        print(result.stdout)
        
        if result.stderr:
            print("Warnings/Errors:")
            print(result.stderr)
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Error executing SQL: {e}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
    except FileNotFoundError:
        print("❌ Docker not found. Make sure Docker is installed and running.")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    create_parent_users_db()
