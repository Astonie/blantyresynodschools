from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.schemas.finance import InvoiceCreate, InvoiceRead, PaymentCreate, PaymentRead
from app.tenancy.deps import get_tenant_db
from app.api.deps import require_roles, require_permissions, get_current_user_id


router = APIRouter()


@router.get("/invoices", response_model=list[InvoiceRead], dependencies=[Depends(require_permissions(["finance.read"]))])
def list_invoices(db: Session = Depends(get_tenant_db), user_id: int = Depends(get_current_user_id)):
    rows = db.execute(text("SELECT id, student_id, term, currency, amount, status, due_date, issued_at FROM invoices ORDER BY id DESC")).mappings().all()
    return [InvoiceRead(**dict(r)) for r in rows]


@router.post("/invoices", response_model=InvoiceRead, dependencies=[Depends(require_permissions(["finance.write"]))])
def create_invoice(payload: InvoiceCreate, db: Session = Depends(get_tenant_db)):
    try:
        db.execute(
            text(
                """
                INSERT INTO invoices(student_id, term, currency, amount, due_date, issued_at)
                VALUES (:sid, :t, :c, :a, :d, :i)
                """
            ),
            {
                "sid": payload.student_id,
                "t": payload.term,
                "c": payload.currency,
                "a": payload.amount,
                "d": payload.due_date,
                "i": payload.issued_at,
            },
        )
        row = db.execute(text("SELECT id, student_id, term, currency, amount, status, due_date, issued_at FROM invoices ORDER BY id DESC LIMIT 1")).mappings().first()
        db.commit()
        return InvoiceRead(**dict(row))
    except Exception as ex:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(ex))


@router.get("/payments", response_model=list[PaymentRead], dependencies=[Depends(require_permissions(["finance.read"]))])
def list_payments(db: Session = Depends(get_tenant_db), user_id: int = Depends(get_current_user_id)):
    rows = db.execute(text("SELECT id, invoice_id, amount, method, reference, paid_at FROM payments ORDER BY id DESC")).mappings().all()
    return [PaymentRead(**dict(r)) for r in rows]


@router.post("/payments", response_model=PaymentRead, dependencies=[Depends(require_permissions(["finance.write"]))])
def record_payment(payload: PaymentCreate, db: Session = Depends(get_tenant_db)):
    try:
        db.execute(
            text(
                """
                INSERT INTO payments(invoice_id, amount, method, reference, paid_at)
                VALUES (:iid, :a, :m, :r, :p)
                """
            ),
            {
                "iid": payload.invoice_id,
                "a": payload.amount,
                "m": payload.method,
                "r": payload.reference,
                "p": payload.paid_at,
            },
        )
        row = db.execute(text("SELECT id, invoice_id, amount, method, reference, paid_at FROM payments ORDER BY id DESC LIMIT 1")).mappings().first()
        db.commit()
        return PaymentRead(**dict(row))
    except Exception as ex:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(ex))


