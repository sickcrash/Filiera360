import json
import os
import random
import secrets
import traceback
from datetime import datetime, timedelta

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

from database_mongo.setup_indexes import setup_indexes
setup_indexes()  # Setup indici MongoDB
# Import CRUD utenti
from database_mongo.queries.users_queries import (
    create_user,
    get_user_by_email,
    get_user_by_manufacturer,
    get_user_by_id,
    update_user
)

# Import CRUD OTP
from database_mongo.queries.otp_queries import (
    create_otp,
    get_otp_by_user_id,
    delete_otp_by_user_id
)

# Import CRUD token invito
from database_mongo.queries.token_queries import (
    create_token,
    get_token,
    mark_token_as_used,
    get_tokens_by_inviter,
    get_tokens_used_by
)

# Import CRUD prodotti
from database_mongo.queries.products_queries import (
    create_product,
    get_product_by_id,
    get_product_by_blockchain_id,
    update_product_by_blockchain_id
)

# Import CRUD modelli 3D
from database_mongo.queries.models_queries import (
    create_model,
    get_model_by_id,
    get_model_by_blockchain_id,
    get_models_by_user,
    update_model,
    delete_model
)

# Import CRUD liked products
from database_mongo.queries.liked_queries import (
    like_a_product,
    unlike_a_product,
    get_liked_products_by_user,
    get_users_who_liked_product
)

# Import CRUD cronologia prodotti
from database_mongo.queries.history_queries import (
    add_history_entry,
    delete_history_entry,
    get_history_by_blockchain_id,
    get_history_by_user,
    get_last_history_entry
)

# Import CRUD ricerche recenti
from database_mongo.queries.recently_searched_queries import (
    add_recently_searched,
    get_recently_searched
)
from database_mongo.mongo_client import users as users_collection

# Update the CORS configuration to allow all methods
app = Flask(__name__, instance_relative_config=True)
CORS(app, resources={r"/*": {"origins": "*"}})
app.config['CORS_HEADERS'] = 'Content-Type'

cors = CORS(app, resources={r"/*": {"origins": "*", "methods": ["GET", "POST", "DELETE", "OPTIONS"]}})
app.config['CORS_HEADERS'] = 'Content-Type'

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


otp_store_file = "./jsondb/users-otp.json"
otp_lifetime = timedelta(minutes=5)


# @app.route('/send-otp', methods=['POST'])
def send_otp(email):
    user = get_user_by_email(email)
    if not user:
        return jsonify({"message": "User not found."}), 404

    otp = generate_otp()
    create_otp(user["_id"], str(otp))
    send_otp_email(email, otp)
    return jsonify({"message": "OTP sent to your email."})

"""     if send_otp_email(email, otp):
        return jsonify({"message": "OTP sent to your email."})
    else:
        return jsonify({"message": "Failed to send OTP."}), 500 """



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
    
    if not get_user_by_email(email):
        return jsonify({"message": "Email not found"}), 404

    token = generate_reset_token(email)

    reset_url = f"/api/reset-password/{token}"
    msg = Message('Password Reset Request',
                  sender='noreply@example.com',
                  recipients=[email])
    msg.body = f"To reset your password, visit the following link: {reset_url}"
    mail.send(msg)
    
    return jsonify({"message": "Password reset email sent"}), 200

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

        update_user(get_user_by_email(email)["_id"], {"password": hashed_password})

        return jsonify({"message": "Password updated successfully"}), 200

    return jsonify({"message": "Token is valid, proceed with password reset"}), 200

# Carica gli utenti dal file JSON (database utenti)
'''def load_users():
    try:
        with open('./jsondb/users.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}  # Se il file non esiste o è vuoto, restituisce un dizionario vuoto
    
# Carica i modelli 3D dal file JSON
def load_models():
    try:
        with open('models.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}  # Se il file non esiste o è vuoto, restituisce un dizionario vuoto
    
# Salva gli utenti nel file JSON
def save_users(users):
    with open('./jsondb/users.json', 'w') as f:
        json.dump(users, f, indent=4)

# Salva i modelli nel file JSON
def save_models(models):
    with open('models.json', 'w') as f:
        json.dump(models, f, indent=4)

# Carica i database all'avvio del server
users = load_users()
models = load_models()'''

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

# Caricamento token
'''def load_invite_tokens():
    try:
        with open("./jsondb/invite_tokens.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

# Salvataggio token aggiornati
def save_invite_tokens(tokens):
    with open("./jsondb/invite_tokens.json", "w") as file:
        json.dump(tokens, file, indent=4)'''

# Salvataggio degli utenti in un file JSON
def save_users(users):
    with open("./jsondb/users.json", "w") as file:
        json.dump(users, file, indent=4)

# Verifichiamo se un token è valido e non scaduto
'''def is_valid_invite_token(token):
    tokens = load_invite_tokens()
    if token not in tokens:
        return False, "Invalid invitation token."

    token_data = tokens[token]
    expiration_date = datetime.fromisoformat(token_data["expires_at"])

    if datetime.now() > expiration_date:
        return False, "Expired invitation token."
        
    # Se il token è già usato
    if token_data.get("used", False): 
        return False, "Invitation token already used."

    return True, "Valid token."'''

@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    email = data.get('email')
    manufacturer = data.get('manufacturer')
    password = data.get('password')
    role = data.get('role', 'user') 
    invite_token = data.get('inviteToken', None) 
    
    # Verifica che tutti i campi siano forniti
    if not email or not manufacturer or not password:
        return jsonify({"message": "All fields are required"}), 400
    
    # Controlla se l'email è già registrata
    if get_user_by_email(email):
        return jsonify({"message": "Email already exists"}), 409
    
    # Controlla se il manufacturer è già registrato
    if get_user_by_manufacturer(manufacturer):
        return jsonify({"message": "Manufacturer already exists"}), 409

    # Controlla il token di invito per i produttori
    if role == "producer":
        if not invite_token:
            return jsonify({"message": "The invite token is required for producers."}), 400

        token_doc = get_token(invite_token)
        if not token_doc:
            return jsonify({"message": "Invalid invitation token."}), 403
        if token_doc.get("used"):
            return jsonify({"message": "Invitation token already used."}), 403
    # Crea un hash della password con bcrypt
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # DOPO MODIFICA: Aggiungi l'utente al DB (Aggiungi l'utente al dizionario degli utenti)
    create_user(email, hashed_password, manufacturer, role)

    # Se il token è stato usato, viene segnato come utilizzato
    if role == "producer" and invite_token:
        mark_token_as_used(invite_token, email)

    return jsonify({"message": "User registered successfully"}), 201


@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

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

    if user["flags"][2]: # flags[2] == user
        token = create_access_token(email)
        return jsonify({"message": "Login successful", "access_token": token, "role": user['role'], "manufacturer": user['manufacturer'], "email": email})
    else:
        if send_otp(email):
            return jsonify({"message": "OTP sent to your email."})
        else:
            return jsonify({"message": "Failed to send OTP."}), 500

    # Se la 2FA non è necessaria, crea un token JWT
    


# Endpoint per la verifica dell'OTP
@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    data = request.get_json()
    email = data.get('email')
    otp = data.get('otp')

    user = get_user_by_email(email)
    if not user:
        return jsonify({"message": "User not found."}), 404

    otp_entry = get_otp_by_user_id(user["_id"])
    if not otp_entry or otp_entry["otp"] != str(otp):
        return jsonify({"message": "Invalid or expired OTP."}), 400

    delete_otp_by_user_id(user["_id"])
    token = create_access_token(email)
    return jsonify({
        "message": "OTP validated successfully.",
        "access_token": token,
        "role": user['role'],
        "manufacturer": user['manufacturer'],
        "email": email
    })


@app.route('/operators', methods=['GET'])
@jwt_required()
def get_operators():
    if not required_permissions(get_jwt_identity(), ['producer']):
        return jsonify({"operators": None})

    user = get_user_by_email(get_jwt_identity())
    operators = user.get("operators", [])

    return jsonify({"operators": operators})

@app.route('/operators/add', methods=['POST'])
@jwt_required()
def add_operator():
    print("chiamata ricevuta")
    if not required_permissions(get_jwt_identity(), ['producer']):
        return jsonify({"message": "Unauthorized: Insufficient permissions."}), 403

    data = request.json
    operator_email = data.get("email")
    if not operator_email:
        return jsonify({"message": "Email is required."}), 400

    operator = get_user_by_email(operator_email)
    if not operator:
        return jsonify({"message": "Operator not found."}), 404

    if not operator.get("flags", [])[1]:  # flags[1] == operator
        return jsonify({"message": "User is not an operator and cannot be added."}), 400

    user = get_user_by_email(get_jwt_identity())
    if any(op["email"] == operator_email for op in user.get("operators", [])):
        return jsonify({"message": "Operator already added."}), 409

    # Aggiorna la lista operatori su MongoDB
    user["operators"].append({"operatorId": operator["_id"], "email": operator_email})
    update_user(user["_id"], {"operators": user["operators"]})

    return jsonify({"message": "Operator added successfully."}), 201

@app.route('/operators/delete', methods=['POST'])
@jwt_required()
def remove_operator():
    if not required_permissions(get_jwt_identity(), ['producer']):
        return jsonify({"message": "Unauthorized: Insufficient permissions."}), 403

    data = request.json
    operator_email = data.get("email")

    if not operator_email:
        return jsonify({"message": "Email is required."}), 400

    user = get_user_by_email(get_jwt_identity())
    if not any(op["email"] == operator_email for op in user.get("operators", [])):
        return jsonify({"message": "Operator not found."}), 404

    # Aggiorna la lista operatori su MongoDB
    user["operators"] = [op for op in user["operators"] if op["email"] != operator_email]
    update_user(user["_id"], {"operators": user["operators"]})

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
    return users_collection.find_one({
        "operators": {
            "$elemMatch": {"email": operator_email}
        }
    })

def required_permissions(manufacturer, roles):
    print("chiamata a required permissions")
    user = get_user_by_email(manufacturer)
    if not user:
        return False

    role_map = {"producer": 0, "operator": 1, "user": 2}
    for role in roles:
        if user["flags"][role_map[role]]:
            return True
    return False

def verify_product_authorization(email, product_id):
    user = get_user_by_email(email)
    if not user or not product_id:
        return False

    if user["flags"][1]:  # flags[1] == operator
        user = find_producer_by_operator(email)
        if not user:
            return False

    try: 
        response = requests.get(f'http://middleware:3000/readProduct?productId={product_id}')
        if response.status_code != 200:
            return jsonify({'message': 'Failed to get product.'}), 500
            
        product = response.json()
        return product.get("Manufacturer") == user["manufacturer"]
    except Exception as e:
        print("Failed to get product:", e)
        return jsonify({'message': 'Failed to get product.'}), 500

# ora in uso + autenticazione jwt
@app.route('/uploadProduct', methods=['POST'])
@jwt_required()
def upload_product():
    if not required_permissions(get_jwt_identity(), ['producer']):
        return jsonify({"message": "Unauthorized: Insufficient permissions."}), 403

    print("Sono arrivata al backend")
    product_data = request.json
    real_manufacturer = get_user_by_email(get_jwt_identity())["manufacturer"]
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

    real_operator = get_user_by_email(get_jwt_identity())["manufacturer"]
    print("operator authenticated: " + real_operator)
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
    if not required_permissions(get_jwt_identity(), ['producer']):
        return jsonify({"message": "Unauthorized: Insufficient permissions."}), 403

    try:
        product_data = request.json
        # log del manufacturer che effettua la richiesta di upload
        real_manufacturer = get_user_by_email(get_jwt_identity())["manufacturer"]
        print("Manufacturer authenticated: ", real_manufacturer)

        # prendo l'id del prodotto dalla richiesta POST
        product_id = product_data.get("ID")
        if not product_id:
            return jsonify({"message": "Product ID is required."}), 400
        
        print("product id: " + product_id)

        # verifica che il manufacturer autenticato corrisponda al manufacturer del prodotto
        verification_result = verify_manufacturer(product_id, real_manufacturer)
        if verification_result:
            return verification_result  # Restituisce l'errore se la verifica non è passata

        print("converting file...")
        # in caso di successo
        glbFile = product_data.get('ModelBase64')
        if not glbFile:
            return jsonify({"message": "missing GLB file"}), 400
        print("Uploading 3D model...")
            
        create_model(product_id, glbFile, get_user_by_email(get_jwt_identity())["_id"])
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
    
    model = get_model_by_blockchain_id(productId)
    if not model:
        return jsonify({"message": "No model found for the provided product ID."}), 404

    return jsonify({"ModelBase64": model["modelString"]}), 200


# già usata su frontend + autenticazione jwt
@app.route('/updateProduct', methods=['POST'])
@jwt_required()
def update_product():
    if not required_permissions(get_jwt_identity(), ['producer']):
        return jsonify({"message": "Unauthorized: Insufficient permissions."}), 403
    product_data  = request.json
    # log del manufacturer che effettua la richiesta di update
    real_manufacturer = get_user_by_email(get_jwt_identity())["manufacturer"]
    print("Manufacturer authenticated:", real_manufacturer)

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

    real_operator = get_user_by_email(get_jwt_identity())["manufacturer"]
    print("operator authenticated: " + real_operator)
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
    real_manufacturer = get_user_by_email(get_jwt_identity())["manufacturer"]
    print("Manufacturer authenticated:", real_manufacturer)

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
    real_manufacturer = get_user_by_email(get_jwt_identity())["manufacturer"]
    print("Manufacturer authenticated:", real_manufacturer)

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
    certification_data  = request.json
    # log del manufacturer che effettua la richiesta di update
    real_manufacturer = get_user_by_email(get_jwt_identity())["manufacturer"]
    print("Manufacturer authenticated:", real_manufacturer)

    product_id = certification_data.get("id")
    if not product_id:
        return jsonify({"message": "Product ID is required."}), 400

    # verifica che il manufacturer autenticato corrisponda al manufacturer del prodotto
    verification_result = verify_manufacturer(product_id, real_manufacturer)
    if verification_result:
        return verification_result  # Restituisce l'errore se la verifica non è passata
    
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

# Managing Liked Products Per User Account

# Modify the liked products structure to be user-specific
'''def load_liked_products():
    try:
        with open('liked_products.json', 'r') as f:
            data = json.load(f)
            # Ensure the structure is an object with user IDs as keys
            if isinstance(data, list):
                # Convert old format to new format if needed
                return {"default": data}
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        # If file doesn't exist, create it with an empty object
        save_liked_products({})
        return {}
'''
# Update the likeProduct endpoint to handle user-specific likes
@app.route('/likeProduct', methods=['POST', 'OPTIONS'])
@jwt_required()
def like_product():
    if request.method == 'OPTIONS':
        response = jsonify({'message': 'OK'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        return response

    data = request.json
    product_data = data.get('product')
    user_id = data.get('userId', None)
    if not user_id or not product_data or not product_data.get('ID'):
        return jsonify({"message": "Missing userId or product data"}), 400

    # Controllo duplicato (puoi anche toglierlo se l'indice unico è già sul DB)
    already_liked = get_liked_products_by_user(user_id)
    if any(p["blockchainProductId"] == product_data["ID"] for p in already_liked):
        return jsonify({"message": "Product already liked"}), 200

    like_a_product(user_id, product_data["ID"])
    return jsonify({"message": "Product added to liked products"}), 201
    
    # Save to JSON file
'''    save_liked_products(liked_products)
    
    print(f"Product {product_data['ID']} added to liked products for user {user_id}. Total: {len(liked_products[user_id])}")
    return jsonify({"message": "Product added to liked products"}), 201'''

# Update the unlikeProduct endpoint for user-specific unlikes
@app.route('/unlikeProduct', methods=['DELETE'])
@jwt_required()
def unlike_product():
    product_id = request.args.get('productId')
    user_id = request.args.get('userId', None)
    if not user_id or not product_id:
        response = jsonify({"message": "Missing userId or productId"})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'DELETE')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response, 400

    liked = get_liked_products_by_user(user_id)
    if not any(p["blockchainProductId"] == product_id for p in liked):
        response = jsonify({"message": "Product not found in liked products"})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'DELETE')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response, 404

    unlike_a_product(user_id, product_id)
    response = jsonify({"message": "Product removed from liked products"})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Methods', 'DELETE')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    return response, 200

# Update the getLikedProducts endpoint for user-specific retrieval
@app.route('/getLikedProducts', methods=['GET'])
@jwt_required()
def get_liked_products():
    user_id = request.args.get('userId', None)
    if not user_id:
        return jsonify([])

    liked = get_liked_products_by_user(user_id)
    return jsonify(liked)

# Add this function to save liked products to JSON file
def save_liked_products(products):
    with open('liked_products.json', 'w') as f:
        json.dump(products, f, indent=4)

# Initialize the liked_products variable
#liked_products = load_liked_products()



# Add these new routes for recently searched products

@app.route('/addRecentlySearched', methods=['POST'])
@jwt_required()
def add_recently_searched_route():
    data = request.json
    user_id = data.get('userId')
    blockchain_product_id = data.get('blockchainProductId')
    if not user_id or not blockchain_product_id:
        return jsonify({"message": "Missing userId or product data"}), 400

    add_recently_searched(user_id, blockchain_product_id)
    return jsonify({"message": "Product added to recently searched"})

@app.route('/getRecentlySeached', methods=['GET'])
@jwt_required()
def get_recently_searched_route():
    user_id = request.args.get('userId')
    if not user_id:
        return jsonify([])

    products = get_recently_searched(user_id)
    return jsonify(products)

'''def load_recently_searched():
    try:
        with open('recently_searched.json', 'r') as f:
            data = json.load(f)
            # Ensure the structure is an object with user IDs as keys
            if isinstance(data, list):
                # Convert old format to new format if needed
                return {"default": data}
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        # If file doesn't exist, create it with an empty object
        save_recently_searched({})
        return {}

def save_recently_searched(products):
    with open('recently_searched.json', 'w') as f:
        json.dump(products, f, indent=4)'''


# Make sure the if __name__ block is inside the code
if __name__ == "__main__":
    app.run(debug=True) # on deploy: app.run(host="0.0.0.0", port=5000, debug=True)