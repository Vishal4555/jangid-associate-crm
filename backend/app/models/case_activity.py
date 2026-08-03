from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func

from app.db.database import Base


class CaseActivity(Base):
    __tablename__ = "case_activities"

    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False, index=True)
    activity_type = Column(String(50), nullable=False)
    field_name = Column(String(100), nullable=True)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    performed_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    performed_by_name = Column(String(200), nullable=True)
    performed_at = Column(DateTime, nullable=False, server_default=func.now())
    remarks = Column(Text, nullable=True)
