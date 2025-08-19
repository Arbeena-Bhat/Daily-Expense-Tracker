from bson import ObjectId
from models import Expense
from typing import Optional

def expense_serializer(expense) -> dict:
    return {
        "id": str(expense["_id"]),
        "amount": expense["amount"],
        "category": expense["category"],
        "date": expense["date"].strftime("%Y-%m-%d") if expense.get("date") else None,
        "description": expense.get("description", ""),
        "email_id": expense.get("email_id")  # 👈 include email of the owner
    }


def category_serializer(category) -> dict:
    return {
        "id": str(category["_id"]),
        "name": category["name"]
    }

# --- Role Serializer ---
def role_serializer(role) -> dict:
    return {
        "id": str(role["_id"]),
        "role_name": role["role_name"]
    }
def user_serializer(user) -> dict:
    return {
        "id": str(user["_id"]),                 # Convert ObjectId to string
        "first_name": user.get("first_name"),
        "middle_name": user.get("middle_name"),
        "last_name": user.get("last_name"),
        "email_id": user.get("email_id"),
        "password": user.get("password"),     # Normally store hashed password
        "role_name": user.get("role_name")        # default role if not provided
    }
def fund_serializer(fund) -> dict:
    return {
        "id": str(fund["_id"]),
        "email_id": fund["email_id"],
        "total_funds": fund.get("total_funds", 0),
        "spent": fund.get("spent", 0),
        "balance": fund.get("balance", fund.get("total_funds", 0) - fund.get("spent", 0)),
        "created_at": fund.get("created_at"),
        "updated_at": fund.get("updated_at")
    }