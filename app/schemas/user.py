from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr = Field(description= "User email", examples=['email@email.com'])
    password: str = Field(description= "User password")



# class UserInDBBase(UserBase):
#     wallet_id: str = Field(description= "User's wallet id")
#     is_admin: Optional[bool] = Field(default=False, description="Is Admin")
#     created_at: datetime = Field(description="Created datetime")
    
#     class Config:
#         from_attributes = True
#         populate_by_name = True

# class UserInDB(UserInDBBase):
#     password: str = Field(description="User's password")

# class UserCreate(UserBase):
#     password: str = Field(description= "User password")