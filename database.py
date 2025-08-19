# from datetime import date, datetime
from pymongo import MongoClient  
from bson import ObjectId

MONGO_URI="mongodb://localhost:27017/"
client=MongoClient(MONGO_URI)
db = client["DailyExpenseTracker"]
expenses_collection = db["expenses"]
categories_collection = db["categories"]
roles_collection = db["roles"]
users_collection = db["users"]
funds_collection = db["funds"]
funds_collection.create_index("email_id", unique=True)
# print(client.list_database_names())



