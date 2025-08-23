from flask import jsonify

from ..database_mongo.queries.users_queries import get_user_by_email, find_producer_by_operator
import requests

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


def build_auth_response(user, email, token, message):
    return {
        "message": message,
        "access_token": token,
        "role": user.get("role"),
        "manufacturer": user.get("manufacturer"),
        "email": email
    }
