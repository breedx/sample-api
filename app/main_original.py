"""
Simple User Management API for pytest Assessment
Mimics RAD team's FastAPI patterns (similar to VizioGram API)
"""
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from typing import Dict, List, Optional
from datetime import datetime
import uuid

app = FastAPI(title="User Management API", version="1.0.0")

# In-memory storage (simulating database)
users_db: Dict[str, dict] = {}


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=100)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)


class User(BaseModel):
    id: str
    username: str
    email: str
    full_name: str
    created_at: datetime
    updated_at: datetime
    is_active: bool = True


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.post("/users", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate):
    """Create a new user"""
    # Check if username already exists
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

    user_id = str(uuid.uuid4())
    now = datetime.utcnow()

    user = {
        "id": user_id,
        "username": user_data.username,
        "email": user_data.email,
        "full_name": user_data.full_name,
        "created_at": now,
        "updated_at": now,
        "is_active": True
    }

    users_db[user_id] = user
    return user


@app.get("/users", response_model=List[User])
async def list_users(active_only: bool = True):
    """List all users, optionally filter by active status"""
    if not active_only:
        return [user for user in users_db.values() if user["is_active"]]
    return list(users_db.values())


@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: str):
    """Get a specific user by ID"""
    if user_id not in users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id '{user_id}' not found"
        )
    return users_db[user_id]


@app.put("/users/{user_id}", response_model=User)
async def update_user(user_id: str, user_data: UserUpdate):
    """Update a user's information"""
    if user_id not in users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id '{user_id}' not found"
        )

    user = users_db[user_id]

    # Check for email conflicts if email is being updated
    if user_data.email and user_data.email != user["email"]:
        for uid, u in users_db.items():
            if uid != user_id and u["email"] == user_data.email:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Email '{user_data.email}' already exists"
                )

    # Update fields
    if user_data.email:
        user["email"] = user_data.email
    if user_data.full_name is not None:
        user["full_name"] = user_data.full_name

    user["updated_at"] = datetime.utcnow()
    users_db[user_id] = user

    return user


@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str):
    """Soft delete a user (sets is_active to False)"""
    if user_id not in users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id '{user_id}' not found"
        )

    users_db[user_id]["is_active"] = False
    users_db[user_id]["updated_at"] = datetime.utcnow()


@app.delete("/users/{user_id}/permanent", status_code=status.HTTP_204_NO_CONTENT)
async def permanently_delete_user(user_id: str):
    """Permanently delete a user from the database"""
    if user_id not in users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id '{user_id}' not found"
        )

    user = users_db[user_id]
    del users_db[user_id]
    return {"deleted": user["username"]}


# Test helper endpoint - clear all data
@app.post("/test/reset")
async def reset_database():
    """Reset the database (for testing purposes only)"""
    users_db.clear()
    return {"message": "Database reset successfully"}
