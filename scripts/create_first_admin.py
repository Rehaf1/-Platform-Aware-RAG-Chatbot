"""
One-time bootstrap: creates the very first admin account directly in the
database. Every account after this one is created by an admin through
POST /api/v1/admin/accounts -- but that endpoint itself requires an
admin token to call, so the first admin has to be seeded some other way.
Run this once, then log in through the UI from then on.

Usage:
    python scripts/create_first_admin.py
"""

from dotenv import load_dotenv
load_dotenv(".env")

from app.db.database import SessionLocal
from app.db.crud import get_or_create_platform, get_or_create_tenant, create_user_account, get_user_by_email
from app.auth.password import hash_password


def main():
    email = input("Admin email: ").strip()
    password = input("Admin password (min 8 chars): ").strip()
    platform_id = input("Platform id (e.g. imtithal): ").strip()
    tenant_id = input("Tenant id (e.g. demo_tenant): ").strip()

    db = SessionLocal()
    try:
        if get_user_by_email(db, email) is not None:
            print(f"An account with email {email!r} already exists. Nothing to do.")
            return

        platform = get_or_create_platform(db, platform_id)
        tenant = get_or_create_tenant(db, platform, tenant_id)

        create_user_account(
            db,
            email=email,
            password_hash=hash_password(password),
            platform=platform,
            tenant=tenant,
            role_name="admin",
        )
        print(f"Admin account created: {email} ({platform_id}/{tenant_id})")
    finally:
        db.close()


if __name__ == "__main__":
    main()
