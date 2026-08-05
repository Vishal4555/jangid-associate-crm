import os
import unittest

os.environ.setdefault("DATABASE_URL", "sqlite:///./permission-tests.db")

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import app.db.base
from app.api.users import create_user, update_user_permissions, update_user
from app.core.permissions import ALL_PERMISSION_CODES, default_permissions
from app.core.security import has_permission, require_permission
from app.db.database import Base
from app.models.master import Executive
from app.models.user import User, UserAuditLog
from app.schemas.auth import UserCreate, UserUpdate
from app.schemas.permission import UserPermissionsUpdate


PASSWORD="StrongPassword1!"


class PermissionTests(unittest.TestCase):
    def setUp(self):
        self.engine=create_engine("sqlite://",connect_args={"check_same_thread":False},poolclass=StaticPool);Base.metadata.create_all(self.engine);self.db=Session(self.engine)
        self.admin=User(full_name="Admin",username="admin",email="admin@example.com",mobile="9999999999",password_hash="x",role="Admin",is_active=True)
        self.executive_master=Executive(full_name="Exec One",status="Active");self.db.add_all([self.admin,self.executive_master]);self.db.commit()

    def tearDown(self): self.db.close();Base.metadata.drop_all(self.engine);self.engine.dispose()

    def test_admin_always_has_every_permission(self):
        self.assertEqual(set(self.admin.permissions),set(ALL_PERMISSION_CODES))
        self.assertTrue(all(has_permission(self.admin,code) for code in ALL_PERMISSION_CODES))

    def test_new_manager_and_executive_receive_defaults(self):
        manager=create_user(UserCreate(full_name="Manager",username="manager",email="manager@example.com",mobile="8888888888",password=PASSWORD,role="Manager"),self.db,self.admin)
        executive=create_user(UserCreate(full_name="Executive",username="executive",email="executive@example.com",mobile="7777777777",password=PASSWORD,role="Executive",executive_id=self.executive_master.id),self.db,self.admin)
        self.assertEqual(set(manager.permissions),default_permissions("Manager"));self.assertEqual(set(executive.permissions),default_permissions("Executive"))

    def test_grant_and_removal_control_permission_dependency(self):
        manager=create_user(UserCreate(full_name="Manager",username="manager",email="manager@example.com",mobile="8888888888",password=PASSWORD,role="Manager"),self.db,self.admin)
        codes=set(manager.permissions)|{"billing.view","users.manage_permissions"}
        result=update_user_permissions(manager.id,UserPermissionsUpdate(permission_codes=sorted(codes)),self.db,self.admin)
        self.assertIn("billing.view",result["permission_codes"]);self.assertIs(require_permission("billing.view")(manager),manager)
        update_user_permissions(manager.id,UserPermissionsUpdate(permission_codes=sorted(codes-{"billing.view"})),self.db,self.admin)
        with self.assertRaises(HTTPException) as raised: require_permission("billing.view")(manager)
        self.assertEqual(raised.exception.status_code,403)

    def test_manage_permission_is_required_and_inactive_fails(self):
        manager=create_user(UserCreate(full_name="Manager",username="manager",email="manager@example.com",mobile="8888888888",password=PASSWORD,role="Manager"),self.db,self.admin)
        with self.assertRaises(HTTPException) as raised: require_permission("users.manage_permissions")(manager)
        self.assertEqual(raised.exception.status_code,403)
        manager.is_active=False;self.assertFalse(has_permission(manager,"cases.view"))

    def test_role_change_adds_defaults_without_removing_manual_grants(self):
        manager=create_user(UserCreate(full_name="Manager",username="manager",email="manager@example.com",mobile="8888888888",password=PASSWORD,role="Manager"),self.db,self.admin)
        update_user_permissions(manager.id,UserPermissionsUpdate(permission_codes=[*manager.permissions,"billing.view"]),self.db,self.admin)
        update_user(manager.id,UserUpdate(role="Executive",executive_id=self.executive_master.id),self.db,self.admin)
        self.assertIn("billing.view",manager.permissions)
        self.assertTrue(default_permissions("Executive").issubset(set(manager.permissions)))
        self.assertEqual(self.db.query(UserAuditLog).filter_by(target_user_id=manager.id,action="ROLE_CHANGED").count(),1)


if __name__=="__main__": unittest.main()
