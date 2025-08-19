from flask import request, jsonify

from ..services.ai_service import scan_service, ask_service

def scan_controller():
    item_code = request.json.get("item_code")
    result = scan_service(item_code)
    return jsonify(result["body"]), result["status"]

def ask_controller():
    user_input = request.json.get("message")
    item_code = request.json.get("item_code")
    result = ask_service(user_input, item_code)
    return jsonify(result["body"]), result["status"]
