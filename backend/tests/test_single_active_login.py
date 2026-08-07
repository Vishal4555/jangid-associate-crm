import os, unittest
os.environ.setdefault("DATABASE_URL","sqlite://")
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import app.db.base  # noqa
from app.db.database import Base
from app.core.security import verify_token
from app.core.security import get_current_user
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from app.models.user import User, UserSession
from app.services.auth_service import build_token_response
from app.api.auth import logout
from app.api.users import force_logout

class SingleActiveLoginTests(unittest.TestCase):
    def setUp(self):
        self.engine=create_engine("sqlite://");Base.metadata.create_all(self.engine);self.db=Session(self.engine)
    def tearDown(self):self.db.close();self.engine.dispose()
    def user(self,role,name):
        row=User(full_name=name,username=name.lower(),email=f"{name.lower()}@test.local",password_hash="x",role=role,is_active=True);self.db.add(row);self.db.commit();return row
    def sessions(self,user):return self.db.query(UserSession).filter(UserSession.user_id==user.id).order_by(UserSession.id).all()
    def test_manager_and_executive_second_login_revoke_first(self):
        for role in ("Manager","Executive"):
            user=self.user(role,role);first=build_token_response(self.db,user,"A","1.1.1.1");second=build_token_response(self.db,user,"B","2.2.2.2")
            rows=self.sessions(user);self.assertIsNotNone(rows[0].revoked_at);self.assertEqual(rows[0].revoke_reason,"NEW_LOGIN");self.assertIsNone(rows[1].revoked_at)
            self.assertNotEqual(verify_token(first.access_token)["jti"],verify_token(second.access_token)["jti"])
            with self.assertRaises(HTTPException) as revoked:
                get_current_user(HTTPAuthorizationCredentials(scheme="Bearer",credentials=first.access_token),self.db)
            self.assertEqual((revoked.exception.status_code,revoked.exception.detail),(401,"SESSION_REVOKED"))
    def test_admin_sessions_coexist(self):
        user=self.user("Admin","AdminSessions");build_token_response(self.db,user);build_token_response(self.db,user)
        self.assertEqual(sum(x.revoked_at is None for x in self.sessions(user)),2)
    def test_logout_and_force_logout(self):
        user=self.user("Manager","LogoutManager");token=build_token_response(self.db,user);user.current_session_jti=verify_token(token.access_token)["jti"]
        logout(user,self.db);self.assertEqual(self.sessions(user)[0].revoke_reason,"LOGOUT")
        build_token_response(self.db,user);admin=self.user("Admin","ForceAdmin");force_logout(user.id,self.db,admin)
        self.assertFalse(any(x.revoked_at is None for x in self.sessions(user)))

if __name__=="__main__":unittest.main()
