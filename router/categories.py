
from fastapi import APIRouter, HTTPException
from models import Category
from database import categories_collection
from serializers import category_serializer
from bson import ObjectId
from typing import List

router = APIRouter()

# POST REQUEST TO ADD CATEGORY:IF CATEGORY ALREADY EXISTS,BLOCK THAT REQUEST
@router.post("/categories/")
def add_category(category: Category):
    category_dict = category.dict()

    # Capitalize category name (first letter uppercase, rest lowercase)
    category_dict["name"] = category_dict["name"].strip().capitalize()

    # Duplicate check
    existing_category = categories_collection.find_one(
        {"name": {"$regex": f"^{category_dict['name']}$", "$options": "i"}}
    )
    if existing_category:
        raise HTTPException(status_code=400, detail=f"Category '{category_dict['name']}' already exists.")

    # Insert new category
    result = categories_collection.insert_one(category_dict)

    # Return clean JSON-safe response
    return {
        "id": str(result.inserted_id),
        "name": category_dict["name"]
    }

@router.get("/categories/", response_model=List[Category])
def get_all_categories():
    categories = list(categories_collection.find())
    return [category_serializer(cat) for cat in categories]

# @router.delete("/categories/{category_id}")
# def delete_category(category_id: str):
#     result = categories_collection.delete_one({"_id": ObjectId(category_id)})
#     if result.deleted_count == 0:
#         raise HTTPException(status_code=404, detail="Category not found")
#     return {"message": "Category deleted"}

