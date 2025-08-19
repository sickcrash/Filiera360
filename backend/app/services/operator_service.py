from ..utils.permissions_utils import required_permissions
from database_mongo.queries.users_queries import get_user_by_email, update_user


def get_operators_service(user_email):
    if not required_permissions(user_email, ['producer']):
        return {"operators": []}, 403 # Utente non autorizzato

    user = get_user_by_email(user_email)
    if not user:
        return {"operators": []}, 404 # Utente non trovato

    operators = user.get("operators") or []
    # Serializza ObjectId in stringa
    for op in operators:
        if "operatorId" in op and not isinstance(op["operatorId"], str):
            op["operatorId"] = str(op["operatorId"])
    return {"operators": operators}, 200

def add_operator_service(user_email, data):
    if not required_permissions(user_email, ['producer']):
        return {"message": "Unauthorized: Insufficient permissions."}, 403

    operator_email = data.get("email")
    if not operator_email:
        return {"message": "Email is required."}, 400

    operator = get_user_by_email(operator_email)
    if not operator:
        return {"message": "Operator not found."}, 404

    if not operator.get("flags", [])[1]:  # flags[1] == operator
        return {"message": "User is not an operator and cannot be added."}, 400

    user = get_user_by_email(user_email)
    if any(op["email"] == operator_email for op in user.get("operators", [])):
        return {"message": "Operator already added."}, 409

    # Aggiorna la lista operatori su MongoDB
    user["operators"].append({"operatorId": operator["_id"], "email": operator_email})
    update_user(user["_id"], {"operators": user["operators"]})

    return {"message": "Operator added successfully."}, 201

def remove_operator_service(user_email, data):
    if not required_permissions(user_email, ['producer']):
        return {"message": "Unauthorized: Insufficient permissions."}, 403

    operator_email = data.get("email")
    if not operator_email:
        return {"message": "Email is required."}, 400

    user = get_user_by_email(user_email)
    if not any(op["email"] == operator_email for op in user.get("operators", [])):
        return {"message": "Operator not found."}, 404

    user["operators"] = [op for op in user["operators"] if op["email"] != operator_email]
    update_user(user["_id"], {"operators": user["operators"]})

    return {"message": "Operator removed successfully."}, 200
