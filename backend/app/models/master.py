from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import relationship

from app.db.database import Base


class Bank(Base):
    __tablename__ = "banks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), unique=True, nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    branches = relationship("Branch", back_populates="bank", cascade="all, delete-orphan")


class Company(Base):
    __tablename__ = "companies"
    __table_args__ = (CheckConstraint("source_type IN ('WhatsApp', 'Email', 'Both', 'Other')", name="ck_companies_source_type"),)
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    code = Column(String(50), nullable=True, unique=True, index=True)
    source_type = Column(String(20), nullable=False, default="Other", server_default="Other")
    contact_person = Column(String(200), nullable=True)
    email = Column(String(255), nullable=True)
    mobile = Column(String(20), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, server_default="true", index=True)
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    banks = relationship("CompanyBank", back_populates="company")


class CompanyBank(Base):
    __tablename__ = "company_banks"
    __table_args__ = (UniqueConstraint("company_id", "bank_id", name="uq_company_banks_company_bank"),)
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True)
    bank_id = Column(Integer, ForeignKey("banks.id", ondelete="RESTRICT"), nullable=False, index=True)
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    company = relationship("Company", back_populates="banks")
    bank = relationship("Bank")

    @property
    def company_name(self): return self.company.name if self.company else ""

    @property
    def bank_name(self): return self.bank.name if self.bank else ""


class District(Base):
    __tablename__ = "districts"
    __table_args__ = (UniqueConstraint("state", "name", name="uq_districts_state_name"),)
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    state = Column(String(100), nullable=False, default="Rajasthan", server_default="Rajasthan", index=True)
    is_active = Column(Boolean, nullable=False, default=True, server_default="true", index=True)


class Branch(Base):
    __tablename__ = "branches"
    __table_args__ = (
        UniqueConstraint("bank_id", "name", name="uq_branches_bank_name"),
    )

    id = Column(Integer, primary_key=True, index=True)
    bank_id = Column(Integer, ForeignKey("banks.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(200), nullable=False, index=True)
    code = Column(String(50), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    bank = relationship("Bank", back_populates="branches")

    @property
    def bank_name(self) -> str:
        return self.bank.name if self.bank else ""


class Executive(Base):
    __tablename__ = "executives"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(200), nullable=False, index=True)
    email = Column(String(255), nullable=True, index=True)
    mobile = Column(String(20), nullable=True, index=True)
    status = Column(String(20), nullable=False, default="Active", index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class LoanType(Base):
    __tablename__ = "loan_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), unique=True, nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class ProductType(Base):
    __tablename__ = "product_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), unique=True, nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
