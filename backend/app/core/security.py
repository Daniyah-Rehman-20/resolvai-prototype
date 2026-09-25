from dataclasses import dataclass
from fastapi import Depends, Header, HTTPException, status
from app.core.config import settings

ROLES = {"viewer": 1, "analyst": 2, "approver": 3, "admin": 4}

@dataclass(frozen=True)
class Principal:
    subject: str
    role: str

async def current_principal(
    authorization: str | None = Header(default=None),
    x_demo_role: str | None = Header(default=None),
    x_demo_user: str | None = Header(default=None),
) -> Principal:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    if token != settings.auth_demo_token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid bearer token")

    role = (x_demo_role or "viewer").lower()
    if role not in ROLES:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Unknown role")
    return Principal(subject=(x_demo_user or "demo-user").strip(), role=role)

def require(min_role: str):
    if min_role not in ROLES:
        raise ValueError(f"Unknown minimum role: {min_role}")

    async def dependency(principal: Principal = Depends(current_principal)) -> Principal:
        if ROLES[principal.role] < ROLES[min_role]:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient role")
        return principal
    return dependency
