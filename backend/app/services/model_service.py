from ..utils.blockchain_utils import verify_manufacturer
from ..utils.permissions_utils import required_permissions
from database_mongo.queries.models_queries import upsert_model_for_product, get_model_by_blockchain_id
from database_mongo.queries.users_queries import get_user_by_email


def upload_model_service(user_email, product_data):
    if not required_permissions(user_email, ['producer']):
        return {"message": "Unauthorized: Insufficient permissions."}, 403

    try:
        real_manufacturer = get_user_by_email(user_email)["manufacturer"]
        print("Manufacturer authenticated: ", real_manufacturer)

        product_id = product_data.get("ID")
        if not product_id:
            return {"message": "Product ID is required."}, 400

        print("Product ID:", product_id)

        # Verifica che il manufacturer autenticato corrisponda
        verification_result = verify_manufacturer(product_id, real_manufacturer)
        if verification_result:
            return verification_result  # restituisce eventuale errore della verifica

        glbFile = product_data.get('ModelBase64')
        if not glbFile:
            return {"message": "Missing GLB file"}, 400

        print("Uploading 3D model...")
        upsert_model_for_product(product_id, glbFile, get_user_by_email(user_email)["_id"])

        return {"message": "Model uploaded successfully"}, 201

    except Exception as e:
        print(f"ERRORE nel service upload_model_service: {e}")
        return {"message": f"An error occurred: {str(e)}"}, 500

def get_model_service(product_id):
    if not product_id:
        return {"message": "Product ID is required."}, 400

    try:
        model = get_model_by_blockchain_id(product_id)
        if not model:
            return {"message": "No model found for the provided product ID."}, 404

        return {"ModelBase64": model["modelString"]}, 200

    except Exception as e:
        print(f"ERRORE nel service get_model_service: {e}")
        return {"message": f"An error occurred: {str(e)}"}, 500