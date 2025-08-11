from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime

# Model for adding expenses
class Expense(BaseModel):
    amount: float
    category: str
    date: datetime
    description: str
    # description: Optional[str] = None

# Model for categories collection
class Category(BaseModel):
    name: str

