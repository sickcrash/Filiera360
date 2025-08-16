from flask import jsonify

from database_mongo.queries.users_queries import get_user_by_email
from database_mongo.mongo_client import users as users_collection
import requests


def find_producer_by_operator(operator_email):
    return users_collection.find_one({
        "operators": {
            "$elemMatch": {"email": operator_email}
        }
    })

def verify_product_authorization(email, product_id):
    user = get_user_by_email(email)
    if not user or not product_id:
        return False

    if user["flags"][1]:  # flags[1] == operator
        user = find_producer_by_operator(email)
        if not user:
            return False

    try:
        response = requests.get(f'http://middleware:3000/readProduct?productId={product_id}')
        if response.status_code != 200:
            return jsonify({'message': 'Failed to get product.'}), 500

        product = response.json()
        return product.get("Manufacturer") == user["manufacturer"]
    except Exception as e:
        print("Failed to get product:", e)
        return jsonify({'message': 'Failed to get product.'}), 500