#!/usr/bin/env python3
"""
Test the fixed students API endpoint
"""
import requests

def test_students_api():
    print('🧪 TESTING STUDENTS API ENDPOINTS')
    print('=' * 50)
    
    # Login first
    print('\n1️⃣ Logging in...')
    login_response = requests.post('http://localhost:8000/api/auth/login', json={
        'email': 'admin@ndirande-high.edu',
        'password': 'admin123'
    })
    
    if login_response.status_code == 200:
        token = login_response.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        print('   ✅ Login successful')
        
        # Test students listing
        print('\n2️⃣ Testing students listing...')
        students_response = requests.get('http://localhost:8000/api/students', headers=headers)
        
        if students_response.status_code == 200:
            students = students_response.json()
            print(f'   ✅ Students API working! Found {len(students)} students')
            
            if students:
                print('\n📋 Sample student data:')
                sample = students[0]
                for key, value in sample.items():
                    print(f'   {key}: {value}')
                    
                # Test individual student lookup
                print(f'\n3️⃣ Testing individual student lookup (ID: {sample["id"]})...')
                single_response = requests.get(f'http://localhost:8000/api/students/{sample["id"]}', headers=headers)
                
                if single_response.status_code == 200:
                    print('   ✅ Individual student lookup working!')
                else:
                    print(f'   ❌ Individual student lookup failed: {single_response.status_code} - {single_response.text}')
            else:
                print('   ⚠️ No students found in database')
        else:
            print(f'   ❌ Students API failed: {students_response.status_code} - {students_response.text}')
    else:
        print(f'   ❌ Login failed: {login_response.status_code} - {login_response.text}')

if __name__ == "__main__":
    test_students_api()
