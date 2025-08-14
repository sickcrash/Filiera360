from dotenv import load_dotenv
import os

load_dotenv()  # carica le variabili dal file .env

jwt_secret = os.getenv("JWT_SECRET_KEY")
print(jwt_secret)
