from flask import request, jsonify

from ..services.products_service import fetch_product_from_js_server, fetch_product_history_from_js_server

def get_product():
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

def get_product_history():
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

# ora in uso + autenticazione jwt
# @app.route('/uploadProduct', methods=['POST'])
# @jwt_required()
# def upload_product():
#     identity = get_jwt_identity()
#     if not required_permissions(identity, ['producer']):
#         return jsonify({"message": "Unauthorized: Insufficient permissions."}), 403
#
#     user = get_user_by_email(identity)
#     if not user:
#         return jsonify({"message": "User not found."}), 404
#
#     product_data = request.json
#     client_manufacturer = product_data.get("Manufacturer")
#     real_manufacturer = user.get("manufacturer")
#
#     print(f"Authenticated manufacturer: {real_manufacturer}")
#     print(f"Upload request by: {client_manufacturer}")
#
#     # Reject operation if the authenticated manufacturer doesn't match the one in the request
#     if real_manufacturer != client_manufacturer:
#         return jsonify({"message": "Unauthorized: Manufacturer mismatch."}), 403
#
#     # Set default fields if not present
#     product_data.setdefault("SensorData", [])
#     product_data.setdefault("CustomObject", {})
#
#     print(f"Uploading new product data: {product_data}")
#
#     try:
#         # Send the cleaned product data to the external service
#         # DEBUG: usare localhost al posto di middleware
#         response = requests.post(f'http://middleware:3000/uploadProduct', json=product_data)
#         if response.status_code == 200:
#             # Salvataggio su mongoDB dei metadati
#             try:
#                 create_product(product_data["ID"], user["_id"])
#                 print("Product metadata saved in MongoDB.")
#             except Exception as e:
#                 print("Error saving to MongoDB:", e)
#
#             return jsonify({'message': response.json().get('message', 'Product uploaded successfully!')})
#         else:
#             return jsonify({'message': response.json().get('message', 'Failed to upload product.')}), response.status_code
#
#     except requests.exceptions.RequestException as e:
#         print("Error uploading product to middleware:", e)
#         return jsonify({'message': 'Error uploading product.', 'error': str(e)}), 500


# # Gestione errore: token mancante
# @jwt.unauthorized_loader
# def missing_token_callback(err_str):
#     return jsonify({"error": "Token mancante o non valido", "message": err_str}), 401