from fastapi import APIRouter, HTTPException, Query, Body
from models import Expense
from database import expenses_collection,funds_collection
from serializers import expense_serializer,fund_serializer
from router.funds import update_user_funds
from bson.son import SON
from bson import ObjectId
from typing import Optional, Any, Dict,cast
from datetime import datetime
import traceback

router = APIRouter()

# Add Expense (email_id required as query parameter)
@router.post("/expenses/")
def add_expense(expense: Expense, email_id: str = Query(..., description="Email ID of logged-in user")):
    try:
        expense_dict = expense.dict()
        # Validate amount
        try:
            expense_amount = float(expense_dict.get("amount", 0))
            if expense_amount <= 0:
                raise HTTPException(status_code=400, detail="Amount must be a positive number")
        except ValueError:
            raise HTTPException(status_code=400, detail="Amount must be a valid number")

        # Override email_id in expense with the logged-in user's email_id for security
        expense_dict["email_id"] = email_id.strip().lower()

        # Normalize category
        expense_dict["category"] = expense_dict["category"].strip().capitalize()

        # Default to current datetime if no date provided

        expense_dict["date"] = expense.date or datetime.utcnow()
        expense_dict["created_at"] = datetime.utcnow()
        expense_dict["updated_at"] = datetime.utcnow()

        # Check funds
        fund_doc = funds_collection.find_one({"email_id": email_id})
        if not fund_doc or fund_doc.get("total_funds", 0) == 0:
            raise HTTPException(status_code=400, detail="User has no allocated funds yet")
        total_funds = fund_doc.get("total_funds", 0)

        # Calculate total spent dynamically from MongoDB
        pipeline = [
            {"$match": {"email_id": email_id.strip().lower()}},
            {"$group": {"_id": None, "total_spent": {"$sum": "$amount"}}}
        ]
        result = list(expenses_collection.aggregate(pipeline))
        current_spent = result[0]["total_spent"] if result else 0

        available_balance = total_funds - current_spent
        if expense_amount > available_balance:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient funds. Available balance: {available_balance}"
            )
        # current_balance = fund_doc.get("balance", 0)
        # if expense_dict["amount"] > current_balance:
        #     raise HTTPException(
        #         status_code=400,
        #         detail=f"Insufficient funds. Available balance: {current_balance}"
        #     )
        # Insert into MongoDB
       
        result = expenses_collection.insert_one(expense_dict)


        # 🔥 update funds after expense
        update_user_funds(email_id)

        return {"message": "Expense added", "id": str(result.inserted_id)}

    except HTTPException:
        raise
        
    except Exception as e:
        print("Error adding expense:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error adding expense: {str(e)}")


# Get Expenses (email_id required as query parameter)
@router.get("/expenses/")
def get_expenses(
    email_id: str = Query(..., description="Email ID of logged-in user"),
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
):
    try:
        query: Dict[str, Any] = {"email_id": email_id.strip().lower()}

        if start and end:
            start_date = datetime.strptime(start, "%Y-%m-%d")
            end_date = datetime.strptime(end, "%Y-%m-%d")
            query["date"] = {"$gte": start_date, "$lte": end_date}

        if category:
            query["category"] = {
                "$regex": f"^{category}$",
                "$options": "i"
            }
        
        expenses = list(expenses_collection.find(query))
        fund_doc = funds_collection.find_one({"email_id": email_id})
        funds_data = fund_serializer(fund_doc) if fund_doc else {"total_funds": 0, "spent": 0, "balance": 0}

        return {
            "expenses": [expense_serializer(exp) for exp in expenses],
            "funds": funds_data
        }
        
        # expenses = expenses_collection.find(query)
        # return [expense_serializer(exp) for exp in expenses]

    except Exception as e:
        # print("Error in get_expenses:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")


@router.get("/summary/monthly")
def get_monthly_summary(email_id: str = Query(...)):
    try:
        pipeline = [
            {"$match": {"email_id": email_id.strip().lower()}},
            {
                "$group": {
                    "_id": {
                        "year": {"$year": "$date"},
                        "month": {"$month": "$date"}
                    },
                    "total": {"$sum": "$amount"}
                }
            },
            {"$sort": {"_id.year": -1, "_id.month": -1}}
        ]
        results = list(expenses_collection.aggregate(pipeline))
   

        summary = []
        for item in results:
            year = item["_id"]["year"]
            month = item["_id"]["month"]
            key = f"{year}-{month:02d}"
            summary.append({"month": key, "total_expense": item["total"]})

        # 🔥 Get funds info
        fund_doc = funds_collection.find_one({"email_id": email_id})
        funds_data = fund_serializer(fund_doc) if fund_doc else {"total_funds": 0, "spent": 0, "balance": 0}

        return {"monthly_summary": summary, "funds": funds_data}
        # return summary

    except Exception as e:
        print("ERROR in /summary/monthly:", e)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# @router.get("/summary/weekly")
# def get_weekly_summary(email_id: str = Query(...)):
#     pipeline = [
#         {"$match": {"email_id": email_id.strip().lower()}},
#         {
#             "$group": {
#                 "_id": {
#                     "year": {"$year": "$date"},
#                     "week": {"$isoWeek": "$date"}
#                 },
#                 "total_amount": {"$sum": "$amount"}
#             }
#         },
#         {"$sort": SON([("_id.year", -1), ("_id.week", -1)])}
#     ]

#     summary = list(expenses_collection.aggregate(pipeline))
#     return [
#         {
#             "year": item["_id"]["year"],
#             "week": item["_id"]["week"],
#             "total_amount": item["total_amount"]
#         }
#         for item in summary
#     ]


@router.get("/summary/top-categories")
def get_top_spending_categories(email_id: str = Query(...)):
    try:
        pipeline = [
            {"$match": {"email_id": email_id.strip().lower()}},
            {
                "$group": {
                    "_id": "$category",
                    "total": {"$sum": "$amount"}
                }
            },
            {"$sort": {"total": -1}},
            {"$limit": 3}
        ]

        result = list(expenses_collection.aggregate(pipeline))
        categories = [{"category": item["_id"], "total": item["total"]} for item in result]

        # 🔥===== Fetch Funds Info =====
        fund_doc = funds_collection.find_one({"email_id": email_id})
        # funds_data = {
        #     "total_funds": funds.get("total_funds", 0),
        #     "spent": funds.get("spent", 0),
        #     "balance": funds.get("balance", 0)
        # } if funds else {"total_funds": 0, "spent": 0, "balance": 0}
        funds_data = fund_serializer(fund_doc) if fund_doc else {"total_funds": 0, "spent": 0, "balance": 0}

        # return [{"category": item["_id"], "total": item["total"]} for item in result]
        return {"top_categories": categories, "funds": funds_data}

    except Exception as e:
        print("Error in top categories:", e)
        raise HTTPException(status_code=500, detail="Internal server error")
    
@router.get("/summary/by-category")
def get_category_summary(email_id: str = Query(...)):
    """
    Summarize total expenses grouped by category for the given user.
    Returns all categories with total amounts, sorted from highest to lowest.
    """
    try:
        pipeline = [
            {"$match": {"email_id": email_id.strip().lower()}},
            {
                "$group": {
                    "_id": "$category",
                    "total": {"$sum": "$amount"}
                }
            },
            {"$sort": {"total": -1}}
        ]

        results = list(expenses_collection.aggregate(pipeline))
        categories = [{"category": item["_id"], "total": item["total"]} for item in results]

        # 🔥 ===== Fetch funds info =====
        fund_doc = funds_collection.find_one({"email_id": email_id})
        # funds_data = {
        #     "total_funds": funds.get("total_funds", 0),
        #     "spent": funds.get("spent", 0),
        #     "balance": funds.get("balance", 0)
        # } if funds else {"total_funds": 0, "spent": 0, "balance": 0}
        funds_data = fund_serializer(fund_doc) if fund_doc else {"total_funds": 0, "spent": 0, "balance": 0}
        return {"Categories": categories, "funds": funds_data}
        # return [{"category": item["_id"], "total": item["total"]} for item in results]

    except Exception as e:
        print("Error in /summary/by-category:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")



# Update Expense (by expense_id, email_id required for security)
@router.put("/update/expenses/{expense_id}")
def update_expense(
    expense_id: str,
    updated_data: dict = Body(...),
    email_id: str = Query(..., description="Email ID of logged-in user")
):
    try:
        if not ObjectId.is_valid(expense_id):
            raise HTTPException(status_code=400, detail="Invalid expense ID")

        # Normalize fields
        if "category" in updated_data:
            updated_data["category"] = updated_data["category"].strip().capitalize()

        if "date" in updated_data:
            try:
                updated_data["date"] = datetime.strptime(updated_data["date"], "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

        if "description" in updated_data:
            updated_data["description"] = str(updated_data["description"])

        if "amount" in updated_data:
            try:
                updated_data["amount"] = float(updated_data["amount"])
                if updated_data["amount"] <= 0:
                    raise ValueError
                
            except ValueError:
                raise HTTPException(status_code=400, detail="Amount must be a positive number")

            # Fetch old expense
            old_expense = expenses_collection.find_one({"_id": ObjectId(expense_id), "email_id": email_id.strip().lower()})
            if not old_expense:
                raise HTTPException(status_code=404, detail="Expense not found or not owned by this user")

            # Calculate total spent dynamically from MongoDB (excluding this expense)
            pipeline = [
                {"$match": {"email_id": email_id.strip().lower(), "_id": {"$ne": ObjectId(expense_id)}}},
                {"$group": {"_id": None, "total_spent": {"$sum": "$amount"}}}
            ]
            result = list(expenses_collection.aggregate(pipeline))
            current_spent = result[0]["total_spent"] if result else 0

            # Check available funds
            fund_doc = funds_collection.find_one({"email_id": email_id})
            total_funds = fund_doc.get("total_funds", 0) if fund_doc else 0
            new_total_spent = current_spent + updated_data["amount"]

            if new_total_spent > total_funds:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient funds. Available balance: {total_funds - current_spent}"
                )

        updated_data["updated_at"] = datetime.utcnow()

        # Update expense
        result = expenses_collection.update_one(
            {"_id": ObjectId(expense_id), "email_id": email_id.strip().lower()},
            {"$set": updated_data}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Expense not found or not owned by this user")

        # Recalculate funds after update
        update_user_funds(email_id)

        return {"message": "Expense updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error updating expense: {str(e)}")


# ✅ Delete Expense
@router.delete("/expenses/{expense_id}")
def delete_expense(expense_id: str, email_id: str = Query(...)):
    try:
        if not ObjectId.is_valid(expense_id):
            raise HTTPException(status_code=400, detail="Invalid expense ID")

        result = expenses_collection.delete_one(
            {"_id": ObjectId(expense_id), "email_id": email_id.strip().lower()}
        )
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Expense not found")

        # 🔥 Recalculate funds after delete
        update_user_funds(email_id)

        return {"message": "Expense deleted"}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error deleting expense: {str(e)}")



@router.get("/")
def read_root():
    return {"message": "Welcome to the Daily Expense Tracker API!"}

