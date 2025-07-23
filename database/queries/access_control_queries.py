import json
import requests
from database.db_connection import get_db_connection

def find_producer_by_operator(operator_email):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT u.email, u.manufacturer
                FROM users u
                JOIN roles r ON u.role_id = r.id
                WHERE r.name = 'producer'
            """)
            producers = cursor.fetchall()

        for producer in producers:
            with conn.cursor() as cursor2:
                cursor2.execute("""
                    SELECT operator_email FROM user_operators
                    WHERE user_email = %s
                """, (producer["email"],))
                linked_operators = [row["operator_email"] for row in cursor2.fetchall()]
                if operator_email in linked_operators:
                    return producer
    finally:
        conn.close()

    return None

def required_permissions(email, allowed_roles):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT r.name FROM users u
            JOIN roles r ON u.role_id = r.id
            WHERE u.email = %s
        """, (email,))
        result = cursor.fetchone()
        return result and result["name"] in allowed_roles
    conn.close()

def verify_product_authorization(email, product_id):
    print(f"Verifica autorizzazione per utente: {email} sul prodotto: {product_id}")
    if not email or not product_id:
        print("Email o Product ID mancante")
        return False

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT u.manufacturer, r.name AS role
                FROM users u
                JOIN roles r ON u.role_id = r.id
                WHERE u.email = %s
            """, (email,))

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


