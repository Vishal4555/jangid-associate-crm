from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import relationship

from app.db.database import Base


class CaseImportSession(Base):
    __tablename__ = "case_import_sessions"

    id = Column(Integer, primary_key=True)
    token = Column(String(64), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    rows = relationship("CaseImportRow", cascade="all, delete-orphan", order_by="CaseImportRow.row_number")


class CaseImportRow(Base):
    __tablename__ = "case_import_rows"
    __table_args__ = (UniqueConstraint("session_id", "row_number", name="uq_case_import_rows_session_row"),)

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("case_import_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    row_number = Column(Integer, nullable=False)
    data_json = Column(Text, nullable=False)
    state = Column(String(20), nullable=False, index=True)
    intended_action = Column(String(50), nullable=False)
    errors_json = Column(Text, nullable=False, default="[]")
    warnings_json = Column(Text, nullable=False, default="[]")
    imported_at = Column(DateTime(timezone=True), nullable=True)

