from bson import ObjectId
from models import Expense

def expense_serializer(expense) -> dict:
    return {
        "id": str(expense["_id"]),
        "amount": expense["amount"],
        "category": expense["category"],
        "date": expense["date"].strftime("%Y-%m-%d") if expense.get("date") else None,
        "description": expense.get("description", "")
    }
def category_serializer(category) -> dict:
    return {
        "id": str(category["_id"]),
        "name": category["name"]
    }

