import os
import unittest
from datetime import date

os.environ.setdefault("DATABASE_URL", "sqlite:///./case-deletion-tests.db")

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import app.db.base
from app.db.database import Base
from app.main import delete_case
from app.models.billing import Billing
from app.models.billing_month import BankMonthlyBillingSnapshot, BillingMonth
from app.models.case import Case
from app.models.case_activity import CaseActivity
from app.models.case_visit import CaseVisit
from app.models.user import User


class CaseDeletionTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.admin = User(full_name="Admin", username="delete-admin", email="admin@test.local", password_hash="x", role="Admin")
        self.manager = User(full_name="Manager", username="delete-manager", email="manager@test.local", password_hash="x", role="Manager")
        self.db.add_all([self.admin, self.manager])
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def _case(self, status="Pending"):
        item = Case(case_no=f"DELETE-{status}-{self.db.query(Case).count()}", status=status)
        self.db.add(item)
        self.db.commit()
        return item

    def test_admin_deletes_all_statuses_and_disposable_children(self):
        for case_status in ("Pending", "Positive", "Negative"):
            item = self._case(case_status)
            self.db.add_all([
                CaseActivity(case_id=item.id, activity_type="CASE_CREATED"),
                CaseVisit(case_id=item.id, visit_type="Residence", status="Pending"),
            ])
            self.db.commit()
            delete_case(item.id, self.db, self.admin)
            self.assertIsNone(self.db.get(Case, item.id))
            self.assertEqual(self.db.query(CaseActivity).filter_by(case_id=item.id).count(), 0)
            self.assertEqual(self.db.query(CaseVisit).filter_by(case_id=item.id).count(), 0)

    def test_non_admin_receives_403_even_with_direct_function_access(self):
        item = self._case()
        with self.assertRaises(HTTPException) as raised:
            delete_case(item.id, self.db, self.manager)
        self.assertEqual(raised.exception.status_code, 403)
        self.assertIsNotNone(self.db.get(Case, item.id))

    def test_billing_history_returns_409(self):
        item = self._case()
        self.db.add(Billing(case_id=item.id))
        self.db.commit()
        with self.assertRaises(HTTPException) as raised:
            delete_case(item.id, self.db, self.admin)
        self.assertEqual(raised.exception.status_code, 409)
        self.assertEqual(raised.exception.detail, "This case is part of finalized billing or payment history and cannot be deleted.")

    def test_finalized_snapshot_returns_409(self):
        item = self._case()
        month = BillingMonth(billing_month=date(2026, 8, 1), status="FINALIZED")
        self.db.add(month)
        self.db.flush()
        self.db.add(BankMonthlyBillingSnapshot(
            billing_month_id=month.id, case_id=item.id, date=date(2026, 8, 1),
            case_status="Positive", rate=100, rate_status="MATCHED",
        ))
        self.db.commit()
        with self.assertRaises(HTTPException) as raised:
            delete_case(item.id, self.db, self.admin)
        self.assertEqual(raised.exception.status_code, 409)


if __name__ == "__main__":
    unittest.main()
