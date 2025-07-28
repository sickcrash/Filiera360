from locust import HttpUser, task, between
import uuid
import random
import json

class MiddlewareUser(HttpUser):
    wait_time = between(1, 2)
    host = "http://middleware:3000"  # oppure http://localhost:3000 se fuori da Docker

    def generate_product(self):
        return {
            "ID": str(uuid.uuid4()),
            "Name": f"Product-{random.randint(1000, 9999)}",
            "Manufacturer": "ACME Inc.",
            "ExpiryDate": "2026-12-31",
            "Ingredients": "Sugar, Water",
            "Allergens": "None",
            "Nutritional_information": "100kcal",
            "HarvestDate": "2025-07-01",
            "PesticideUse": "Low",
            "FertilizerUse": "Organic",
            "CountryOfOrigin": "Italy",
            "ProducerInfo": {
                "legalName": "ACME s.r.l.",
                "vat": "12345678901"
            },
            "CustomObject": {
                "batchNumber": f"BN-{random.randint(1000, 9999)}"
            }
        }

    @task
    def upload_product(self):
        product = self.generate_product()
        headers = {"Content-Type": "application/json"}
        with self.client.post("/uploadProduct", data=json.dumps(product), headers=headers, catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Errore: {response.status_code} - {response.text}")
            else:
                response.success()
