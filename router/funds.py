from fastapi import APIRouter, HTTPException, Query,Body
from database import funds_collection, expenses_collection
from serializers import fund_serializer
from bson import ObjectId
from datetime import datetime
import traceback

router = APIRouter(prefix="/funds", tags=["Funds"])

# =========================
# HELPER FUNCTION
# =========================
def update_user_funds(email_id: str):
    """
    Recalculate spent & balance after expense changes.
    Ensures balance is never negative.
    """
    try:
        email_id = email_id.strip().lower()
        # Fetch user's funds document
        fund_doc = funds_collection.find_one({"email_id": email_id})
        now = datetime.utcnow()
        if not fund_doc:
            # If no funds record exists, create one with defaults
            fund_doc = {
                "email_id": email_id,
                "total_funds": 0,
                "spent": 0,
                "balance": 0,
                "created_at": now,
                "updated_at": now
            }
            funds_collection.insert_one(fund_doc)

        total_funds = fund_doc.get("total_funds", 0)

        # Sum all expenses for this user
        pipeline = [
            {"$match": {"email_id": email_id}},
            {"$group": {"_id": None, "total_spent": {"$sum": "$amount"}}}
        ]
        result = list(expenses_collection.aggregate(pipeline))
        spent = result[0]["total_spent"] if result else 0

        # Prevent overspending
        # if spent > total_funds:
        #     spent = total_funds
        spent = min(spent, total_funds)
        balance = total_funds - spent

        # Update funds document
        funds_collection.update_one(
            {"email_id": email_id},
            {"$set": {
                "spent": spent,
                "balance": balance,
                "updated_at": now
            }}
        )
        return {"message": "Funds updated", "total_funds": total_funds, "spent": spent, "balance": balance}

    except Exception as e:
        traceback.print_exc()
        return {"error": str(e)}


# =========================
# API ENDPOINTS
# =========================

# 1️⃣ Allocate Funds (add funds to user)
@router.post("/allocate")
def allocate_funds(email_id: str = Body(...), amount: float = Body(..., gt=0)):
    try:
        email_id = email_id.strip().lower()
        now = datetime.utcnow()
        fund_doc = funds_collection.find_one({"email_id": email_id})

        if not fund_doc:
            # Create new funds record
            fund_doc = {
                "email_id": email_id,
                "total_funds": amount,
                "spent": 0,
                "balance": amount,
                "created_at": now,
                "updated_at": now
            }
            funds_collection.insert_one(fund_doc)
        else:
            # Increment total_funds
            total_funds = fund_doc.get("total_funds", 0) + amount
            funds_collection.update_one(
                {"email_id": email_id},
                {"$set": {
                    "total_funds": total_funds,
                    # "balance": total_funds - fund_doc.get("spent", 0),
                    "updated_at": now
                }}
            )
        # Recalculate balance after allocation
        return update_user_funds(email_id)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# 2️⃣ View Current Funds
@router.get("/")
def get_funds(email_id: str = Query(...)):
    try:
        email_id = email_id.strip().lower()
        fund_doc = funds_collection.find_one({"email_id": email_id})
        # if not fund_doc:
        #     raise HTTPException(status_code=404, detail="Funds record not found")
        # return {
        #     "total_funds": fund_doc.get("total_funds", 0),
        #     "spent": fund_doc.get("spent", 0),
        #     "balance": fund_doc.get("balance", 0),
        #     "created_at": fund_doc.get("created_at"),
        #     "updated_at": fund_doc.get("updated_at")
        # }
        if not fund_doc:
            return {"total_funds": 0, "spent": 0, "balance": 0, "created_at": None, "updated_at": None}
        return fund_serializer(fund_doc)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# 3️⃣ Update Funds (set new total_funds)
@router.put("/update")
def update_funds(email_id: str = Body(...), total_funds: float = Body(..., ge=0)):
    try:
        email_id = email_id.strip().lower()
        fund_doc = funds_collection.find_one({"email_id": email_id})
        if not fund_doc:
            raise HTTPException(status_code=404, detail="Funds record not found")

        funds_collection.update_one(
            {"email_id": email_id},
            {"$set": {
                "total_funds": total_funds,
                "updated_at": datetime.utcnow()
            }}
        )
        # Recalculate balance
        return update_user_funds(email_id)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# 4️⃣ Delete Funds Record (reset)
@router.delete("/{email_id}")
def delete_funds(email_id: str):
    try:
        email_id = email_id.strip().lower()
        result = funds_collection.update_one(
            {"email_id": email_id},
            {"$set": {"total_funds": 0, "spent": 0, "balance": 0, "updated_at": datetime.utcnow()}}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Funds record not found")
        return {"message": f"Funds record reset for {email_id}"}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
