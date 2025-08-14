import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import text


class TestClassManagement:
    """Test class management endpoints."""
    
    def test_list_classes_empty(self, client: TestClient, auth_headers: dict):
        """Test listing classes when no classes exist."""
        response = client.get("/api/academic/classes", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_list_classes_forbidden_without_permission(self, client: TestClient, readonly_auth_headers: dict):
        """Users without academic.read should not list classes."""
        response = client.get("/api/academic/classes", headers=readonly_auth_headers)
        assert response.status_code in (401, 403)
    
    def test_create_class_success(self, client: TestClient, auth_headers: dict):
        """Test creating a new class."""
        class_data = {
            "name": "Form 2A",
            "grade_level": "Form 2",
            "capacity": 35,
            "academic_year": "2024"
        }
        
        response = client.post("/api/academic/classes", json=class_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == class_data["name"]
        assert data["grade_level"] == class_data["grade_level"]
        assert data["capacity"] == class_data["capacity"]
        assert data["academic_year"] == class_data["academic_year"]
    
    def test_get_class_success(self, client: TestClient, auth_headers: dict, test_class: dict):
        """Test getting a specific class."""
        response = client.get(f"/api/academic/classes/{test_class['id']}", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == test_class["id"]
        assert data["name"] == test_class["name"]


class TestSubjectManagement:
    """Test subject management endpoints."""
    
    def test_list_subjects_empty(self, client: TestClient, auth_headers: dict):
        """Test listing subjects when no subjects exist."""
        response = client.get("/api/academic/subjects", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []
    
    def test_create_subject_success(self, client: TestClient, auth_headers: dict):
        """Test creating a new subject."""
        subject_data = {
            "name": "English Language",
            "code": "ENG",
            "description": "English language and literature"
        }
        
        response = client.post("/api/academic/subjects", json=subject_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == subject_data["name"]
        assert data["code"] == subject_data["code"]
        assert data["description"] == subject_data["description"]

    def test_create_subject_forbidden_without_permission(self, client: TestClient, readonly_auth_headers: dict):
        """Users without settings.manage should not create subjects."""
        subject_data = {"name": "Chemistry", "code": "CHEM"}
        response = client.post("/api/academic/subjects", json=subject_data, headers=readonly_auth_headers)
        assert response.status_code in (401, 403)


class TestAttendanceManagement:
    """Test attendance management endpoints."""
    
    def test_create_attendance_success(self, client: TestClient, auth_headers: dict, test_student: dict, test_class: dict):
        """Test creating an attendance record."""
        attendance_data = {
            "student_id": test_student["id"],
            "class_id": test_class["id"],
            "date": "2024-01-15",
            "status": "present",
            "notes": "Student attended class"
        }
        
        response = client.post("/api/academic/attendance", json=attendance_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["student_id"] == attendance_data["student_id"]
        assert data["class_id"] == attendance_data["class_id"]
        assert data["date"] == attendance_data["date"]
        assert data["status"] == attendance_data["status"]

    def test_create_attendance_forbidden_without_permission(self, client: TestClient, readonly_auth_headers: dict, test_student: dict, test_class: dict):
        """Users without academic.attendance should not create attendance."""
        attendance_data = {"student_id": test_student["id"], "class_id": test_class["id"], "date": "2024-01-15", "status": "present"}
        response = client.post("/api/academic/attendance", json=attendance_data, headers=readonly_auth_headers)
        assert response.status_code in (401, 403)
    
    def test_list_attendance_with_filters(self, client: TestClient, auth_headers: dict, test_student: dict, test_class: dict):
        """Test listing attendance with various filters."""
        # First create an attendance record
        attendance_data = {
            "student_id": test_student["id"],
            "class_id": test_class["id"],
            "date": "2024-01-17",
            "status": "present"
        }
        client.post("/api/academic/attendance", json=attendance_data, headers=auth_headers)
        
        # Test filtering by class
        response = client.get(f"/api/academic/attendance?class_id={test_class['id']}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert all(record["class_id"] == test_class["id"] for record in data)


class TestAcademicRecords:
    """Test academic records endpoints."""
    
    def test_create_academic_record_success(self, client: TestClient, auth_headers: dict, test_student: dict, test_class: dict, test_subject: dict):
        """Test creating an academic record."""
        record_data = {
            "student_id": test_student["id"],
            "subject_id": test_subject["id"],
            "class_id": test_class["id"],
            "term": "Term 1",
            "academic_year": "2024",
            "score": 85.5,
            "grade": "A",
            "remarks": "Excellent performance"
        }
        
        response = client.post("/api/academic/academic-records", json=record_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["student_id"] == record_data["student_id"]
        assert data["subject_id"] == record_data["subject_id"]
        assert data["term"] == record_data["term"]
        assert data["score"] == record_data["score"]
        assert data["grade"] == record_data["grade"]

    def test_create_academic_record_forbidden_without_permission(self, client: TestClient, readonly_auth_headers: dict, test_student: dict, test_class: dict, test_subject: dict):
        record_data = {"student_id": test_student["id"], "subject_id": test_subject["id"], "class_id": test_class["id"], "term": "Term 1", "academic_year": "2024", "score": 75.0}
        response = client.post("/api/academic/academic-records", json=record_data, headers=readonly_auth_headers)
        assert response.status_code in (401, 403)
    
    def test_get_student_academic_summary(self, client: TestClient, auth_headers: dict, test_student: dict, test_class: dict, test_subject: dict):
        """Test getting student academic summary."""
        # First create an academic record
        record_data = {
            "student_id": test_student["id"],
            "subject_id": test_subject["id"],
            "class_id": test_class["id"],
            "term": "Term 1",
            "academic_year": "2024",
            "score": 85.5,
            "grade": "A"
        }
        client.post("/api/academic/academic-records", json=record_data, headers=auth_headers)
        
        # Get academic summary
        response = client.get(
            f"/api/academic/academic-summary/{test_student['id']}?term=Term 1&academic_year=2024",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["student_id"] == test_student["id"]
        assert data["term"] == "Term 1"
        assert data["academic_year"] == "2024"
        assert data["average_score"] == 85.5
        assert data["total_subjects"] == 1
