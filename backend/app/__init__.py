from flask import Flask
from flask_mail import Mail
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
import os, secrets

#from .routes.views import views_bp
from .routes.products import products_bp
from .routes.auth import auth_bp

# --- CREAZIONE APP ---
app = Flask(__name__)
load_dotenv()  # carica le variabili dal file .env

# --- CONFIG MAIL ---
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

mail = Mail()
mail.init_app(app)  # inizializza Mail

# --- CONFIG JWT ---
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', secrets.token_hex(32))
jwt = JWTManager(app)

# --- BLUEPRINT ---
app.register_blueprint(products_bp)
app.register_blueprint(auth_bp)
#app.register_blueprint(views_bp, url_prefix='/')

#GET /products/getProduct → prende un prodotto
#/ → la home page definita in misc.py
