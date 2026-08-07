import os
import unittest

os.environ.setdefault("DATABASE_URL", "sqlite://")

from fastapi import HTTPException
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import app.db.base
from app.db.database import Base
from app.main import create_case
from app.models.case import Case
from app.models.case_visit import CaseVisit
from app.models.master import Bank, Company
from app.models.user import User
from app.schemas.case import CaseCreate


class CaseCreateLosFlowTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine); self.db = Session(self.engine)
        self.company = Company(name="Jangid Agency", is_active=True)
        self.other_company = Company(name="Other Agency", is_active=True)
        self.bank = Bank(name="AU Bank"); self.other_bank = Bank(name="HDFC")
        self.user = User(full_name="Admin", username="los-admin", email="los@test.local", password_hash="x", role="Admin")
        self.db.add_all([self.company, self.other_company, self.bank, self.other_bank, self.user]); self.db.commit()

    def tearDown(self):
        self.db.close(); Base.metadata.drop_all(self.engine); self.engine.dispose()

    def payload(self, **changes):
        values = dict(los_no=" LOS-100 ", company_id=self.company.id, bank=self.bank.name,
            applicant="Ravi Kumar", visit_type="Residence", status="Pending")
        values.update(changes); return CaseCreate(**values)

    def test_new_then_existing_los_creates_one_parent_and_two_visits(self):
        first = create_case(self.payload(case_no="USER-SUPPLIED"), self.db, self.user)
        second = create_case(self.payload(los_no="los-100", visit_type="Office", address="Office address"), self.db, self.user)
        self.assertRegex(first.case_no, r"^JA-[0-9A-F]{12}$")
        self.assertNotEqual(first.case_no, "USER-SUPPLIED")
        self.assertEqual(first.id, second.id)
        self.assertEqual(second.message, "New visit added to existing application.")
        self.assertEqual(self.db.scalar(select(func.count(Case.id))), 1)
        self.assertEqual(self.db.scalar(select(func.count(CaseVisit.id))), 2)

    def test_same_los_with_different_company_or_bank_creates_new_parent(self):
        create_case(self.payload(mobile="9999999999"), self.db, self.user)
        create_case(self.payload(company_id=self.other_company.id, mobile="9999999999"), self.db, self.user)
        create_case(self.payload(bank=self.other_bank.name, mobile="9999999999"), self.db, self.user)
        self.assertEqual(self.db.scalar(select(func.count(Case.id))), 3)
        self.assertEqual(self.db.scalar(select(func.count(CaseVisit.id))), 3)

    def test_same_los_different_applicants_create_distinct_parents(self):
        first = create_case(self.payload(applicant="Ravi Kumar", visit_type="Residence", mobile="9999999999"), self.db, self.user)
        second = create_case(self.payload(applicant="Seema Sharma", visit_type="Office", mobile="9999999999"), self.db, self.user)
        third = create_case(self.payload(applicant="Mohan Lal", visit_type="Permanent", mobile="9999999999"), self.db, self.user)
        self.assertEqual(len({first.id, second.id, third.id}), 3)
        self.assertIn("Mobile already exists in 1 visits.", second.message)
        self.assertIn("Mobile already exists in 2 visits.", third.message)
        self.assertEqual(self.db.scalar(select(func.count(Case.id))), 3)
        self.assertEqual(self.db.scalar(select(func.count(CaseVisit.id))), 3)

    def test_normalized_same_applicant_reuses_parent(self):
        first = create_case(self.payload(applicant="  Ravi   Kumar  "), self.db, self.user)
        second = create_case(self.payload(applicant="ravi kumar", visit_type="Business"), self.db, self.user)
        self.assertEqual(first.id, second.id)
        self.assertEqual(self.db.scalar(select(func.count(Case.id))), 1)
        self.assertEqual(self.db.scalar(select(func.count(CaseVisit.id))), 2)

    def test_blank_los_is_invalid(self):
        with self.assertRaises(HTTPException) as error:
            create_case(self.payload(los_no="  "), self.db, self.user)
        self.assertEqual(error.exception.status_code, 422)


if __name__ == "__main__": unittest.main()
