"""Explicit operator-only staff provisioning; never expose this as a public endpoint.

Run from backend: python -m scripts.create_staff staff@example.com --role analyst
"""
import argparse
import asyncio
import getpass
import uuid

from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.auth import User
from app.services.auth import hash_password
from app.api.routes.auth import Credentials


async def create(email: str, role: str, password: str):
    credentials = Credentials(email=email, password=password)
    if len(password) < 12 or len(set(password)) < 5:
        raise ValueError("Use at least 12 characters with at least 5 distinct characters")
    async with SessionLocal() as db:
        if await db.scalar(select(User).where(User.email == credentials.email)):
            raise ValueError("Account already exists; review it directly before changing privileges")
        db.add(User(id=str(uuid.uuid4()), email=credentials.email, role=role,
                    password_hash=hash_password(password)))
        await db.commit()
    print(f"Created {role} account for {credentials.email}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("email")
    parser.add_argument("--role", choices=["viewer", "analyst", "approver", "admin"], default="analyst")
    args = parser.parse_args()
    password = getpass.getpass("Password (minimum 12 characters): ")
    if password != getpass.getpass("Repeat password: "):
        parser.error("Passwords do not match")
    try:
        asyncio.run(create(args.email, args.role, password))
    except ValueError as exc:
        parser.error(str(exc))
