import os
import unittest
from datetime import date, datetime, timedelta, timezone

os.environ.setdefault("DATABASE_URL", "sqlite:///./case-visits-tests.db")

from fastapi import HTTPException
from pydantic import TypeAdapter, ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import app.db.base
from app.api.case_visits import VisitSort, create_visit, list_case_visits, update_visit
from app.db.database import Base
from app.models.case import Case
from app.models.case_visit import CaseVisit
from app.models.master import District, Executive
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
        self.assertIsNotNone(first.created_at); self.assertIsNotNone(second.created_at)
        completed = update_visit(self.case.id, first.id, CaseVisitUpdate(status="Positive"), self.db, self.user)
        self.assertEqual(completed.closed_date, date.today())
        swapped = update_visit(self.case.id, first.id, CaseVisitUpdate(
            status="Negative", negative_reason="Verification failed"), self.db, self.user)
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

    def test_server_side_visit_sorting_and_pagination(self):
        base = datetime(2026, 8, 8, 7, 0, tzinfo=timezone.utc)
        visits = [
            CaseVisit(case_id=self.case.id, visit_type="Residence", status="Pending", receive_date=date(2026, 8, 9), created_at=base),
            CaseVisit(case_id=self.case.id, visit_type="Office", status="Pending", receive_date=date(2026, 8, 7), created_at=base + timedelta(hours=2)),
            CaseVisit(case_id=self.case.id, visit_type="Business", status="Pending", receive_date=date(2026, 8, 7), created_at=base + timedelta(hours=1)),
        ]
        self.db.add_all(visits); self.db.commit()
        args = dict(search=None, status_filter=None, visit_type=None, company_id=None, bank=None,
            district_id=None, city=None, executive=None, date_from=None, date_to=None,
            page=1, page_size=20, db=self.db, user=self.user)
        latest = list_case_visits(**args, sort="latest_added")["items"]
        oldest = list_case_visits(**args, sort="oldest_added")["items"]
        receive_desc = list_case_visits(**args, sort="receive_date_desc")["items"]
        receive_asc = list_case_visits(**args, sort="receive_date_asc")["items"]
        self.assertEqual([row["visit_id"] for row in latest], [visits[1].id, visits[2].id, visits[0].id])
        self.assertEqual([row["visit_id"] for row in oldest], [visits[0].id, visits[2].id, visits[1].id])
        self.assertEqual([row["visit_id"] for row in receive_desc], [visits[0].id, visits[1].id, visits[2].id])
        self.assertEqual([row["visit_id"] for row in receive_asc], [visits[2].id, visits[1].id, visits[0].id])
        page = list_case_visits(**{**args, "page_size": 1}, sort="latest_added")["items"]
        self.assertEqual(page[0]["visit_id"], visits[1].id)

    def test_latest_added_uses_id_tie_breaker_and_company_filter(self):
        self.case.company_id = 10
        other = Case(case_no="OTHER-COMPANY", applicant="Other", company_id=20)
        self.db.add(other); self.db.flush()
        stamp = datetime(2026, 8, 8, 7, 0, tzinfo=timezone.utc)
        first = CaseVisit(case_id=self.case.id, visit_type="Residence", status="Pending", created_at=stamp)
        second = CaseVisit(case_id=self.case.id, visit_type="Office", status="Pending", created_at=stamp)
        newest_other = CaseVisit(case_id=other.id, visit_type="Business", status="Pending", created_at=stamp + timedelta(days=1))
        self.db.add_all([first, second, newest_other]); self.db.commit()
        result = list_case_visits(search=None, status_filter=None, visit_type=None, company_id=10, bank=None,
            district_id=None, city=None, executive=None, date_from=None, date_to=None, sort="latest_added",
            page=1, page_size=20, db=self.db, user=self.user)
        self.assertEqual([row["visit_id"] for row in result["items"]], [second.id, first.id])

    def test_invalid_sort_value_is_rejected(self):
        with self.assertRaises(ValidationError): TypeAdapter(VisitSort).validate_python("created_at desc")

    def test_editing_one_visit_does_not_change_sibling(self):
        first = create_visit(self.case.id, CaseVisitCreate(visit_type="Residence", address="Before"), self.db, self.user)
        second = create_visit(self.case.id, CaseVisitCreate(visit_type="Office", address="Sibling"), self.db, self.user)
        executive = Executive(full_name="Amit", status="Active")
        self.db.add(executive); self.db.commit(); self.db.refresh(executive)
        update_visit(self.case.id, first.id, CaseVisitUpdate(address="After", executive_id=executive.id), self.db, self.user)
        self.db.refresh(second)
        self.assertEqual(second.address, "Sibling")
        self.assertIsNone(second.executive)

    def test_canonical_executive_and_district_assignment(self):
        executive = Executive(full_name="Active Executive", status="Active")
        district = District(name="Kota", state="Rajasthan", is_active=True)
        self.db.add_all([executive, district]); self.db.commit()
        visit = create_visit(self.case.id, CaseVisitCreate(visit_type="Residence"), self.db, self.user)

        updated = update_visit(self.case.id, visit.id, CaseVisitUpdate(
            executive_id=executive.id, district_id=district.id, city="Kota City"), self.db, self.user)

        self.assertEqual(updated.executive_id, executive.id)
        self.assertEqual(updated.executive, "Active Executive")
        self.assertEqual(updated.district_id, district.id)
        self.assertEqual(updated.district, "Kota")
        self.assertEqual(updated.city, "Kota City")

    def test_inactive_executive_cannot_be_newly_assigned(self):
        executive = Executive(full_name="Inactive Executive", status="Inactive")
        self.db.add(executive); self.db.commit()
        visit = create_visit(self.case.id, CaseVisitCreate(), self.db, self.user)
        with self.assertRaises(HTTPException) as raised:
            update_visit(self.case.id, visit.id, CaseVisitUpdate(executive_id=executive.id), self.db, self.user)
        self.assertEqual(raised.exception.status_code, 422)

    def test_negative_reason_validation_and_nonnegative_clear(self):
        visit = create_visit(self.case.id, CaseVisitCreate(), self.db, self.user)
        with self.assertRaises(HTTPException) as raised:
            update_visit(self.case.id, visit.id, CaseVisitUpdate(status="Negative"), self.db, self.user)
        self.assertEqual(raised.exception.status_code, 422)
        negative = update_visit(self.case.id, visit.id, CaseVisitUpdate(
            status="Negative", negative_reason="Address not found"), self.db, self.user)
        self.assertEqual(negative.negative_reason, "Address not found")
        positive = update_visit(self.case.id, visit.id, CaseVisitUpdate(status="Positive"), self.db, self.user)
        self.assertIsNone(positive.negative_reason)

    def test_visit_edit_preserves_parent_identity(self):
        self.case.los_no = "LOS-PRESERVE"; self.case.applicant = "Original Applicant"
        self.case.company = "Original Company"; self.case.bank = "Original Bank"; self.db.commit()
        visit = create_visit(self.case.id, CaseVisitCreate(), self.db, self.user)
        update_visit(self.case.id, visit.id, CaseVisitUpdate(address="New visit address"), self.db, self.user)
        self.db.refresh(self.case)
        self.assertEqual((self.case.los_no, self.case.applicant, self.case.company, self.case.bank),
            ("LOS-PRESERVE", "Original Applicant", "Original Company", "Original Bank"))


if __name__ == "__main__": unittest.main()
