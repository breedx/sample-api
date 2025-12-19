"""
JWT-based authentication for multi-tenant API
"""
from datetime import datetime, timedelta, UTC
from typing import Optional
import jwt
import bcrypt
from fastapi import HTTPException, status, Depends, Header
from pydantic import BaseModel
from app.config import settings


class TokenData(BaseModel):
    """JWT token payload"""
    user_id: str
    tenant_id: str
    username: str
    role: str  # "admin" or "user"
    exp: datetime


class TokenPair(BaseModel):
    """Access and refresh tokens"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


def hash_password(password: str) -> str:
    """Hash password with bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


def create_access_token(user_id: str, tenant_id: str, username: str, role: str) -> str:
    """Create JWT access token"""
    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "user_id": user_id,
        "tenant_id": tenant_id,
        "username": username,
        "role": role,
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(user_id: str, tenant_id: str) -> str:
    """Create JWT refresh token"""
    expire = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    payload = {
        "user_id": user_id,
        "tenant_id": tenant_id,
        "exp": expire,
        "type": "refresh",
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(authorization: Optional[str] = Header(None)) -> TokenData:
    """Dependency to extract current user from JWT token"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(token)

    # Verify it's an access token
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    return TokenData(
        user_id=payload["user_id"],
        tenant_id=payload["tenant_id"],
        username=payload["username"],
        role=payload["role"],
        exp=datetime.fromtimestamp(payload["exp"], UTC),
    )


async def require_admin(current_user: TokenData = Depends(get_current_user)) -> TokenData:
    """Dependency to require admin role"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user
