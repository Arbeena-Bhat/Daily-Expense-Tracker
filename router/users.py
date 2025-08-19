from fastapi import APIRouter, HTTPException
from models import User
from database import users_collection, roles_collection
from serializers import user_serializer
from bson import ObjectId
from typing import List
import bcrypt

router = APIRouter()

# REGISTER USER
#CORRECT ONE
@router.post("/users/register")
def register_user(user: User):
    user_dict = user.dict()

    # Check if email already exists
    existing_user = users_collection.find_one({"email_id": user_dict["email_id"]})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Hash password
    hashed_pw = bcrypt.hashpw(user_dict["password"].encode("utf-8"), bcrypt.gensalt())
    user_dict["password"] = hashed_pw.decode("utf-8")

    # Insert into DB
    result = users_collection.insert_one(user_dict)
    return {"message": "User registered successfully", "id": str(result.inserted_id)}

# LOGIN USER
@router.get("/users/login")
def login_user(email: str, password: str):
    
    # Find the user by email
    user = users_collection.find_one({"email_id": email})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    stored_password = user["password"]

    # Case 1: If stored as plain text
    if stored_password == password:
        pass  # Login success

    # Case 2: If stored as hashed (bcrypt)
    elif bcrypt.checkpw(password.encode("utf-8"), stored_password.encode("utf-8")):
        pass  # Login success

    else:
        raise HTTPException(status_code=401, detail="Invalid password")

    return {
        "message": "Login successful",
        "user": {
            "id": str(user["_id"]),
            "first_name": user.get("first_name"),
            "middle_name": user.get("middle_name"),
            "last_name": user.get("last_name"),
            "email_id": user.get("email_id"),
            "role_name": user.get("role_name")
        }
    }

# GET ALL USERS (no password in output)
@router.get("/users/", response_model=List[dict])
def get_all_users():
    users = list(users_collection.find())
    return [user_serializer(u) for u in users]


# UPDATE USER - Only update allowed fields
@router.put("/users/{user_id}")
def update_user(user_id: str, updated_data: dict):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")

    update_fields = {}

    # Update first_name
    if "first_name" in updated_data and updated_data["first_name"]:
        update_fields["first_name"] = updated_data["first_name"]

    # Update middle_name
    if "middle_name" in updated_data and updated_data["middle_name"]:
        update_fields["middle_name"] = updated_data["middle_name"]

    # Update last_name
    if "last_name" in updated_data and updated_data["last_name"]:
        update_fields["last_name"] = updated_data["last_name"]

    # Update email_id
    if "email_id" in updated_data and updated_data["email_id"]:
        update_fields["email_id"] = updated_data["email_id"]

    # Update password (with hashing)
    if "password" in updated_data and updated_data["password"]:
        hashed_pw = bcrypt.hashpw(updated_data["password"].encode("utf-8"), bcrypt.gensalt())
        update_fields["password"] = hashed_pw.decode("utf-8")

    # Update role_name
    if "role_name" in updated_data and updated_data["role_name"]:
        update_fields["role_name"] = updated_data["role_name"]

    if not update_fields:
        raise HTTPException(status_code=400, detail="No valid fields provided for update")

    result = users_collection.update_one({"_id": ObjectId(user_id)}, {"$set": update_fields})

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": "User updated successfully", "updated_fields": list(update_fields.keys())}

# DELETE USER
@router.delete("/users/{user_id}")
def delete_user(user_id: str):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")

    result = users_collection.delete_one({"_id": ObjectId(user_id)})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": "User deleted successfully"}










