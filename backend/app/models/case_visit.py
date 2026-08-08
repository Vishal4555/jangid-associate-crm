from sqlalchemy import CheckConstraint, Column, Date, DateTime, ForeignKey, Integer, String, Text, func

from app.db.database import Base


class CaseVisit(Base):
    __tablename__ = "case_visits"
    __table_args__ = (
        CheckConstraint("visit_type IN ('Residence','Office','Permanent','Business','Other')", name="ck_case_visits_type"),
        CheckConstraint("status IN ('Pending','Positive','Negative')", name="ck_case_visits_status"),
        CheckConstraint("(status = 'Pending' AND closed_date IS NULL) OR (status IN ('Positive','Negative') AND closed_date IS NOT NULL)", name="ck_case_visits_closed_date"),
    )

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    visit_type = Column(String(30), nullable=False)
    address = Column(String(500), nullable=True)
    district_id = Column(Integer, ForeignKey("districts.id", ondelete="SET NULL"), nullable=True, index=True)
    district = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    landmark = Column(String(300), nullable=True)
    executive_id = Column(Integer, ForeignKey("executives.id", ondelete="SET NULL"), nullable=True, index=True)
    executive = Column(String(100), nullable=True)
    status = Column(String(20), nullable=False, default="Pending", server_default="Pending")
    negative_reason = Column(String(300), nullable=True)
    receive_date = Column(Date, nullable=True)
    closed_date = Column(Date, nullable=True)
    remarks = Column(String(1000), nullable=True)
    next_follow_up_at = Column(DateTime, nullable=True)
    follow_up_note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    @property
    def tat_days(self):
        if self.receive_date is None or self.closed_date is None:
            return None
        return (self.closed_date - self.receive_date).days
