from database.db_connection import get_db_connection
from datetime import datetime

def has_user_liked_product(user_email, product_id):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*) as cnt FROM liked_products
            WHERE user_email = %s AND ID = %s
        """, (user_email, product_id))
        result = cursor.fetchone()
    conn.close()
    return result['cnt'] > 0

def add_product_like(user_email, product):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        # Verifica quanti like ha già l'utente
        cursor.execute("""
            SELECT COUNT(*) as cnt FROM liked_products
            WHERE user_email = %s
        """, (user_email,))
        count_result = cursor.fetchone()

        if count_result and count_result["cnt"] >= 100:
            # Elimina il like più vecchio se sono già 100
            cursor.execute("""
                DELETE FROM liked_products
                WHERE user_email = %s
                ORDER BY timestamp ASC
                LIMIT 1
            """, (user_email,))

        # Inserisci o aggiorna il like
        cursor.execute("""
            INSERT INTO liked_products (ID, user_email, timestamp)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE timestamp = VALUES(timestamp)
        """, (
            product["ID"],
            user_email,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))

        conn.commit()
    conn.close()

def remove_product_like(user_email, product_id):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("""
            DELETE FROM liked_products
            WHERE user_email = %s AND ID = %s
        """, (user_email, product_id))
        conn.commit()
    conn.close()

def get_user_liked_products(user_email):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT ID, timestamp
            FROM liked_products
            WHERE user_email = %s
            ORDER BY timestamp DESC
        """, (user_email,))
        results = cursor.fetchall()
    conn.close()
    return results
