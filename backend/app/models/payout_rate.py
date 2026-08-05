from sqlalchemy import Boolean, CheckConstraint, Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import relationship

from app.db.database import Base


class RateColumns:
    city = Column(String(100), nullable=True)
    loan_type = Column(String(100), nullable=True)
    product_type = Column(String(100), nullable=True)
    payout_rate = Column(Numeric(14, 2), nullable=False)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)


class BankPayoutRate(RateColumns, Base):
    __tablename__ = "bank_payout_rates"
    __table_args__ = (
        CheckConstraint("payout_rate >= 0", name="ck_bank_payout_rate_nonnegative"),
        CheckConstraint("effective_to IS NULL OR effective_to >= effective_from", name="ck_bank_payout_rate_dates"),
    )

    id = Column(Integer, primary_key=True)
    # NULL is the normalized wildcard for "All Banks" on structured rates.
    bank_id = Column(Integer, ForeignKey("banks.id", ondelete="RESTRICT"), nullable=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="RESTRICT"), nullable=True, index=True)
    district_id = Column(Integer, ForeignKey("districts.id", ondelete="RESTRICT"), nullable=True, index=True)
    district_scope = Column(String(30), nullable=True, index=True)
    state = Column(String(100), nullable=True, default="Rajasthan", server_default="Rajasthan")
    bank = relationship("Bank")
    company = relationship("Company")
    district = relationship("District")


class ExecutivePayoutRate(RateColumns, Base):
    __tablename__ = "executive_payout_rates"
    __table_args__ = (
        CheckConstraint("payout_rate >= 0", name="ck_executive_payout_rate_nonnegative"),
        CheckConstraint("effective_to IS NULL OR effective_to >= effective_from", name="ck_executive_payout_rate_dates"),
    )

    id = Column(Integer, primary_key=True)
    executive_id = Column(Integer, ForeignKey("executives.id", ondelete="RESTRICT"), nullable=False, index=True)
    bank_id = Column(Integer, ForeignKey("banks.id", ondelete="RESTRICT"), nullable=True, index=True)
    executive = relationship("Executive")
    bank = relationship("Bank")
