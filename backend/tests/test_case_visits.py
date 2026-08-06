import os
import unittest
from datetime import date

os.environ.setdefault("DATABASE_URL", "sqlite:///./case-visits-tests.db")

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import app.db.base
from app.api.case_visits import create_visit, list_case_visits, update_visit
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

    def test_operational_list_returns_and_filters_visit_rows(self):
        self.case.los_no = "LOS-1001"; self.case.company = "R Samdani"; self.case.bank = "HDFC"
        self.case.mobile = "9999999999"; self.db.commit()
        visits = [
            CaseVisit(case_id=self.case.id, visit_type="Residence", address="Home", executive="Amit", status="Positive", receive_date=date(2026, 8, 1), closed_date=date(2026, 8, 2)),
            CaseVisit(case_id=self.case.id, visit_type="Office", address="Office", executive="Beena", status="Pending", receive_date=date(2026, 8, 3)),
            CaseVisit(case_id=self.case.id, visit_type="Permanent", address="Permanent", executive="Chetan", status="Negative", receive_date=date(2026, 8, 4), closed_date=date(2026, 8, 6)),
        ]
        self.db.add_all(visits); self.db.commit()
        args = dict(search="LOS-1001", status_filter=None, visit_type=None, company_id=None, bank=None,
            district_id=None, city=None, executive=None, date_from=None, date_to=None, page=1, page_size=2,
            db=self.db, user=self.user)
        first_page = list_case_visits(**args)
        self.assertEqual(first_page["total"], 3)
        self.assertEqual(len(first_page["items"]), 2)
        self.assertEqual({row["visit_type"] for row in first_page["items"]}, {"Office", "Permanent"})
        residence = list_case_visits(**{**args, "search": None, "visit_type": "Residence", "page_size": 20})
        self.assertEqual(residence["total"], 1)
        self.assertEqual(residence["items"][0]["address"], "Home")

    def test_editing_one_visit_does_not_change_sibling(self):
        first = create_visit(self.case.id, CaseVisitCreate(visit_type="Residence", address="Before"), self.db, self.user)
        second = create_visit(self.case.id, CaseVisitCreate(visit_type="Office", address="Sibling"), self.db, self.user)
        update_visit(self.case.id, first.id, CaseVisitUpdate(address="After", executive="Amit"), self.db, self.user)
        self.db.refresh(second)
        self.assertEqual(second.address, "Sibling")
        self.assertIsNone(second.executive)


if __name__ == "__main__": unittest.main()
