import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str = Field(min_length=8, repr=False)


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    username: str
    sleeper_user_id: str | None = Field(default=None)
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )
