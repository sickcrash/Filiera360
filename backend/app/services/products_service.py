import requests

def fetch_product_from_js_server(product_id):
    try:
        response = requests.get(f'http://middleware:3000/readProduct?productId={product_id}')
        if response.status_code == 200:
            return response.json()
        return {"error": f"Failed to fetch product, status {response.status_code}"}
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def fetch_product_history_from_js_server(product_id):
    try:
        response = requests.get(f'http://localhost:3000/productHistory?productId={product_id}')
        print(f"JS server responded with status {response.status_code}")

        if response.status_code == 200:
            return response.json()
        return {'error': f"Failed to get product history {response.status_code}"},

    except requests.exceptions.RequestException as e:
        return {"error": str(e)}
