from database.db_connection import get_db_connection
from datetime import datetime
import pytz

def now_italy():
    return datetime.now(pytz.timezone("Europe/Rome")).strftime('%Y-%m-%d %H:%M:%S')

def add_recent_search(user_email, product):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        # Rimuovi eventuale duplicato
        cursor.execute("""
            DELETE FROM searches
            WHERE user_email = %s AND product_id = %s
        """, (user_email, product.get('ID')))

        # Inserisci nuovo record
        cursor.execute("""
            INSERT INTO searches (product_id, timestamp, user_email)
            VALUES (%s, %s, %s)
        """, (
            product.get('ID'),
            now_italy(),
            user_email
        ))

        # Mantieni solo le ultime 50 ricerche
        cursor.execute("""
            DELETE FROM searches
            WHERE user_email = %s AND ID NOT IN (
                SELECT ID FROM (
                    SELECT ID FROM searches
                    WHERE user_email = %s
                    ORDER BY timestamp DESC
                    LIMIT 50
                ) AS recent
            )
        """, (user_email, user_email))

        conn.commit()
    conn.close()

def get_recent_searches(user_email):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT product_id AS ID, timestamp
            FROM searches
            WHERE user_email = %s
            ORDER BY timestamp DESC
            LIMIT 50
        """, (user_email,))
        results = cursor.fetchall()
    conn.close()
    return results
