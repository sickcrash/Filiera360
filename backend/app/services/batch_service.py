import requests

from ..utils.auth_utils import verify_product_authorization
from ..utils.permissions_utils import required_permissions
from database_mongo.queries.users_queries import get_user_by_email


def get_batch_service(batch_id):
    if not batch_id:
        return {'message': 'Batch ID is required'}, 400

    try:
        response = requests.get(f'http://middleware:3000/readBatch?batchId={batch_id}')
        if response.status_code == 200:
            return response.json(), 200
        else:
            return {'message': 'Failed to get batch.'}, 500
    except Exception as e:
        print("Failed to get batch:", e)
        return {'message': 'Failed to get batch.'}, 500

def get_batch_history_service(batch_id):
    if not batch_id:
        return {'message': 'Batch ID is required'}, 400

    try:
        response = requests.get(f'http://middleware:3000/batchHistory?batchId={batch_id}')
        if response.status_code == 200:
            return response.json(), 200
        else:
            return {'message': 'Failed to get batch history'}, 500
    except Exception as e:
        print("Failed to get batch history:", e)
        return {'message': 'Failed to get batch history.'}, 500

def upload_batch_service(user_email, batch_data):
    # Controllo permessi
    if not required_permissions(user_email, ['producer', 'operator']):
        return {"message": "Unauthorized: Insufficient permissions."}, 403

    if not batch_data:
        return {"message": "No batch data provided."}, 400

    # Controllo autorizzazione al prodotto
    if not verify_product_authorization(user_email, batch_data.get("ProductId")):
        return {"message": "Unauthorized: You do not have access to this product."}, 403

    # Controllo operatore reale
    real_operator = get_user_by_email(user_email).get("manufacturer")
    client_operator = batch_data.get("Operator")
    if real_operator != client_operator:
        return {"message": "Unauthorized: Operator mismatch."}, 403

    # Assicura che CustomObject esista
    batch_data["CustomObject"] = batch_data.get("CustomObject", {})

    try:
        # Chiamata al middleware esterno
        response = requests.post('http://middleware:3000/uploadBatch', json=batch_data)
        if response.status_code == 200:
            return {'message': response.json().get('message', 'Batch uploaded successfully!')}, 200
        else:
            return {'message': response.json().get('message', 'Failed to upload batch.')}, response.status_code
    except Exception as e:
        print("Error uploading batch:", e)
        return {'message': 'Error uploading batch.', 'error': str(e)}, 500

def update_batch_service(user_email, batch_data):
    if not required_permissions(user_email, ['producer', 'operator']):
        return {"message": "Unauthorized: Insufficient permissions."}, 403

    if not batch_data:
        return {"message": "No batch data provided."}, 400

    if not verify_product_authorization(user_email, batch_data.get("ProductId")):
        return {"message": "Unauthorized: You do not have access to this product."}, 403

    real_operator = get_user_by_email(user_email).get("manufacturer")
    client_operator = batch_data.get("Operator")
    if real_operator != client_operator:
        return {"message": "Unauthorized: Operator mismatch."}, 403

    # Assicura che CustomObject esista
    batch_data["CustomObject"] = batch_data.get("CustomObject", {})

    print("✅ Autorizzato, procedo con l'aggiornamento del batch...")

    try:
        print("📢 Invia i dati aggiornati alla blockchain...")
        response = requests.post('http://middleware:3000/api/batch/updateBatch', json=batch_data)
        print("📢 Risposta dalla blockchain:", response.status_code, response.text)

        if response.status_code == 200:
            return {'message': 'Batch updated successfully!'}, 200
        else:
            return {'message': 'Failed to update batch.'}, response.status_code

    except Exception as e:
        print(f"❌ ERRORE nel service update_batch_service: {e}")
        return {'message': 'Internal Server Error'}, 500


