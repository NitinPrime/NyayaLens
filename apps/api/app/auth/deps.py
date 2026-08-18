"""FastAPI dependencies."""

from typing import Optional
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import TokenUser, decode_token
from app.db.models import CaseRecord, User
from app.db.session import get_db


async def get_current_user_optional(
    authorization: Optional[str] = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> Optional[TokenUser]:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split(" ", 1)[1]
    user = decode_token(token)
    if not user:
        return None
    result = await db.execute(select(User).where(User.id == user.id, User.is_active.is_(True)))
    if result.scalar_one_or_none() is None:
        return None
    return user


async def require_user(
    user: Optional[TokenUser] = Depends(get_current_user_optional),
) -> TokenUser:
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return user


async def assert_case_access(case: CaseRecord, user: Optional[TokenUser]) -> None:
    if case.user_id is None or case.is_demo:
        return
    if user is None or user.id != case.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to access this case")
