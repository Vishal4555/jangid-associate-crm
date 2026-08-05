import os
import unittest

os.environ.setdefault("DATABASE_URL", "sqlite:///./executive-scope-tests.db")

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import app.db.base
from app.api.case_visits import list_visits, update_visit
from app.db.database import Base
from app.models.case import Case
from app.models.case_visit import CaseVisit
from app.models.master import Executive
from app.models.user import User
from app.schemas.case_visit import CaseVisitUpdate


class ExecutiveScopeTests(unittest.TestCase):
    def setUp(self):
        self.engine=create_engine("sqlite://",connect_args={"check_same_thread":False},poolclass=StaticPool);Base.metadata.create_all(self.engine);self.db=Session(self.engine)
        master=Executive(full_name="Exec One",status="Active"); self.db.add(master); self.db.flush()
        self.user=User(full_name="Exec Login",username="exec",email="exec@test.local",password_hash="x",role="Executive",executive_id=master.id)
        self.case=Case(case_no="C-1",applicant="Applicant");self.db.add_all([self.user,self.case]);self.db.flush()
        self.assigned=CaseVisit(case_id=self.case.id,visit_type="Residence",executive="Exec One",status="Pending")
        self.other=CaseVisit(case_id=self.case.id,visit_type="Office",executive="Exec Two",status="Pending")
        self.db.add_all([self.assigned,self.other]);self.db.commit()

    def tearDown(self): self.db.close();Base.metadata.drop_all(self.engine);self.engine.dispose()

    def test_executive_sees_only_assigned_visits(self):
        rows=list_visits(self.case.id,self.db,self.user)
        self.assertEqual([row.id for row in rows],[self.assigned.id])

    def test_executive_can_update_operational_fields_only(self):
        row=update_visit(self.case.id,self.assigned.id,CaseVisitUpdate(remarks="Visited"),self.db,self.user)
        self.assertEqual(row.remarks,"Visited")
        with self.assertRaises(HTTPException) as raised:
            update_visit(self.case.id,self.assigned.id,CaseVisitUpdate(executive="Exec Two"),self.db,self.user)
        self.assertEqual(raised.exception.status_code,403)
        with self.assertRaises(HTTPException) as unassigned:
            update_visit(self.case.id,self.other.id,CaseVisitUpdate(remarks="No"),self.db,self.user)
        self.assertEqual(unassigned.exception.status_code,403)


if __name__ == "__main__": unittest.main()
