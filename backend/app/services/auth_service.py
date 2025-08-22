import bcrypt
from flask import jsonify
from flask_jwt_extended import create_access_token
from flask_mail import Message
from flask import current_app
# from datetime import timedelta

from ..database_mongo.queries.otp_queries import create_otp, delete_otp_by_user_id, get_otp_by_user_id
from ..database_mongo.queries.token_queries import get_token, mark_token_as_used
from ..database_mongo.queries.users_queries import get_user_by_email, get_user_by_manufacturer, create_user, update_user
from ..utils.bcrypt_utils import hash_password
from ..utils.otp_utils import generate_otp
from ..utils.email_utils import send_otp_email
from ..utils.token_utils import generate_reset_token, verify_reset_token

# OTP_LIFETIME = timedelta(minutes=5)
def send_otp(email, user):
    """Genera e invia un OTP a un utente."""
    otp = generate_otp()
    create_otp(user["_id"], str(otp))

    return send_otp_email(email, otp)

def process_login(email, password):
    user = get_user_by_email(email)

    # Verifica se l'utente esiste e la password è corretta
    if not user or not bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
        return jsonify({"message": "Invalid email or password"}), 401

    """ # Se la 2FA è abilitata, invia il codice OTP
    if user.get('two_factor_enabled', False):
        secret = user.get('2fa_secret', None)
        if not secret:
            secret = pyotp.random_base32()  # Genera un segreto se non esiste
            user['2fa_secret'] = secret
            save_users(users)  # Salva l'utente con il nuovo segreto

        otp = pyotp.TOTP(secret).now()  # Genera il codice OTP
        # In un'app reale, invieresti l'OTP via email o SMS, ma per ora lo restituiamo nel corpo della risposta
        return jsonify({"message": "2FA required", "otp": otp})  # Solo per scopi di sviluppo """

    # Se l'utente ha il flag user attivo
    if user["flags"][2]: # flags[2] == user
        token = create_access_token(email)
        return jsonify({
            "message": "Login successful",
            "access_token": token,
            "role": user['role'],
            "manufacturer": user['manufacturer'],
            "email": email
        })

    # Se il flag non è attivo → OTP
    if send_otp(email, user):
        return jsonify({"message": "OTP sent to your email."})
    else:
        return jsonify({"message": "Failed to send OTP."}), 500

    # Se la 2FA non è necessaria, crea un token JWT

def process_signup(data):
    email = data.get('email')
    manufacturer = data.get('manufacturer')
    password = data.get('password')
    role = data.get('role', 'user')
    invite_token = data.get('inviteToken', None)

    # Verifica che tutti i campi siano forniti
    if not email or not manufacturer or not password:
        return {"message": "All fields are required"}, 400

    # Controlla se l'email è già registrata
    if get_user_by_email(email):
        return {"message": "Email already exists"}, 409

    # Controlla se il manufacturer è già registrato
    if get_user_by_manufacturer(manufacturer):
        return {"message": "Manufacturer already exists"}, 409

    # Controlla il token di invito per i produttori
    if role == "producer":
        if not invite_token:
            return {"message": "The invite token is required for producers."}, 400

        token_doc = get_token(invite_token)
        if not token_doc:
            return {"message": "Invalid invitation token."}, 403
        if token_doc.get("used"):
            return {"message": "Invitation token already used."}, 403

    # Crea un hash della password con bcrypt
    hashed_password = hash_password(password)
    create_user(email, hashed_password, manufacturer, role)

    # Se il token è stato usato, viene segnato come utilizzato
    if role == "producer" and invite_token:
        mark_token_as_used(invite_token, email)

    return {"message": "User registered successfully"}, 201

def verify_otp_service(data):
    email = data.get('email')
    otp = data.get('otp')

    user = get_user_by_email(email)
    if not user:
        return {"message": "User not found."}, 404

    otp_entry = get_otp_by_user_id(user["_id"])
    if not otp_entry or otp_entry["otp"] != str(otp):
        return {"message": "Invalid or expired OTP."}, 400

    delete_otp_by_user_id(user["_id"])
    token = create_access_token(email)

    return {
        "message": "OTP validated successfully.",
        "access_token": token,
        "role": user['role'],
        "manufacturer": user['manufacturer'],
        "email": email
    }, 200

def change_password_service(data, user_identity):
    current_password = data.get('currentPassword')
    new_password = data.get('newPassword')

    if not current_password or not new_password:
        return {"message": "Both current and new password are required."}, 400

    user = get_user_by_email(user_identity)
    if not user:
        return {"message": "User not found."}, 404

    # Verifica la password attuale
    if not bcrypt.checkpw(current_password.encode('utf-8'), user['password'].encode('utf-8')):
        return {"message": "Current password is incorrect."}, 401

    # Aggiorna la password
    hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    update_user(user["_id"], {"password": hashed_password})

    return {"message": "Password changed successfully."}, 200

def forgot_password_service(data):
    email = data.get('email')

    if not email or not get_user_by_email(email):
        return {"message": "Email not found"}, 404

    token = generate_reset_token(email)
    reset_url = f"/api/reset-password/{token}"

    msg = Message(
        'Password Reset Request',
        sender='noreply@example.com',
        recipients=[email]
    )
    msg.body = f"To reset your password, visit the following link: {reset_url}"
    mail = current_app.extensions.get('mail')
    mail.send(msg)

    return {"message": "Password reset email sent"}, 200

def reset_password_service(token, request):
    email = verify_reset_token(token)
    if email is None:
        return {"message": "Invalid or expired token"}, 400

    if request.method == 'POST':
        if request.content_type != 'application/json':
            return {"message": "Content-Type must be application/json"}, 415

        new_password = request.json.get('password')
        if not new_password:
            return {"message": "Password is required"}, 400

        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        update_user(get_user_by_email(email)["_id"], {"password": hashed_password})
        return {"message": "Password updated successfully"}, 200

    return {"message": "Token is valid, proceed with password reset"}, 200
