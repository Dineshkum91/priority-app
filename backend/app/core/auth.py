"""
Authentication — Supabase Auth JWT validation.

For the prototype, also supports a bypass mode for local development
when SUPABASE_JWT_SECRET is not configured.
"""

import logging
from typing import Optional
from uuid import UUID
from fastapi import Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from app.core.config import get_settings
from app.core.database import get_db
from app.models.models import User

logger = logging.getLogger(__name__)


async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> User:
    """
    Validate the Supabase JWT and return the corresponding User.

    In development mode (no JWT secret configured), accepts a header
    like "Bearer dev:<user_id>" for local testing.
    """
    settings = get_settings()

    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required.",
        )

    token = authorization.replace("Bearer ", "")

    # Dev mode bypass
    if not settings.supabase_jwt_secret or settings.supabase_jwt_secret == "your-jwt-secret":
        if token.startswith("dev:"):
            user_id_str = token[4:]
            try:
                user = db.query(User).filter(User.id == UUID(user_id_str)).first()
            except ValueError:
                # Try by supabase_uid
                user = db.query(User).filter(User.supabase_uid == user_id_str).first()

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Dev user not found: {user_id_str}",
                )
            return user
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="JWT secret not configured. Use 'Bearer dev:<user_id>' for local testing.",
            )

    # Production mode: validate Supabase JWT
    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e}",
        )

    supabase_uid = payload.get("sub")
    if not supabase_uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing 'sub' claim.",
        )

    user = db.query(User).filter(User.supabase_uid == supabase_uid).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found. Register first.",
        )

    return user
