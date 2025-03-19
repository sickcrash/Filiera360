import json
import os
import secrets
from datetime import datetime, timedelta

import bcrypt
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

import prompts_variables_storage

app = Flask(__name__, instance_relative_config=True)

cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'filiera360@gmail.com'  
app.config['MAIL_PASSWORD'] = 'bspi hkbw jcwh yckx '
mail = Mail(app)

# Verifica che il manufacturer autenticato corrisponda al manufacturer del prodotto
def verify_manufacturer(product_id, real_manufacturer):
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
    
    if email not in users:
        return jsonify({"message": "Email not found"}), 404

    token = generate_reset_token(email)

    reset_url = f"http://localhost:3001/reset-password/{token}"
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

        users[email]["password"] = hashed_password
        save_users(users)

        return jsonify({"message": "Password updated successfully"}), 200

    return jsonify({"message": "Token is valid, proceed with password reset"}), 200

# Carica gli utenti dal file JSON (database utenti)
def load_users():
    try:
        with open('users.json', 'r') as f:
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
    with open('users.json', 'w') as f:
        json.dump(users, f, indent=4)

# Salva i modelli nel file JSON
def save_models(models):
    with open('models.json', 'w') as f:
        json.dump(models, f, indent=4)

# Carica i database all'avvio del server
users = load_users()
models = load_models()

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
            response = requests.post(f'http://localhost:3000/uploadProduct', json=product)
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
def load_invite_tokens():
    try:
        with open("invite_tokens.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

# Salvataggio token aggiornati
def save_invite_tokens(tokens):
    with open("invite_tokens.json", "w") as file:
        json.dump(tokens, file, indent=4)

# Salvataggio degli utenti in un file JSON
def save_users(users):
    with open("users.json", "w") as file:
        json.dump(users, file, indent=4)

# Verifichiamo se un token è valido e non scaduto
def is_valid_invite_token(token):
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

    return True, "Valid token."

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
    if email in users:
        return jsonify({"message": "Email already exists"}), 409
    
    # Controlla se il manufacturer è già registrato
    if any(user["manufacturer"] == manufacturer for user in users.values()):
        return jsonify({"message": "Manufacturer already exists"}), 409

    # Controlla il token di invito per i produttori
    if role == "producer":
        if not invite_token:
            return jsonify({"message": "The invite token is required for producers."}), 400

        is_valid, message = is_valid_invite_token(invite_token)
        if not is_valid:
            return jsonify({"message": message}), 403

    # Crea un hash della password con bcrypt
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Aggiungi l'utente al dizionario degli utenti
    users[email] = {
        "manufacturer": manufacturer,
        "password": hashed_password,
        "role": role,
        "flags": {
            "producer": role == "producer",
            "operator": role == "operator",
            "user": role == "user" 
        }
    }

    save_users(users)

    # Se il token è stato usato, viene segnato come utilizzato
    if role == "producer" and invite_token:
        tokens = load_invite_tokens()
        tokens[invite_token]["used"] = True
        save_invite_tokens(tokens)

    return jsonify({"message": "User registered successfully"}), 201

# nuova aggiunta
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    # Verifica se l'email esiste, e in tal caso se la password
    # corrispondente è giusta:
    if email not in users or not bcrypt.checkpw(password.encode('utf-8'), users[email]["password"].encode('utf-8')):
        return jsonify({"message": "Wrong email or password"}), 401
    
    # Se l'email esiste accedo al manufacturer
    manufacturer = users[email]["manufacturer"]
    
    access_token = create_access_token(identity=manufacturer, expires_delta=False)
    return jsonify(access_token=access_token, manufacturer=manufacturer, email=email), 200

# già usata su frontend
@app.route('/getProduct', methods=['GET'])
#@jwt_required()
def get_product():
    productId = request.args.get('productId')
    print("ATTEMPTING TO CONNECT:")
     # Send request to JavaScript server to get product details
    try: 
        response = requests.get(f'http://localhost:3000/readProduct?productId={productId}')
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
#@jwt_required()
def get_product_history():
    productId = request.args.get('productId')
    print("ATTEMPTING TO CONNECT TO JS SERVER FOR PRODUCT HISTORY:")
    
    # Invia richiesta al server JavaScript per ottenere la cronologia del prodotto
    try:
        response = requests.get(f'http://localhost:3000/productHistory?productId={productId}')
        if response.status_code == 200:
            product_history = response.json()
            return jsonify(product_history)
        else:
            return jsonify({'message': 'Failed to get product history.'}), 500
    except Exception as e:
        print("Failed to get product history:", e)
        return jsonify({'message': 'Failed to get product history.'}), 500

# def required_permissions(manufacturer, roles):
#     user = [user for user in users.values() if user["manufacturer"] == manufacturer]
#     user = user[0] if user else None

#     if not user:
#         return False

#     for role in roles:
#         if user["flags"].get(role):
#             return True

#     return False

# ora in uso + autenticazione jwt
@app.route('/uploadProduct', methods=['POST'])
@jwt_required()
def upload_product():
    # if not required_permissions(get_jwt_identity(), ['producer', 'operator']):
    #     return jsonify({"message": "Unauthorized: Insufficient permissions."}), 403

    print("Sono arrivata al backend")
    product_data = request.json
    real_manufacturer = get_jwt_identity()
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
        response = requests.post(f'http://localhost:3000/uploadProduct', json=product_data)
        if response.status_code == 200:
            return jsonify({'message': response.json().get('message', 'Product uploaded successfully!')})
        else:
            return jsonify({'message': response.json().get('message', 'Failed to upload product.')}), response.status_code

        
    except Exception as e:
        print("Error uploading product:", e)
        return jsonify({'message': 'Error uploading product.', 'error': str(e)}), 500
    
# nuova aggiunta
@app.route('/uploadModel', methods=['POST'])
@jwt_required()
def upload_model():
    try:
        product_data = request.json
        # log del manufacturer che effettua la richiesta di upload
        real_manufacturer = get_jwt_identity()
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
        
        # Aggiungi il file Base64 al dizionario dei modelli
        models[product_id] = glbFile
        
        # Salva il risultato nel file JSON
        save_models(models)
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
    
    # prendo il file GLB associato al prodotto
    glbFile = models.get(productId)
    if not glbFile:
        return jsonify({"message": "No model found for the provided product ID."}), 404

    # Se il file esiste, lo restituiamo come risposta
    return jsonify({"ModelBase64": glbFile}), 200


# già usata su frontend + autenticazione jwt
@app.route('/updateProduct', methods=['POST'])
@jwt_required()
def update_product():
    product_data  = request.json
    # log del manufacturer che effettua la richiesta di update
    real_manufacturer = get_jwt_identity()
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
        response = requests.post(f'http://localhost:3000/api/product/updateProduct', json=product_data)
        if response.status_code == 200:
            return jsonify({'message': 'Product updated successfully!'})
        else:
            return jsonify({'message': 'Failed to update product.'}), 500
    except Exception as e:
        print("Error uploading product:", e)
        return jsonify({'message': 'Error uploading product.'}), 500

# ora in uso + autenticazione jwt
@app.route('/addSensorData', methods=['POST'])
@jwt_required()
def add_sensor_data():
    sensor_data  = request.json
    # log del manufacturer che effettua la richiesta di update
    real_manufacturer = get_jwt_identity()
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
        response = requests.post(f'http://localhost:3000/api/product/sensor', json=sensor_data)
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
    real_manufacturer = get_jwt_identity()
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
        response = requests.post(f'http://localhost:3000/api/product/movement', json=movement_data)
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
    real_manufacturer = get_jwt_identity()
    print("Manufacturer authenticated:", real_manufacturer)

    product_id = certification_data.get("id")
    if not product_id:
        return jsonify({"message": "Product ID is required."}), 400

    # verifica che il manufacturer autenticato corrisponda al manufacturer del prodotto
    verification_result = verify_manufacturer(product_id, real_manufacturer)
    if verification_result:
        return verification_result  # Restituisce l'errore se la verifica non è passata
    
    # in caso di corrispondenza manufacturer
    print("Add certification data:", certification_data)
    try:
        response = requests.post(f'http://localhost:3000/api/product/certification', json=certification_data)
        if response.status_code == 200:
            return jsonify({'message': 'Product uploaded successfully!'})
        else:
            return jsonify({'message': 'Failed to upload product.'}), 500
    except Exception as e:
        print("Error uploading product:", e)
        return jsonify({'message': 'Error uploading product.'}), 500

# NON UTILIZZATA
@app.route('/verifyProductCompliance', methods=['POST'])
def verify_product_compliance():
    compliance_data  = request.json
    print("Check if product is complaint:", compliance_data)
    try:
        response = requests.post(f'http://localhost:3000/api/product/verifyProductCompliance', json=compliance_data)
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
        response = requests.get(f'http://localhost:3000/api/product/getMovements?productId={productId}')
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
        response = requests.get(f'http://localhost:3000/api/product/getSensorData?productId={productId}')
        print(response.json())
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'message': 'Failed to get sensor data'}), 500
    except Exception as e:
        print("EFailed to get movements:", e)
        return jsonify({'message': 'Failed to get sensor data.'}), 500

# già usata su frontend
@app.route('/getAllCertifications', methods=['GET'])
def get_all_certifications():
    productId = request.args.get('productId')
    print("get all certifications:", productId)
    try:
        response = requests.get(f'http://localhost:3000/api/product/getCertifications?productId={productId}')
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
        response = requests.get(f'http://localhost:3000/readProduct?productId={item_code}')
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

if __name__ == "__main__":
    app.run(debug=True)