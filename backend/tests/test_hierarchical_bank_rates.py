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
from app.models.master import Bank, Company, District
from app.models.payout_rate import BankPayoutRate
from app.models.user import User
from app.schemas.payout_rate import BankRateBulkCreate, BankRateCreate
from app.services.monthly_billing_service import resolve_monthly_bank_rate
from app.services.payout_rate_service import create_bank_rates_bulk, create_rate


class HierarchicalBankRateTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.company = Company(name="ALETHEIA")
        self.hdfc, self.sbi = Bank(name="HDFC"), Bank(name="SBI")
        self.jaipur, self.baran = District(name="Jaipur"), District(name="Baran")
        self.user = User(full_name="Admin", username="hierarchy", email="hierarchy@test.local", password_hash="x", role="Admin")
        self.db.add_all([self.company, self.hdfc, self.sbi, self.jaipur, self.baran, self.user]); self.db.commit()

    def tearDown(self):
        self.db.close(); self.engine.dispose()

    def case(self, bank=None, district=None, city="Baran"):
        bank, district = bank or self.hdfc, district or self.baran
        return Case(case_no="R-1", company_id=self.company.id, company=self.company.name, bank=bank.name,
            district_id=district.id, district=district.name, city=city, receive_date=date(2026, 8, 10))

    def rate(self, amount, bank=None, district=None, city=None):
        row = BankPayoutRate(company_id=self.company.id, bank_id=bank.id if bank else None,
            district_id=district.id if district else None, city=city, payout_rate=Decimal(amount),
            effective_from=date(2026, 8, 1), is_active=True)
        self.db.add(row); self.db.commit(); return row

    def test_company_default_matches_any_bank_and_district(self):
        row = self.rate("100")
        self.assertEqual(resolve_monthly_bank_rate(self.db, self.case(self.sbi, self.jaipur, "Bagru")).rate_id, row.id)

    def test_specific_bank_overrides_company_default(self):
        self.rate("100"); row = self.rate("110", bank=self.hdfc)
        self.assertEqual(resolve_monthly_bank_rate(self.db, self.case()).rate_id, row.id)

    def test_district_override_beats_all_rajasthan(self):
        self.rate("100"); row = self.rate("150", district=self.baran)
        self.assertEqual(resolve_monthly_bank_rate(self.db, self.case()).rate_id, row.id)

    def test_specific_bank_and_district_beats_district_default(self):
        self.rate("150", district=self.baran); row = self.rate("200", self.hdfc, self.baran)
        self.assertEqual(resolve_monthly_bank_rate(self.db, self.case()).rate_id, row.id)

    def test_jaipur_exact_city_beats_jaipur_all_cities(self):
        self.rate("100", district=self.jaipur); row = self.rate("125", district=self.jaipur, city="Bagru")
        self.assertEqual(resolve_monthly_bank_rate(self.db, self.case(self.sbi, self.jaipur, " bagru ")).rate_id, row.id)

    def test_missing_when_no_rule_exists(self):
        self.assertEqual(resolve_monthly_bank_rate(self.db, self.case()).status, "MISSING")

    def test_equal_dimension_date_overlap_is_blocked(self):
        payload = BankRateCreate(company_id=self.company.id, bank_id=None, district_id=None,
            payout_rate=Decimal("100"), effective_from=date(2026, 8, 1))
        create_rate(self.db, "bank", payload, self.user)
        with self.assertRaises(HTTPException): create_rate(self.db, "bank", payload, self.user)

    def test_bulk_selected_banks_and_districts_is_atomic(self):
        payload = BankRateBulkCreate(company_id=self.company.id, bank_ids=[self.hdfc.id, 99999],
            district_ids=[self.baran.id], payout_rate=Decimal("100"), effective_from=date(2026, 8, 1))
        with self.assertRaises(HTTPException): create_bank_rates_bulk(self.db, payload, self.user)
        self.assertEqual(self.db.query(BankPayoutRate).count(), 0)


if __name__ == "__main__": unittest.main()
