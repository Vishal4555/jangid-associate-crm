import os
import unittest

os.environ.setdefault("DATABASE_URL", "sqlite:///./users-security-tests.db")

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import app.db.base
from app.api.users import create_user, reset_password, update_user
from app.core.security import hash_password, require_roles, verify_password
from app.db.database import Base
from app.models.master import Executive
from app.models.user import User, UserAuditLog
from app.schemas.auth import PasswordReset, UserCreate, UserLogin, UserUpdate
from app.services.auth_service import authenticate_user


PASSWORD = "StrongPassword1!"


class UsersSecurityTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine); self.db = Session(self.engine)
        self.admin = User(full_name="Admin", username="admin", email="admin@example.com", password_hash=hash_password(PASSWORD), role="Admin", is_active=True)
        self.manager = User(full_name="Manager", username="manager", email="manager@example.com", password_hash=hash_password(PASSWORD), role="Manager", is_active=True)
        self.executive = Executive(full_name="Assigned Executive", status="Active")
        self.db.add_all([self.admin, self.manager, self.executive]); self.db.commit()

    def tearDown(self):
        self.db.close(); Base.metadata.drop_all(self.engine); self.engine.dispose()

    def test_duplicate_email_is_rejected_case_insensitively(self):
        with self.assertRaises(HTTPException) as raised:
            create_user(UserCreate(full_name="Duplicate", username="different", email="ADMIN@EXAMPLE.COM", mobile="9999999999", password=PASSWORD, role="Manager"), self.db, self.admin)
        self.assertEqual(raised.exception.status_code, 409)

    def test_last_admin_cannot_be_deactivated(self):
        with self.assertRaises(HTTPException) as raised:
            update_user(self.admin.id, UserUpdate(is_active=False), self.db, self.admin)
        self.assertEqual(raised.exception.status_code, 400)

    def test_executive_link_is_required_and_unique_for_active_users(self):
        with self.assertRaises(ValidationError):
            UserCreate(full_name="Unlinked", username="unlinked", email="u@example.com", mobile="9999999999", password=PASSWORD, role="Executive")
        first = create_user(UserCreate(full_name="First", username="first", email="first@example.com", mobile="9999999999", password=PASSWORD, role="Executive", executive_id=self.executive.id), self.db, self.admin)
        self.assertEqual(first.executive_id, self.executive.id)
        with self.assertRaises(HTTPException) as raised:
            create_user(UserCreate(full_name="Second", username="second", email="second@example.com", mobile="8888888888", password=PASSWORD, role="Executive", executive_id=self.executive.id), self.db, self.admin)
        self.assertEqual(raised.exception.status_code, 409)

    def test_inactive_user_cannot_login(self):
        self.manager.is_active = False; self.db.commit()
        self.assertIsNone(authenticate_user(self.db, UserLogin(username="MANAGER", password=PASSWORD)))

    def test_password_reset_rehashes_and_audits(self):
        replacement = "ReplacementPass2@"
        reset_password(self.manager.id, PasswordReset(password=replacement), self.db, self.admin)
        self.db.refresh(self.manager)
        self.assertTrue(verify_password(replacement, self.manager.password_hash))
        self.assertEqual(self.db.query(UserAuditLog).filter_by(target_user_id=self.manager.id, action="PASSWORD_RESET").count(), 1)

    def test_unauthorized_role_guard_returns_403(self):
        dependency = require_roles("Admin")
        with self.assertRaises(HTTPException) as raised: dependency(self.manager)
        self.assertEqual(raised.exception.status_code, 403)

    def test_manager_create_accepts_email_username_and_normalizes_identity(self):
        created = create_user(UserCreate(full_name=' Nisha Kumari ', username=' prasadnisha727@gmail.com ', email=' PRASADNISHA727@GMAIL.COM ', mobile='82090 08140', password=PASSWORD, role='Manager'), self.db, self.admin)
        self.assertEqual(created.username, 'prasadnisha727@gmail.com')
        self.assertEqual(created.email, 'prasadnisha727@gmail.com')
        self.assertEqual(created.mobile, '8209008140')

    def test_invalid_mobile_has_field_validation_error(self):
        with self.assertRaises(ValidationError) as raised:
            UserCreate(full_name='Invalid', username='invalid-user', email='invalid@example.com', mobile='123', password=PASSWORD, role='Manager')
        self.assertEqual(raised.exception.errors()[0]['loc'], ('mobile',))

    def test_non_admin_cannot_create_admin(self):
        with self.assertRaises(HTTPException) as raised:
            create_user(UserCreate(full_name='New Admin', username='new-admin', email='new-admin@example.com', mobile='8888888888', password=PASSWORD, role='Admin'), self.db, self.manager)
        self.assertEqual(raised.exception.status_code, 403)


if __name__ == "__main__": unittest.main()
