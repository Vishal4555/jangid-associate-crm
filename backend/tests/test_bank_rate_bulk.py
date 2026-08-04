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
from app.models.master import Bank, Company, District
from app.models.payout_rate import BankPayoutRate
from app.models.user import User
from app.schemas.payout_rate import BankRateBulkCreate, BankRateCreate
from app.services.payout_rate_service import create_bank_rates_bulk, create_rate


class BankRateBulkTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.company = Company(name="Agency")
        self.jaipur = District(name="Jaipur")
        self.kota = District(name="Kota")
        self.banks = [Bank(name=f"Bank {number}") for number in range(1, 4)]
        self.user = User(full_name="Admin", username="bulk-admin", email="bulk@test.local", password_hash="x", role="Admin")
        self.db.add_all([self.company, self.jaipur, self.kota, self.user, *self.banks])
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def payload(self, district=None, city=None, bank_ids=None):
        return BankRateBulkCreate(company_id=self.company.id,
            bank_ids=bank_ids or [bank.id for bank in self.banks], district_id=(district or self.kota).id,
            city=city, payout_rate=Decimal("125.00"), effective_from=date(2026, 8, 1))

    def test_bulk_creates_multiple_and_deduplicates_ids(self):
        ids = [self.banks[0].id, self.banks[1].id, self.banks[0].id]
        result = create_bank_rates_bulk(self.db, self.payload(bank_ids=ids), self.user)
        self.assertEqual((result.created_count, result.failed_count, len(result.items)), (2, 0, 2))

    def test_invalid_bank_rejects_whole_transaction(self):
        with self.assertRaises(HTTPException):
            create_bank_rates_bulk(self.db, self.payload(bank_ids=[self.banks[0].id, 99999]), self.user)
        self.assertEqual(self.db.query(BankPayoutRate).count(), 0)

    def test_overlap_rejects_whole_transaction(self):
        create_rate(self.db, "bank", BankRateCreate(company_id=self.company.id, bank_id=self.banks[1].id,
            district_id=self.kota.id, payout_rate=Decimal("100"), effective_from=date(2026, 1, 1)), self.user)
        before = self.db.query(BankPayoutRate).count()
        with self.assertRaisesRegex(HTTPException, self.banks[1].name):
            create_bank_rates_bulk(self.db, self.payload(bank_ids=[self.banks[0].id, self.banks[1].id]), self.user)
        self.assertEqual(self.db.query(BankPayoutRate).count(), before)

    def test_jaipur_exact_city_and_all_cities(self):
        exact = create_bank_rates_bulk(self.db, self.payload(district=self.jaipur, city="Chomu",
            bank_ids=[self.banks[0].id]), self.user)
        fallback = create_bank_rates_bulk(self.db, BankRateBulkCreate(company_id=self.company.id,
            bank_ids=[self.banks[1].id], district_id=self.jaipur.id, city=None, payout_rate=Decimal("125"),
            effective_from=date(2026, 8, 1)), self.user)
        self.assertEqual((exact.items[0].city, fallback.items[0].city), ("Chomu", None))

    def test_non_jaipur_city_is_rejected_without_writes(self):
        with self.assertRaisesRegex(HTTPException, "City-specific rates"):
            create_bank_rates_bulk(self.db, self.payload(city="Kota"), self.user)
        self.assertEqual(self.db.query(BankPayoutRate).count(), 0)


if __name__ == "__main__":
    unittest.main()
