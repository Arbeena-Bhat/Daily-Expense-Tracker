from fastapi import APIRouter, HTTPException
from models import Role
from database import roles_collection
from serializers import role_serializer
from bson import ObjectId
from typing import List

router = APIRouter()

# POST REQUEST TO ADD ROLE
@router.post("/roles/")
def add_role(role: Role):
    role_dict = role.dict()

    # Capitalize role name
    role_dict["role_name"] = role_dict["role_name"].strip().capitalize()

    # Duplicate check (case-insensitive)
    existing_role = roles_collection.find_one(
        {"role_name": {"$regex": f"^{role_dict['role_name']}$", "$options": "i"}}
    )
    if existing_role:
        raise HTTPException(status_code=400, detail=f"Role '{role_dict['role_name']}' already exists.")

    # Insert new role
    result = roles_collection.insert_one(role_dict)

    return {
        "id": str(result.inserted_id),
        "role_name": role_dict["role_name"]
    }

# GET ALL ROLES
@router.get("/roles/", response_model=List[Role])
def get_all_roles():
    roles = list(roles_collection.find())
    return [role_serializer(r) for r in roles]
