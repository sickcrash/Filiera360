import json
import os
import random
import secrets
import traceback
from datetime import datetime, timedelta
import pymysql
import time
import pytz
import base64

import bcrypt
import jwt
import pyotp
import requests
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from flask_jwt_extended import (JWTManager, create_access_token, decode_token,
                                get_jwt_identity, jwt_required)
from flask_jwt_extended.exceptions import JWTExtendedException
from flask_mail import Mail, Message
from langchain_community.llms import Ollama
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from werkzeug.security import check_password_hash

import prompts_variables_storage

# le variabili d'ambiente ottenute da Docker Compose
MYSQL_HOST = os.getenv("MYSQL_HOST", "mysql")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DB = os.getenv("MYSQL_DB", "filiera360")
def get_db_connection():
    max_retries = 10

    for attempt in range(max_retries):
     try:
        connection = pymysql.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB,
            port=3306,
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    
     except pymysql.MySQLError as e:
        print(f"Connection failed on attempt {attempt + 1}/{max_retries}: {e}")
        time.sleep(2)
    raise Exception("Could not connect to MySQL after several retries.")

# Update the CORS configuration to allow all methods
app = Flask(__name__, instance_relative_config=True)
app.config['MAX_CONTENT_LENGTH'] = 300 * 1024 * 1024
CORS(app, resources={r"/*": {"origins": "*"}})
app.config['CORS_HEADERS'] = 'Content-Type'

cors = CORS(app, resources={r"/*": {"origins": "*", "methods": ["GET", "POST", "DELETE", "OPTIONS"]}})
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['DEBUG'] = True

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'filiera360@gmail.com'  
app.config['MAIL_PASSWORD'] = 'bspi hkbw jcwh yckx'

mail = Mail(app)
# Funzione per generare l'OTP
def generate_otp():
    return random.randint(100000, 999999) 

def create_jwt_token(email):
    expiration = datetime.utcnow() + timedelta(hours=1)
    token = jwt.encode({'email': email, 'exp': expiration}, app.config['SECRET_KEY'], algorithm='HS256')
    return token


# Funzione per inviare l'OTP tramite email
def send_otp_email(email, otp):
    try:
        msg = Message('OTP Code',
                  sender='noreply@example.com',
                  recipients=[email])
        msg.body = f"This is your OTP code: {otp}"
        mail.send(msg)
    except Exception as e:
        print(f"Error sending email: {e}")
        return False
    return True



otp_lifetime = timedelta(minutes=5)


# @app.route('/send-otp', methods=['POST'])
def send_otp(email):
    otp = generate_otp()
    local_tz = pytz.timezone("Europe/Rome")
    expiration_time = (datetime.now(local_tz) + otp_lifetime).strftime("%Y-%m-%d %H:%M:%S")

    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Controlla se l'utente esiste
            cursor.execute("SELECT email FROM users WHERE email = %s", (email,))
            if not cursor.fetchone():
                return jsonify({"message": "User not found."}), 404

            # Inserisci o aggiorna OTP
            cursor.execute("""
                INSERT INTO otp_codes (email, otp, expiration)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE otp = VALUES(otp), expiration = VALUES(expiration)
            """, (email, otp, expiration_time))
        
        connection.commit()  
        connection.close()

    except Exception as e:
        print(f"[OTP ERROR] {e}")
        traceback.print_exc()
        return jsonify({"message": "Error saving OTP to database."}), 500


    '''if send_otp_email(email, otp):
        return jsonify({"message": "OTP sent to your email."})
    else:
        return jsonify({"message": "Failed to send OTP."}), 500'''
    # CODICE AGGIUNTO PER LO STRESS TEST
    print(f"[TEST] OTP generato per {email}: {otp} (non inviato)")
    return jsonify({"message": f"OTP generated for {email} (simulato)."}), 200




# Verifica che il manufacturer autenticato corrisponda al manufacturer del prodotto
def verify_manufacturer(product_id, real_manufacturer):
    try:
        blockchain_response = requests.get(f'http://middleware:3000/readProduct?productId={product_id}')
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

# Verifica che il manufacturer autenticato corrisponda al manufacturer del prodotto
def verify_operator(batch_id, real_operator):
    try:
        blockchain_response = requests.get(f'http://middleware:3000/readBatch?batchId={batch_id}')
        print("📢 Risposta dalla blockchain:", blockchain_response)
        if blockchain_response.status_code != 200:
            print(f"Errore: impossibile recuperare batch {batch_id}")
            return jsonify({"message": "Failed to retrieve batch from blockchain."}), 500  # Restituisce solo il codice di errore

        blockchain_data = blockchain_response.json()
        registered_operator = blockchain_data.get("Operator")

        if not registered_operator:
            print("Errore: Operatore non trovato sulla blockchain")
            return jsonify({"message": "Operator not found on blockchain."}), 404  #  Operatore non trovato
        if real_operator != registered_operator:
            print("Errore: Operatore non autorizzato")
            return jsonify({"message": "Unauthorized: Operator mismatch."}), 403  #  Operatore non autorizzato

        return None  # ✅ Verifica OK

    except Exception as e:
        print("Error connecting to blockchain:", e)
        return  jsonify({"message": "Error retrieving batch from blockchain.", "error": str(e)}), 500   # Errore generico


@app.route('/')
def index():
    return render_template('index.html')

# configurazione JWT: genera una chiave sicura
# se la variabile di ambiente non è impostata
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', secrets.token_hex(32)) 
jwt = JWTManager(app)


def generate_reset_token(email):
    expiration = timedelta(hours=1)  

    token = create_access_token(email, expires_delta=expiration)
    return token


def verify_reset_token(token):
    try:
        decoded_token = decode_token(token)
        return decoded_token['sub']
    except JWTExtendedException as e:
        print(f"Errore nel token: {e}")
        return None

@app.route('/forgot-password', methods=['POST'])
def forgot_password():
    email = request.json.get('email')
    try:
        # Query al database per verificare se l'email esiste
        connection = get_db_connection()
        with connection.cursor() as cursor:
            sql = "SELECT email FROM users WHERE email = %s"
            cursor.execute(sql, (email,))
            user = cursor.fetchone()

        if not user:
            return jsonify({"message": "Email not found"}), 404

        token = generate_reset_token(email)
        reset_url = f"/api/reset-password/{token}"

        msg = Message('Password Reset Request',
                      sender='noreply@example.com',
                      recipients=[email])
        msg.body = f"To reset your password, visit the following link: {reset_url}"
        mail.send(msg)

        return jsonify({"message": "Password reset email sent"}), 200
    
    except Exception as e:
        print("Error while handling forgot-password request:", e)
        return jsonify({"message": "Internal server error", "error": str(e)}), 500


@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    email = verify_reset_token(token)

    if email is None:
        return jsonify({"message": "Invalid or expired token"}), 400


    if request.method == 'POST':
        if request.content_type != 'application/json':
            return jsonify({"message": "Content-Type must be application/json"}), 415  

        new_password = request.json.get('password')

        if not new_password:
            return jsonify({"message": "Password is required"}), 400

        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        try:
            connection = get_db_connection()
            with connection.cursor() as cursor:
                sql = "UPDATE users SET password = %s WHERE email = %s"
                cursor.execute(sql, (hashed_password, email))
                connection.commit()

            return jsonify({"message": "Password updated successfully"}), 200

        except Exception as e:
            print("Database error while updating password:", e)
            return jsonify({"message": "Database error", "error": str(e)}), 500

    return jsonify({"message": "Token is valid, proceed with password reset"}), 200

###################
# Carica dal db
def load_users():
    connection = get_db_connection()
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        return {user['email']: user for user in users}

 
# Carica i modelli 3D dal db
def load_models():
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM models")
            models = cursor.fetchall()
            return {str(model['id']): model for model in models}
    except Exception as e:
        print("Error loading models from database:", e)
        return {}  # Se il file non esiste o è vuoto, restituisce un dizionario vuoto
    
 #################   
# Salva gli utenti nel db
def save_users(users):
    connection = get_db_connection()
    with connection.cursor() as cursor:
        for email, user in users.items():
            cursor.execute("""
                INSERT INTO users (email, manufacturer, password, role, operators)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    manufacturer=VALUES(manufacturer),
                    password=VALUES(password),
                    role=VALUES(role),
                    operators=VALUES(operators)
            """, (
                user.get('email'),
                user.get('manufacturer'),
                user.get('password'),
                user.get('role'),
                user.get('operators')
            ))
    connection.commit()


# Salva i modelli nel DB
def save_models(models):
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            for product_id, glbFile in models.items():
                cursor.execute("""
                    INSERT INTO models (id, stringa) VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE stringa = VALUES(stringa)
                """, (product_id, glbFile))
        connection.commit()
    except Exception as e:
        print("Error saving model to database:", e)



# questa funzione va chiamata solamente alla prima scrittura
# della rete o dopo suoi eventuali reset
@app.route('/initLedger', methods=['POST'])
def init_ledger():
    # Leggi il file sampleData.json
    try:
        with open('sampleData.json', 'r') as file:
            print(file)
            products = json.load(file)
    except Exception as e:
        print("Errore nella lettura di sampleData.json:", e)
        return jsonify({"message": "Errore nella lettura del file di dati iniziali."}), 500

    # Invio dei dati del prodotto alla rete
    errors = []
    for product in products:
        try:
            response = requests.post(f'http://middleware:3000/uploadProduct', json=product)
            if response.status_code != 200:
                errors.append({"product_id": product.get("ID"), "error": response.json().get("message", "Unknown error")})
        except Exception as e:
            print(f"Errore nell'upload del prodotto {product.get('ID')}: {e}")
            errors.append({"product_id": product.get("ID"), "error": str(e)})

    if errors:
        return jsonify({"message": "Errore durante l'inizializzazione del ledger.", "errors": errors}), 500
    else:
        return jsonify({"message": "Ledger initialized successfully with sample data."})

def is_valid_invite_token(token):
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Recupera il token dal DB
            sql = "SELECT code, expires_at, used FROM invite_token WHERE code = %s"
            cursor.execute(sql, (token,))
            token_data = cursor.fetchone()

            if not token_data:
                return False, "Invalid invitation token."

            expires_at = token_data["expires_at"]
            used = token_data["used"]

            # Verifica scadenza
            if datetime.now() > expires_at:
                return False, "Expired invitation token."

            # Verifica se è già usato
            if used:
                return False, "Invitation token already used."

            return True, "Valid token."

    except Exception as e:
        print("Database error while validating token:", e)
        return False, "Internal error during token validation."

###########
@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    email = data.get('email')
    manufacturer = data.get('manufacturer')
    password = data.get('password')
    role = data.get('role', 'user') 
    invite_token = data.get('inviteToken', None) 
    
    #Verifica che tutti i campi siano forniti
    if not email or not manufacturer or not password:
        return jsonify({"message": "All fields are required"}), 400
    
    #Controlla se l'email è già presente nel database
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT email FROM users WHERE email = %s", (email,))
            if cursor.fetchone():  # Se l'email esiste già nel DB
                return jsonify({"message": "Email already exists"}), 409

            #Controlla se il manufacturer è già registrato nel database
            cursor.execute("SELECT manufacturer FROM users WHERE manufacturer = %s", (manufacturer,))
            if cursor.fetchone():  # Se il manufacturer esiste già nel DB
                return jsonify({"message": "Manufacturer already exists"}), 409

            
            if role == "producer":
                if not invite_token:
                    return jsonify({"message": "The invite token is required for producers."}), 400

                is_valid, message = is_valid_invite_token(invite_token)
                if not is_valid:
                    return jsonify({"message": message}), 403

            # Crea un hash della password con bcrypt
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            #Inserisci l'utente nel db
            cursor.execute("""
                INSERT INTO users (email, manufacturer, password, role)
                VALUES (%s, %s, %s, %s)
            """, (
                email,
                manufacturer,
                hashed_password,
                role
            ))

            connection.commit()

            #Se il token è stato usato, viene segnato come utilizzato
        if role == "producer" and invite_token:
         try:
            connection = get_db_connection()
            with connection.cursor() as cursor:
             sql = "UPDATE invite_token SET used = TRUE WHERE code = %s"
             cursor.execute(sql, (invite_token,))
            connection.commit()
         except Exception as e:
          print("Errore durante l'aggiornamento dello stato del token:", e)
          return jsonify({"message": "Database error while updating token status"}), 500
        return jsonify({"message": "User registered successfully"}), 201

    except pymysql.MySQLError as e:
        print(f"Error: {e}")
        return jsonify({"message": "Database error"}), 500



####################################
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    try:
        connection = get_db_connection()
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:  
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()

        if not user or not bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            return jsonify({"message": "Invalid email or password"}), 401

        # Per utenti con ruolo "user", login diretto con JWT
        if user['role'] == 'user':
            token = create_access_token(identity=email)
            return jsonify({
                "message": "Login successful",
                "access_token": token,
                "role": user['role'],
                "manufacturer": user.get('manufacturer'),
                "email": email
            })

        # Per altri ruoli
        otp_response = send_otp(email)
        return otp_response  

    except Exception as e:
        print(f"Error during login: {e}")
        return jsonify({"message": "Internal server error"}), 500

    


# Endpoint per la verifica dell'OTP
@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    data = request.get_json()
    email = data.get('email')
    otp = str(data.get('otp')) 

    # Controlla se l'email o l'OTP sono vuoti
    if not email or not otp:
        return jsonify({"message": "Email and OTP are required."}), 400

    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
        
            cursor.execute("SELECT otp, expiration FROM otp_codes WHERE email = %s", (email,))
            record = cursor.fetchone()

            if not record:
                return jsonify({"message": "OTP has expired or is invalid."}), 400

            stored_otp = record['otp']
            expiration_time = record['expiration']

            #Verifica se l'OTP corrisponde e se non è scaduto
            if str(stored_otp) == otp and expiration_time > datetime.now():
                # OTP valido, genera access token e restituisci i dati utente
                cursor.execute("SELECT email, role, manufacturer FROM users WHERE email = %s", (email,))
                user = cursor.fetchone()

                #verifica se l'utente non esiste
                if not user:
                    return jsonify({"message": "User not found."}), 404

                #Crea il token JWT
                token = create_access_token(email)
                
                return jsonify({
                    "message": "OTP validated successfully.",
                    "access_token": token,
                    "role": user['role'],
                    "manufacturer": user['manufacturer'],
                    "email": email
                }), 200
            else:
                return jsonify({"message": "Invalid or expired OTP."}), 400

    except Exception as e:
        print(f"Errore nella verifica dell'OTP: {e}")
        return jsonify({"message": "Internal server error"}), 500

 # CODICE AGGIUNTO PER LO STRESS TEST
@app.route('/get-latest-otp', methods=['GET'])
def get_latest_otp():
    email = request.args.get('email')
    if not email:
        return jsonify({"message": "Email is required"}), 400

    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT otp FROM otp_codes WHERE email = %s", (email,))
            record = cursor.fetchone()

            if not record:
                return jsonify({"message": "OTP not found"}), 404

            return jsonify({"otp": record['otp']})
    except Exception as e:
        print(f"Errore nel recupero OTP: {e}")
        return jsonify({"message": "Internal server error"}), 500


@app.route('/operators', methods=['GET'])
@jwt_required()
def get_operators():
    user_email = get_jwt_identity()

    if not required_permissions(user_email, ['producer']):
        return jsonify({"operators": None}), 403
    connection = get_db_connection()
    with connection.cursor() as cursor:
        cursor.execute("SELECT operators FROM users WHERE email = %s", (user_email,))
        result = cursor.fetchone()
        operators = json.loads(result["operators"]) if result and result["operators"] else []

    return jsonify({"operators": operators})




@app.route('/operators/add', methods=['POST'])
@jwt_required()
def add_operator():
    user_email = get_jwt_identity()

    if not required_permissions(user_email, ['producer']):
        return jsonify({"message": "Unauthorized: Insufficient permissions."}), 403

    data = request.json
    operator_email = data.get("email")
    if not operator_email:
        return jsonify({"message": "Email is required."}), 400
    connection = get_db_connection()
    with connection.cursor() as cursor:
        #verifica se l'utente da aggiungere è un operatore
        cursor.execute("SELECT role FROM users WHERE email = %s", (operator_email,))
        operator = cursor.fetchone()
        if not operator:
            return jsonify({"message": "Operator not found."}), 404
        if operator["role"] != "operator":
            return jsonify({"message": "User is not an operator."}), 400

        cursor.execute("SELECT operators FROM users WHERE email = %s", (user_email,))
        user = cursor.fetchone()
        operators = json.loads(user["operators"]) if user and user["operators"] else []

        if operator_email in operators:
            return jsonify({"message": "Operator already added."}), 409

        operators.append(operator_email)

        # Salva nel db
        cursor.execute("UPDATE users SET operators = %s WHERE email = %s",
                       (json.dumps(operators), user_email))
        connection.commit()
    return jsonify({"message": "Operator added successfully."}), 201



@app.route('/operators/delete', methods=['POST'])
@jwt_required()
def remove_operator():
    user_email = get_jwt_identity()

    if not required_permissions(user_email, ['producer']):
        return jsonify({"message": "Unauthorized: Insufficient permissions."}), 403

    data = request.json
    operator_email = data.get("email")
    if not operator_email:
        return jsonify({"message": "Email is required."}), 400
    connection = get_db_connection()
    with connection.cursor() as cursor:
        cursor.execute("SELECT operators FROM users WHERE email = %s", (user_email,))
        user = cursor.fetchone()
        operators = json.loads(user["operators"]) if user and user["operators"] else []

        if operator_email not in operators:
            return jsonify({"message": "Operator not found."}), 404

        operators.remove(operator_email)

        cursor.execute("UPDATE users SET operators = %s WHERE email = %s",
                       (json.dumps(operators), user_email))
        connection.commit()
    return jsonify({"message": "Operator removed successfully."})






# già usata su frontend
@app.route('/getProduct', methods=['GET'])
# @jwt_required()
def get_product():
    productId = request.args.get('productId')
    print("ATTEMPTING TO CONNECT:")
     # Send request to JavaScript server to get product details
    try: 
        response = requests.get(f'http://middleware:3000/readProduct?productId={productId}')
        if response.status_code == 200:
            productinfo = response.json()
            return jsonify(response.json())
        else:
            return jsonify({'message': 'Failed to get product.'}), 500
    except Exception as e:
        print("Failed to get product:", e)
        return jsonify({'message': 'Failed to get product.'}), 500
    
# nuova aggiunta
@app.route('/getProductHistory', methods=['GET'])
# @jwt_required()
def get_product_history():


    productId = request.args.get('productId')
    print("ATTEMPTING TO CONNECT TO JS SERVER FOR PRODUCT HISTORY:")
    
    # Invia richiesta al server JavaScript per ottenere la cronologia del prodotto
    try:
        response = requests.get(f'http://middleware:3000/productHistory?productId={productId}')
        if response.status_code == 200:
            product_history = response.json()
            return jsonify(product_history)
        else:
            return jsonify({'message': 'Failed to get product history.'}), 500
    except Exception as e:
        print("Failed to get product history:", e)
        return jsonify({'message': 'Failed to get product history.'}), 500

# già usata su frontend
@app.route('/getBatch', methods=['GET'])
def get_batch():
    batchId = request.args.get('batchId')
    print("ATTEMPTING TO CONNECT:")
     # Send request to JavaScript server to get product details
    try: 
        response = requests.get(f'http://middleware:3000/readBatch?batchId={batchId}')
        if response.status_code == 200:
            batchinfo = response.json()
            return jsonify(response.json())
        else:
            return jsonify({'message': 'Failed to get batch.'}), 500
    except Exception as e:
        print("Failed to get batch:", e)
        return jsonify({'message': 'Failed to get batch.'}), 500
    
# nuova aggiunta
@app.route('/getBatchHistory', methods=['GET'])
def get_batch_history():
    batch_id = request.args.get('batchId')
    if not batch_id:
        return jsonify({'message': 'Batch ID is required'}), 400
    
    try:
        response = requests.get(f'http://middleware:3000/batchHistory?batchId={batch_id}')
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'message': 'Failed to get batch history'}), 500
    except Exception as e:
        print("Failed to get batch history:", e)
        return jsonify({'message': 'Failed to get batch history.'}), 500

def find_producer_by_operator(operator_email):
    connection = get_db_connection()
    with connection.cursor() as cursor:
        cursor.execute("SELECT email, operators FROM users WHERE role = 'producer'")
        producers = cursor.fetchall()
        for producer in producers:
            operators = json.loads(producer["operators"]) if producer["operators"] else []
            if operator_email in operators:
                return producer  
    return None

def required_permissions(email, allowed_roles):
    connection = get_db_connection()
    with connection.cursor() as cursor:
        cursor.execute("SELECT role FROM users WHERE email = %s", (email,))
        result = cursor.fetchone()
        return result and result["role"] in allowed_roles


def verify_product_authorization(email, product_id):
    if not email or not product_id:
        return False

    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT role, manufacturer, operators FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            if not user:
                return False

            if user["role"] == "operator":
                producer = find_producer_by_operator(email)
                if not producer:
                    return False
                manufacturer = producer["manufacturer"]
            else:
                # L'utente è un producer o altro
                manufacturer = user["manufacturer"]

        # ottengo il prodotto dal middleware
        response = requests.get(f'http://middleware:3000/readProduct?productId={product_id}')
        if response.status_code != 200:
            print('Failed to get product.')
            return False

        product = response.json()
        return product.get("Manufacturer") == manufacturer

    except Exception as e:
        print("Failed to verify product authorization:", e)
        return False


# ora in uso + autenticazione jwt
@app.route('/uploadProduct', methods=['POST'])
@jwt_required()
def upload_product():
    email = get_jwt_identity()
    if not required_permissions(email, ['producer']):
        return jsonify({"message": "Unauthorized: Insufficient permissions."}), 403

    print("Sono arrivata al backend")
    product_data = request.json

    #debug 
    print("dati ricevuti nella richiesta:", product_data)

   # ottengo manufacturer dal DB in base all'utente loggato
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT manufacturer FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            if not user:
                return jsonify({"message": "User not found."}), 404
            real_manufacturer = user["manufacturer"]
    except Exception as e:
        print("DB error:", e)
        return jsonify({"message": "Database error."}), 500

    print("manufacturer authenticated: " + real_manufacturer)
    client_manufacturer = product_data.get("Manufacturer")
    print("upload request by: " + client_manufacturer)
    # Reject operation if the authenticated manufacturer doesn't match the one in the request
    if real_manufacturer != client_manufacturer:
        return jsonify({"message": "Unauthorized: Manufacturer mismatch."}), 403
    print("Uploading new product data:", product_data)
    product_data["CustomObject"] = product_data.get("CustomObject", {})
    print("Uploading custom object:", product_data["CustomObject"])

    try:
        # Send the cleaned product data to the external service
        print("Faccio la chiamata all'AppServer")
        response = requests.post(f'http://middleware:3000/uploadProduct', json=product_data)

        # DEBUG
        print("REQUEST SENT:", product_data)
        print("RESPONSE STATUS:", response.status_code)
        print("RESPONSE TEXT:", response.text)

        if response.status_code == 200:
            return jsonify({'message': response.json().get('message', 'Product uploaded successfully!')})
        else:
            return jsonify({'message': response.json().get('message', 'Failed to upload product.')}), response.status_code

        
    except Exception as e:
        print("Error uploading product:", e)
        return jsonify({'message': 'Error uploading product.', 'error': str(e)}), 500
    # uploadBatch

@app.route('/uploadBatch', methods=['POST'])
@jwt_required()
def uploadBatch():
    if not required_permissions(get_jwt_identity(), ['producer', 'operator']):
        return jsonify({"message": "Unauthorized: Insufficient permissions."}), 403

    print("Sono arrivata al backend")

    print("Dati ricevuti dal fe:",request.json)
    batch_data = request.json
    print("Dati:",batch_data)

    if not verify_product_authorization(get_jwt_identity(), batch_data.get("ProductId")):
        return jsonify({"message": "Unauthorized: You do not have access to this product."}), 403

    identity = get_jwt_identity()

    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            sql = "SELECT manufacturer FROM users WHERE email = %s"
            cursor.execute(sql, (identity,))
            user = cursor.fetchone()

        if not user:
            return jsonify({"message": "User not found"}), 404

        real_operator = user["manufacturer"]
        print("operator authenticated: " + real_operator)

    except Exception as e:
        print("Database error while fetching user:", e)
        return jsonify({"message": "Database error", "error": str(e)}), 500

    client_operator = batch_data.get("Operator")
    print("upload request by: " + client_operator)
    # Reject operation if the authenticated manufacturer doesn't match the one in the request
    if real_operator != client_operator:
        return jsonify({"message": "Unauthorized: Operator mismatch."}), 403
    print("Uploading new batch data:", batch_data)
    batch_data["CustomObject"] = batch_data.get("CustomObject", {})
    print("Uploading custom object:", batch_data["CustomObject"])

    try:
        # Send the cleaned product data to the external service
        print("Faccio la chiamata all'AppServer")
        response = requests.post('http://middleware:3000/uploadBatch', json=batch_data)
        if response.status_code == 200:
            print('Risposta dalla blockchain: ',response.status_code)
            return jsonify({'message': response.json().get('message', 'Batch uploaded successfully!')})
        else:
            print('Risposta dalla blockchain: ',response.status_code)

            return jsonify({'message': response.json().get('message', 'Failed to upload batch.')}), response.status_code

        
    except Exception as e:
        print("Error uploading batch:", e)
        return jsonify({'message': 'Error uploading batch.', 'error': str(e)}), 500
    
# nuova aggiunta
@app.route('/uploadModel', methods=['POST'])
@jwt_required()
def upload_model():
    email = get_jwt_identity()
    if not required_permissions(email, ['producer']):
        return jsonify({"message": "Unauthorized: Insufficient permissions."}), 403

    try:
        product_data = request.json
        
       #  produttore autenticato dal DB
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT manufacturer FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            if not user:
                return jsonify({"message": "User not found in database."}), 404
            real_manufacturer = user["manufacturer"]
        print("Manufacturer authenticated: ", real_manufacturer)

        # prendo l'id del prodotto dalla richiesta POST
        product_id = product_data.get("ID")
        glbFile = product_data.get('ModelBase64')
        if not product_id:
            return jsonify({"message": "Product ID is required."}), 400
        
        print("product id: " + product_id)
        print("glbFile length:", len(glbFile) if glbFile else "No file")

        # verifica che il manufacturer autenticato corrisponda al manufacturer del prodotto
        verification_result = verify_manufacturer(product_id, real_manufacturer)
        if verification_result:
            return verification_result  # Restituisce l'errore se la verifica non è passata

        
        if not glbFile:
            return jsonify({"message": "missing GLB file"}), 400
        #debug
        print(f"Product ID: {product_id}")
        print(f"Length of incoming Base64 string: {len(glbFile)}")
        print(f"First 100 characters: {glbFile[:100]}")

        #decodifico il file Base64
        print("Decoding base64...")
        decoded_glb = base64.b64decode(glbFile)
        print(f"Decoded file size: {len(decoded_glb)} bytes")


        print("Uploading 3D model...")
        
       # salva il modello nella tabella 'models'
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO models (id, stringa)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE stringa = VALUES(stringa)
            """, (product_id, glbFile))
        connection.commit()
        return jsonify({"message": "Model uploaded successfully"}), 201

    except Exception as e:
        # Log the error to the console
        print(f"Error occurred: {str(e)}")
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500

# nuova aggiunta
@app.route('/getModel', methods=['GET'])
def get_model():
    productId = request.args.get('productId')
    if not productId:
        return jsonify({"message": "Product ID is required."}), 400
    try:
        # prendo il file GLB dal database
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT stringa FROM models WHERE id = %s", (productId,))
            result = cursor.fetchone()
            if not result:
                return jsonify({"message": "No model found for the provided product ID."}), 404
            glbFile = result["stringa"]
    # Se il file esiste, lo restituiamo come risposta
        return jsonify({"ModelBase64": glbFile}), 200

    except Exception as e:
        print("Error occurred:", e)
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500



# già usata su frontend + autenticazione jwt
@app.route('/updateProduct', methods=['POST'])
@jwt_required()
def update_product():
    email = get_jwt_identity()
    if not required_permissions(email, ['producer']):
        return jsonify({"message": "Unauthorized: Insufficient permissions."}), 403
    product_data  = request.json
   # Recupera il manufacturer dell'utente loggato
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT manufacturer FROM users WHERE email = %s", (email,))
            result = cursor.fetchone()
            if not result:
                return jsonify({"message": "User not found."}), 404
            real_manufacturer = result["manufacturer"]
            print("Manufacturer authenticated:", real_manufacturer)
    except Exception as e:
        print("Database error while fetching manufacturer:", e)
        return jsonify({"message": "Database error."}), 500

    product_id = product_data.get("ID")
    if not product_id:
        return jsonify({"message": "Product ID is required."}), 400

    # verifica che il manufacturer autenticato corrisponda al manufacturer del prodotto
    verification_result = verify_manufacturer(product_id, real_manufacturer)
    if verification_result:
        return verification_result  # Restituisce l'errore se la verifica non è passata

    # annulla operazione se manufacturer autorizzato inserisce nuovo manufacturer
    client_manufacturer = product_data.get("Manufacturer")
    if real_manufacturer != client_manufacturer:
        return jsonify({"message": "Unauthorized: Manufacturer mismatch."}), 403

    # in caso di corrispondenza manufacturer
    print("Updating Product:", product_data)
    try:
        response = requests.post(f'http://middleware:3000/api/product/updateProduct', json=product_data)
        if response.status_code == 200:
            return jsonify({'message': 'Product updated successfully!'})
        else:
            return jsonify({'message': 'Failed to update product.'}), 500
    except Exception as e:
        print("Error uploading product:", e)
        return jsonify({'message': 'Error uploading product.'}), 500

#################################################################################################################################
@app.route('/updateBatch', methods=['POST'])
@jwt_required()
def update_batch():
    if not required_permissions(get_jwt_identity(), ['producer', 'operator']):
        return jsonify({"message": "Unauthorized: Insufficient permissions."}), 403

    print("update batch chiamata")

    #print("Dati ricevuti dal fe:",request.json)
    batch_data = request.json
    print("Dati:",batch_data)

    #print(get_jwt_identity())
    # PROBLEMA: CAMPO PRODUCTID ARRIVA NULLO
    print("batch_data.get(\"ProductId\"):", batch_data.get("ProductId"))
    if not verify_product_authorization(get_jwt_identity(), batch_data.get("ProductId")):
        return jsonify({"message": "Unauthorized: You do not have access to this product."}), 403
    identity = get_jwt_identity()
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            sql = "SELECT manufacturer FROM users WHERE email = %s"
            cursor.execute(sql, (identity,))
            user = cursor.fetchone()

        if not user:
            return jsonify({"message": "User not found"}), 404

        real_operator = user["manufacturer"]
        print("operator authenticated: " + real_operator)

    except Exception as e:
        print("Database error while fetching user:", e)
        return jsonify({"message": "Database error", "error": str(e)}), 500
    client_operator = batch_data.get("Operator")
    print("upload request by: " + client_operator)
    # Reject operation if the authenticated manufacturer doesn't match the one in the request
    if real_operator != client_operator:
        return jsonify({"message": "Unauthorized: Operator mismatch."}), 403
    print("Uploading new batch data:", batch_data)
    batch_data["CustomObject"] = batch_data.get("CustomObject", {})
    print("Uploading custom object:", batch_data["CustomObject"])

    print("✅ Autorizzato, procedo con l'aggiornamento del batch...")

    try:
        # Aggiorno i dati del batch
        batch_data["CustomObject"] = batch_data.get("CustomObject", {})

        # Invio i dati aggiornati alla blockchain
        print("📢 Invia i dati aggiornati alla blockchain...")
        response = requests.post('http://middleware:3000/api/batch/updateBatch', json=batch_data)

        print("📢 Risposta dalla blockchain:", response.status_code, response.text)

        if response.status_code == 200:
            return jsonify({'message': 'Batch updated successfully!'})
        else:
            return jsonify({'message': 'Failed to update batch.'}), response.status_code

    except Exception as e:
        print(f"❌ ERRORE nel backend: {e}")
        return jsonify({'message': 'Internal Server Error'}), 500

# ora in uso + autenticazione jwt
@app.route('/addSensorData', methods=['POST'])
@jwt_required()
def add_sensor_data():
    sensor_data  = request.json
    # log del manufacturer che effettua la richiesta di update
    identity = get_jwt_identity()

    try:
        # query al database per ottenere il manufacturer dell'utente autenticato
        connection = get_db_connection()
        with connection.cursor() as cursor:
            sql = "SELECT manufacturer FROM users WHERE email = %s"
            cursor.execute(sql, (identity,))
            user = cursor.fetchone()

        if not user:
            return jsonify({"message": "User not found"}), 404

        real_manufacturer = user["manufacturer"]
        print("Manufacturer authenticated:", real_manufacturer)

    except Exception as e:
        print("Database error while fetching user:", e)
        return jsonify({"message": "Database error", "error": str(e)}), 500


    product_id = sensor_data.get("id")
    if not product_id:
        return jsonify({"message": "Product ID is required."}), 400

    # verifica che il manufacturer autenticato corrisponda al manufacturer del prodotto
    verification_result = verify_manufacturer(product_id, real_manufacturer)
    if verification_result:
        return verification_result  # Restituisce l'errore se la verifica non è passata

    # in caso di corrispondenza manufacturer
    print("Uploading sensor data:", sensor_data)
    try:
        response = requests.post(f'http://middleware:3000/api/product/sensor', json=sensor_data)
        if response.status_code == 200:
            return jsonify({'message': 'Product uploaded successfully!'})
        else:
            return jsonify({'message': 'Failed to upload product.'}), 500
    except Exception as e:
        print("Error uploading product:", e)
        return jsonify({'message': 'Error uploading product.'}), 500

# già usata su frontend + autenticazione jwt
@app.route('/addMovementsData', methods=['POST'])
@jwt_required()
def add_movement_data():
    movement_data  = request.json
    # log del manufacturer che effettua la richiesta di update
    identity = get_jwt_identity()

    try:
        # query al database per ottenere il manufacturer dell'utente autenticato
        connection = get_db_connection()
        with connection.cursor() as cursor:
            sql = "SELECT manufacturer FROM users WHERE email = %s"
            cursor.execute(sql, (identity,))
            user = cursor.fetchone()

        if not user:
            return jsonify({"message": "User not found"}), 404

        real_manufacturer = user["manufacturer"]
        print("Manufacturer authenticated:", real_manufacturer)

    except Exception as e:
        print("Database error while fetching user:", e)
        return jsonify({"message": "Database error", "error": str(e)}), 500

    product_id = movement_data.get("id")
    if not product_id:
        return jsonify({"message": "Product ID is required."}), 400

    # verifica che il manufacturer autenticato corrisponda al manufacturer del prodotto
    verification_result = verify_manufacturer(product_id, real_manufacturer)
    if verification_result:
        return verification_result  # Restituisce l'errore se la verifica non è passata

    # in caso di corrispondenza manufacturer
    print("Add movement data:", movement_data)
    try:
        response = requests.post(f'http://middleware:3000/api/product/movement', json=movement_data)
        if response.status_code == 200:
            return jsonify({'message': 'Product uploaded successfully!'})
        else:
            return jsonify({'message': 'Failed to upload product.'}), 500
    except Exception as e:
        print("Error uploading product:", e)
        return jsonify({'message': 'Error uploading product.'}), 500

# già usata su frontend + autenticazione jwt 
@app.route('/addCertification', methods=['POST'])
@jwt_required()
def add_certification_data():
    email = get_jwt_identity()
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT manufacturer FROM users WHERE email = %s", (email,))
            result = cursor.fetchone()
            if not result:
                return jsonify({"message": "User not found."}), 404
            real_manufacturer = result["manufacturer"]
            print("Manufacturer authenticated:", real_manufacturer)
    except Exception as e:
        print("Database error while fetching manufacturer:", e)
        return jsonify({"message": "Database error."}), 500
    
    certification_data  = request.json
    product_id = certification_data.get("id")
    if not product_id:
        return jsonify({"message": "Product ID is required."}), 400

    # verifica che il manufacturer autenticato corrisponda al manufacturer del prodotto
    verification_result = verify_manufacturer(product_id, real_manufacturer)
    if verification_result:
        return verification_result  

# NON UTILIZZATA
@app.route('/verifyProductCompliance', methods=['POST'])
def verify_product_compliance():
    compliance_data  = request.json
    print("Check if product is complaint:", compliance_data)
    try:
        response = requests.post(f'http://middleware:3000/api/product/verifyProductCompliance', json=compliance_data)
        print(response.json())
        if response.status_code == 200:
            return jsonify({'message': 'Product is compliant!'})
        else:
            return jsonify({'message': 'Product is not compliant'}), 500
    except Exception as e:
        print("Error while checking product:", e)
        return jsonify({'message': 'Error while checking product.'}), 500

# già usata su frontend
@app.route('/getAllMovements', methods=['GET'])
def get_all_movements():
    productId = request.args.get('productId')
    print("get all movements:", productId)
    try:
        response = requests.get(f'http://middleware:3000/api/product/getMovements?productId={productId}')
        print(response.json())
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'message': 'Failed to get movements'}), 500
    except Exception as e:
        print("EFailed to get movements:", e)
        return jsonify({'message': 'Failed to get movements.'}), 500

# già usata su frontend
@app.route('/getAllSensorData', methods=['GET'])
def get_all_sensor_data():
    productId = request.args.get('productId')
    print("get all sensor:", productId)
    try:
        response = requests.get(f'http://middleware:3000/api/product/getSensorData?productId={productId}')
        print(response.json())
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'message': 'Failed to get sensor data'}), 500
    except Exception as e:
        print("EFailed to get movements:", e)
        return jsonify({'message': 'Failed to get sensor data.'}), 500
        batch_data = request.get_json()
        print("📢 JSON ricevuto nel backend:", batch_data)

        if not batch_data:
            print("❌ ERRORE: Nessun JSON ricevuto!")
            return jsonify({"message": "Invalid JSON data"}), 422
        
        print("📢 Dati ricevuti:", batch_data)

        real_operator = get_jwt_identity()
        print("📢 Operatore autenticato:", real_operator)

        batch_id = batch_data.get("ID")
        if not batch_id:
            print("❌ ERRORE: Batch ID mancante!")
            return jsonify({"message": "Batch ID is required."}), 422

        # Verifica dell'operatore
        verification_result = verify_operator(batch_id, real_operator)
        if verification_result is not None:  # Verifica se ha restituito un errore JSON
            return verification_result  # Restituisce l'errore HTTP se la verifica fallisce

        # Annullo se l'operatore autenticato non corrisponde a quello nel batch
        client_operator = batch_data.get("Operator")
        if real_operator != client_operator:
            print("❌ ERRORE: Operatore non autorizzato!")
            return jsonify({"message": "Unauthorized: Operator mismatch."}), 403

        print("✅ Operatore verificato, aggiornamento batch in corso...")
        
        # Invio dei dati aggiornati alla blockchain
        response = requests.post('http://middleware:3000/api/batch/updateBatch', json=batch_data)
        print("📢 Dati inviati a AppServer:", batch_data)

        
        print(f"📢 Risposta dalla blockchain: {response.status_code}, {response.text}")
        if response.status_code == 200:
            return jsonify({'message': 'Batch updated successfully!'})
        else:
            return jsonify({'message': 'Failed to update batch.'}), 500

    except Exception as e:
        print(f"❌ ERRORE nel backend: {e}")
        return jsonify({'message': 'Internal Server Error'}), 500


# # ora in uso + autenticazione jwt
# @app.route('/addSensorData', methods=['POST'])
# @jwt_required()
# def add_sensor_data():
#     sensor_data  = request.json
#     # log del manufacturer che effettua la richiesta di update
#     real_manufacturer = get_jwt_identity()
#     print("Manufacturer authenticated:", real_manufacturer)

#     product_id = sensor_data.get("id")
#     if not product_id:
#         return jsonify({"message": "Product ID is required."}), 400

#     # verifica che il manufacturer autenticato corrisponda al manufacturer del prodotto
#     verification_result = verify_manufacturer(product_id, real_manufacturer)
#     if verification_result:
#         return verification_result  # Restituisce l'errore se la verifica non è passata

#     # in caso di corrispondenza manufacturer
#     print("Uploading sensor data:", sensor_data)
#     try:
#         response = requests.post('http://middleware:3000/api/product/sensor', json=sensor_data)
#         if response.status_code == 200:
#             return jsonify({'message': 'Product uploaded successfully!'})
#         else:
#             return jsonify({'message': 'Failed to upload product.'}), 500
#     except Exception as e:
#         print("Error uploading product:", e)
#         return jsonify({'message': 'Error uploading product.'}), 500

# # già usata su frontend + autenticazione jwt
# @app.route('/addMovementsData', methods=['POST'])
# @jwt_required()
# def add_movement_data():
#     movement_data  = request.json
#     # log del manufacturer che effettua la richiesta di update
#     real_manufacturer = get_jwt_identity()
#     print("Manufacturer authenticated:", real_manufacturer)

#     product_id = movement_data.get("id")
#     if not product_id:
#         return jsonify({"message": "Product ID is required."}), 400

#     # verifica che il manufacturer autenticato corrisponda al manufacturer del prodotto
#     verification_result = verify_manufacturer(product_id, real_manufacturer)
#     if verification_result:
#         return verification_result  # Restituisce l'errore se la verifica non è passata

#     # in caso di corrispondenza manufacturer
#     print("Add movement data:", movement_data)
#     try:
#         response = requests.post('http://middleware:3000/api/product/movement', json=movement_data)
#         if response.status_code == 200:
#             return jsonify({'message': 'Product uploaded successfully!'})
#         else:
#             return jsonify({'message': 'Failed to upload product.'}), 500
#     except Exception as e:
#         print("Error uploading product:", e)
#         return jsonify({'message': 'Error uploading product.'}), 500

# # già usata su frontend + autenticazione jwt 
# @app.route('/addCertification', methods=['POST'])
# @jwt_required()
# def add_certification_data():
#     certification_data  = request.json
#     # log del manufacturer che effettua la richiesta di update
#     real_manufacturer = get_jwt_identity()
#     print("Manufacturer authenticated:", real_manufacturer)

#     product_id = certification_data.get("id")
#     if not product_id:
#         return jsonify({"message": "Product ID is required."}), 400

#     # verifica che il manufacturer autenticato corrisponda al manufacturer del prodotto
#     verification_result = verify_manufacturer(product_id, real_manufacturer)
#     if verification_result:
#         return verification_result  # Restituisce l'errore se la verifica non è passata
    
#     # in caso di corrispondenza manufacturer
#     print("Add certification data:", certification_data)
#     try:
#         response = requests.post('http://middleware:3000/api/product/certification', json=certification_data)
#         if response.status_code == 200:
#             return jsonify({'message': 'Product uploaded successfully!'})
#         else:
#             return jsonify({'message': 'Failed to upload product.'}), 500
#     except Exception as e:
#         print("Error uploading product:", e)
#         return jsonify({'message': 'Error uploading product.'}), 500

# # NON UTILIZZATA
# @app.route('/verifyProductCompliance', methods=['POST'])
# def verify_product_compliance():
#     compliance_data  = request.json
#     print("Check if product is complaint:", compliance_data)
#     try:
#         response = requests.post('http://middleware:3000/api/product/verifyProductCompliance', json=compliance_data)
#         print(response.json())
#         if response.status_code == 200:
#             return jsonify({'message': 'Product is compliant!'})
#         else:
#             return jsonify({'message': 'Product is not compliant'}), 500
#     except Exception as e:
#         print("Error while checking product:", e)
#         return jsonify({'message': 'Error while checking product.'}), 500

# # già usata su frontend
# @app.route('/getAllMovements', methods=['GET'])
# def get_all_movements():
#     productId = request.args.get('productId')
#     print("get all movements:", productId)
#     try:
#         response = requests.get(f'http://middleware:3000/api/product/getMovements?productId={productId}')
#         print(response.json())
#         if response.status_code == 200:
#             return jsonify(response.json())
#         else:
#             return jsonify({'message': 'Failed to get movements'}), 500
#     except Exception as e:
#         print("EFailed to get movements:", e)
#         return jsonify({'message': 'Failed to get movements.'}), 500

# # già usata su frontend
# @app.route('/getAllSensorData', methods=['GET'])
# def get_all_sensor_data():
#     productId = request.args.get('productId')
#     print("get all sensor:", productId)
#     try:
#         response = requests.get(f'http://middleware:3000/api/product/getSensorData?productId={productId}')
#         print(response.json())
#         if response.status_code == 200:
#             return jsonify(response.json())
#         else:
#             return jsonify({'message': 'Failed to get sensor data'}), 500
#     except Exception as e:
#         print("EFailed to get movements:", e)
#         return jsonify({'message': 'Failed to get sensor data.'}), 500

# # già usata su frontend
# @app.route('/getAllCertifications', methods=['GET'])
# def get_all_certifications():
    productId = request.args.get('productId')
    print("get all certifications:", productId)
    try:
        response = requests.get(f'http://middleware:3000/api/product/getCertifications?productId={productId}')
        print(response.json())
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'message': 'Failed to get certifications'}), 500
    except Exception as e:
        print("Failed to get certifications:", e)
        return jsonify({'message': 'Failed to get certifications.'}), 500


# AI CONFIG & AI API CALLS

#llm = Ollama(model="llama3")
#llm = Ollama(model="gemma2")
llm = Ollama(model="llama3:latest") #oppure: model="llama3.1"
chat_history = []
start = prompts_variables_storage.smaller_initprompt
productinfo= "No information available for this product at the moment"

def init_variables(productinfo):
    prompt_template_msg="{start} This is your knowledge base: {product_details}"
    prompt_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            prompt_template_msg,
        ),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
    ]
)
    chain = prompt_template | llm
    return chain

def chatbot_response(user_prompt, itemcode, productinfo):
    question = "You: "+ user_prompt
    
    if question == "done":
        return "Bye bye"

    response = llm.invoke(question)
    chain=init_variables(productinfo)
    response = chain.invoke({"input": question, "chat_history": chat_history,"start":start,"product_details":productinfo})
    chat_history.append(HumanMessage(content=question))
    chat_history.append(AIMessage(content=response))
    print(chat_history)
    return response

# usata dall'interfaccia AI
@app.route('/scan', methods=['POST'])
def scan():
    item_code = request.json['item_code']
    print("ATTEMPTING TO CONNECT:")
     # Send request to JavaScript server to get product details
    try: 
        response = requests.get(f'http://middleware:3000/readProduct?productId={item_code}')
        if response.status_code == 200:
            productinfo = response.json()
            globals()["productinfo"]=productinfo
            initial_message = f"Hello, you just scanned the item {item_code}. What would you like to know about it?"
        else:
            initial_message = f"Hello, you just scanned the item {item_code}. At the moment i'm unable to retrieve product details."

    except: initial_message = "Cannot connect to the server"
    
    return jsonify({'message': initial_message, 'item_code': item_code})

# usata dall'interfaccia AI
@app.route('/ask', methods=['POST'])
def ask():
    user_input = request.json['message']
    item_code = request.json['item_code']
    print("Sending the request with the following informations:")
    print(productinfo)
    bot_response = chatbot_response(user_input, item_code, productinfo)
    return jsonify({'message': bot_response})




@app.route('/likeProduct', methods=['POST'])
@jwt_required()
def like_product():
    user_email = get_jwt_identity()
    data = request.get_json()
    product = data.get('product')

    required_fields = ['ID', 'Name', 'Manufacturer']
    if not product or not all(field in product for field in required_fields):
        return jsonify({"message": "Missing required product fields."}), 400

    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Verifica se il like esiste già
            cursor.execute("""
                SELECT COUNT(*) as cnt FROM liked_products
                WHERE user_email = %s AND ID = %s
            """, (user_email, product['ID']))
            result = cursor.fetchone()

            if result['cnt'] > 0:
                return jsonify({"message": "Product already liked"}), 200

            # Inserisci nella tabella liked_products
            cursor.execute("""
                INSERT INTO liked_products (ID, Name, Manufacturer, timestamp, user_email)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                product['ID'],
                product['Name'],
                product['Manufacturer'],
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                user_email
            ))
            connection.commit()

        return jsonify({"message": "Product liked successfully"}), 201

    except Exception as e:
        print("Errore nel likeProduct:", e)
        return jsonify({"message": f"Database error: {str(e)}"}), 500


@app.route('/unlikeProduct', methods=['DELETE'])
@jwt_required()
def unlike_product():
    user_email = get_jwt_identity()
    product_id = request.args.get('productId')

    if not product_id:
        return jsonify({"message": "Product ID is required."}), 400

    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("""
                DELETE FROM liked_products
                WHERE user_email = %s AND ID = %s
            """, (user_email, product_id))
            connection.commit()

        return jsonify({"message": "Product unliked successfully"}), 200

    except Exception as e:
        print("Errore nel unlikeProduct:", e)
        return jsonify({"message": f"Database error: {str(e)}"}), 500


@app.route('/getLikedProducts', methods=['GET'])
@jwt_required()
def get_liked_products():
    user_email = get_jwt_identity()

    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT ID, Name, Manufacturer, CreationDate, timestamp FROM liked_products
                WHERE user_email = %s
            """, (user_email,))
            results = cursor.fetchall()

        return jsonify(results), 200

    except Exception as e:
        print("Errore nel getLikedProducts:", e)
        return jsonify({"message": f"Database error: {str(e)}"}), 500




# Add these new routes for recently searched products

@app.route('/addRecentlySearched', methods=['POST'])
def add_recently_searched():
    data = request.json
    product = data.get('product')
    user_email = data.get('userEmail') or data.get('userId')

    if not product or not user_email:
        return jsonify({"error": "Missing product or userEmail"}), 400

    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("""
                DELETE FROM searches
                WHERE user_email = %s AND product_id = %s
            """, (user_email, product.get('ID')))

            cursor.execute("""
                INSERT INTO searches (product_id, Name, Manufacturer, CreationDate, timestamp, user_email)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                product.get('ID'),
                product.get('Name'),
                product.get('Manufacturer'),
                product.get('CreationDate'),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                user_email
            ))

            cursor.execute("""
                DELETE FROM searches
                WHERE user_email = %s AND ID NOT IN (
                    SELECT ID FROM (
                        SELECT ID FROM searches
                        WHERE user_email = %s
                        ORDER BY timestamp DESC
                        LIMIT 5
                    ) AS recent
                )
            """, (user_email, user_email))

            connection.commit()
        return jsonify({"message": "Product added to recently searched"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/getRecentlySearched', methods=['GET'])
def get_recently_searched():
    user_email = request.args.get('userEmail') or request.args.get('userId')

    if not user_email:
        return jsonify({"error": "Missing userEmail"}), 400

    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT product_id AS ID, Name, Manufacturer, CreationDate, timestamp
                FROM searches
                WHERE user_email = %s
                ORDER BY timestamp DESC
                LIMIT 5
            """, (user_email,))
            results = cursor.fetchall()
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500



# Make sure the if __name__ block is inside the code
if __name__ == "__main__":
    app.run(debug=True) # on deploy: app.run(host="0.0.0.0", port=5000, debug=True)