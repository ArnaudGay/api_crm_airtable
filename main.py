from typing import Dict, Any, List
from fastapi import FastAPI
import requests

app = FastAPI()

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
    records = data.get("records", [])
else:
    print(f"Failed to retrieve records: {response.status_code}")
    print(response.json())


@app.get("/products")
def products():
    total_revenue: Dict[int] = 0
    total_products: Dict[int] = 0
    sold_products_count: Dict[int] = 0
    sold_products_prices: List[str] = []
    products_by_sector: Dict[str, List[str]] = {}
    product_list: Dict[List[str]] = []

    for record in records:
        fields = record.get("fields", {})
        deal_stage = fields.get("deal_stage", "")
        close_value = fields.get("close_value", 0)
        product = fields.get("product (from product)", [None])[0]
        sector = fields.get("sector (from account)", "Unknown")

        if isinstance(sector, list):
            sector = sector[0]

        # Ajouter au chiffre d'affaires total
        if deal_stage == "Won":
            total_revenue += close_value
            sold_products_count += 1
            sales_price = fields.get("close_value", 0)
            sold_products_prices.append(sales_price)

        # Grouper les produits par secteur
        if deal_stage == "Won" and product:
            if sector not in products_by_sector:
                products_by_sector[sector] = []
            products_by_sector[sector].append(product)

        
        if product not in product_list:
            product_list.append(product)
            total_products += 1

    # Calculer le prix moyen des produits vendus
    average_sales_price = (
        sum(sold_products_prices) / len(sold_products_prices)
        if sold_products_prices else 0
    )

    # Préparer la réponse
    return {
        "total_revenue": total_revenue,
        "total_products": total_products,
        "product_list": product_list,
        "sold_products_count": sold_products_count,
        "average_sales_price": average_sales_price,
        "products_by_sector": products_by_sector,
    }


@app.get("/products/{name_product}")
def product_details(name_product: str) -> Dict[str, Any]:
    total_revenue = 0
    total_sold = 0
    sales_prices = []

    for record in records:
        fields = record.get("fields", {})
        deal_stage = fields.get("deal_stage", "")
        product_name = fields.get("product (from product)", [None])[0]

        # Vérifier si le produit correspond au nom recherché et qu'il a été vendu
        if product_name == name_product and deal_stage == "Won":
            total_revenue += fields.get("close_value", 0)
            total_sold += 1
            sales_price = fields.get("close_value", 0)
            sales_prices.append(sales_price)

    # Calculer le prix moyen de vente
    average_sales_price = (
        sum(sales_prices) / len(sales_prices) if sales_prices else 0
    )

    # Préparer la réponse
    return {
        "product_name": name_product,
        "total_revenue": total_revenue,
        "total_sold": total_sold,
        "average_sales_price": average_sales_price,
    }
