from locust import HttpUser, task, between
import uuid
import random
import time

class FullUserFlow(HttpUser):
    host = "http://localhost:5001"
    wait_time = between(1, 3)

    def on_start(self):
        producer_email = "user6799@gmail.com"

        # 1. Richiedi OTP
        login_resp = self.client.post("/login", json={
            "email": producer_email,
            "password": "user6799"
        })
        if login_resp.status_code != 200:
            print("Login OTP trigger fallito")
            self.token = None
            return

        # 2. Aspetta che il backend scriva l’OTP
        time.sleep(1.2)

        # 3. Recupera OTP
        otp_resp = self.client.get("/get-latest-otp", params={"email": producer_email})
        if otp_resp.status_code != 200:
            print("OTP non recuperato:", otp_resp.status_code, otp_resp.text)
            self.token = None
            return

        otp = otp_resp.json().get("otp")

        # 4. Verifica OTP
        verify_resp = self.client.post("/verify-otp", json={
            "email": producer_email,
            "otp": otp
        })
        if verify_resp.status_code == 200 and "access_token" in verify_resp.json():
            self.token = verify_resp.json()["access_token"]
        else:
            print("Verifica OTP fallita:", verify_resp.status_code, verify_resp.text)
            self.token = None


    @task(1)
    def login(self):
        response = self.client.post("/login", json={
            "email": "user6799@gmail.com",
            "password": "user6799"
        })
        if response.status_code != 200 or "access_token" not in response.json():
            print("Login fallito:", response.status_code, response.text)

    @task(2)
    def signup(self):
        email = f"user_{uuid.uuid4().hex[:6]}@example.com"
        password = "testpass"
        manufacturer = f"mfg_{uuid.uuid4().hex[:6]}"

        resp = self.client.post("/signup", json={
            "email": email,
            "manufacturer": manufacturer,
            "password": password
        })

        if resp.status_code != 201:
            print("Signup fallito:", resp.status_code, resp.text)

    @task(2)
    def like_product(self):
        if not self.token:
            return
        headers = {"Authorization": f"Bearer {self.token}"}
        self.client.post("/likeProduct", json={
            "product": {
                "ID": "cocco",
                "Name": "Cocco",
                "Manufacturer": "user6799"
            }
        }, headers=headers)

    @task(2)
    def add_recently_searched(self):
        if not self.token:
            return
        headers = {"Authorization": f"Bearer {self.token}"}
        self.client.post("/addRecentlySearched", json={
            "userEmail": "user6799@gmail.com",
            "product": {
                "ID": "cocco",
                "Name": "Cocco",
                "Manufacturer": "user6799",
                "CreationDate": "2025-07-23"
            }
        }, headers=headers)


    @task(1)
    def get_recently_searched(self):
        if not self.token:
            return
        headers = {"Authorization": f"Bearer {self.token}"}
        self.client.get("/getRecentlySearched", params={
            "userEmail": "user6799@gmail.com"
        }, headers=headers)

    @task(1)
    def get_liked_products(self):
        if not self.token:
            return
        headers = {"Authorization": f"Bearer {self.token}"}
        self.client.get("/getLikedProducts", headers=headers)

    