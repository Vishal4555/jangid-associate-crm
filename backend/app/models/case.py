from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Text

from app.db.database import Base


class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)

    case_no = Column(String(100), unique=True, nullable=False)

    los_no = Column(String(100), nullable=True)

    receive_date = Column(Date)

    closed_date = Column(Date, nullable=True)

    bank = Column(String(200))
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True)
    company = Column(String(200), nullable=True)
    district_id = Column(Integer, ForeignKey("districts.id", ondelete="SET NULL"), nullable=True, index=True)
    district = Column(String(100), nullable=True)

    branch = Column(String(200))

    loan_type = Column(String(100))

    applicant = Column(String(200))

    product_type = Column(String(100))

    address = Column(String(500))

    city = Column(String(100))

    mobile = Column(String(20))

    executive = Column(String(100))

    status = Column(String(100))

    negative_reason = Column(String(300))

    landmark = Column(String(300))

    remarks = Column(String(1000))

    next_follow_up_at = Column(DateTime, nullable=True)

    follow_up_note = Column(Text, nullable=True)
