from sqlalchemy.exc import SQLAlchemyError

from app.core.security import hash_password
from app.db.base import Base
from app.db.database import SessionLocal, engine
from app.models.user import User
from app.services.permission_service import ensure_permission_catalog


ADMIN_USERNAME = "admin"
ADMIN_EMAIL = "admin@jangidcrm.com"
ADMIN_PASSWORD = "Admin@Change123!"
ADMIN_ROLE = "Admin"


def seed_admin_user() -> None:
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        ensure_permission_catalog(db)
        existing_user = (
            db.query(User)
            .filter((User.username == ADMIN_USERNAME) | (User.email == ADMIN_EMAIL))
            .first()
        )

        if existing_user is not None:
            db.commit()
            print("Admin user already exists. No changes made.")
            return

        admin_user = User(
            full_name="Admin User",
            username=ADMIN_USERNAME,
            email=ADMIN_EMAIL,
            password_hash=hash_password(ADMIN_PASSWORD),
            role=ADMIN_ROLE,
            is_active=True,
        )

        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

        print(f"Admin user created with id={admin_user.id}.")
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_admin_user()
