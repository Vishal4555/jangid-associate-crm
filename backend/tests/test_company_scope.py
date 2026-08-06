import os
import unittest
from datetime import date

os.environ.setdefault("DATABASE_URL","sqlite:///./company-scope-tests.db")

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from starlette.requests import Request

import app.db.base
from app.api.masters import get_companies
from app.api.users import update_user_companies
from app.db.database import Base
from app.main import get_cases
from app.models.case import Case
from app.models.case_visit import CaseVisit
from app.models.master import Company, Executive
from app.models.user import User, UserCompany
from app.schemas.user_company import UserCompaniesUpdate
from app.services.dashboard_service import get_dashboard_summary


class CompanyScopeTests(unittest.TestCase):
    def setUp(self):
        self.engine=create_engine("sqlite://",connect_args={"check_same_thread":False},poolclass=StaticPool);Base.metadata.create_all(self.engine);self.db=Session(self.engine)
        self.a,self.b=Company(name="Company A"),Company(name="Company B");master=Executive(full_name="Exec One",status="Active")
        self.admin=User(full_name="Admin",username="admin",email="admin@example.com",password_hash="x",role="Admin")
        self.manager=User(full_name="Manager",username="manager",email="manager@example.com",password_hash="x",role="Manager")
        self.executive=User(full_name="Executive",username="exec",email="exec@example.com",password_hash="x",role="Executive",executive=master)
        self.db.add_all([self.a,self.b,master,self.admin,self.manager,self.executive]);self.db.flush()
        self.db.add_all([UserCompany(user_id=self.manager.id,company_id=self.a.id),UserCompany(user_id=self.executive.id,company_id=self.a.id)])
        self.case_a=Case(case_no="A-1",company_id=self.a.id,company=self.a.name,executive="Exec One",status="Pending")
        self.case_b=Case(case_no="B-1",company_id=self.b.id,company=self.b.name,executive="Exec One",status="Pending")
        self.db.add_all([self.case_a,self.case_b]);self.db.flush();self.db.add_all([CaseVisit(case_id=self.case_a.id,visit_type="Residence",executive="Exec One",status="Pending"),CaseVisit(case_id=self.case_b.id,visit_type="Residence",executive="Exec One",status="Pending")]);self.db.commit()
        self.request=Request({"type":"http","headers":[]})

    def tearDown(self):self.db.close();Base.metadata.drop_all(self.engine);self.engine.dispose()

    def test_admin_sees_all_and_manager_executive_see_assigned_only(self):
        self.assertEqual({x.id for x in get_companies(db=self.db,user=self.admin)["items"]},{self.a.id,self.b.id})
        self.assertEqual([x.id for x in get_cases(self.request,self.db,self.manager)],[self.case_a.id])
        self.assertEqual([x.id for x in get_cases(self.request,self.db,self.executive)],[self.case_a.id])

    def test_no_assignments_and_removal_never_fall_back_to_all(self):
        update_user_companies(self.manager.id,UserCompaniesUpdate(company_ids=[]),self.db,self.admin)
        self.assertEqual(get_cases(self.request,self.db,self.manager),[])
        summary=get_dashboard_summary(self.db,company_ids=set())
        self.assertEqual(summary.total_cases,0)

    def test_non_admin_cannot_change_assignments(self):
        with self.assertRaises(HTTPException) as raised:update_user_companies(self.manager.id,UserCompaniesUpdate(company_ids=[self.b.id]),self.db,self.manager)
        self.assertEqual(raised.exception.status_code,403)

    def test_manager_dashboard_is_company_scoped(self):
        summary=get_dashboard_summary(self.db,company_ids={self.a.id})
        self.assertEqual(summary.total_cases,1)

    def test_dashboard_totals_match_scoped_visit_status_filters(self):
        # Keep the parent legacy status Pending to prove dashboard statistics use visits.
        self.db.add_all([
            CaseVisit(case_id=self.case_a.id,visit_type="Office",executive="Exec One",status="Positive",closed_date=date.today()),
            CaseVisit(case_id=self.case_a.id,visit_type="Business",executive="Exec One",status="Negative",closed_date=date.today()),
        ])
        self.db.commit()
        summary=get_dashboard_summary(self.db,company_ids={self.a.id})
        self.assertEqual(summary.total_cases,3)
        self.assertEqual(summary.pending_cases,1)
        self.assertEqual(summary.positive_cases,1)
        self.assertEqual(summary.negative_cases,1)

        executive_summary=get_dashboard_summary(self.db,executive_scope="Exec One",company_ids={self.a.id})
        self.assertEqual(executive_summary,summary)


if __name__=="__main__":unittest.main()
