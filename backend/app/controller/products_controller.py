from flask import request, jsonify
from flask_jwt_extended import get_jwt_identity

from ..services.products_service import fetch_product_from_js_server, fetch_product_history_from_js_server, \
    upload_product_service, update_product_service, like_product_service, unlike_product_service, \
    get_liked_products_service


def get_product_controller():
    product_id = request.args.get('productId')
    if not product_id:
        return jsonify({'message': 'productId is required'}), 400

    print(f"ATTEMPTING TO CONNECT TO JS SERVER FOR PRODUCT ID: {product_id}")
    product_data = fetch_product_from_js_server(product_id)

    if "error" in product_data:
        print("Error fetching product:", product_data["error"])
        return jsonify({'message': 'Failed to get product.', 'error': product_data["error"]}), 500

    print("Success:", product_data)
    return jsonify(product_data)

def get_product_history_controller():
    product_id = request.args.get('productId')
    if not product_id:
        return jsonify({'message': 'productId is required'}), 400

    print(f"ATTEMPTING TO CONNECT TO JS SERVER FOR PRODUCT ID: {product_id}")
    product_history_data = fetch_product_history_from_js_server(product_id)

    if "error" in product_history_data:
        print("Error fetching product history:", product_history_data["error"])
        return jsonify({'message': 'Failed to get product history.', 'error': product_history_data["error"]}), 500

    print("Success:", product_history_data)
    return jsonify(product_history_data)

def upload_product_controller():
    product_data = request.json
    user_identity = get_jwt_identity()
    result, status = upload_product_service(product_data, user_identity)
    return jsonify(result), status

def update_product_controller():
    product_data = request.json
    user_identity = get_jwt_identity()
    result, status = update_product_service(product_data, user_identity)
    return jsonify(result), status

def like_product_controller():
    result, status = like_product_service(request)
    return jsonify(result), status

def unlike_product_controller():
    result, status = unlike_product_service(request)
    return jsonify(result), status

def get_liked_products_controller():
    result, status = get_liked_products_service(request)
    return jsonify(result), status


# # Gestione errore: token mancante
# @jwt.unauthorized_loader
# def missing_token_callback(err_str):
#     return jsonify({"error": "Token mancante o non valido", "message": err_str}), 401