import requests
import time
import uuid
from database_mongo.queries.users_queries import get_user_by_email
from database_mongo.queries.otp_queries import get_otp_by_user_id

BASE_URL = "http://backend:5000"

def wait_for_backend(url, timeout=60):
    print(f"Waiting for backend at {url}/signup ...")
    for _ in range(timeout):
        try:
            r = requests.get(f"{url}/signup")
            if r.status_code < 500:
                print("Backend is up!")
                return
        except Exception:
            pass
        time.sleep(1)
    raise RuntimeError("Backend not available after waiting.")

def test_signup(email, role="user", invite_token=None, manufacturer=None):
    data = {
        "email": email,
        "manufacturer": manufacturer or "TestManuf",
        "password": "testpass",
        "role": role,
        "flags": [True, False, False]
    }
    if invite_token:
        data["inviteToken"] = invite_token
    start = time.time()
    r = requests.post(f"{BASE_URL}/signup", json=data, timeout=10)
    elapsed = time.time() - start
    try:
        response_json = r.json()
    except Exception:
        response_json = r.text
    print("Signup:", r.status_code, response_json, f"{elapsed:.4f}s")
    return elapsed

def test_login(email):
    data = {
        "email": email,
        "password": "testpass"
    }
    start = time.time()
    r = requests.post(f"{BASE_URL}/login", json=data, timeout=10)
    elapsed = time.time() - start
    try:
        response_json = r.json()
    except Exception:
        response_json = r.text
    print("Login:", r.status_code, response_json, f"{elapsed:.4f}s")
    token = response_json.get("access_token") if isinstance(response_json, dict) else None
    return elapsed, token

def test_add_product(token, product_id, manufacturer):
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "ID": product_id,
        "Name": "TestProduct",
        "Manufacturer": manufacturer,
        "HarvestDate": "2024-06-05",
        "ExpiryDate": "2024-12-10",
        "Nutritional_information": "47 kcal",
        "CountryOfOrigin": "Spain",
        "Ingredients": "Orange",
        "Allergens": "none",
        "PesticideUse": "none",
        "FertilizerUse": "none",
        "CustomObject": {"color": "red"}
    }
    start = time.time()
    r = requests.post(f"{BASE_URL}/uploadProduct", json=data, headers=headers, timeout=10)
    elapsed = time.time() - start
    try:
        response_json = r.json()
    except Exception:
        response_json = r.text
    print("AddProduct:", r.status_code, response_json, f"{elapsed:.4f}s")
    return elapsed

def test_get_product(token, product_id):
    headers = {"Authorization": f"Bearer {token}"}
    params = {"productId": product_id}
    start = time.time()
    r = requests.get(f"{BASE_URL}/getProduct", params=params, headers=headers, timeout=10)
    elapsed = time.time() - start
    try:
        response_json = r.json()
    except Exception:
        response_json = r.text
    print("GetProduct:", r.status_code, response_json, f"{elapsed:.4f}s")
    return elapsed

def get_otp_for_user(email, max_wait=10):
    user = get_user_by_email(email)
    if not user:
        return None
    for _ in range(max_wait):
        otp_doc = get_otp_by_user_id(user["_id"])
        if otp_doc:
            return otp_doc["otp"]
        time.sleep(1)
    return None

def test_verify_otp(email, otp):
    data = {"email": email, "otp": otp}
    r = requests.post(f"{BASE_URL}/verify-otp", json=data, timeout=10)
    try:
        response_json = r.json()
    except Exception:
        response_json = r.text
    print("Verify OTP:", r.status_code, response_json)
    token = response_json.get("access_token") if isinstance(response_json, dict) else None
    return token

if __name__ == "__main__":
    wait_for_backend(BASE_URL)
    N = 5
    signup_times = []
    login_times = []
    addprod_times = []
    getprod_times = []

    # Signup e login utenti normali (senza OTP)
    for i in range(4):
        unique = str(uuid.uuid4())[:8]
        email = f"user{i}_{unique}@example.com"
        manufacturer = f"Manuf_{unique}"
        signup_times.append(test_signup(email, role="user", manufacturer=manufacturer))
        login_time, _ = test_login(email)
        login_times.append(login_time)

    # Signup e login producer (con OTP)
    producer_unique = str(uuid.uuid4())[:8]
    producer_email = f"producer_{producer_unique}@example.com"
    producer_manufacturer = f"ProducerManuf_{producer_unique}"
    test_signup(producer_email, role="producer", invite_token="INVITE456", manufacturer=producer_manufacturer)
    test_login(producer_email)
    otp = get_otp_for_user(producer_email)
    producer_token = None
    if otp:
        producer_token = test_verify_otp(producer_email, otp)

    # Creazione prodotti con il producer loggato
    product_ids = []
    for i in range(N):
        unique = str(uuid.uuid4())[:8]
        product_id = f"PROD_TEST_{unique}"
        product_ids.append(product_id)
        if producer_token:
            addprod_times.append(test_add_product(producer_token, product_id, producer_manufacturer))
        else:
            addprod_times.append(None)

    # Attendi che la blockchain si sincronizzi
    time.sleep(2)

    # Lettura prodotti con il producer loggato
    for product_id in product_ids:
        if producer_token:
            getprod_times.append(test_get_product(producer_token, product_id))
        else:
            getprod_times.append(None)

    print("\n--- TEMPO MEDIO DI RISPOSTA ROUTE", N, "CICLI ---")
    print("Tempo medio route /Signup:", sum(signup_times)/4, "s")
    print("Tempo medio route /Login:", sum(login_times)/4, "s")
    print("Tempo medio route /AddProduct:", sum([t for t in addprod_times if t is not None])/N, "s")
    print("Tempo medio route /GetProduct:", sum([t for t in getprod_times if t is not None])/N, "s")