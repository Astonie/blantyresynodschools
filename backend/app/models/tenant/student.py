from datetime import date

from sqlalchemy import String, UniqueConstraint, Date
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import TenantBase, TimestampMixin


class Student(TenantBase, TimestampMixin):
    __tablename__ = "students"
    __table_args__ = (
        UniqueConstraint("admission_no", name="uq_student_admission"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(128), nullable=False)
    last_name: Mapped[str] = mapped_column(String(128), nullable=False)
    gender: Mapped[str | None] = mapped_column(String(16))
    date_of_birth: Mapped[date | None] = mapped_column(Date())
    admission_no: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    current_class: Mapped[str | None] = mapped_column(String(64))



