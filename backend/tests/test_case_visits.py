import os
import unittest
from datetime import date

os.environ.setdefault("DATABASE_URL", "sqlite:///./case-visits-tests.db")

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import app.db.base
from app.api.case_visits import create_visit, update_visit
from app.db.database import Base
from app.models.case import Case
from app.models.case_visit import CaseVisit
from app.models.user import User
from app.schemas.case_visit import CaseVisitCreate, CaseVisitUpdate


class CaseVisitTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine); self.db = Session(self.engine)
        self.user = User(full_name="Admin", username="visits-admin", email="visits@test.local", password_hash="x", role="Admin")
        self.case = Case(case_no="CASE-VISITS-1", applicant="Applicant")
        self.db.add_all([self.user, self.case]); self.db.commit(); self.db.refresh(self.user); self.db.refresh(self.case)

    def tearDown(self):
        self.db.close(); Base.metadata.drop_all(self.engine); self.engine.dispose()

    def test_one_case_has_multiple_visits_and_status_dates(self):
        first = create_visit(self.case.id, CaseVisitCreate(visit_type="Residence", receive_date=date(2026, 8, 1)), self.db, self.user)
        second = create_visit(self.case.id, CaseVisitCreate(visit_type="Office", receive_date=date(2026, 8, 2)), self.db, self.user)
        self.assertEqual(self.db.query(CaseVisit).filter_by(case_id=self.case.id).count(), 2)
        completed = update_visit(self.case.id, first.id, CaseVisitUpdate(status="Positive"), self.db, self.user)
        self.assertEqual(completed.closed_date, date.today())
        swapped = update_visit(self.case.id, first.id, CaseVisitUpdate(status="Negative"), self.db, self.user)
        self.assertEqual(swapped.closed_date, completed.closed_date)
        pending = update_visit(self.case.id, first.id, CaseVisitUpdate(status="Pending"), self.db, self.user)
        self.assertIsNone(pending.closed_date)
        self.assertIsNone(second.closed_date)


if __name__ == "__main__": unittest.main()
