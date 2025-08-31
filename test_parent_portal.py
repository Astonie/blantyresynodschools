import requests
import json

# Test parent login and data access
API_BASE = "http://localhost:8000"

def test_parent_login():
    # Test login with a real parent account
    login_data = {
        "username": "parent.isaac.banda@parent.ndirande-high.edu",
        "password": "Parent123"
    }
    
    headers = {"X-Tenant": "ndirande-high", "Content-Type": "application/json"}
    
    print("🔐 Testing parent login...")
    response = requests.post(f"{API_BASE}/api/auth/login", json=login_data, headers=headers)
    
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data["access_token"]
        print("✅ Login successful!")
        
        # Test getting children data
        headers = {"Authorization": f"Bearer {access_token}", "X-Tenant": "ndirande-high"}
        children_response = requests.get(f"{API_BASE}/api/parents/children", headers=headers)
        
        if children_response.status_code == 200:
            children_data = children_response.json()
            print(f"👨‍👩‍👧‍👦 Children data retrieved successfully!")
            print(f"📊 Number of children: {len(children_data)}")
            
            for child in children_data:
                print(f"  👤 {child['first_name']} {child['last_name']} (ID: {child['id']})")
                
                # Get report card for this child
                report_response = requests.get(
                    f"{API_BASE}/api/parents/children/{child['id']}/report-card?academic_year=2024&term=Term 1 Final", 
                    headers=headers
                )
                
                if report_response.status_code == 200:
                    report_data = report_response.json()
                    subjects = report_data.get('subjects', [])
                    print(f"    📚 Academic records: {len(subjects)} subjects")
                    
                    # Show a sample of academic records
                    for i, subject in enumerate(subjects[:3]):
                        subject_name = subject.get('subject_name', 'Unknown')
                        overall_score = subject.get('overall_score', 0)
                        print(f"      📝 {subject_name}: Overall Score {overall_score}")
                    
                    if len(subjects) > 3:
                        print(f"      ... and {len(subjects) - 3} more subjects")
                        
                    # Show GPA
                    gpa = report_data.get('gpa', 0)
                    print(f"    🎓 Term GPA: {gpa}")
                else:
                    print(f"    ❌ Could not get report card: {report_response.status_code}")
                    if report_response.status_code != 404:
                        print(f"    Error: {report_response.text}")
        else:
            print(f"❌ Failed to get children data: {children_response.status_code}")
            print(children_response.text)
    else:
        print(f"❌ Login failed: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_parent_login()
