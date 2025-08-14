from flask import request, jsonify
from ..services.auth_service import process_login, process_signup

def login():
    data = request.get_json()
    if not data or not data.get("email") or not data.get("password"):
        return jsonify({"message": "Email and password are required"}), 400

    return process_login(data["email"], data["password"])

def signup():
    data = request.get_json()
    result, status_code = process_signup(data)
    return jsonify(result), status_code

