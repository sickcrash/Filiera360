import bcrypt
from flask import jsonify
from flask_jwt_extended import create_access_token
# from datetime import timedelta

from database_mongo.queries.otp_queries import create_otp
from database_mongo.queries.users_queries import get_user_by_email
from ..utils.otp_utils import generate_otp
from ..utils.email_utils import send_otp_email

# OTP_LIFETIME = timedelta(minutes=5)

def send_otp(email):
    """Genera e invia un OTP a un utente."""
    user = get_user_by_email(email)
    if not user:
        return jsonify({"message": "User not found."}), 404

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
    if send_otp(email):
        return jsonify({"message": "OTP sent to your email."})
    else:
        return jsonify({"message": "Failed to send OTP."}), 500

    # Se la 2FA non è necessaria, crea un token JWT