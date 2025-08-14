import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import text


class TestInvoiceManagement:
    """Test invoice management endpoints."""
    
    def test_list_invoices_empty(self, client: TestClient, auth_headers: dict):
        """Test listing invoices when no invoices exist."""
        response = client.get("/api/finance/invoices", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_list_invoices_unauthorized_without_permission(self, client: TestClient, readonly_auth_headers: dict):
        """Users without finance.read should get 403."""
        response = client.get("/api/finance/invoices", headers=readonly_auth_headers)
        assert response.status_code in (401, 403)
    
    def test_create_invoice_success(self, client: TestClient, auth_headers: dict, test_student: dict):
        """Test creating a new invoice."""
        invoice_data = {
            "student_id": test_student["id"],
            "term": "Term 1",
            "amount": 50000.00,
            "currency": "MWK",
            "due_date": "2024-02-15"
        }
        
        response = client.post("/api/finance/invoices", json=invoice_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["student_id"] == invoice_data["student_id"]
        assert data["term"] == invoice_data["term"]
        assert data["amount"] == invoice_data["amount"]
        assert data["currency"] == invoice_data["currency"]
        assert data["due_date"] == invoice_data["due_date"]
        assert data["status"] == "pending"
        assert "id" in data
        # created_at not included in API response schema

    def test_create_invoice_forbidden_without_permission(self, client: TestClient, readonly_auth_headers: dict, test_student: dict):
        """Users without finance.write should not create invoices."""
        invoice_data = {
            "student_id": test_student["id"],
            "term": "Term 1",
            "amount": 50000.00,
            "currency": "MWK",
            "due_date": "2024-02-15"
        }
        response = client.post("/api/finance/invoices", json=invoice_data, headers=readonly_auth_headers)
        assert response.status_code in (401, 403)
    
    def test_create_invoice_invalid_student(self, client: TestClient, auth_headers: dict):
        """Test creating an invoice for non-existent student."""
        invoice_data = {
            "student_id": 99999,  # Non-existent student
            "term": "Term 1",
            "amount": 50000.00,
            "currency": "MWK"
        }
        
        response = client.post("/api/finance/invoices", json=invoice_data, headers=auth_headers)
        assert response.status_code == 400
        assert "FOREIGN KEY constraint failed" in response.json()["detail"]
    
    # No GET-by-id endpoint; validate created invoice shows up in listing
    def test_invoices_list_contains_created(self, client: TestClient, auth_headers: dict, test_student: dict):
        invoice_data = {
            "student_id": test_student["id"],
            "term": "Term X",
            "amount": 12345.00,
            "currency": "MWK"
        }
        client.post("/api/finance/invoices", json=invoice_data, headers=auth_headers)
        response = client.get("/api/finance/invoices", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert any(inv["term"] == "Term X" and inv["student_id"] == test_student["id"] for inv in data)
    
    def test_list_invoices_contains_multiple(self, client: TestClient, auth_headers: dict, test_student: dict):
        """API doesn't support filters; ensure multiple created invoices are returned and identifiable."""
        client.post("/api/finance/invoices", json={
            "student_id": test_student["id"],
            "term": "Term 1",
            "amount": 50000.00,
            "currency": "MWK"
        }, headers=auth_headers)
        client.post("/api/finance/invoices", json={
            "student_id": test_student["id"],
            "term": "Term 2",
            "amount": 60000.00,
            "currency": "MWK"
        }, headers=auth_headers)
        response = client.get("/api/finance/invoices", headers=auth_headers)
        assert response.status_code == 200
        terms = {inv["term"] for inv in response.json()}
        assert {"Term 1", "Term 2"}.issubset(terms)


class TestPaymentManagement:
    """Test payment management endpoints."""
    
    def test_list_payments_empty(self, client: TestClient, auth_headers: dict):
        """Test listing payments when no payments exist."""
        response = client.get("/api/finance/payments", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_list_payments_forbidden_without_permission(self, client: TestClient, readonly_auth_headers: dict):
        """Users without finance.read should not list payments."""
        response = client.get("/api/finance/payments", headers=readonly_auth_headers)
        assert response.status_code in (401, 403)
    
    def test_create_payment_success(self, client: TestClient, auth_headers: dict, test_student: dict):
        """Test creating a new payment."""
        # First create an invoice
        invoice_data = {
            "student_id": test_student["id"],
            "term": "Term 1",
            "amount": 50000.00,
            "currency": "MWK"
        }
        invoice_response = client.post("/api/finance/invoices", json=invoice_data, headers=auth_headers)
        invoice_id = invoice_response.json()["id"]
        
        # Then create a payment
        payment_data = {
            "invoice_id": invoice_id,
            "amount": 50000.00,
            "method": "mobile_money",
            "reference": "MM123456789"
        }
        
        response = client.post("/api/finance/payments", json=payment_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["invoice_id"] == payment_data["invoice_id"]
        assert data["amount"] == payment_data["amount"]
        assert data["method"] == payment_data["method"]
        assert data["reference"] == payment_data["reference"]
        assert "id" in data
        # created_at not included in API response schema

    def test_create_payment_forbidden_without_permission(self, client: TestClient, readonly_auth_headers: dict, test_student: dict):
        """Users without finance.write should not create payments."""
        invoice_data = {
            "student_id": test_student["id"],
            "term": "Term 1",
            "amount": 50000.00,
            "currency": "MWK"
        }
        # Attempt should fail early on POST /payments regardless of invoice presence
        response = client.post("/api/finance/payments", json={"invoice_id": 1, "amount": 1000, "method": "cash"}, headers=readonly_auth_headers)
        assert response.status_code in (401, 403)
    
    def test_create_payment_invalid_invoice(self, client: TestClient, auth_headers: dict):
        """Test creating a payment for non-existent invoice."""
        payment_data = {
            "invoice_id": 99999,  # Non-existent invoice
            "amount": 50000.00,
            "method": "mobile_money",
            "reference": "MM123456789"
        }
        
        response = client.post("/api/finance/payments", json=payment_data, headers=auth_headers)
        assert response.status_code == 400
        assert "FOREIGN KEY constraint failed" in response.json()["detail"]
    
    # No GET-by-id; ensure created payments appear in listing
    def test_payments_list_contains_created(self, client: TestClient, auth_headers: dict, test_student: dict):
        invoice_id = client.post("/api/finance/invoices", json={
            "student_id": test_student["id"],
            "term": "Term 1",
            "amount": 100000.00,
            "currency": "MWK"
        }, headers=auth_headers).json()["id"]
        client.post("/api/finance/payments", json={
            "invoice_id": invoice_id,
            "amount": 50000.00,
            "method": "mobile_money",
            "reference": "MM111111111"
        }, headers=auth_headers)
        response = client.get("/api/finance/payments", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert any(p["invoice_id"] == invoice_id and p["method"] == "mobile_money" for p in data)
    
    def test_list_payments_contains_multiple(self, client: TestClient, auth_headers: dict, test_student: dict):
        """API doesn't support filters; ensure multiple payments are present and identifiable."""
        invoice_id = client.post("/api/finance/invoices", json={
            "student_id": test_student["id"],
            "term": "Term 1",
            "amount": 100000.00,
            "currency": "MWK"
        }, headers=auth_headers).json()["id"]
        client.post("/api/finance/payments", json={
            "invoice_id": invoice_id,
            "amount": 50000.00,
            "method": "mobile_money",
            "reference": "MM111111111"
        }, headers=auth_headers)
        client.post("/api/finance/payments", json={
            "invoice_id": invoice_id,
            "amount": 50000.00,
            "method": "bank_transfer",
            "reference": "BT222222222"
        }, headers=auth_headers)
        response = client.get("/api/finance/payments", headers=auth_headers)
        assert response.status_code == 200
        methods = {p["method"] for p in response.json() if p["invoice_id"] == invoice_id}
        assert {"mobile_money", "bank_transfer"}.issubset(methods)


class TestFinanceValidation:
    """Test finance data validation."""
    
    def test_invoice_negative_amount(self, client: TestClient, auth_headers: dict, test_student: dict):
        """Test creating invoice with negative amount."""
        invoice_data = {
            "student_id": test_student["id"],
            "term": "Term 1",
            "amount": -1000.00,  # Negative amount
            "currency": "MWK"
        }
        
        response = client.post("/api/finance/invoices", json=invoice_data, headers=auth_headers)
        # This should still work as we don't have strict amount validation
        assert response.status_code == 200
    
    def test_payment_amount_exceeds_invoice(self, client: TestClient, auth_headers: dict, test_student: dict):
        """Test creating payment with amount exceeding invoice amount."""
        # Create invoice
        invoice_data = {
            "student_id": test_student["id"],
            "term": "Term 1",
            "amount": 50000.00,
            "currency": "MWK"
        }
        invoice_response = client.post("/api/finance/invoices", json=invoice_data, headers=auth_headers)
        invoice_id = invoice_response.json()["id"]
        
        # Create payment with higher amount
        payment_data = {
            "invoice_id": invoice_id,
            "amount": 60000.00,  # Higher than invoice amount
            "method": "mobile_money",
            "reference": "MM123456789"
        }
        
        response = client.post("/api/finance/payments", json=payment_data, headers=auth_headers)
        # This should still work as we don't have strict amount validation
        assert response.status_code == 200
    
    def test_invalid_currency(self, client: TestClient, auth_headers: dict, test_student: dict):
        """Test creating invoice with invalid currency."""
        invoice_data = {
            "student_id": test_student["id"],
            "term": "Term 1",
            "amount": 50000.00,
            "currency": "INVALID"  # Invalid currency
        }
        
        response = client.post("/api/finance/invoices", json=invoice_data, headers=auth_headers)
        # This should still work as we don't have strict currency validation
        assert response.status_code == 200
