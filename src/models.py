from typing import Optional
from sqlalchemy import Column, Integer, String
from pydantic import BaseModel, Field
from .database import Base

#SQLAlchemy model for the database
class UserDB(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)

#Pydantic model for request validation (input)
class UserCreate(BaseModel):
    username: str = Field(..., example="testuser")
    password: str = Field(..., example="testpassword")

# Pydantic model for response (output)
class UserResponse(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True 

#Pydantic model for updating user details
class UserUpdate(BaseModel):
    #Optional choices to update said user
    id: Optional[int] = Field(None)  # self explanatory
    username: Optional[str] = Field(None)  # self explanatory
    password: Optional[str] = Field(None)  # self explanatory

    class Config:
        from_attributes = True
    