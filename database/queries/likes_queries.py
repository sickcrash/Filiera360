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
        cursor.execute("""
            INSERT INTO liked_products (ID, Name, Manufacturer, timestamp, user_email)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            product['ID'],
            product['Name'],
            product['Manufacturer'],
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            user_email
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
            SELECT ID, Name, Manufacturer, CreationDate, timestamp FROM liked_products
            WHERE user_email = %s
        """, (user_email,))
        results = cursor.fetchall()
    conn.close()
    return results
