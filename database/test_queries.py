import time
import uuid
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.queries.otp_queries import (
    insert_or_update_otp,
    get_otp_record,
    delete_otp,
    get_latest_otp
)

from database.queries.invite_token_queries import (
    fetch_invite_token_data,
    mark_invite_token_used,
    delete_expired_or_used_tokens
)

from database.queries.users_queries import (
    check_email_exists,
    check_manufacturer_exists,
    insert_user,
    get_user_by_email,
    get_user_operators,
    get_user_role,
    get_manufacturer_by_email,
    update_user_password,
    add_operator_to_user,
    remove_operator_from_user
)

from database.queries.models_queries import (
    save_or_update_model,
    get_model_by_product_id,
    insert_product_if_not_exists
)

from database.queries.likes_queries import (
    has_user_liked_product,
    add_product_like,
    remove_product_like,
    get_user_liked_products
)

from database.queries.searches_queries import (
    add_recent_search,
    get_recent_searches
)

from database.db_connection import get_db_connection

test_email = f"test_user_{uuid.uuid4().hex[:6]}@example.com"
test_operator_email = f"operator_{uuid.uuid4().hex[:6]}@example.com"
test_product_id = f"PROD_TEST_{uuid.uuid4().hex[:6]}"
test_token = f"TOKEN_{uuid.uuid4().hex[:6]}"


def time_query(label, func, *args, **kwargs):
    start = time.time()
    try:
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        print(f"{label}: {elapsed:.4f}s")
        return elapsed
    except Exception as e:
        print(f"{label} FAILED: {e}")
        return 0.0  # oppure None se vuoi escluderlo



def test_users():
    print("\n=== TEST USERS ===")
    times = []
    times.append(time_query("Insert user", insert_user, test_email, "testpass", "TestManuf", "producer"))
    times.append(time_query("Check email exists", check_email_exists, test_email))
    times.append(time_query("Check manufacturer exists", check_manufacturer_exists, "TestManuf"))
    times.append(time_query("Get user by email", get_user_by_email, test_email))
    times.append(time_query("Update user password", update_user_password, test_email, "newpass"))
    times.append(time_query("Get user role", get_user_role, test_email))
    times.append(time_query("Get manufacturer by email", get_manufacturer_by_email, test_email))

    times.append(time_query("Insert operator user", insert_user, test_operator_email, "operatorpass", "OpManuf", "operator"))

    times.append(time_query("Add operator", add_operator_to_user, test_email, test_operator_email))
    times.append(time_query("Get user operators", get_user_operators, test_email))
    times.append(time_query("Remove operator", remove_operator_from_user, test_email, test_operator_email))
    print(f"TEMPO MEDIO USERS: {sum(map(lambda x: x if isinstance(x, float) else 0.0, times))/len(times):.4f} s\n")


def test_otp():
    print("\n=== TEST OTP ===")
    times = []
    times.append(time_query("Insert or update OTP", insert_or_update_otp, test_email, "654321"))
    times.append(time_query("Get OTP record", get_otp_record, test_email))
    times.append(time_query("Get latest OTP", get_latest_otp, test_email))
    times.append(time_query("Delete OTP", delete_otp, test_email))
    print(f"TEMPO MEDIO OTP: {sum(times):.4f} s\n")

from datetime import datetime, timedelta

datetime_obj = datetime.now() + timedelta(minutes=60)

def test_invite_tokens():
    print("\n=== TEST INVITE TOKENS ===")
    times = []
    conn = get_db_connection()
    cur = conn.cursor()
    start = time.time()
    cur.execute("""
    INSERT INTO invite_token (code, expires_at, used, used_by, used_at)
    VALUES (%s, %s, %s, %s, %s)
    """, ("TOKEN5", datetime_obj, 0, None, None)) 
    conn.commit()
    t = time.time() - start
    print(f"Insert token manually: {t:.4f}s")
    times.append(t)
    cur.close()
    conn.close()

    times.append(time_query("Fetch token", fetch_invite_token_data, test_token))
    times.append(time_query("Mark token as used", mark_invite_token_used, test_token, test_email))
    times.append(time_query("Delete expired or used tokens", delete_expired_or_used_tokens))
    print(f"TEMPO MEDIO INVITE TOKENS: {sum(times)/len(times):.4f} s\n")



def test_models():
    print("\n=== TEST MODELS ===")
    times = []
    times.append(time_query("Insert product if not exists", insert_product_if_not_exists, test_product_id))
    times.append(time_query("Save or update model", save_or_update_model, test_product_id, "base64model"))
    times.append(time_query("Get model by product ID", get_model_by_product_id, test_product_id))
    print(f"TEMPO MEDIO MODELS: {sum(times)/len(times):.4f} s\n")


def test_likes():
    print("\n=== TEST LIKES ===")
    times = []
    times.append(time_query("Add product like", add_product_like, test_email, {"ID": test_product_id}))
    times.append(time_query("Has user liked product", has_user_liked_product, test_email, test_product_id))
    times.append(time_query("Get user liked products", get_user_liked_products, test_email))
    times.append(time_query("Remove product like", remove_product_like, test_email, test_product_id))
    print(f"TEMPO MEDIO LIKES: {sum(times)/len(times):.4f} s\n")


def test_searches():
    print("\n=== TEST RECENTLY SEARCHED ===")
    times = []
    for i in range(6):
        pid = f"{test_product_id}_{i}"
        insert_product_if_not_exists(pid)
        times.append(time_query(f"Add recent search {i}", add_recent_search, test_email, {"ID": pid}))
        time.sleep(0.2)
    times.append(time_query("Get recent searches", get_recent_searches, test_email))
    print(f"TEMPO MEDIO RECENTLY SEARCHED: {sum(times)/len(times):.4f} s\n")


def cleanup():
    print("\n=== CLEANUP ===")
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("DELETE FROM users WHERE email = %s", (test_email,))
    cur.execute("DELETE FROM users WHERE email = %s", (test_operator_email,))
    cur.execute("DELETE FROM otp_codes WHERE email = %s", (test_email,))
    cur.execute("DELETE FROM invite_token WHERE code = %s", (test_token,))
    cur.execute("DELETE FROM models WHERE id LIKE %s", (f"{test_product_id}%",))
    cur.execute("DELETE FROM liked_products WHERE user_email = %s", (test_email,))
    cur.execute("DELETE FROM searches WHERE user_email = %s", (test_email,))


    conn.commit()
    cur.close()
    conn.close()
    print("CLEANUP completato\n")



def run_all_tests():
    total_start = time.time()
    test_users()
    test_otp()
    test_invite_tokens()
    '''test_access_control()'''
    test_models()
    test_likes()
    test_searches()
    cleanup()
    total_end = time.time()
    print(f"\nTUTTI I TEST COMPLETATI IN {total_end - total_start:.2f} secondi\n")


if __name__ == "__main__":
    run_all_tests()
