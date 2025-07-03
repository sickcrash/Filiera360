from locust import HttpUser, task, between
import uuid
import random

class FullUserFlow(HttpUser):
    host = "http://localhost:5001"
    wait_time = between(1, 3)

    def on_start(self):
        # Login per ottenere il token
        response = self.client.post("/login", json={
            "email": "user1@gmail.com",
            "password": "user1"
        })
        if response.status_code == 200 and "access_token" in response.json():
            self.token = response.json()["access_token"]
        else:
            self.token = None
            print("Login fallito in on_start:", response.text)

    @task(1)
    def login(self):
        self.client.post("/login", json={
            "email": "user1@gmail.com",
            "password": "user1"
        })

    @task(2)
    def signup(self):
     email = f"user_{uuid.uuid4().hex[:6]}@example.com"
     password = "testpass"  # o random string
     manufacturer = f"mfg_{random.randint(1000, 9999)}"

     self.client.post("/signup", json={
        "email": email,
        "manufacturer": manufacturer,
        "password": password
    })

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
            "userEmail": "user1@gmail.com",
            "product": {
                "ID": "99999",
                "Name": "Banana",
                "Manufacturer": "locustUser",
                "CreationDate": "2025-01-01"
            }
        }, headers=headers)
