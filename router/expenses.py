from fastapi import APIRouter, HTTPException
from models import Expense
from database import expenses_collection
# from database import categories_collection
from serializers import expense_serializer
# from serializers import category_serializer
from bson import ObjectId
from fastapi import Query
from typing import List, Optional
from bson.son import SON
from datetime import datetime,date
import traceback

router = APIRouter()

# with normalizing
@router.post("/expenses/")
def add_expense(expense: Expense):
    try:
        # Convert to dictionary
        expense_dict = expense.dict()

        # Normalize category: strip spaces and capitalize first letter
        expense_dict["category"] = expense_dict["category"].strip().capitalize()

        # Insert into MongoDB
        result = expenses_collection.insert_one(expense_dict)
        return {"message": "Expense added", "id": str(result.inserted_id)}
    
    except Exception as e:
        # Print full error in server logs
        print("Error adding expense:", e)
        traceback.print_exc()
        
        # Send error message to client
        raise HTTPException(
            status_code=500,
            detail=f"Error adding expense: {str(e)}"
        )



    

@router.get("/expenses/")
def get_expenses(
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
    category: Optional[str] = Query(None)
):
    try:
        query = {}

        # Date range filter
        if start and end:
            start_date = datetime.strptime(start, "%Y-%m-%d")
            end_date = datetime.strptime(end, "%Y-%m-%d")
            query["date"] = {"$gte": start_date, "$lte": end_date}

        # Category filter
        if category:
            query["category"] = {
                "$regex": f"^{category}$",  # exact match from start to end
                "$options": "i"             # case-insensitive
            }
        # Fetch filtered or unfiltered expenses
        expenses = expenses_collection.find(query)

        #  Serialize and return
        return [expense_serializer(exp) for exp in expenses]

    except Exception as e:
        print("Error in get_expenses:", e)
        raise HTTPException(status_code=500, detail="Something went wrong")


@router.get("/summary/monthly")
def get_monthly_summary():
    try:
        pipeline = [
            {
                "$group": {
                    "_id": {
                        "year": { "$year": "$date" },
                        "month": { "$month": "$date" }
                    },
                    "total": { "$sum": "$amount" }
                }
            },
            {
                "$sort": { "_id.year": -1, "_id.month": -1 }
            }
        ]

        results = list(expenses_collection.aggregate(pipeline))
        print("Aggregation Results:", results)

        summary = []
        for item in results:
            year = item["_id"]["year"]
            month = item["_id"]["month"]
            key = f"{year}-{month:02d}"
            summary.append({
                "month": key,
                "total_expense": item["total"]
            })

        return summary

    except Exception as e:
        print("ERROR in /summary/monthly:", type(e).__name__, str(e))  # 🟡 add this
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")  # 🟡 show real error

@router.get("/summary/weekly")
def get_weekly_summary():
    pipeline = [
        {
            "$addFields": {
                "date_obj": { "$dateFromString": { "dateString": "$date" } }
            }
        },
        {
            "$group": {
                "_id": {
                    "year": { "$isoWeekYear": "$date_obj" },
                    "week": { "$isoWeek": "$date_obj" }
                },
                "total_amount": { "$sum": "$amount" }
            }
        },
        {
            "$sort": SON([("_id.year", -1), ("_id.week", -1)])
        }
    ]

    summary = list(expenses_collection.aggregate(pipeline))

    # Convert to readable format
    result = [
        {
            "year": item["_id"]["year"],
            "week": item["_id"]["week"],
            "total_amount": item["total_amount"]
        }
        for item in summary
    ]
    return result

@router.get("/summary/top-categories")
def get_top_spending_categories():
    try:
        pipeline = [
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

        return [
            {
                "category": item["_id"],
                "total": item["total"]
            }
            for item in result
        ]

    except Exception as e:
        print("Error in top categories:", e)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/")
def read_root():
    return {"message": "Welcome to the Daily Expense Tracker API!"}