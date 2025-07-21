from database.db_connection import get_db_connection
from datetime import datetime

def fetch_invite_token_data(token):
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            sql = "SELECT code, expires_at, used FROM invite_token WHERE code = %s"
            cursor.execute(sql, (token,))
            return cursor.fetchone()
    except Exception as e:
        print("DB error:", e)
        return None
    finally:
        connection.close()

def mark_invite_token_used(token):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("UPDATE invite_token SET used = TRUE WHERE code = %s", (token,))
        conn.commit()