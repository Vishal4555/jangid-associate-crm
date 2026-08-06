from sqlalchemy import Boolean, CheckConstraint, Column, Date, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import relationship

from app.db.database import Base


class BillingMonth(Base):
    __tablename__ = "billing_months"
    __table_args__ = (
        UniqueConstraint("billing_month", name="uq_billing_months_month"),
        CheckConstraint("status IN ('DRAFT', 'FINALIZED', 'REOPENED')", name="ck_billing_months_status"),
        CheckConstraint("revision_number >= 0", name="ck_billing_months_revision"),
    )
    id = Column(Integer, primary_key=True)
    billing_month = Column(Date, nullable=False, index=True)
    status = Column(String(20), nullable=False, default="DRAFT", server_default="DRAFT")
    finalized_at = Column(DateTime(timezone=True))
    finalized_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    reopened_at = Column(DateTime(timezone=True))
    reopened_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    revision_number = Column(Integer, nullable=False, default=0, server_default="0")
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class ExecutiveMonthlyPayment(Base):
    __tablename__ = "executive_monthly_payments"
    __table_args__ = (
        UniqueConstraint("billing_month", "executive_id", name="uq_monthly_payment_month_executive"),
        CheckConstraint("gross_payment >= 0", name="ck_monthly_payment_gross_nonnegative"),
        CheckConstraint("advance_amount >= 0", name="ck_monthly_payment_advance_nonnegative"),
        CheckConstraint("net_payment >= 0", name="ck_monthly_payment_net_nonnegative"),
        CheckConstraint("paid_amount >= 0 AND paid_amount <= net_payment", name="ck_monthly_payment_paid_valid"),
        CheckConstraint("balance_amount = net_payment - paid_amount", name="ck_monthly_payment_balance_consistent"),
        CheckConstraint("status IN ('Pending', 'Partially Paid', 'Paid', 'Done')", name="ck_monthly_payment_status"),
    )

    id = Column(Integer, primary_key=True)
    billing_month = Column(Date, nullable=False, index=True)
    executive_id = Column(Integer, ForeignKey("executives.id", ondelete="RESTRICT"), nullable=False, index=True)
    gross_payment = Column(Numeric(14, 2), nullable=False)
    advance_amount = Column(Numeric(14, 2), nullable=False, default=0, server_default="0")
    net_payment = Column(Numeric(14, 2), nullable=False)
    paid_amount = Column(Numeric(14, 2), nullable=False, default=0, server_default="0")
    balance_amount = Column(Numeric(14, 2), nullable=False)
    status = Column(String(30), nullable=False, default="Pending", server_default="Pending")
    payment_date = Column(Date, nullable=True)
    payment_reference = Column(String(200), nullable=True)
    remarks = Column(Text, nullable=True)
    is_finalized = Column(Boolean, nullable=False, default=False, server_default="false")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    executive = relationship("Executive")


class ExecutiveMonthlyBillingSnapshot(Base):
    __tablename__ = "executive_monthly_billing_snapshots"
    __table_args__ = (
        UniqueConstraint("billing_month_id", "executive_id", name="uq_exec_snapshot_month_executive"),
        CheckConstraint("total_points >= 0 AND gross_payment >= 0 AND advance_amount >= 0 AND net_payment >= 0 AND paid_amount >= 0 AND balance_amount >= 0", name="ck_exec_snapshot_amounts"),
        CheckConstraint("paid_amount <= net_payment AND balance_amount = net_payment - paid_amount", name="ck_exec_snapshot_payment"),
        CheckConstraint("payment_status IN ('Pending', 'Partially Paid', 'Paid', 'Cancelled')", name="ck_exec_snapshot_status"),
        CheckConstraint("rate_status IN ('MATCHED', 'MISSING', 'AMBIGUOUS')", name="ck_exec_snapshot_rate_status"),
    )
    id = Column(Integer, primary_key=True)
    billing_month_id = Column(Integer, ForeignKey("billing_months.id", ondelete="CASCADE"), nullable=False, index=True)
    executive_id = Column(Integer, ForeignKey("executives.id", ondelete="SET NULL"), nullable=True, index=True)
    executive_name = Column(String(200), nullable=False)
    rate_display = Column(String(200), nullable=False)
    total_points = Column(Integer, nullable=False)
    gross_payment = Column(Numeric(14, 2), nullable=False)
    advance_amount = Column(Numeric(14, 2), nullable=False, server_default="0")
    net_payment = Column(Numeric(14, 2), nullable=False)
    paid_amount = Column(Numeric(14, 2), nullable=False, server_default="0")
    balance_amount = Column(Numeric(14, 2), nullable=False)
    payment_status = Column(String(30), nullable=False)
    bank_counts = Column(JSON, nullable=False, default=dict)
    rate_status = Column(String(20), nullable=False)
    remarks = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class BankMonthlyBillingSnapshot(Base):
    __tablename__ = "bank_monthly_billing_snapshots"
    __table_args__ = (CheckConstraint("rate >= 0", name="ck_bank_snapshot_rate"), CheckConstraint("rate_status IN ('MATCHED', 'MISSING', 'AMBIGUOUS')", name="ck_bank_snapshot_rate_status"))
    id = Column(Integer, primary_key=True)
    billing_month_id = Column(Integer, ForeignKey("billing_months.id", ondelete="CASCADE"), nullable=False, index=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="SET NULL"), index=True)
    visit_id = Column(Integer, ForeignKey("case_visits.id", ondelete="SET NULL"), index=True)
    visit_type = Column(String(30))
    executive = Column(String(200))
    executive_rate = Column(Numeric(14, 2))
    executive_rate_status = Column(String(20))
    date = Column(Date, nullable=False)
    company = Column(String(200))
    bank = Column(String(200))
    los_no = Column(String(200))
    applicant = Column(String(255))
    address = Column(Text)
    city = Column(String(100))
    district = Column(String(100))
    mobile = Column(String(50))
    case_status = Column(String(100), nullable=False)
    remark = Column(Text)
    rate = Column(Numeric(14, 2), nullable=False)
    rate_status = Column(String(20), nullable=False)
    bank_payout_rate_id = Column(Integer, ForeignKey("bank_payout_rates.id", ondelete="RESTRICT"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class BankMonthlyPayment(Base):
    __tablename__ = "bank_monthly_payments"
    __table_args__ = (
        UniqueConstraint("billing_month", "company", "bank", "district", name="uq_bank_payment_month_company_bank_district"),
        CheckConstraint("billed_amount >= 0 AND received_amount >= 0 AND received_amount <= billed_amount", name="ck_bank_payment_amounts"),
        CheckConstraint("balance_amount = billed_amount - received_amount", name="ck_bank_payment_balance"),
        CheckConstraint("status IN ('Pending', 'Partially Paid', 'Paid', 'Cancelled')", name="ck_bank_payment_status"),
    )
    id = Column(Integer, primary_key=True)
    billing_month = Column(Date, nullable=False, index=True)
    company = Column(String(200), nullable=False, default="", server_default="", index=True)
    bank = Column(String(200), nullable=False, index=True)
    district = Column(String(100), nullable=False, default="", server_default="", index=True)
    city = Column(String(100), nullable=False, default="", server_default="", index=True)
    billed_amount = Column(Numeric(14, 2), nullable=False)
    received_amount = Column(Numeric(14, 2), nullable=False, server_default="0")
    balance_amount = Column(Numeric(14, 2), nullable=False)
    status = Column(String(30), nullable=False, server_default="Pending")
    payment_date = Column(Date)
    payment_reference = Column(String(200))
    remarks = Column(Text)
    is_finalized = Column(Boolean, nullable=False, server_default="false")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    updated_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
