import os
import unittest
os.environ.setdefault("DATABASE_URL", "sqlite://")
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import app.db.base  # noqa: F401
from app.db.database import Base
from app.models.master import District, Executive
from app.schemas.master import ExecutiveCreate, ExecutiveUpdate
from app.services.masters_service import create_executive, update_executive

class ExecutiveAddressTests(unittest.TestCase):
    def setUp(self):
        self.engine=create_engine("sqlite://"); Base.metadata.create_all(self.engine); self.db=Session(self.engine)
        self.district=District(name="Jaipur",state="Rajasthan"); self.db.add(self.district); self.db.commit()
    def tearDown(self): self.db.close(); self.engine.dispose()
    def test_existing_blank_and_create_full_address(self):
        blank=create_executive(self.db,ExecutiveCreate(full_name="Blank Executive"))
        self.assertIsNone(blank.address)
        row=create_executive(self.db,ExecutiveCreate(full_name="Address Executive",address="Plot 12",district_id=self.district.id,city="Mansarovar",pincode="302020",mobile="9999999999"))
        self.assertEqual((row.address,row.district_name,row.city,row.pincode),("Plot 12","Jaipur","Mansarovar","302020"))
    def test_update_and_invalid_district(self):
        row=create_executive(self.db,ExecutiveCreate(full_name="Update Executive")); original_id=row.id
        updated=update_executive(self.db,row.id,ExecutiveUpdate(address="New address",district_id=self.district.id))
        self.assertEqual((updated.id,updated.address),(original_id,"New address"))
        with self.assertRaises(HTTPException): update_executive(self.db,row.id,ExecutiveUpdate(district_id=99999))

if __name__ == "__main__": unittest.main()
