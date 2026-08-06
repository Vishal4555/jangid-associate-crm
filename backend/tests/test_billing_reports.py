import os
import unittest
from datetime import date
from decimal import Decimal
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "sqlite://")

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import app.db.base  # noqa: F401
from app.db.database import Base
from app.models.billing_month import BankMonthlyPayment
from app.models.case import Case
from app.models.case_visit import CaseVisit
from app.models.master import Company, District, Executive
from app.models.user import User
from app.services.billing_report_service import company_report, executive_report
from app.services.payout_rate_service import RateMatch


class BillingReportTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.company_a, self.company_b = Company(name="Company A"), Company(name="Company B")
        self.district = District(name="Jaipur", state="Rajasthan")
        self.master = Executive(full_name="Exec One", mobile="9999999999", address="Plot 12", city="Mansarovar", pincode="302020", district=self.district)
        self.admin = User(full_name="Admin", username="admin-report", email="admin-report@test.local", password_hash="x", role="Admin")
        self.executive = User(full_name="Exec", username="exec-report", email="exec-report@test.local", password_hash="x", role="Executive", executive=self.master)
        self.db.add_all([self.company_a, self.company_b, self.district, self.master, self.admin, self.executive]); self.db.flush()
        self.case_a = Case(case_no="A", los_no="LOS-A", company_id=self.company_a.id, company=self.company_a.name,
            bank="Bank One", applicant="Applicant A", mobile="111", executive="Exec One", status="Pending")
        self.case_b = Case(case_no="B", company_id=self.company_b.id, company=self.company_b.name,
            bank="Bank Two", applicant="Applicant B", executive="Other Exec", status="Pending")
        self.db.add_all([self.case_a, self.case_b]); self.db.flush()
        self.db.add_all([
            CaseVisit(case_id=self.case_a.id, visit_type="Residence", address="Applicant visit address", receive_date=date(2026, 8, 1), executive="Exec One", status="Pending"),
            CaseVisit(case_id=self.case_a.id, visit_type="Office", receive_date=date(2026, 8, 2), executive="Exec One", status="Positive", closed_date=date(2026, 8, 3)),
            CaseVisit(case_id=self.case_a.id, visit_type="Permanent", receive_date=date(2026, 8, 4), executive="Exec One", status="Negative", closed_date=date(2026, 8, 5)),
            CaseVisit(case_id=self.case_b.id, visit_type="Residence", receive_date=date(2026, 8, 1), executive="Other Exec", status="Positive", closed_date=date(2026, 8, 2)),
            BankMonthlyPayment(billing_month=date(2026, 8, 1), company="Company A", bank="Bank One", district="",
                city="", billed_amount=Decimal("300"), received_amount=Decimal("120"), balance_amount=Decimal("180"), status="Partially Paid"),
        ]); self.db.commit()

    def tearDown(self):
        self.db.close(); self.engine.dispose()

    @patch("app.services.billing_report_service.resolve_monthly_bank_rate", return_value=RateMatch("MATCHED", amount=Decimal("100")))
    @patch("app.services.billing_report_service.resolve_monthly_executive_rate", return_value=RateMatch("MATCHED", amount=Decimal("50")))
    def test_company_totals_and_payment_register_are_authoritative(self, _exec, _bank):
        report = company_report(self.db, self.admin, None, self.company_a.id, date(2026, 8, 1), date(2026, 8, 31))
        self.assertEqual(len(report.items), 3)
        self.assertEqual((report.totals["pending"], report.totals["positive"], report.totals["negative"]), (1, 1, 1))
        self.assertEqual(report.totals["company_billing_total"], Decimal("300"))
        self.assertEqual((report.totals["paid_total"], report.totals["balance_total"]), (Decimal("120"), Decimal("180")))
        self.assertEqual(len(report.items[0].model_dump()), 16)  # 14 export columns plus explicit rate-status fields.

    @patch("app.services.billing_report_service.resolve_monthly_executive_rate", return_value=RateMatch("MATCHED", amount=Decimal("50")))
    def test_executive_group_totals_details_and_scope(self, _rate):
        report = executive_report(self.db, self.executive, {self.company_a.id}, date(2026, 8, 1), date(2026, 8, 31))
        self.assertEqual(len(report.items), 1)
        self.assertEqual(len(report.items[0].details), 3)
        self.assertEqual(report.totals, {"total_visits": 3, "pending": 1, "positive": 1, "negative": 1,
            "executive_rate_total": Decimal("150"), "missing_rate_count": 0})
        self.assertTrue(all(x.company == "Company A" for x in report.items[0].details))
        self.assertEqual(report.items[0].details[0].address, "Applicant visit address")
        self.assertEqual(report.items[0].details[0].mobile, "111")
        self.assertNotEqual(report.items[0].details[0].address, self.master.address)
        self.assertNotEqual(report.items[0].details[0].mobile, self.master.mobile)

    @patch("app.services.billing_report_service.resolve_monthly_executive_rate", return_value=RateMatch("MATCHED", amount=Decimal("50")))
    def test_multiple_applicants_remain_separate_details_in_one_group(self, _rate):
        second = Case(case_no="A-2", los_no="LOS-A2", company_id=self.company_a.id, company=self.company_a.name,
            bank="Bank One", applicant="Applicant B", mobile="222", executive="Exec One", status="Pending")
        self.db.add(second); self.db.flush(); self.db.add(CaseVisit(case_id=second.id, visit_type="Residence",
            address="Second visit address", receive_date=date(2026, 8, 6), executive="Exec One", status="Pending")); self.db.commit()
        report = executive_report(self.db, self.admin, None, date(2026, 8, 1), date(2026, 8, 31))
        group = next(x for x in report.items if x.executive == "Exec One" and x.bank_finance_company == "Bank One")
        self.assertEqual(group.total_cases_visits, 4)
        self.assertEqual({x.applicant for x in group.details}, {"Applicant A", "Applicant B"})
        second_detail = next(x for x in group.details if x.applicant == "Applicant B")
        self.assertEqual((second_detail.address, second_detail.mobile), ("Second visit address", "222"))

    def test_company_scope_rejects_out_of_scope_company(self):
        with self.assertRaises(HTTPException) as raised:
            company_report(self.db, self.executive, {self.company_a.id}, self.company_b.id, date(2026, 8, 1), date(2026, 8, 31))
        self.assertEqual(raised.exception.status_code, 403)


if __name__ == "__main__":
    unittest.main()
