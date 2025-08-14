from datetime import date, datetime

from pydantic import BaseModel


class InvoiceCreate(BaseModel):
    student_id: int
    term: str
    currency: str = "MWK"
    amount: float
    due_date: date | None = None
    issued_at: datetime | None = None


class InvoiceRead(BaseModel):
    id: int
    student_id: int
    term: str
    currency: str
    amount: float
    status: str
    due_date: date | None
    issued_at: datetime | None

    class Config:
        from_attributes = True


class PaymentCreate(BaseModel):
    invoice_id: int
    amount: float
    method: str
    reference: str | None = None
    paid_at: datetime | None = None


class PaymentRead(BaseModel):
    id: int
    invoice_id: int
    amount: float
    method: str
    reference: str | None
    paid_at: datetime | None

    class Config:
        from_attributes = True



