from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.security import hash_password
from app.db.session import get_session_factory
from app.models.admin_user import AdminUser
from app.repositories.admin_user_repository import AdminUserRepository


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create or update an admin user for local testing.")
    parser.add_argument("--email", required=True, help="Admin email address")
    parser.add_argument("--password", required=True, help="Admin password")
    parser.add_argument("--full-name", default=None, help="Optional full name")
    parser.add_argument("--superuser", action="store_true", help="Mark this admin as a superuser")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    session_factory = get_session_factory()
    repository = AdminUserRepository()

    with session_factory() as db:
        email = args.email.strip().lower()
        existing = repository.get_by_email(db, email)
        if existing is None:
            admin_user = AdminUser(
                email=email,
                password_hash=hash_password(args.password),
                full_name=args.full_name,
                is_active=True,
                is_superuser=args.superuser,
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            print(f"Created admin user: {admin_user.email}")
            return

        existing.password_hash = hash_password(args.password)
        existing.full_name = args.full_name
        existing.is_active = True
        existing.is_superuser = args.superuser
        db.add(existing)
        db.commit()
        print(f"Updated admin user: {existing.email}")


if __name__ == "__main__":
    main()
