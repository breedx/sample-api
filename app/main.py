"""
Advanced Multi-Tenant User & File Management API with Authentication
For Senior QA Automation Assessment
"""
from fastapi import FastAPI, HTTPException, status, Depends, File, UploadFile, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr, Field
from typing import Dict, List, Optional
from datetime import datetime, UTC
import uuid
import io
import asyncio
from collections import defaultdict
from time import time

from app.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    require_admin,
    TokenData,
    TokenPair,
)
from app.config import settings

app = FastAPI(
    title="Multi-Tenant User & File Management API",
    version="2.0.0",
    description="Advanced assessment with authentication, multi-tenancy, and file management",
)

# In-memory storage (simulating database)
tenants_db: Dict[str, dict] = {}  # tenant_id -> tenant data
users_db: Dict[str, dict] = {}  # user_id -> user data
files_db: Dict[str, dict] = {}  # file_id -> file metadata
file_storage: Dict[str, bytes] = {}  # file_id -> file content
blacklisted_tokens: set = set()  # Invalidated tokens

# Rate limiting storage (in production, use Redis)
rate_limit_store: Dict[str, List[float]] = defaultdict(list)


# ============================================================================
# MODELS
# ============================================================================


class TenantRegister(BaseModel):
    """Register a new tenant with admin user"""

    tenant_name: str = Field(..., min_length=3, max_length=50)
    admin_email: EmailStr
    admin_username: str = Field(..., min_length=3, max_length=50)
    admin_password: str = Field(..., min_length=8)


class LoginRequest(BaseModel):
    """Login credentials"""

    username: str
    password: str


class RefreshRequest(BaseModel):
    """Refresh token request"""

    refresh_token: str


class UserCreate(BaseModel):
    """Create a new user in tenant"""

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=100)
    role: str = Field(default="user", pattern="^(user|admin)$")


class UserUpdate(BaseModel):
    """Update user information"""

    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)


class User(BaseModel):
    """User response model"""

    id: str
    tenant_id: str
    username: str
    email: str
    full_name: str
    role: str
    created_at: datetime
    updated_at: datetime
    is_active: bool = True


class PaginatedResponse(BaseModel):
    """Generic paginated response"""

    data: List[dict]
    page: int
    page_size: int
    total_count: int
    has_next: bool
    has_prev: bool


class FileMetadata(BaseModel):
    """File metadata response"""

    id: str
    tenant_id: str
    filename: str
    content_type: str
    size_bytes: int
    uploaded_by: str
    uploaded_at: datetime


# ============================================================================
# RATE LIMITING MIDDLEWARE
# ============================================================================


def check_rate_limit(request: Request, user_id: str):
    """Check if request exceeds rate limit"""
    endpoint = f"{request.method}:{request.url.path}"
    key = f"{user_id}:{endpoint}"
    now = time()

    # Clean old entries
    rate_limit_store[key] = [
        ts for ts in rate_limit_store[key] if now - ts < 60
    ]  # Last minute

    if len(rate_limit_store[key]) >= settings.rate_limit_per_minute:
        reset_time = int(rate_limit_store[key][0] + 60)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={
                "X-RateLimit-Limit": str(settings.rate_limit_per_minute),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(reset_time),
            },
        )

    rate_limit_store[key].append(now)


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(UTC).isoformat(),
        "environment": settings.api_env,
        "version": "2.0.0",
    }


@app.post("/auth/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register_tenant(tenant_data: TenantRegister):
    """Register a new tenant with admin user"""

    # Check if tenant name already exists
    for tenant in tenants_db.values():
        if tenant["name"].lower() == tenant_data.tenant_name.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Tenant '{tenant_data.tenant_name}' already exists",
            )

    # Check if username already exists
    for user in users_db.values():
        if user["username"] == tenant_data.admin_username:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Username '{tenant_data.admin_username}' already exists",
            )

    # Create tenant
    tenant_id = str(uuid.uuid4())
    now = datetime.now(UTC)
    tenants_db[tenant_id] = {
        "id": tenant_id,
        "name": tenant_data.tenant_name,
        "created_at": now,
        "is_active": True,
    }

    # Create admin user
    user_id = str(uuid.uuid4())
    users_db[user_id] = {
        "id": user_id,
        "tenant_id": tenant_id,
        "username": tenant_data.admin_username,
        "email": tenant_data.admin_email,
        "full_name": "Admin User",
        "password_hash": hash_password(tenant_data.admin_password),
        "role": "admin",
        "created_at": now,
        "updated_at": now,
        "is_active": True,
    }

    return {
        "message": "Tenant registered successfully",
        "tenant_id": tenant_id,
        "admin_user_id": user_id,
    }


@app.post("/auth/login", response_model=TokenPair)
async def login(credentials: LoginRequest):
    """Authenticate and get access/refresh tokens"""

    # Find user by username
    user = None
    for u in users_db.values():
        if u["username"] == credentials.username:
            user = u
            break

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    # Verify password
    if not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    # Check if user is active
    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User account is deactivated"
        )

    # Create tokens
    access_token = create_access_token(
        user["id"], user["tenant_id"], user["username"], user["role"]
    )
    refresh_token = create_refresh_token(user["id"], user["tenant_id"])

    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
    )


@app.post("/auth/refresh", response_model=TokenPair)
async def refresh_tokens(request: RefreshRequest):
    """Refresh access token using refresh token"""

    payload = decode_token(request.refresh_token)

    # Verify it's a refresh token
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type"
        )

    # Check if token is blacklisted
    if request.refresh_token in blacklisted_tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked"
        )

    user_id = payload["user_id"]
    user = users_db.get(user_id)

    if not user or not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive"
        )

    # Create new tokens
    access_token = create_access_token(
        user["id"], user["tenant_id"], user["username"], user["role"]
    )
    new_refresh_token = create_refresh_token(user["id"], user["tenant_id"])

    # Blacklist old refresh token
    blacklisted_tokens.add(request.refresh_token)

    return TokenPair(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
    )


@app.post("/auth/logout")
async def logout(
    authorization: str = Depends(lambda auth=None: auth),
    current_user: TokenData = Depends(get_current_user),
):
    """Logout and invalidate token"""
    # In a real system, would blacklist the token
    # For this assessment, we simulate it
    return {"message": "Logged out successfully"}


# ============================================================================
# USER MANAGEMENT ENDPOINTS (Multi-Tenant + Authenticated)
# ============================================================================


@app.get("/api/v1/users", response_model=PaginatedResponse)
async def list_users(
    request: Request,
    page: int = 1,
    page_size: int = 20,
    active_only: bool = True,
    current_user: TokenData = Depends(get_current_user),
):
    """List users in current tenant (paginated)"""

    check_rate_limit(request, current_user.user_id)

    # Filter users by tenant
    tenant_users = [
        u for u in users_db.values() if u["tenant_id"] == current_user.tenant_id
    ]

    # Filter by active status
    if active_only:
        tenant_users = [u for u in tenant_users if u["is_active"]]

    # Pagination
    total_count = len(tenant_users)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    page_data = tenant_users[start_idx:end_idx]

    # Remove sensitive fields
    safe_users = [
        {k: v for k, v in u.items() if k != "password_hash"} for u in page_data
    ]

    return PaginatedResponse(
        data=safe_users,
        page=page,
        page_size=page_size,
        total_count=total_count,
        has_next=end_idx < total_count,
        has_prev=page > 1,
    )


@app.post("/api/v1/users", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: Request,
    user_data: UserCreate,
    current_user: TokenData = Depends(get_current_user),
):
    """Create a new user in current tenant"""

    check_rate_limit(request, current_user.user_id)

    # Check if username already exists
    for user in users_db.values():
        if user["username"] == user_data.username:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Username '{user_data.username}' already exists",
            )
        if user["email"] == user_data.email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Email '{user_data.email}' already exists",
            )

    user_id = str(uuid.uuid4())
    now = datetime.now(UTC)

    new_user = {
        "id": user_id,
        "tenant_id": current_user.tenant_id,  # Scoped to current tenant
        "username": user_data.username,
        "email": user_data.email,
        "full_name": user_data.full_name,
        "password_hash": hash_password("TempPassword123!"),  # Temporary password
        "role": user_data.role,
        "created_at": now,
        "updated_at": now,
        "is_active": True,
    }

    users_db[user_id] = new_user

    # Return without password_hash
    return User(**{k: v for k, v in new_user.items() if k != "password_hash"})


@app.get("/api/v1/users/{user_id}", response_model=User)
async def get_user(
    request: Request,
    user_id: str,
    current_user: TokenData = Depends(get_current_user),
):
    """Get specific user (tenant-scoped)"""

    check_rate_limit(request, current_user.user_id)

    user = users_db.get(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id '{user_id}' not found",
        )

    # Verify tenant access
    if user["tenant_id"] != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id '{user_id}' not found",
        )

    return User(**{k: v for k, v in user.items() if k != "password_hash"})


@app.put("/api/v1/users/{user_id}", response_model=User)
async def update_user(
    request: Request,
    user_id: str,
    user_data: UserUpdate,
    current_user: TokenData = Depends(get_current_user),
):
    """Update user information (tenant-scoped)"""

    check_rate_limit(request, current_user.user_id)

    user = users_db.get(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id '{user_id}' not found",
        )

    # Verify tenant access
    if user["tenant_id"] != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id '{user_id}' not found",
        )

    # Check email conflicts
    if user_data.email and user_data.email != user["email"]:
        for uid, u in users_db.items():
            if uid != user_id and u["email"] == user_data.email:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Email '{user_data.email}' already exists",
                )

    # Update fields
    if user_data.email:
        user["email"] = user_data.email
    if user_data.full_name is not None:
        user["full_name"] = user_data.full_name

    user["updated_at"] = datetime.now(UTC)

    return User(**{k: v for k, v in user.items() if k != "password_hash"})


@app.delete("/api/v1/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    request: Request,
    user_id: str,
    current_user: TokenData = Depends(get_current_user),
):
    """Soft delete user (tenant-scoped)"""

    check_rate_limit(request, current_user.user_id)

    user = users_db.get(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id '{user_id}' not found",
        )

    # Verify tenant access
    if user["tenant_id"] != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id '{user_id}' not found",
        )

    user["is_active"] = False
    user["updated_at"] = datetime.now(UTC)


@app.post("/api/v1/users/bulk", response_model=List[User], status_code=status.HTTP_201_CREATED)
async def create_users_bulk(
    request: Request,
    users_data: List[UserCreate],
    current_user: TokenData = Depends(get_current_user),
):
    """
    Create multiple users in parallel (demonstrates async patterns).

    This endpoint uses asyncio.gather() to simulate concurrent operations.
    Tests should use @pytest.mark.asyncio to properly test async behavior.
    """
    check_rate_limit(request, current_user.user_id)

    if len(users_data) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create more than 50 users at once"
        )

    async def create_single_user(user_data: UserCreate):
        """Async helper to simulate I/O-bound user creation"""
        # Check for duplicates
        for user in users_db.values():
            if user["username"] == user_data.username:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Username '{user_data.username}' already exists"
                )
            if user["email"] == user_data.email:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Email '{user_data.email}' already exists"
                )

        # Simulate async operation (e.g., database write, external API call)
        await asyncio.sleep(0.01)  # Simulate I/O delay

        user_id = str(uuid.uuid4())
        now = datetime.now(UTC)

        new_user = {
            "id": user_id,
            "tenant_id": current_user.tenant_id,
            "username": user_data.username,
            "email": user_data.email,
            "full_name": user_data.full_name,
            "password_hash": hash_password("TempPassword123!"),
            "role": user_data.role,
            "created_at": now,
            "updated_at": now,
            "is_active": True,
        }

        users_db[user_id] = new_user
        return User(**{k: v for k, v in new_user.items() if k != "password_hash"})

    # Execute all user creations concurrently
    try:
        created_users = await asyncio.gather(
            *[create_single_user(user_data) for user_data in users_data]
        )
        return created_users
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk user creation failed: {str(e)}"
        )


# ============================================================================
# FILE MANAGEMENT ENDPOINTS (Simulating S3)
# ============================================================================


@app.post("/api/v1/files/upload", response_model=FileMetadata, status_code=status.HTTP_201_CREATED)
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    current_user: TokenData = Depends(get_current_user),
):
    """Upload a file (simulating S3 upload)"""

    check_rate_limit(request, current_user.user_id)

    # Validate file type
    if file.content_type not in settings.allowed_file_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File type '{file.content_type}' not allowed",
        )

    # Read file content
    content = await file.read()

    # Validate file size
    size_mb = len(content) / (1024 * 1024)
    if size_mb > settings.max_file_size_mb:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size {size_mb:.2f}MB exceeds limit of {settings.max_file_size_mb}MB",
        )

    # Store file
    file_id = str(uuid.uuid4())
    now = datetime.now(UTC)

    file_metadata = {
        "id": file_id,
        "tenant_id": current_user.tenant_id,
        "filename": file.filename,
        "content_type": file.content_type,
        "size_bytes": len(content),
        "uploaded_by": current_user.user_id,
        "uploaded_at": now,
    }

    files_db[file_id] = file_metadata
    file_storage[file_id] = content

    return FileMetadata(**file_metadata)


@app.get("/api/v1/files/{file_id}")
async def download_file(
    request: Request,
    file_id: str,
    current_user: TokenData = Depends(get_current_user),
):
    """Download a file (tenant-scoped)"""

    check_rate_limit(request, current_user.user_id)

    file_meta = files_db.get(file_id)

    if not file_meta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with id '{file_id}' not found",
        )

    # Verify tenant access
    if file_meta["tenant_id"] != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with id '{file_id}' not found",
        )

    content = file_storage.get(file_id)
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File content not found",
        )

    return StreamingResponse(
        io.BytesIO(content),
        media_type=file_meta["content_type"],
        headers={"Content-Disposition": f'attachment; filename="{file_meta["filename"]}"'},
    )


@app.get("/api/v1/files", response_model=PaginatedResponse)
async def list_files(
    request: Request,
    page: int = 1,
    page_size: int = 20,
    current_user: TokenData = Depends(get_current_user),
):
    """List files in current tenant (paginated)"""

    check_rate_limit(request, current_user.user_id)

    # Filter files by tenant
    tenant_files = [
        f for f in files_db.values() if f["tenant_id"] == current_user.tenant_id
    ]

    # Pagination
    total_count = len(tenant_files)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    page_data = tenant_files[start_idx:end_idx]

    return PaginatedResponse(
        data=page_data,
        page=page,
        page_size=page_size,
        total_count=total_count,
        has_next=end_idx < total_count,
        has_prev=page > 1,
    )


@app.delete("/api/v1/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    request: Request,
    file_id: str,
    current_user: TokenData = Depends(get_current_user),
):
    """Delete a file (tenant-scoped)"""

    check_rate_limit(request, current_user.user_id)

    file_meta = files_db.get(file_id)

    if not file_meta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with id '{file_id}' not found",
        )

    # Verify tenant access
    if file_meta["tenant_id"] != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with id '{file_id}' not found",
        )

    # Delete file
    del files_db[file_id]
    if file_id in file_storage:
        del file_storage[file_id]


# ============================================================================
# ADMIN ENDPOINTS (Admin Role Only)
# ============================================================================


@app.get("/api/v1/admin/tenants")
async def list_all_tenants(
    request: Request, current_user: TokenData = Depends(require_admin)
):
    """List all tenants (admin only)"""

    check_rate_limit(request, current_user.user_id)

    return {"tenants": list(tenants_db.values()), "total": len(tenants_db)}


@app.get("/api/v1/admin/stats")
async def get_system_stats(
    request: Request, current_user: TokenData = Depends(require_admin)
):
    """Get system-wide statistics (admin only)"""

    check_rate_limit(request, current_user.user_id)

    return {
        "total_tenants": len(tenants_db),
        "total_users": len(users_db),
        "total_files": len(files_db),
        "total_storage_bytes": sum(len(content) for content in file_storage.values()),
    }


# ============================================================================
# TEST HELPER ENDPOINTS (For Testing Only)
# ============================================================================


@app.post("/test/reset")
async def reset_all_data():
    """Reset all data (for testing purposes only)"""
    tenants_db.clear()
    users_db.clear()
    files_db.clear()
    file_storage.clear()
    blacklisted_tokens.clear()
    rate_limit_store.clear()
    return {"message": "All data reset successfully"}
