from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr = Field(description= "User email", examples=['email@email.com'])
    password: str = Field(description= "User password")
