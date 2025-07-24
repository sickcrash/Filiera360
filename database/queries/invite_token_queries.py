from database.db_connection import get_db_connection
from datetime import datetime
from datetime import datetime
import pytz

italian_time = datetime.now(pytz.timezone("Europe/Rome"))

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

def mark_invite_token_used(token, used_by_email):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("""
            UPDATE invite_token
            SET used = TRUE,
                used_by = %s,
                used_at = %s
            WHERE code = %s
        """, (
            used_by_email,
            datetime.now(pytz.timezone("Europe/Rome")).strftime("%Y-%m-%d %H:%M:%S"),
            token
        ))
        conn.commit()
    conn.close()

def delete_expired_or_used_tokens():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("""
            DELETE FROM invite_token
            WHERE used = TRUE OR expires_at < %s
        """, (datetime.now(pytz.timezone("Europe/Rome")).strftime("%Y-%m-%d %H:%M:%S"),))
        conn.commit()
    conn.close()
