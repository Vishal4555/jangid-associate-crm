import os,unittest
from datetime import date
from io import BytesIO
os.environ.setdefault("DATABASE_URL","sqlite://")
from openpyxl import Workbook,load_workbook
from sqlalchemy import create_engine,select
from sqlalchemy.orm import Session
import app.db.base  # noqa
from app.db.database import Base
from app.models.case import Case
from app.models.case_visit import CaseVisit
from app.models.master import Bank,Company,District,Executive
from app.models.user import User,UserCompany
from app.services.case_import_service import HEADERS,import_cases,template_bytes
from app.services.dashboard_service import get_dashboard_summary
from app.services.monthly_billing_service import monthly_billing

class CaseImportTests(unittest.TestCase):
 def setUp(self):
  self.engine=create_engine("sqlite://");Base.metadata.create_all(self.engine);self.db=Session(self.engine)
  self.company=Company(name="Agency",is_active=True);self.other=Company(name="Other",is_active=True);self.bank=Bank(name="AU Bank");self.bank2=Bank(name="BOB");self.district=District(name="Jaipur",state="Rajasthan",is_active=True);self.executive=Executive(full_name="Exec One",status="Active");self.admin=User(full_name="Admin",username="import-admin",email="import-admin@test",password_hash="x",role="Admin");self.db.add_all([self.company,self.other,self.bank,self.bank2,self.district,self.executive,self.admin]);self.db.commit()
 def tearDown(self):self.db.close();self.engine.dispose()
 def book(self,rows):
  wb=Workbook();ws=wb.active;ws.title="Case Import";ws.append(HEADERS)
  for row in rows:ws.append(row)
  out=BytesIO();wb.save(out);return out.getvalue()
 def row(self,**changes):
  values={"Visit Type":"Residence","LOS / Application No":"LOS-1","Receive Date":date(2026,8,1),"Company":"Agency","Bank / Finance Company":"AU Bank","Applicant":"Applicant","Mobile":"9876543210","Loan Type":"","Address":"Address","District":"Jaipur","City":"Jaipur","Landmark":"","Executive":"Exec One","Status":"Pending","Negative Reason":"","Remarks":""};values.update(changes);return [values[x] for x in HEADERS]
 def test_template_and_valid_multi_visit_identity(self):
  wb=load_workbook(BytesIO(template_bytes()));self.assertEqual(wb.sheetnames,["Case Import","Instructions"]);self.assertEqual([x.value for x in wb["Case Import"][1]],HEADERS)
  result=import_cases(self.db,self.admin,self.book([self.row(),self.row(**{"Visit Type":"Office","Receive Date":date(2026,8,2)})]));self.assertTrue(result.success);self.assertEqual((result.created_applications,result.created_visits),(1,2));self.assertEqual(self.db.query(CaseVisit).count(),2)
 def test_different_bank_creates_parent_and_existing_adds_visit(self):
  first=import_cases(self.db,self.admin,self.book([self.row()]));self.assertTrue(first.success)
  result=import_cases(self.db,self.admin,self.book([self.row(**{"Visit Type":"Office"}),self.row(**{"Bank / Finance Company":"BOB"})]));self.assertTrue(result.success);self.assertEqual((result.created_applications,result.updated_existing_applications),(1,1));self.assertEqual(self.db.query(Case).count(),2)
 def test_one_invalid_row_rolls_back_and_duplicate_rejected(self):
  result=import_cases(self.db,self.admin,self.book([self.row(),self.row(**{"Company":"Missing"})]));self.assertFalse(result.success);self.assertEqual(self.db.query(Case).count(),0)
  duplicate=import_cases(self.db,self.admin,self.book([self.row(),self.row()]));self.assertFalse(duplicate.success);self.assertTrue(any(x.message=="Duplicate visit row in file" for x in duplicate.errors))
 def test_negative_reason_and_manager_scope(self):
  manager=User(full_name="Manager",username="import-manager",email="import-manager@test",password_hash="x",role="Manager");self.db.add(manager);self.db.flush();self.db.add(UserCompany(user_id=manager.id,company_id=self.company.id));self.db.commit()
  negative=import_cases(self.db,manager,self.book([self.row(**{"Status":"Negative"})]));self.assertFalse(negative.success)
  scoped=import_cases(self.db,manager,self.book([self.row(**{"Company":"Other"})]));self.assertFalse(scoped.success);self.assertTrue(any("not assigned" in x.message for x in scoped.errors))
 def test_invalid_masters_and_executive_own_scope(self):
  for field,value in (("Bank / Finance Company","Missing"),("District","Missing"),("Executive","Missing")):
   result=import_cases(self.db,self.admin,self.book([self.row(**{field:value})]));self.assertFalse(result.success);self.assertEqual(self.db.query(Case).count(),0)
  other_exec=Executive(full_name="Other Exec",status="Active");executive_user=User(full_name="Exec User",username="import-exec",email="import-exec@test",password_hash="x",role="Executive",executive=self.executive);self.db.add_all([other_exec,executive_user]);self.db.flush();self.db.add(UserCompany(user_id=executive_user.id,company_id=self.company.id));self.db.commit()
  result=import_cases(self.db,executive_user,self.book([self.row(**{"Executive":"Other Exec"})]));self.assertFalse(result.success);self.assertTrue(any("only their own" in x.message for x in result.errors))
 def test_imported_visit_is_visible_to_dashboard_and_billing(self):
  result=import_cases(self.db,self.admin,self.book([self.row(**{"Status":"Positive"})]));self.assertTrue(result.success)
  dashboard=get_dashboard_summary(self.db);self.assertEqual((dashboard.total_cases,dashboard.positive_cases),(1,1))
  billing=monthly_billing(self.db,"2026-08");self.assertEqual(billing.summary.billable_cases,1)

if __name__=="__main__":unittest.main()
