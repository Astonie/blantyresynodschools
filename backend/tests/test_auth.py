import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.services.security import hash_password, verify_password, create_access_token


class TestAuthentication:
    """Test authentication endpoints and functionality."""
    
    def test_health_endpoint(self, client: TestClient):
        """Test the health check endpoint."""
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
    
    def test_login_success(self, client: TestClient, test_user: dict):
        """Test successful login with valid credentials."""
        login_data = {
            "username": test_user["email"],
            "password": "testpassword123"
        }
        
        response = client.post("/api/auth/login", json=login_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self, client: TestClient):
        """Test login with invalid credentials."""
        login_data = {
            "username": "nonexistent@example.com",
            "password": "wrongpassword"
        }

        response = client.post("/api/auth/login", json=login_data)
        # The API returns 401 for invalid credentials
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]
    
    def test_login_inactive_user(self, client: TestClient, tenant_db_session: Session):
        """Test login with inactive user."""
        # Create an inactive user
        hashed_password = hash_password("testpassword123")
        tenant_db_session.execute(text("""
            INSERT INTO users(email, full_name, hashed_password, is_active)
            VALUES (:email, :name, :password, :active)
        """), {
            "email": "inactive@example.com",
            "name": "Inactive User",
            "password": hashed_password,
            "active": False
        })
        tenant_db_session.commit()

        login_data = {
            "username": "inactive@example.com",
            "password": "testpassword123"
        }

        response = client.post("/api/auth/login", json=login_data)
        # The API returns 403 for inactive users
        assert response.status_code == 403
        assert "Inactive user" in response.json()["detail"]
    
    def test_protected_endpoint_with_valid_token(self, client: TestClient, auth_headers: dict):
        """Test accessing protected endpoint with valid token."""
        response = client.get("/api/students", headers=auth_headers)
        assert response.status_code == 200
    
    def test_protected_endpoint_without_token(self, client: TestClient):
        """Test accessing protected endpoint without token."""
        response = client.get("/api/students")
        assert response.status_code == 401
        assert "Missing or invalid Authorization header" in response.json()["detail"]
    
    def test_protected_endpoint_with_invalid_token(self, client: TestClient):
        """Test accessing protected endpoint with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/students", headers=headers)
        assert response.status_code == 401
        assert "Invalid token" in response.json()["detail"]
    
    def test_password_hashing(self):
        """Test password hashing and verification."""
        password = "testpassword123"
        hashed = hash_password(password)
        
        # Verify the password
        assert verify_password(password, hashed) is True
        assert verify_password("wrongpassword", hashed) is False
    
    def test_token_creation(self, test_user: dict):
        """Test JWT token creation."""
        token = create_access_token(subject=str(test_user["id"]), extra={"tenant": "test_tenant"})
        
        assert isinstance(token, str)
        assert len(token) > 0


class TestTenantOnboarding:
    """Test tenant onboarding functionality."""
    
    def test_tenant_onboarding_success(self, client: TestClient):
        """Test successful tenant onboarding."""
        # Skip this test for SQLite as it requires PostgreSQL schemas
        import pytest
        pytest.skip("Tenant onboarding requires PostgreSQL schemas - skipping for SQLite tests")
        
        onboarding_data = {
            "name": "New Test School",
            "slug": "new-test-school",
            "admin_email": "admin@newschool.com",
            "admin_password": "adminpassword123"
        }

        response = client.post("/api/tenants/onboard", json=onboarding_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "id" in data
        assert data["name"] == onboarding_data["name"]
        assert data["slug"] == onboarding_data["slug"]
    
    def test_tenant_onboarding_duplicate_slug(self, client: TestClient, test_tenant: dict):
        """Test tenant onboarding with duplicate slug."""
        # Skip this test for SQLite as it requires PostgreSQL schemas
        import pytest
        pytest.skip("Tenant onboarding requires PostgreSQL schemas - skipping for SQLite tests")
        
        onboarding_data = {
            "name": "Another School",
            "slug": test_tenant["slug"],  # Use existing slug
            "admin_email": "admin@anotherschool.com",
            "admin_password": "adminpassword123"
        }
        
        response = client.post("/api/tenants/onboard", json=onboarding_data)
        assert response.status_code == 400
        assert "Tenant already exists" in response.json()["detail"]
    
    def test_tenant_onboarding_invalid_email(self, client: TestClient):
        """Test tenant onboarding with invalid email."""
        # Skip this test for SQLite as it requires PostgreSQL schemas
        import pytest
        pytest.skip("Tenant onboarding requires PostgreSQL schemas - skipping for SQLite tests")
        
        onboarding_data = {
            "name": "Invalid School",
            "slug": "invalid-school",
            "admin_email": "invalid-email",
            "admin_password": "adminpassword123"
        }
        
        response = client.post("/api/tenants/onboard", json=onboarding_data)
        assert response.status_code == 422  # Validation error
    
    def test_tenant_onboarding_missing_fields(self, client: TestClient):
        """Test tenant onboarding with missing required fields."""
        # Skip this test for SQLite as it requires PostgreSQL schemas
        import pytest
        pytest.skip("Tenant onboarding requires PostgreSQL schemas - skipping for SQLite tests")
        
        onboarding_data = {
            "name": "Incomplete School"
            # Missing slug, admin_email, admin_password
        }
        
        response = client.post("/api/tenants/onboard", json=onboarding_data)
        assert response.status_code == 422  # Validation error


class TestHQEndpoints:
    """Test HQ (Headquarters) endpoints."""
    
    def test_list_tenants(self, client: TestClient, test_tenant: dict):
        """Test listing all tenants."""
        response = client.get("/api/hq/tenants")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        # Check if our test tenant is in the list
        tenant_ids = [tenant["id"] for tenant in data]
        assert test_tenant["id"] in tenant_ids
