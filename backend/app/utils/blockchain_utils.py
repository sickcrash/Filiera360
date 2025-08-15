import requests
from flask import jsonify

def verify_manufacturer(product_id, real_manufacturer):
    """
    Verifica che il manufacturer autenticato corrisponda al manufacturer registrato sulla blockchain per un prodotto.
    Restituisce None se la verifica passa, altrimenti jsonify con errore e status code.
    """
    try:
        blockchain_response = requests.get(f'http://localhost:3000/readProduct?productId={product_id}')
        if blockchain_response.status_code == 200:
            blockchain_data = blockchain_response.json()
            registered_manufacturer = blockchain_data.get("Manufacturer")
            if not registered_manufacturer:
                return jsonify({"message": "Manufacturer not found on blockchain."}), 404
            if real_manufacturer != registered_manufacturer:
                return jsonify({"message": "Unauthorized: Manufacturer mismatch."}), 403
            return None  # Nessun errore
        else:
            return jsonify({"message": "Failed to retrieve product from blockchain."}), 500
    except Exception as e:
        print("Error connecting to blockchain:", e)
        return jsonify({"message": "Error retrieving product from blockchain."}), 500
