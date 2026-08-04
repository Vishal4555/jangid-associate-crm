import os
import unittest

os.environ.setdefault("DATABASE_URL", "sqlite://")

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import app.db.base  # noqa: F401
from app.db.database import Base
from app.main import _validate_case_dimensions
from app.models.master import Bank, Company


class GlobalCompanyBankTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.companies = [Company(name="Company One"), Company(name="Company Two")]
        self.banks = [Bank(name="Bank One"), Bank(name="Bank Two")]
        self.db.add_all([*self.companies, *self.banks])
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_every_global_bank_is_valid_for_every_company_without_mappings(self):
        for company in self.companies:
            for bank in self.banks:
                dimensions = {"company_id":company.id,"bank":bank.name}
                _validate_case_dimensions(self.db, dimensions)
                self.assertEqual(dimensions["company"], company.name)


if __name__ == "__main__":
    unittest.main()
