# from datetime import date, datetime
from pymongo import MongoClient  
from bson import ObjectId
from serializers import expense_serializer

MONGO_URI="mongodb://localhost:27017/"
client=MongoClient(MONGO_URI)
db = client["DailyExpenseTracker"]
expenses_collection = db["expenses"]
categories_collection = db["categories"]
# print(client.list_database_names())



