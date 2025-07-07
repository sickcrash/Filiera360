from locust import HttpUser, task, between
import uuid
import random

class FullUserFlow(HttpUser):
    host = "http://localhost:5001"
    wait_time = between(1, 3)

    def on_start(self):
        producer_email = "user90@gmail.com"

        # recupero OTP 
        otp_resp = self.client.get("/get-latest-otp", params={"email": producer_email})
        if otp_resp.status_code != 200:
            print("OTP non recuperato:", otp_resp.status_code, otp_resp.text)
            self.token = None
            return

        otp = str(otp_resp.json().get("otp"))

        # verifica OTP e ottiengo token
        verify_resp = self.client.post("/verify-otp", json={
            "email": producer_email,
            "otp": otp
        })

        if verify_resp.status_code == 200 and "access_token" in verify_resp.json():
            self.token = verify_resp.json()["access_token"]
            print("Login producer riuscito")
        else:
            print("Login producer fallito:", verify_resp.status_code, verify_resp.text)
            self.token = None

    @task(1)
    def login(self):
        response = self.client.post("/login", json={
            "email": "user90@gmail.com",
            "password": "user90"
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
                "ID": "12345",
                "Name": "Mela",
                "Manufacturer": "user3"
            }
        }, headers=headers)

    @task(2)
    def add_recently_searched(self):
        if not self.token:
            return
        headers = {"Authorization": f"Bearer {self.token}"}
        self.client.post("/addRecentlySearched", json={
            "userEmail": "user90@gmail.com",
            "product": {
                "ID": "99999",
                "Name": "Banana",
                "Manufacturer": "locustUser",
                "CreationDate": "2025-01-01"
            }
        }, headers=headers)

    @task(1)
    def get_recently_searched(self):
        if not self.token:
            return
        headers = {"Authorization": f"Bearer {self.token}"}
        self.client.get("/getRecentlySearched", params={
            "userEmail": "user90@gmail.com"
        }, headers=headers)

    @task(1)
    def get_liked_products(self):
        if not self.token:
            return
        headers = {"Authorization": f"Bearer {self.token}"}
        self.client.get("/getLikedProducts", headers=headers)

    