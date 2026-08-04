import os
import unittest
from datetime import date
from decimal import Decimal

os.environ.setdefault("DATABASE_URL", "sqlite://")

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import app.db.base  # noqa: F401
from app.db.database import Base
from app.models.case import Case
from app.models.master import Bank, Executive
from app.models.payout_rate import BankPayoutRate, ExecutivePayoutRate
from app.models.user import User
from app.schemas.monthly_billing import BankPaymentUpdate, PaymentRegisterUpdate
from app.services.monthly_billing_service import (finalize_month, monthly_billing, reopen_month,
    save_bank_payment, save_payment_register)


class MonthlyBillingTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.bank = Bank(name="AU Bank")
        self.other_bank = Bank(name="BOB")
        self.executive = Executive(full_name="Abdul Hameed")
        self.user = User(full_name="Admin", username="admin", email="admin@test.local", password_hash="x", role="Admin")
        self.db.add_all([self.bank, self.other_bank, self.executive, self.user]); self.db.flush()

    def tearDown(self):
        self.db.close(); self.engine.dispose()

    def case(self, number, day, bank="AU BANK", city="Jaipur", status="Positive", los_no=None):
        item = Case(case_no=number, los_no=los_no, receive_date=day, applicant="Applicant", address="Address", city=city,
            mobile="9999999999", bank=bank, executive="abdul hameed", status=status, remarks="Remark")
        self.db.add(item); self.db.commit(); return item

    def executive_rate(self, amount, start=date(2026, 1, 1), end=None):
        row = ExecutivePayoutRate(executive_id=self.executive.id, payout_rate=Decimal(amount), effective_from=start, effective_to=end)
        self.db.add(row); self.db.commit(); return row

    def bank_rate(self, amount, city="JAIPUR", start=date(2026, 1, 1), end=None):
        row = BankPayoutRate(bank_id=self.bank.id, city=city, payout_rate=Decimal(amount), effective_from=start, effective_to=end)
        self.db.add(row); self.db.commit(); return row

    def test_fixed_executive_rate_and_bank_counts(self):
        self.executive_rate("80"); self.bank_rate("100")
        self.case("L-1", date(2026, 6, 1)); self.case("L-2", date(2026, 6, 2), bank="BOB", status="Negative")
        report = monthly_billing(self.db, "2026-06")
        row = report.executive_billing[0]
        self.assertEqual(row.total_points, 2)
        self.assertEqual(row.bank_counts, {"AU BANK": 1, "BOB": 1})
        self.assertEqual((row.rate, row.gross_payment), (Decimal("80"), Decimal("160")))
        self.assertEqual(report.summary.billable_cases, 2)

    def test_bank_city_is_case_insensitive_and_pending_is_excluded(self):
        self.executive_rate("80"); self.bank_rate("125", city=" jaipur ")
        self.case("L-1", date(2026, 6, 1), city="JAIPUR")
        self.case("L-2", date(2026, 6, 2), city="Jaipur", status="Pending")
        report = monthly_billing(self.db, "2026-06")
        self.assertEqual(len(report.bank_billing), 1)
        self.assertEqual((report.bank_billing[0].rate_status, report.bank_billing[0].rate), ("MATCHED", Decimal("125")))

    def test_bank_billing_uses_structured_los_without_case_number_fallback(self):
        self.executive_rate("80"); self.bank_rate("125")
        self.case("JA-0001", date(2026, 6, 1), los_no="BANK-APP-987")
        self.case("JA-0002", date(2026, 6, 2), los_no=None)
        rows = monthly_billing(self.db, "2026-06").bank_billing
        self.assertEqual(rows[0].los_no, "BANK-APP-987")
        self.assertIsNone(rows[1].los_no)
        self.assertNotEqual(rows[1].los_no, "JA-0002")

    def test_effective_dates_and_multiple_executive_rates(self):
        self.executive_rate("80", end=date(2026, 6, 15)); self.executive_rate("100", start=date(2026, 6, 16))
        self.bank_rate("100")
        self.case("L-1", date(2026, 6, 15)); self.case("L-2", date(2026, 6, 16))
        row = monthly_billing(self.db, "2026-06").executive_billing[0]
        self.assertEqual(row.rate_display, "Multiple rates")
        self.assertIsNone(row.rate)
        self.assertEqual(row.gross_payment, Decimal("180"))

    def test_missing_and_ambiguous_rates_are_explicit(self):
        item = self.case("L-1", date(2026, 6, 1))
        report = monthly_billing(self.db, "2026-06")
        self.assertEqual(report.executive_billing[0].rate_status, "MISSING")
        self.assertEqual(report.bank_billing[0].rate_status, "MISSING")
        self.executive_rate("80"); self.executive_rate("90")
        self.bank_rate("100"); self.bank_rate("110", city="jaipur")
        report = monthly_billing(self.db, "2026-06")
        self.assertEqual(report.executive_billing[0].rate_status, "AMBIGUOUS")
        self.assertEqual(report.bank_billing[0].rate_status, "AMBIGUOUS")

    def test_payment_register_calculation_and_validation(self):
        self.executive_rate("100"); self.bank_rate("150"); self.case("L-1", date(2026, 6, 1)); self.case("L-2", date(2026, 6, 2))
        saved = save_payment_register(self.db, PaymentRegisterUpdate(billing_month="2026-06", executive_id=self.executive.id,
            advance_amount=Decimal("50"), paid_amount=Decimal("100")), self.user)
        self.assertEqual((saved.gross_payment, saved.net_payment, saved.balance_amount, saved.status),
            (Decimal("200"), Decimal("150"), Decimal("50"), "Partially Paid"))
        with self.assertRaises(HTTPException):
            save_payment_register(self.db, PaymentRegisterUpdate(billing_month="2026-06", executive_id=self.executive.id,
                advance_amount=Decimal("50"), paid_amount=Decimal("151")), self.user)

    def test_finalized_register_keeps_snapshot_until_regenerated(self):
        self.executive_rate("100"); self.bank_rate("150"); self.case("L-1", date(2026, 6, 1))
        saved = save_payment_register(self.db, PaymentRegisterUpdate(billing_month="2026-06", executive_id=self.executive.id, finalize=True), self.user)
        self.assertEqual(saved.gross_payment, Decimal("100"))
        self.case("L-2", date(2026, 6, 2))
        preserved = save_payment_register(self.db, PaymentRegisterUpdate(billing_month="2026-06", executive_id=self.executive.id, finalize=True), self.user)
        regenerated = save_payment_register(self.db, PaymentRegisterUpdate(billing_month="2026-06", executive_id=self.executive.id, finalize=True, regenerate=True), self.user)
        self.assertEqual(preserved.gross_payment, Decimal("100"))
        self.assertEqual(regenerated.gross_payment, Decimal("200"))

    def test_month_freeze_preserves_snapshot_and_reopen_records_audit(self):
        self.executive_rate("100"); self.bank_rate("150"); self.case("L-1", date(2026, 6, 1))
        status = finalize_month(self.db, "2026-06", "close", self.user)
        self.assertEqual((status.status, status.revision_number), ("FINALIZED", 0))
        self.case("L-2", date(2026, 6, 2))
        frozen = monthly_billing(self.db, "2026-06")
        self.assertEqual((frozen.summary.billable_cases, frozen.summary.total_bank_billing), (1, Decimal("150")))
        reopened = reopen_month(self.db, "2026-06", "correction", self.user)
        self.assertEqual(reopened.status, "REOPENED"); self.assertIsNotNone(reopened.reopened_at)
        self.assertEqual(monthly_billing(self.db, "2026-06").summary.billable_cases, 2)

    def test_finalization_blocks_missing_and_ambiguous_rates(self):
        self.case("L-1", date(2026, 6, 1))
        with self.assertRaises(HTTPException) as missing: finalize_month(self.db, "2026-06", None, self.user)
        self.assertEqual(missing.exception.status_code, 422)
        self.executive_rate("100"); self.executive_rate("110"); self.bank_rate("150")
        with self.assertRaises(HTTPException) as ambiguous: finalize_month(self.db, "2026-06", None, self.user)
        self.assertEqual(ambiguous.exception.status_code, 422)

    def test_regeneration_increments_revision_and_blocks_overpayment(self):
        self.executive_rate("100"); self.bank_rate("150"); first=self.case("L-1", date(2026, 6, 1)); self.case("L-2", date(2026, 6, 2))
        save_payment_register(self.db, PaymentRegisterUpdate(billing_month="2026-06", executive_id=self.executive.id, paid_amount=Decimal("150")), self.user)
        finalize_month(self.db, "2026-06", None, self.user); reopen_month(self.db, "2026-06", "remove case", self.user)
        self.db.delete(first); self.db.commit()
        with self.assertRaises(HTTPException) as conflict: finalize_month(self.db, "2026-06", None, self.user, regenerate=True)
        self.assertEqual(conflict.exception.status_code, 409)
        payment = self.db.query(__import__('app.models.billing_month', fromlist=['ExecutiveMonthlyPayment']).ExecutiveMonthlyPayment).one()
        payment.paid_amount=Decimal("100"); payment.balance_amount=Decimal("100"); self.db.commit()
        regenerated=finalize_month(self.db, "2026-06", None, self.user, regenerate=True)
        self.assertEqual((regenerated.status, regenerated.revision_number), ("FINALIZED", 1))

    def test_bank_payment_derived_status_date_and_limit(self):
        self.executive_rate("100"); self.bank_rate("150"); self.case("L-1", date(2026, 6, 1)); finalize_month(self.db, "2026-06", None, self.user)
        partial=save_bank_payment(self.db, BankPaymentUpdate(billing_month="2026-06",bank="AU BANK",city="Jaipur",received_amount=Decimal("50")),self.user)
        self.assertEqual(partial.status,"Partially Paid"); self.assertIsNotNone(partial.payment_date)
        zero=save_bank_payment(self.db, BankPaymentUpdate(billing_month="2026-06",bank="AU BANK",city="Jaipur",received_amount=Decimal("0")),self.user)
        self.assertEqual(zero.status,"Pending"); self.assertIsNone(zero.payment_date)
        with self.assertRaises(HTTPException): save_bank_payment(self.db, BankPaymentUpdate(billing_month="2026-06",bank="AU BANK",city="Jaipur",received_amount=Decimal("151")),self.user)


if __name__ == "__main__":
    unittest.main()
