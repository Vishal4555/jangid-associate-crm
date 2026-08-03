import os
import unittest
from datetime import date
from decimal import Decimal

os.environ.setdefault("DATABASE_URL", "sqlite://")

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import app.db.base  # noqa: F401
from app.db.database import Base
from app.models.case import Case
from app.models.master import Bank, Executive
from app.models.payout_rate import BankPayoutRate, ExecutivePayoutRate
from app.models.user import User
from app.schemas.payout_rate import BankRateCreate
from app.services.payout_rate_service import create_rate, resolve_rates
from fastapi import HTTPException


class RateResolutionTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.bank = Bank(name="Example Bank")
        self.executive = Executive(full_name="Asha Sharma")
        self.db.add_all([self.bank, self.executive]); self.db.flush()
        self.case = Case(case_no="C-1", receive_date=date(2026, 4, 10), bank=" example BANK ", city="Jaipur", executive="ASHA SHARMA", loan_type="Home Loan", product_type="Residence")
        self.db.add(self.case); self.db.commit()

    def tearDown(self):
        self.db.close(); self.engine.dispose()

    def bank_rate(self, amount, **values):
        row = BankPayoutRate(bank_id=self.bank.id, payout_rate=Decimal(amount), effective_from=values.pop("effective_from", date(2026, 1, 1)), **values)
        self.db.add(row); self.db.commit(); return row

    def executive_rate(self, amount, **values):
        row = ExecutivePayoutRate(executive_id=self.executive.id, payout_rate=Decimal(amount), effective_from=values.pop("effective_from", date(2026, 1, 1)), **values)
        self.db.add(row); self.db.commit(); return row

    def test_most_specific_beats_wildcard(self):
        self.bank_rate("100"); best = self.bank_rate("250", city=" jaipur ", product_type="RESIDENCE")
        self.executive_rate("50"); executive_best = self.executive_rate("90", bank_id=self.bank.id, city="Jaipur", loan_type="Home Loan", product_type="Residence")
        bank, executive = resolve_rates(self.db, self.case)
        self.assertEqual((bank.status, bank.rate_id, bank.amount), ("MATCHED", best.id, Decimal("250")))
        self.assertEqual((executive.status, executive.rate_id), ("MATCHED", executive_best.id))

    def test_receive_date_controls_effectiveness(self):
        old = self.bank_rate("100", effective_from=date(2025, 1, 1), effective_to=date(2026, 4, 9))
        current = self.bank_rate("150", effective_from=date(2026, 4, 10))
        self.executive_rate("50")
        bank, _ = resolve_rates(self.db, self.case)
        self.assertNotEqual(bank.rate_id, old.id); self.assertEqual(bank.rate_id, current.id)

    def test_missing_and_ambiguous_are_explicit(self):
        bank, executive = resolve_rates(self.db, self.case)
        self.assertEqual((bank.status, executive.status), ("MISSING", "MISSING"))
        self.bank_rate("100", city="Jaipur"); self.bank_rate("120", product_type="Residence")
        bank, _ = resolve_rates(self.db, self.case)
        self.assertEqual(bank.status, "AMBIGUOUS")

    def test_inactive_rate_is_ignored(self):
        self.bank_rate("100", is_active=False); self.executive_rate("50", is_active=False)
        bank, executive = resolve_rates(self.db, self.case)
        self.assertEqual((bank.status, executive.status), ("MISSING", "MISSING"))

    def test_overlapping_identical_dimensions_are_rejected(self):
        user = User(full_name="Admin", username="admin", email="admin@example.com", password_hash="x", role="Admin")
        self.db.add(user); self.db.commit()
        base = dict(bank_id=self.bank.id, city="Jaipur", product_type="Residence", payout_rate=Decimal("100"))
        create_rate(self.db, "bank", BankRateCreate(**base, effective_from=date(2026, 1, 1), effective_to=date(2026, 6, 30)), user)
        with self.assertRaises(HTTPException) as caught:
            create_rate(self.db, "bank", BankRateCreate(**base, effective_from=date(2026, 6, 30)), user)
        self.assertEqual(caught.exception.status_code, 409)


if __name__ == "__main__":
    unittest.main()
