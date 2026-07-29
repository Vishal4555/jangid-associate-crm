from sqlalchemy import Column, Integer, String, Date

from app.db.database import Base


class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)

    case_no = Column(String(100), unique=True, nullable=False)

    receive_date = Column(Date)

    bank = Column(String(200))

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