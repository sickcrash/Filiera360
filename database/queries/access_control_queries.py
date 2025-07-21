import json
import requests
from database.db_connection import get_db_connection

def find_producer_by_operator(operator_email):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT email, manufacturer, operators FROM users WHERE role = 'producer'")
        producers = cursor.fetchall()
        for producer in producers:
            operators = json.loads(producer["operators"]) if producer["operators"] else []
            if operator_email in operators:
                return producer  
    conn.close()
    return None

def required_permissions(email, allowed_roles):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT role FROM users WHERE email = %s", (email,))
        result = cursor.fetchone()
    conn.close()
    return result and result["role"] in allowed_roles

def verify_product_authorization(email, product_id):
    print(f"Verifica autorizzazione per utente: {email} sul prodotto: {product_id}")
    if not email or not product_id:
        print("Email o Product ID mancante")
        return False

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT role, manufacturer, operators FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
        conn.close()

        if not user:
            print("Utente non trovato nel DB")
            return False

        if user["role"] == "operator":
            producer = find_producer_by_operator(email)
            if not producer:
                print("Nessun produttore associato all'operatore")
                return False
            manufacturer = producer["manufacturer"]
        else:
            manufacturer = user["manufacturer"]

        print("Manufacturer trovato:", manufacturer)

        # Middleware
        response = requests.get(f'http://middleware:3000/readProduct?productId={product_id}')
        if response.status_code != 200:
            print('Errore middleware')
            return False

        product = response.json()
        print("Prodotto recuperato:", product)

        return product.get("Manufacturer") == manufacturer

    except Exception as e:
        print("Errore verifica prodotto:", e)
        return False


