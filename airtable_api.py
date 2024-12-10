import requests
import json

# Configuration
API_KEY = "patE9KwHyOaHmMuNs.8472714e36413d5c0f9ec1bfe29ca19fd6c62b0736bcfaeeebbee49741c36cfd"
BASE_ID = "appYaD6sOPRdYO1Hs"
TABLE_NAME = "sales_pipeline"

# API endpoint
url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"

# Headers with API key
headers = {
    "Authorization": f"Bearer {API_KEY}"
}

# GET request to retrieve records
response = requests.get(url, headers=headers)

# Check response status
if response.status_code == 200:
    data = response.json()
    
    # Save the data to a JSON file
    with open("airtable_data.json", "w", encoding="utf-8") as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)
    
    print("Données sauvegardées dans 'airtable_data.json'")
else:
    print(f"Failed to retrieve records: {response.status_code}")
    print(response.json())
