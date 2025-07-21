import json
from database.db_connection import get_db_connection

def check_email_exists(email):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT email FROM users WHERE email = %s", (email,))
        return cursor.fetchone()

def check_manufacturer_exists(manufacturer):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT manufacturer FROM users WHERE manufacturer = %s", (manufacturer,))
        return cursor.fetchone()

def insert_user(email, manufacturer, hashed_password, role):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("""
            INSERT INTO users (email, manufacturer, password, role)
            VALUES (%s, %s, %s, %s)
        """, (email, manufacturer, hashed_password, role))
        conn.commit()



def get_user_by_email(email):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        return cursor.fetchone()

def get_user_operators(email):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT operators FROM users WHERE email = %s", (email,))
        result = cursor.fetchone()
    conn.close()
    return json.loads(result["operators"]) if result and result["operators"] else []

def get_user_role(email):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT role FROM users WHERE email = %s", (email,))
        result = cursor.fetchone()
    conn.close()
    return result["role"] if result else None

def get_raw_operators(email):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT operators FROM users WHERE email = %s", (email,))
        result = cursor.fetchone()
    conn.close()
    return json.loads(result["operators"]) if result and result["operators"] else []

def update_user_operators(email, operators_list):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("UPDATE users SET operators = %s WHERE email = %s",
                       (json.dumps(operators_list), email))
        conn.commit()
    conn.close()


def get_manufacturer_by_email(email):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT manufacturer FROM users WHERE email = %s", (email,))
            result = cursor.fetchone()
            return result["manufacturer"] if result and "manufacturer" in result else None
    finally:
        conn.close()


def update_user_password(email, hashed_password):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("UPDATE users SET password = %s WHERE email = %s", (hashed_password, email))
        conn.commit()
    conn.close()
