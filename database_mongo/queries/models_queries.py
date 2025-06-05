from bson import ObjectId
from database_mongo.mongo_client import models
from database_mongo.models.models_model import create_model_model

def create_model(blockchain_product_id, model_string, uploaded_by):
    model_data = create_model_model(blockchain_product_id, model_string, uploaded_by)
    result = models.insert_one(model_data)
    return result.inserted_id

def get_model_by_id(model_id):
    if isinstance(model_id, str):
        model_id = ObjectId(model_id)
    return models.find_one({"_id": model_id})

def get_model_by_blockchain_id(blockchain_id):
    return models.find_one({"blockchainProductId": blockchain_id})

def get_models_by_user(user_id):
    if isinstance(user_id, str):
        user_id = ObjectId(user_id)
    return list(models.find({"uploadedBy": user_id}))

def update_model(model_id, update_data):
    if isinstance(model_id, str):
        model_id = ObjectId(model_id)
    result = models.update_one({"_id": model_id}, {"$set": update_data})
    return result.modified_count > 0

def delete_model(model_id):
    if isinstance(model_id, str):
        model_id = ObjectId(model_id)
    result = models.delete_one({"_id": model_id})
    return result.deleted_count > 0