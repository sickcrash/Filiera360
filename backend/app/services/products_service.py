import json

import requests

from backend.app.utils.blockchain_utils import verify_manufacturer
from backend.app.utils.permissions_utils import required_permissions
from backend.app.utils.product_utils import get_product_changes
from database_mongo.queries.history_queries import get_last_history_entry, add_history_entry
from database_mongo.queries.liked_queries import get_liked_products_by_user, like_a_product, unlike_a_product
from database_mongo.queries.products_queries import create_product
from database_mongo.queries.users_queries import get_user_by_email

def fetch_product_from_js_server(product_id):
    try:
        response = requests.get(f'http://middleware:3000/readProduct?productId={product_id}')
        if response.status_code == 200:
            return response.json()
        return {"error": f"Failed to fetch product, status {response.status_code}"}
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def fetch_product_history_from_js_server(product_id):
    try:
        response = requests.get(f'http://middleware:3000/productHistory?productId={product_id}')
        print(f"JS server responded with status {response.status_code}")

        if response.status_code == 200:
            return response.json()
        return {'error': f"Failed to get product history {response.status_code}"},

    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def upload_product_service(product_data, user_identity):
    # Controllo permessi
    if not required_permissions(user_identity, ['producer']):
        return {"message": "Unauthorized: Insufficient permissions."}, 403

    # Verifica produttore autenticato
    user = get_user_by_email(user_identity)
    real_manufacturer = user["manufacturer"]
    client_manufacturer = product_data.get("Manufacturer")

    if real_manufacturer != client_manufacturer:
        return {"message": "Unauthorized: Manufacturer mismatch."}, 403

    # Assicurarsi che i campi opzionali siano valorizzati
    product_data["SensorData"] = product_data.get("SensorData", [])
    product_data["CustomObject"] = product_data.get("CustomObject", {})

    try:
        # Invio al middleware esterno
        response = requests.post('http://middleware:3000/uploadProduct', json=product_data)

        if response.status_code == 200:
            try:
                create_product(product_data["ID"], user["_id"])
            except Exception as e:
                print("Errore salvataggio MongoDB:", e)
            return {'message': response.json().get('message', 'Product uploaded successfully!')}, 200
        else:
            return {'message': response.json().get('message', 'Failed to upload product.')}, response.status_code

    except Exception as e:
        return {'message': 'Error uploading product.', 'error': str(e)}, 500


def update_product_service(product_data, user_identity):
    # Controllo permessi
    if not required_permissions(user_identity, ["producer"]):
        return {"message": "Unauthorized: Insufficient permissions."}, 403

    try:
        user = get_user_by_email(user_identity)
        real_manufacturer = user["manufacturer"]

        product_id = product_data.get("ID")
        if not product_id:
            return {"message": "Product ID is required."}, 400

        # Verifica che il manufacturer corrisponda
        verification_result = verify_manufacturer(product_id, real_manufacturer)
        if verification_result:
            return verification_result  # ritorna errore già formattato

        client_manufacturer = product_data.get("Manufacturer")
        if real_manufacturer != client_manufacturer:
            return {"message": "Unauthorized: Manufacturer mismatch."}, 403

        # Chiamata al middleware esterno
        response = requests.post(
            "http://middleware:3000/api/product/updateProduct",
            json=product_data
        )

        if response.status_code != 200:
            return {"message": "Failed to update product."}, response.status_code

        # --- Gestione salvataggio modifiche su DB ---
        last_history = get_last_history_entry(product_id)
        old_data = {}
        if last_history and last_history.get("changes"):
            for change in last_history["changes"]:
                field = change["field"]
                if field.startswith("CustomObject."):
                    _, subkey = field.split(".", 1)
                    if "CustomObject" not in old_data:
                        old_data["CustomObject"] = {}
                    old_data["CustomObject"][subkey] = change["newValue"]
                else:
                    old_data[field] = change["newValue"]

        changes = get_product_changes(old_data, product_data)
        if changes:
            add_history_entry(product_id, user["_id"], changes)

        return {"message": "Product updated successfully!"}, 200

    except Exception as e:
        print("Error updating product:", e)
        return {"message": "Error updating product.", "error": str(e)}, 500

# Funzione per aggiungere un prodotto ai liked products
def like_product_service(request):
    if request.method == 'OPTIONS':
        response = {'message': 'OK'}
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        return response, 200

    data = request.json
    product_data = data.get('product')
    user_id = data.get('userId', None)
    if not user_id or not product_data or not product_data.get('ID'):
        return {"message": "Missing userId or product data"}, 400

    # Controllo duplicato
    already_liked = get_liked_products_by_user(user_id)
    if any(p["blockchainProductId"] == product_data["ID"] for p in already_liked):
        return {"message": "Product already liked"}, 200

    like_a_product(user_id, product_data["ID"])
    return {"message": "Product added to liked products"}, 201

    # Save to JSON file
'''    save_liked_products(liked_products)
    
    print(f"Product {product_data['ID']} added to liked products for user {user_id}. Total: {len(liked_products[user_id])}")
    return jsonify({"message": "Product added to liked products"}), 201'''

# Funzione per rimuovere un prodotto dai liked products
def unlike_product_service(request):
    product_id = request.args.get('productId')
    user_id = request.args.get('userId', None)
    if not user_id or not product_id:
        response = {"message": "Missing userId or productId"}
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'DELETE')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response, 400

    liked = get_liked_products_by_user(user_id)
    if not any(p["blockchainProductId"] == product_id for p in liked):
        response = {"message": "Product not found in liked products"}
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'DELETE')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response, 404

    unlike_a_product(user_id, product_id)
    response = {"message": "Product removed from liked products"}
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Methods', 'DELETE')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    return response, 200

# Funzione per ottenere i liked products di un utente
def get_liked_products_service(request):
    user_id = request.args.get('userId', None)
    if not user_id:
        return [], 200

    liked = get_liked_products_by_user(user_id)
    return liked, 200

# Funzione per salvare i liked products su file JSON (se serve)
def save_liked_products(products):
    with open('liked_products.json', 'w') as f:
        json.dump(products, f, indent=4)

# Initialize the liked_products variable
#liked_products = load_liked_products()
