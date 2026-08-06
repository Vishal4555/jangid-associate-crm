import os
import unittest

os.environ.setdefault("DATABASE_URL", "sqlite://")

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import app.db.base  # noqa: F401
from app.api.masters import add_company_banks_bulk
from app.db.database import Base
from app.models.master import Bank, Company, CompanyBank
from app.models.user import User
from app.schemas.master import CompanyBankBulkCreate


class CompanyBankBulkTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.company = Company(name="Agency", is_active=True)
        self.banks = [Bank(name=f"Bank {number}") for number in range(1, 5)]
        self.admin=User(full_name="Admin",username="admin",email="admin@example.com",password_hash="x",role="Admin")
        self.db.add_all([self.company, *self.banks,self.admin]); self.db.commit()

    def tearDown(self):
        self.db.close(); self.engine.dispose()

    def bulk(self, ids, remarks="Agreement"):
        return add_company_banks_bulk(CompanyBankBulkCreate(
            company_id=self.company.id, bank_ids=ids, remarks=remarks), self.db, self.admin)

    def test_bulk_creates_multiple_and_deduplicates_input(self):
        result = self.bulk([self.banks[0].id, self.banks[1].id, self.banks[0].id])
        self.assertEqual((result.created_count, result.reactivated_count, result.skipped_count), (2, 0, 0))
        self.assertEqual({item.bank_id for item in result.items}, {self.banks[0].id, self.banks[1].id})

    def test_active_is_skipped_and_inactive_is_reactivated(self):
        active = CompanyBank(company_id=self.company.id, bank_id=self.banks[0].id, is_active=True)
        inactive = CompanyBank(company_id=self.company.id, bank_id=self.banks[1].id, is_active=False, remarks="Old")
        self.db.add_all([active, inactive]); self.db.commit()
        result = self.bulk([self.banks[0].id, self.banks[1].id])
        self.assertEqual((result.created_count, result.reactivated_count, result.skipped_count), (0, 1, 1))
        self.assertTrue(self.db.get(CompanyBank, inactive.id).is_active)
        self.assertEqual(self.db.get(CompanyBank, inactive.id).remarks, "Agreement")

    def test_invalid_bank_rejects_entire_transaction(self):
        with self.assertRaises(HTTPException): self.bulk([self.banks[0].id, 99999])
        self.assertEqual(self.db.query(CompanyBank).count(), 0)

    def test_inactive_bank_rejects_entire_transaction(self):
        self.banks[1].is_active = False
        with self.assertRaisesRegex(HTTPException, "inactive"): self.bulk([self.banks[0].id, self.banks[1].id])
        self.assertEqual(self.db.query(CompanyBank).count(), 0)

    def test_unique_constraint_remains_protected(self):
        self.db.add(CompanyBank(company_id=self.company.id, bank_id=self.banks[0].id))
        self.db.commit()
        self.db.add(CompanyBank(company_id=self.company.id, bank_id=self.banks[0].id))
        with self.assertRaises(IntegrityError): self.db.commit()
        self.db.rollback()


if __name__ == "__main__": unittest.main()
