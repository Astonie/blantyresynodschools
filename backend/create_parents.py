#!/usr/bin/env python3
"""Create parent users and link them to students for testing parent portal"""

import requests
import json

def create_parent_users():
    base_url = "http://localhost:8000/api"
    
    # Login as admin first
    print("=== Logging in as administrator ===")
    
    admin_response = requests.post(f"{base_url}/auth/simple-login", json={
        "username": "admin@ndirande-high.edu", 
        "password": "admin123"
    })
    
    if admin_response.status_code != 200:
        print(f"❌ Admin login failed: {admin_response.text}")
        return
    
    admin_token = admin_response.json()['access_token']
    headers = {
        'Authorization': f'Bearer {admin_token}',
        'X-Tenant': 'ndirande-high',
        'Content-Type': 'application/json'
    }
    
    print("✅ Admin login successful!")
    
    # Get some students to link to parents
    print("\n=== Fetching students ===")
    students_response = requests.get(f"{base_url}/students", headers=headers)
    
    if students_response.status_code != 200:
        print(f"❌ Failed to get students: {students_response.text}")
        return
        
    students = students_response.json()
    print(f"Found {len(students)} students")
    
    if len(students) < 2:
        print("❌ Need at least 2 students to create parent relationships")
        return
        
    # Parent data to create
    parent_data = [
        {
            "email": "mary.tembo@parent.ndirande-high.edu",
            "full_name": "Mary Tembo", 
            "password": "parent123",
            "phone": "+265-1-234567",
            "children": [students[0]['id']]  # Hope Tembo's parent
        },
        {
            "email": "john.banda@parent.ndirande-high.edu", 
            "full_name": "John Banda Sr.",
            "password": "parent123", 
            "phone": "+265-1-234568",
            "children": [students[1]['id']]  # John Banda's parent
        }
    ]
    
    print(f"\n=== Creating parent users ===")
    
    for parent in parent_data:
        print(f"\nCreating parent: {parent['full_name']} ({parent['email']})")
        
        # Create user
        user_payload = {
            "email": parent['email'],
            "full_name": parent['full_name'],
            "password": parent['password'],
            "is_active": True,
            "role_names": ["Parent"]
        }
        
        create_response = requests.post(f"{base_url}/hq/users", headers=headers, json=user_payload)
        
        if create_response.status_code == 200:
            user_data = create_response.json()
            user_id = user_data['id']
            print(f"✅ User created with ID: {user_id}")
            
            # Create parent-student relationships
            for child_id in parent['children']:
                child_name = next((s['first_name'] + ' ' + s['last_name'] for s in students if s['id'] == child_id), f"Student {child_id}")
                
                relationship_payload = {
                    "parent_user_id": user_id,
                    "student_id": child_id
                }
                
                # We need to create this relationship directly via raw SQL since there's no endpoint
                print(f"  📝 Need to manually link {parent['full_name']} to {child_name} (ID: {child_id})")
                
        else:
            print(f"❌ Failed to create user: {create_response.text}")

def create_parent_student_links():
    """Create parent-student relationships directly"""
    print("\n=== Creating Parent-Student Links ===")
    print("NOTE: You'll need to run this SQL manually in the database:")
    print()
    
    sql_commands = [
        """
-- Link Mary Tembo to Hope Tembo (assuming user IDs)
INSERT INTO ndirande_high.parent_students (parent_user_id, student_id) 
SELECT u.id, s.id 
FROM ndirande_high.users u, ndirande_high.students s 
WHERE u.email = 'mary.tembo@parent.ndirande-high.edu' 
AND s.first_name = 'Hope' AND s.last_name = 'Tembo';

-- Link John Banda Sr. to John Banda
INSERT INTO ndirande_high.parent_students (parent_user_id, student_id)
SELECT u.id, s.id 
FROM ndirande_high.users u, ndirande_high.students s 
WHERE u.email = 'john.banda@parent.ndirande-high.edu' 
AND s.first_name = 'John' AND s.last_name = 'Banda';
        """.strip()
    ]
    
    for sql in sql_commands:
        print(sql)
        print()

if __name__ == "__main__":
    create_parent_users()
    create_parent_student_links()
