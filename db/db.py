from pymongo import MongoClient

client =  MongoClient("mongodb://localhost:27017/")

db = client["filiera360"]

users_collection = db["users"]







