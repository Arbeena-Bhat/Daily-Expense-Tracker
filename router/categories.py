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

# UPDATE CATEGORY
@router.put("/categories/{category_id}")
def update_category(category_id: str, updated_data: dict):
    if not ObjectId.is_valid(category_id):
        raise HTTPException(status_code=400, detail="Invalid category ID")

    update_fields = {}

    # Update category name (capitalize)
    if "name" in updated_data and updated_data["name"]:
        new_name = updated_data["name"].strip().capitalize()

        # Duplicate check (case-insensitive, exclude current category)
        existing_category = categories_collection.find_one(
            {
                "name": {"$regex": f"^{new_name}$", "$options": "i"},
                "_id": {"$ne": ObjectId(category_id)}
            }
        )
        if existing_category:
            raise HTTPException(status_code=400, detail=f"Category '{new_name}' already exists.")

        update_fields["name"] = new_name

    if not update_fields:
        raise HTTPException(status_code=400, detail="No valid fields provided for update")

    result = categories_collection.update_one({"_id": ObjectId(category_id)}, {"$set": update_fields})

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Category not found")

    return {"message": "Category updated successfully", "updated_fields": list(update_fields.keys())}


@router.delete("/categories/{category_id}")
def delete_category(category_id: str):
    result = categories_collection.delete_one({"_id": ObjectId(category_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"message": "Category deleted"}

