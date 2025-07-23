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

def insert_user(email, manufacturer, hashed_password, role_name):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT id FROM roles WHERE name = %s", (role_name,))
        role = cursor.fetchone()
        if not role:
                raise ValueError(f"Ruolo '{role_name}' non esiste.")
        role_id = role["id"]

        cursor.execute("""
            INSERT INTO users (email, manufacturer, password, role_id)
            VALUES (%s, %s, %s, %s)
        """, (email, manufacturer, hashed_password, role_id))
        conn.commit()



def get_user_by_email(email):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT u.email, u.password, u.manufacturer, r.name AS role
                FROM users u
                JOIN roles r ON u.role_id = r.id
                WHERE u.email = %s
            """, (email,))
            return cursor.fetchone()
    finally:
        conn.close()


def get_user_operators(producer_email):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("""
                SELECT u.email FROM user_operators uo
                JOIN users u ON uo.operator_email = u.email
                WHERE uo.user_email = %s
        """, (producer_email,))
        result = cursor.fetchall()
        return [row["email"] for row in result]
    conn.close()

def get_user_role(email):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("""
                SELECT r.name FROM users u
                JOIN roles r ON u.role_id = r.id
                WHERE u.email = %s
        """, (email,))
        result = cursor.fetchone()
        return result["name"] if result else None
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
def add_operator_to_user(user_email, operator_email):
    """
    Aggiunge un operatore associato a un produttore.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO user_operators (user_email, operator_email)
                VALUES (%s, %s)
            """, (user_email, operator_email))
        conn.commit()
    finally:
        conn.close()

def remove_operator_from_user(user_email, operator_email):
    """
    Rimuove un operatore associato a un produttore.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                DELETE FROM user_operators
                WHERE user_email = %s AND operator_email = %s
            """, (user_email, operator_email))
        conn.commit()
    finally:
        conn.close()