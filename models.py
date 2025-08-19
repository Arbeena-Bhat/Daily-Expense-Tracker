from typing import Optional
from pydantic import BaseModel, Field,EmailStr
from datetime import datetime

# Model for adding expenses
class Expense(BaseModel):
    amount: float
    category: str
    date: datetime
    description: str
    # description: Optional[str] = None
    email_id: EmailStr

# Model for categories collection
class Category(BaseModel):
    id: Optional[str] = None
    name: str

# --- Model for users collection ---
class User(BaseModel):
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    email_id: EmailStr
    password: str  # Ideally hashed before storing
    role_name: str 

# --- Model for roles collection ---
class Role(BaseModel):
    role_name: str

class Fund(BaseModel):
    email_id: EmailStr
    total_funds: float = Field(..., ge=0, description="Total funds allocated to the user")
    spent: float = Field(0, ge=0, description="Total amount spent by the user")
    balance: float = Field(..., ge=0, description="Remaining balance")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# from typing import Optional
# from pydantic import BaseModel

# class CategoryBase(BaseModel):
#     name: str

# class CategoryCreate(CategoryBase):
#     pass  # For POST

# class CategoryRead(CategoryBase):
#     id: str  # For GET/PUT
# And update your router:

# python
# Copy
# Edit
# @router.post("/categories/")
# def add_category(category: CategoryCreate):
#     ...
# 💡 I’d recommend Option 1 if you want a quick fix,
# but Option 2 is better long-term to avoid mismatched requirements between POST and GET.
