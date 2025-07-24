from database.db_connection import get_db_connection

def save_or_update_model(product_id, glb_base64=None):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("""
            INSERT INTO models (id, stringa)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE stringa = VALUES(stringa)
        """, (product_id, glb_base64))
        conn.commit()
    conn.close()

def get_model_by_product_id(product_id):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT stringa FROM models WHERE id = %s", (product_id,))
        result = cursor.fetchone()
    conn.close()
    return result["stringa"] if result else None

def insert_product_if_not_exists(product_id):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("""
            INSERT IGNORE INTO models (id) VALUES (%s)
        """, (product_id,))
        conn.commit()
    conn.close()