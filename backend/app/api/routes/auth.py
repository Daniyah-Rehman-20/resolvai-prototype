import re
import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.core.security import Principal, current_principal
from app.db.session import get_db
from app.models.auth import AuthSession, User
from app.services.auth import DUMMY_PASSWORD_HASH, create_session, hash_password, token_digest, verify_password

router = APIRouter(prefix="/auth", tags=["authentication"])


class Credentials(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        value = value.strip().lower()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            raise ValueError("Enter a valid email address")
        return value


def public_user(user: User) -> dict:
    return {"id": user.id, "email": user.email, "role": user.role}


@router.post("/register", status_code=201)
async def register(payload: Credentials, response: Response, db: AsyncSession = Depends(get_db)):
    if len(payload.password) < 12 or len(set(payload.password)) < 5:
        raise HTTPException(422, "Use a password of at least 12 characters with at least 5 distinct characters")
    user = User(id=str(uuid.uuid4()), email=payload.email, role="customer",
                password_hash=await run_in_threadpool(hash_password, payload.password))
    token, session = create_session(user.id)
    try:
        db.add(user)
        await db.flush()
        db.add(session)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(409, "Unable to register with these details") from None
    response.headers["Cache-Control"] = "no-store"
    return {"access_token": token, "token_type": "bearer", "user": public_user(user)}


@router.post("/login")
async def login(payload: Credentials, response: Response, db: AsyncSession = Depends(get_db)):
    user = await db.scalar(select(User).where(User.email == payload.email))
    valid = await run_in_threadpool(verify_password, payload.password,
                                    user.password_hash if user else DUMMY_PASSWORD_HASH)
    if not user or not valid or not user.active:
        raise HTTPException(401, "Invalid email or password", headers={"WWW-Authenticate": "Bearer"})
    token, session = create_session(user.id)
    db.add(session)
    await db.commit()
    response.headers["Cache-Control"] = "no-store"
    return {"access_token": token, "token_type": "bearer", "user": public_user(user)}


@router.get("/me")
async def me(response: Response, principal: Principal = Depends(current_principal),
             db: AsyncSession = Depends(get_db)):
    user = await db.get(User, principal.subject)
    if not user:
        raise HTTPException(401, "A registered account is required")
    response.headers["Cache-Control"] = "no-store"
    return public_user(user)


@router.post("/logout", status_code=204)
async def logout(principal: Principal = Depends(current_principal),
                 authorization: str = Header(), db: AsyncSession = Depends(get_db)):
    await db.execute(delete(AuthSession).where(
        AuthSession.token_hash == token_digest(authorization.split(" ", 1)[1].strip()),
        AuthSession.user_id == principal.subject))
    await db.commit()
    return Response(status_code=204, headers={"Cache-Control": "no-store"})
