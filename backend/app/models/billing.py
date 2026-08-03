from sqlalchemy import CheckConstraint, Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func

from app.db.database import Base


class Billing(Base):
    __tablename__ = "billing"
    __table_args__ = (
        CheckConstraint("bank_payout_amount >= 0", name="ck_billing_bank_amount_nonnegative"),
        CheckConstraint("bank_paid_amount >= 0", name="ck_billing_bank_paid_nonnegative"),
        CheckConstraint("bank_paid_amount <= bank_payout_amount", name="ck_billing_bank_paid_within_payout"),
        CheckConstraint("executive_payout_amount >= 0", name="ck_billing_executive_amount_nonnegative"),
        CheckConstraint("executive_paid_amount >= 0", name="ck_billing_executive_paid_nonnegative"),
        CheckConstraint("executive_paid_amount <= executive_payout_amount", name="ck_billing_executive_paid_within_payout"),
        CheckConstraint("bank_payment_status IN ('Pending', 'Partially Paid', 'Paid', 'Cancelled')", name="ck_billing_bank_status"),
        CheckConstraint("executive_payment_status IN ('Pending', 'Partially Paid', 'Paid', 'Cancelled')", name="ck_billing_executive_status"),
    )

    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False, unique=True, index=True)
    bank_payout_amount = Column(Numeric(14, 2), nullable=False, default=0, server_default="0")
    bank_paid_amount = Column(Numeric(14, 2), nullable=False, default=0, server_default="0")
    bank_payment_status = Column(String(30), nullable=False, default="Pending", server_default="Pending")
    bank_paid_date = Column(Date, nullable=True)
    bank_payment_reference = Column(String(200), nullable=True)
    executive_payout_amount = Column(Numeric(14, 2), nullable=False, default=0, server_default="0")
    executive_paid_amount = Column(Numeric(14, 2), nullable=False, default=0, server_default="0")
    executive_payment_status = Column(String(30), nullable=False, default="Pending", server_default="Pending")
    executive_paid_date = Column(Date, nullable=True)
    executive_payment_reference = Column(String(200), nullable=True)
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    bank_payout_rate_id = Column(Integer, ForeignKey("bank_payout_rates.id", ondelete="SET NULL"), nullable=True)
    executive_payout_rate_id = Column(Integer, ForeignKey("executive_payout_rates.id", ondelete="SET NULL"), nullable=True)
