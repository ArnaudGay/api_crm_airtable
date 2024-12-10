import requests
import time

API_KEY = "patE9KwHyOaHmMuNs.8472714e36413d5c0f9ec1bfe29ca19fd6c62b0736bcfaeeebbee49741c36cfd"
BASE_ID = "appYaD6sOPRdYO1Hs"
TABLE_NAME = "sales_pipeline"

def fetch_all_records():
    url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"
    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }
    all_records = []
    offset = None

    while True:
        params = {}
        if offset:
            params["offset"] = offset
        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            print(f"Erreur : {response.status_code}, {response.text}")
            break

        data = response.json()
        all_records.extend(data.get("records", []))  # Ajouter les enregistrements à la liste

        offset = data.get("offset")
        if not offset:
            break

        time.sleep(0.2)

    return all_records

fetch_all_records()
