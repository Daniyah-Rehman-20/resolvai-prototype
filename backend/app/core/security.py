from dataclasses import dataclass
from datetime import datetime, timezone
import hmac

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.models.auth import AuthSession, User
from app.services.auth import token_digest

ROLES = {"customer": 0, "viewer": 1, "analyst": 2, "approver": 3, "admin": 4}


@dataclass(frozen=True)
class Principal:
    subject: str
    role: str


async def current_principal(
    authorization: str | None = Header(default=None),
    x_demo_role: str | None = Header(default=None),
    x_demo_user: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> Principal:
    unauthorized = HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired bearer token",
                                 headers={"WWW-Authenticate": "Bearer"})
    if not authorization or not authorization.startswith("Bearer "):
        raise unauthorized
    token = authorization.removeprefix("Bearer ").strip()
    if not token or len(token) > 512:
        raise unauthorized
    if hmac.compare_digest(token.encode("utf-8"), settings.auth_demo_token.encode("utf-8")):
        if not settings.auth_demo_enabled or settings.app_env not in {"development", "test"}:
            raise unauthorized
        role = (x_demo_role or "viewer").lower()
        if role not in ROLES:
            raise HTTPException(403, "Unknown role")
        return Principal(subject=(x_demo_user or "demo-user").strip(), role=role)

    result = await db.execute(select(AuthSession, User).join(User, User.id == AuthSession.user_id)
                              .where(AuthSession.token_hash == token_digest(token)))
    row = result.first()
    if not row:
        raise unauthorized
    session, user = row
    expires = session.expires_at
    if expires.tzinfo is None:  # SQLite returns naive UTC timestamps.
        expires = expires.replace(tzinfo=timezone.utc)
    if expires <= datetime.now(timezone.utc) or not user.active or user.role not in ROLES:
        raise unauthorized
    # Role and identity always come from the database, never caller headers.
    return Principal(subject=user.id, role=user.role)


def require(min_role: str):
    if min_role not in ROLES:
        raise ValueError(f"Unknown minimum role: {min_role}")

    async def dependency(principal: Principal = Depends(current_principal)) -> Principal:
        if ROLES.get(principal.role, -1) < ROLES[min_role]:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient role")
        return principal
    return dependency
