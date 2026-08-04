import os
import unittest
from datetime import date
from decimal import Decimal

os.environ.setdefault("DATABASE_URL", "sqlite://")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi import HTTPException

from app.db.database import Base
import app.db.base  # noqa: F401
from app.models.case import Case
from app.models.master import Bank, Company, CompanyBank, District
from app.models.payout_rate import BankPayoutRate
from app.models.user import User
from app.schemas.payout_rate import BankRateCreate
from app.services.monthly_billing_service import resolve_monthly_bank_rate
from app.services.payout_rate_service import create_rate


class CompanyDistrictRateTests(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(engine)
        self.db = sessionmaker(bind=engine)()
        self.company = Company(name="R Samdani & Associates", source_type="Both")
        self.bank = Bank(name="AU Bank")
        self.district = District(name="Jaipur")
        self.kota = District(name="Kota")
        self.user = User(full_name="Admin", username="admin", email="admin@test.local", password_hash="x", role="Admin")
        self.db.add_all([self.company, self.bank, self.district, self.kota, self.user]); self.db.flush()
        self.db.add(CompanyBank(company_id=self.company.id, bank_id=self.bank.id)); self.db.commit()

    def case(self, day=date(2026, 8, 10), city="Jaipur", district=None):
        district = district or self.district
        return Case(case_no="C-1", company_id=self.company.id, company=self.company.name,
            bank=self.bank.name, district_id=district.id, district=district.name, city=city, receive_date=day)

    def rate(self, amount="125", start=date(2026, 8, 1), end=None, city=None, district=None):
        district = district or self.district
        row = BankPayoutRate(company_id=self.company.id, bank_id=self.bank.id, district_id=district.id, city=city,
            payout_rate=Decimal(amount), effective_from=start, effective_to=end, is_active=True)
        self.db.add(row); self.db.commit(); return row

    def test_jaipur_exact_city_match_has_priority(self):
        self.rate("100"); row = self.rate("150", city="Chomu")
        match = resolve_monthly_bank_rate(self.db, self.case(city="Chomu"))
        self.assertEqual((match.status, match.rate_id, match.amount), ("MATCHED", row.id, Decimal("150")))

    def test_jaipur_all_cities_fallback(self):
        row = self.rate(); match = resolve_monthly_bank_rate(self.db, self.case(city="Sanganer"))
        self.assertEqual((match.status, match.rate_id, match.amount), ("MATCHED", row.id, Decimal("125")))

    def test_jaipur_missing_without_exact_or_fallback(self):
        self.rate(city="Chomu")
        self.assertEqual(resolve_monthly_bank_rate(self.db, self.case(city="Sanganer")).status, "MISSING")

    def test_kota_district_rate_ignores_case_city(self):
        row = self.rate(district=self.kota)
        match = resolve_monthly_bank_rate(self.db, self.case(city="Any Kota City", district=self.kota))
        self.assertEqual((match.status, match.rate_id), ("MATCHED", row.id))

    def test_non_jaipur_city_specific_creation_is_rejected(self):
        payload = BankRateCreate(company_id=self.company.id, bank_id=self.bank.id, district_id=self.kota.id,
            city="Kota", payout_rate=Decimal("100"), effective_from=date(2026, 8, 1))
        with self.assertRaisesRegex(HTTPException, "City-specific rates are allowed only for Jaipur district"):
            create_rate(self.db, "bank", payload, self.user)

    def test_city_matching_is_trimmed_and_case_insensitive(self):
        row = self.rate(city="  ChOmU  ")
        self.assertEqual(resolve_monthly_bank_rate(self.db, self.case(city=" chomu ")).rate_id, row.id)

    def test_missing_structured_dimension_never_falls_back_to_city(self):
        self.rate(); item = self.case(); item.district_id = None; item.city = "Jaipur"
        self.assertEqual(resolve_monthly_bank_rate(self.db, item).status, "MISSING")

    def test_effective_date(self):
        self.rate(start=date(2026, 9, 1))
        self.assertEqual(resolve_monthly_bank_rate(self.db, self.case()).status, "MISSING")

    def test_ambiguous_exact_matches_are_explicit(self):
        self.rate("100", city="Chomu"); self.rate("200", city="chomu")
        self.assertEqual(resolve_monthly_bank_rate(self.db, self.case(city="CHOMU")).status, "AMBIGUOUS")


if __name__ == "__main__": unittest.main()
