import requests
from flask import current_app

def databoom_login():
    """Effettua il login e restituisce il JWT."""
    api_base = current_app.config['DATABOOM_API_BASE']
    username = current_app.config['DATABOOM_USERNAME']
    password = current_app.config['DATABOOM_PASSWORD']

    resp = requests.post(
        f"{api_base}/auth/signin",
        json={'username': username, 'password': password}
    )
    if resp.status_code != 200:
        raise Exception(f"Login failed: {resp.text}")
    jwt = resp.json().get('jwt')
    if not jwt:
        raise Exception("No JWT token received")
    return jwt


def get_devices():
    """Recupera tutti i device da Databoom."""
    api_base = current_app.config['DATABOOM_API_BASE']
    jwt = databoom_login()
    headers = {"Authorization": f"Bearer {jwt}"}

    resp = requests.get(f"{api_base}/devices/all", headers=headers)
    if resp.status_code != 200:
        raise Exception(f"Failed to fetch devices: {resp.text}")
    return resp.json()


def get_signal_averages(device_id, start_date, end_date):
    """Recupera i segnali del device e calcola il valore medio."""
    api_base = current_app.config['DATABOOM_API_BASE']
    jwt = databoom_login()
    headers = {"Authorization": f"Bearer {jwt}"}

    device_resp = requests.get(f"{api_base}/devices/{device_id}", headers=headers)
    if device_resp.status_code != 200:
        raise Exception("Failed to fetch device info")

    device_data = device_resp.json()
    signals = device_data.get("signals", [])

    results = []

    for signal in signals:
        signal_info = requests.get(f"{api_base}/signals/{signal}", headers=headers)
        signal_name = signal_info.json().get("description", "Unnamed")
        if signal_name == "Unnamed":
            continue

        chart_resp = requests.post(
            f"{api_base}/chart",
            headers=headers,
            json={
                "startDate": start_date,
                "endDate": end_date,
                "granularity": "a",
                "signals": [signal]
            }
        )
        if chart_resp.status_code != 200:
            continue

        chart_data = chart_resp.json().get(signal, [])
        values = [entry["value"] for entry in chart_data if "value" in entry]

        if not values:
            continue

        avg_value = round(sum(values) / len(values), 2)
        results.append({
            "signal_id": signal,
            "signal_name": signal_name,
            "average": avg_value
        })

    return results
