from bson import ObjectId
from database_mongo.mongo_client import models
from database_mongo.models.models_model import create_model_model

# Update || Insert
def upsert_model_for_product(blockchain_product_id, model_string, uploaded_by):
    existing = models.find_one({"blockchainProductId": blockchain_product_id})
    model_doc = create_model_model(blockchain_product_id, model_string, uploaded_by)
    if existing:
        # Aggiorna solo i campi modificabili, mantieni uploadedAt aggiornato
        models.update_one(
            {"_id": existing["_id"]},
            {"$set": {
                "modelString": model_string,
                "uploadedBy": ObjectId(uploaded_by),
                "uploadedAt": model_doc["uploadedAt"]
            }}
        )
        return existing["_id"]
    else:
        result = models.insert_one(model_doc)
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