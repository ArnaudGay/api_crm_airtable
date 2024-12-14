from typing import Dict, List, Any, Optional, Union
from fastapi import FastAPI
from collections import defaultdict
import requests
import os
import json
from datetime import datetime
from pydantic import BaseModel

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

# Function to fetch and cache data from Airtable
def fetch_and_cache_data():
    cache_file = "cache_api.json"

    # Check if cache file exists
    if os.path.exists(cache_file):
        with open(cache_file, "r") as file:
            return json.load(file)

    # If cache does not exist, fetch data from Airtable API
    all_records = []
    offset = None

    while True:
        params = {"offset": offset} if offset else {}
        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()
            records = data.get("records", [])
            all_records.extend(records)
            offset = data.get("offset")

            if not offset:  # No more pages
                break
        else:
            print(f"Failed to retrieve records: {response.status_code}")
            print(response.json())
            break

    # Cache the data in a JSON file
    with open(cache_file, "w") as file:
        json.dump(all_records, file)

    return all_records

# Load records
records = fetch_and_cache_data()


# Init docs

class RankedClient(BaseModel):
    client: str
    orders: int
    rank: int

class AccountClientShare(BaseModel):
    total_revenue: float
    percentage_of_total_revenue: str

class NegotiatedProduct(BaseModel):
    name: Optional[str]
    negotiation_difference: float

class TopProduct(BaseModel):
    rank: int
    product: str
    sales: int

class SectorDetails(BaseModel):
    sector: str
    sales: float

class RegionDetails(BaseModel):
    region: str
    revenue: float

class MonthlyStats(BaseModel):
    number_of_sales: int
    total_revenue: float
    clients: Dict[str, int]
    sales_by_seller: Dict[str, int]
    sales_by_sector: Dict[str, int]
    average_price: Optional[float] = None
    top_client: Optional[str] = None

class TopStats(BaseModel):
    name: str
    sales_count: int
    revenue: float

class RegionStats(BaseModel):
    sales_count: int
    total_revenue: float
    average_time_to_sell: Optional[float] = None

class SalesAgentPerformance(BaseModel):
    total_revenue: float
    sales_count: int
    average_sales_price: float
    sectors: Dict[str, int]
    clients: List[str]
    regions: Dict[str, RegionStats]
    average_time_to_sell: Optional[float] = None

class TopAgentProduct(BaseModel):
    name: str
    rank: int
    average_price: float

class TopSector(BaseModel):
    name: str
    rank: int
    average_price: float

class ProductRevenue(BaseModel):
    name: Optional[str]
    revenue: float

# Endpoints

class ProductResponse(BaseModel):
    total_revenue: float
    sold_products_count: int
    average_sales_price: float
    top_products_by_sector: Dict[str, List[TopProduct]]
    sector_revenue: Dict[str, float]
    sector_sales_count: Dict[str, int]
    top_sectors_by_sales: List[SectorDetails]
    region_revenue: Dict[str, float]
    top_products_by_region: Dict[str, List[TopProduct]]
    most_revenue_product: ProductRevenue
    least_revenue_product: ProductRevenue
    most_negotiated_product: NegotiatedProduct
    average_price_by_product: Dict[str, float]

class ProductDetailsResponse(BaseModel):
    product_name: str
    total_revenue: float
    total_sold: int
    average_sales_price: float
    max_sales_price: float
    min_sales_price: float
    average_time_to_sell: float
    top_seller_stats: Optional[TopStats]
    top_sector_stats: Optional[TopStats]
    monthly_stats: Dict[str, MonthlyStats]

class SalesAgentsPerformanceResponse(BaseModel):
    sales_agents_performance: Dict[str, SalesAgentPerformance]
    ranking: List[Dict[str, Union[str, int]]]
    managers_revenue: Dict[str, float]
    client_revenue: Dict[str, float]

class SalesAgentDetailsResponse(BaseModel):
    sales_agent: str
    total_sales: int
    average_sales_price: float
    top_products: List[TopAgentProduct]
    top_sectors: List[TopSector]
    total_revenue: float
    opportunities: Dict[str, int]
    average_time_to_sell: Optional[float] = None

class ValueResponse(BaseModel):
    products: List[str]
    clients: List[str]
    sectors: List[str]
    sellers: List[str]
    managers: List[str]
    engage_months_years: List[str]
    close_months_years: List[str]

class AccountResponse(BaseModel):
    client_revenues: Dict[str, float]
    ranked_clients: List[RankedClient]
    client_revenue_shares: Dict[str, AccountClientShare]
    total_company_revenue: float

app = FastAPI()


@app.get("/products", response_model=ProductResponse)
def products():
    total_revenue: Dict[int] = 0
    sold_products_count: Dict[int] = 0
    sold_products_prices: Dict[List[int]] = []
    products_by_sector = {}
    sector_revenue = {}
    sector_sales_count = {}
    products_by_region = {}
    region_revenue = {}
    product_sales = {}
    product_revenue = {}
    total_won_count: Dict[int] = 0
    total_deals: Dict[int] = 0

    for record in records:
        fields = record.get("fields", {})
        deal_stage = fields.get("deal_stage", "")
        close_value = fields.get("close_value", 0)
        product = fields.get("product (from product)", [None])[0]
        sector = fields.get("sector (from account)", "Unknown")
        region = fields.get("regional_office (from sales_agent)", "Unknown")

        if isinstance(sector, list):
            sector = sector[0]
        if isinstance(region, list):
            region = region[0]

        total_deals += 1

        # Comptabilisation des ventes "Won"
        if deal_stage == "Won":
            total_revenue += close_value
            sold_products_count += 1
            sold_products_prices.append(close_value)
            total_won_count += 1

            # Comptabiliser les ventes par secteur
            if sector not in products_by_sector:
                products_by_sector[sector] = {}
                sector_revenue[sector] = 0
                sector_sales_count[sector] = 0
            sector_revenue[sector] += close_value
            sector_sales_count[sector] += 1

            # Comptabiliser les ventes par région
            if region not in products_by_region:
                products_by_region[region] = {}
                region_revenue[region] = 0
            region_revenue[region] += close_value

            # Comptabiliser les produits vendus
            if product:
                if product not in products_by_sector[sector]:
                    products_by_sector[sector][product] = 0
                if product not in products_by_region[region]:
                    products_by_region[region][product] = 0
                if product not in product_sales:
                    product_sales[product] = 0
                    product_revenue[product] = 0

                products_by_sector[sector][product] += 1
                products_by_region[region][product] += 1
                product_sales[product] += 1
                product_revenue[product] += close_value

    # Calcul du prix moyen
    average_sales_price = (
        sum(sold_products_prices) / len(sold_products_prices)
        if sold_products_prices else 0
    )

    # Prix moyen par produit
    average_price_by_product = {
        product: product_revenue[product] / product_sales[product]
        for product in product_sales if product_sales[product] > 0
    }

    # Top 3 produits par secteur
    top_products_by_sector = {
    sector: [
        {"rank": rank + 1, "product": product, "sales": sales}
        for rank, (product, sales) in enumerate(
            sorted(products.items(), key=lambda x: x[1], reverse=True)[:3]
        )
    ]
    for sector, products in products_by_sector.items()
    }

    # Top 3 produits par région
    top_products_by_region = {
    region: [
        {"rank": rank + 1, "product": product, "sales": sales}
        for rank, (product, sales) in enumerate(
            sorted(products.items(), key=lambda x: x[1], reverse=True)[:3]
        )
    ]
    for region, products in products_by_region.items()
    }


    # Secteurs les plus performants
    top_sectors_by_sales = sorted(
        sector_sales_count.items(), key=lambda x: x[1], reverse=True
    )[:3]
    top_sectors_by_sales = [
    {"sector": sector, "sales": sales} for sector, sales in top_sectors_by_sales
]

    # Produits générant le plus et le moins de revenus
    most_revenue_product = {
        "name": max(product_revenue.items(), key=lambda x: x[1], default=(None, 0))[0],
        "revenue": max(product_revenue.items(), key=lambda x: x[1], default=(None, 0))[1],
    }
    least_revenue_product = {
        "name": min(product_revenue.items(), key=lambda x: x[1], default=(None, 0))[0],
        "revenue": min(product_revenue.items(), key=lambda x: x[1], default=(None, 0))[1],
    }

    # Produit le plus négocié
    most_negotiated_product = max(
    records,
    key=lambda x: abs(
        (
            x["fields"].get("sales_price (from product)", [0])[0]
            if isinstance(x["fields"].get("sales_price (from product)", 0), list)
            else x["fields"].get("sales_price (from product)", 0)
        )
        - (
            x["fields"].get("close_value", [0])[0]
            if isinstance(x["fields"].get("close_value", 0), list)
            else x["fields"].get("close_value", 0)
        )
    )
    if x["fields"].get("close_value") not in [None, 0] else 0,  # Exclure close_value == 0 ou None
    default={},
    )

    most_negotiated_product_name = most_negotiated_product.get("fields", {}).get("product (from product)", [None])[0]

    negotiation_difference = abs(
        (
            most_negotiated_product.get("fields", {}).get("close_value", [0])[0]
            if isinstance(most_negotiated_product.get("fields", {}).get("close_value", 0), list)
            else most_negotiated_product.get("fields", {}).get("close_value", 0)
        )
        - (
            most_negotiated_product.get("fields", {}).get("sales_price (from product)", [0])[0]
            if isinstance(most_negotiated_product.get("fields", {}).get("sales_price (from product)", 0), list)
            else most_negotiated_product.get("fields", {}).get("sales_price (from product)", 0)
        )
    ) if most_negotiated_product.get("fields", {}).get("close_value") not in [None, 0] else 0



    return {
        "total_revenue": total_revenue,
        "sold_products_count": sold_products_count,
        "average_sales_price": average_sales_price,
        "top_products_by_sector": top_products_by_sector,
        "sector_revenue": sector_revenue,
        "sector_sales_count": sector_sales_count,
        "top_sectors_by_sales": top_sectors_by_sales,
        "region_revenue": region_revenue,
        "top_products_by_region": top_products_by_region,
        "most_revenue_product": most_revenue_product,
        "least_revenue_product": least_revenue_product,
        "most_negotiated_product": {
            "name": most_negotiated_product_name,
            "negotiation_difference": negotiation_difference,
        },
        "average_price_by_product": average_price_by_product,
    }


@app.get("/products/{name_product}", response_model=ProductDetailsResponse)
def product_details(name_product: str):
    # Préparer les données
    total_revenue: Dict[int] = 0
    total_sold: Dict[int] = 0
    sales_prices: Dict[int] = []
    times_to_sell: Dict[int] = []
    seller_sales = {}
    seller_revenue = {}
    sector_sales = {}
    sector_revenue = {}
    monthly_stats = {}

    # Parcourir les enregistrements
    for record in records:
        fields = record.get("fields", {})
        deal_stage = fields.get("deal_stage", "")
        product_name = fields.get("product (from product)", [None])[0]
        close_value = fields.get("close_value", 0)
        sales_agent = fields.get("sales_agent (from sales_agent)", "Unknown")
        sector = fields.get("sector (from account)", "Unknown")
        account = fields.get("account (from account)", "Unknown")
        engage_date = fields.get("engage_date", None)
        close_date = fields.get("close_date", None)

        if isinstance(engage_date, str):
            engage_date = datetime.strptime(engage_date, "%Y-%m-%d")
        if isinstance(close_date, str):
            close_date = datetime.strptime(close_date, "%Y-%m-%d")
        if isinstance(sales_agent, list):
            sales_agent = sales_agent[0]
        if isinstance(sector, list):
            sector = sector[0]
        if isinstance(account, list):
            account = account[0]

        # Vérifier si le produit correspond au nom recherché et qu'il a été vendu
        if product_name == name_product and deal_stage == "Won" and close_value > 0:
            total_revenue += close_value
            total_sold += 1
            sales_prices.append(close_value)

            # Temps pour vendre le produit
            if engage_date and close_date:
                times_to_sell.append((close_date - engage_date).days)

            # Compter les ventes et chiffre d'affaires par vendeur
            if sales_agent not in seller_sales:
                seller_sales[sales_agent] = 0
                seller_revenue[sales_agent] = 0
            seller_sales[sales_agent] += 1
            seller_revenue[sales_agent] += close_value

            # Compter les ventes et chiffre d'affaires par secteur
            if sector not in sector_sales:
                sector_sales[sector] = 0
                sector_revenue[sector] = 0
            sector_sales[sector] += 1
            sector_revenue[sector] += close_value

            # Ajouter aux statistiques mensuelles
            if close_date:
                month = close_date.strftime("%Y-%m")
                if month not in monthly_stats:
                    monthly_stats[month] = {
                        "number_of_sales": 0,
                        "total_revenue": 0,
                        "clients": {},
                        "sales_by_seller": {},
                        "sales_by_sector": {},
                    }

                monthly_stats[month]["number_of_sales"] += 1
                monthly_stats[month]["total_revenue"] += close_value

                # Ajouter le client
                if account not in monthly_stats[month]["clients"]:
                    monthly_stats[month]["clients"][account] = 0
                monthly_stats[month]["clients"][account] += 1

                # Ajouter les ventes par vendeur
                if sales_agent not in monthly_stats[month]["sales_by_seller"]:
                    monthly_stats[month]["sales_by_seller"][sales_agent] = 0
                monthly_stats[month]["sales_by_seller"][sales_agent] += 1

                # Ajouter les ventes par secteur
                if sector not in monthly_stats[month]["sales_by_sector"]:
                    monthly_stats[month]["sales_by_sector"][sector] = 0
                monthly_stats[month]["sales_by_sector"][sector] += 1

    # Calculer les statistiques globales
    average_sales_price = sum(sales_prices) / len(sales_prices) if sales_prices else 0
    max_sales_price = max(sales_prices) if sales_prices else 0
    min_sales_price = min(sales_prices) if sales_prices else 0
    average_time_to_sell = sum(times_to_sell) / len(times_to_sell) if times_to_sell else 0

    # Trouver le top vendeur avec ventes et chiffre d'affaires
    top_seller = max(seller_sales, key=seller_sales.get) if seller_sales else None
    top_seller_stats = {
        "name": top_seller,
        "sales_count": seller_sales[top_seller],
        "revenue": seller_revenue[top_seller],
    } if top_seller else None

    # Trouver le top secteur avec ventes et chiffre d'affaires
    top_sector = max(sector_sales, key=sector_sales.get) if sector_sales else None
    top_sector_stats = {
        "name": top_sector,
        "sales_count": sector_sales[top_sector],
        "revenue": sector_revenue[top_sector],
    } if top_sector else None

    # Calculer les statistiques mensuelles
    for month, stats in monthly_stats.items():
        stats["average_price"] = stats["total_revenue"] / stats["number_of_sales"]
        stats["top_client"] = max(stats["clients"], key=stats["clients"].get)

    # Préparer la réponse
    return {
        "product_name": name_product,
        "total_revenue": total_revenue,
        "total_sold": total_sold,
        "average_sales_price": average_sales_price,
        "max_sales_price": max_sales_price,
        "min_sales_price": min_sales_price,
        "average_time_to_sell": average_time_to_sell,
        "top_seller_stats": top_seller_stats,
        "top_sector_stats": top_sector_stats,
        "monthly_stats": monthly_stats,
    }


@app.get("/sales_agents", response_model=SalesAgentsPerformanceResponse)
def sales_agents_performance() -> Dict[str, Any]:
    performance = defaultdict(lambda: {
        "total_revenue": 0,
        "sales_count": 0,
        "average_sales_price": 0,
        "sectors": defaultdict(int),
        "clients": set(),
        "regions": defaultdict(lambda: {
            "sales_count": 0,
            "total_revenue": 0,
            "times_to_sell": []
        }),
        "times_to_sell": []
    })

    managers_revenue = defaultdict(int)
    client_revenue = defaultdict(int)

    for record in records:
        fields = record.get("fields", {})
        deal_stage = fields.get("deal_stage", "")
        sales_agent = fields.get("sales_agent (from sales_agent)", [None])[0]
        manager = fields.get("manager (from sales_agent)", "Unknown")
        sector = fields.get("sector (from account)", "Unknown")
        region = fields.get("regional_office (from sales_agent)", "Unknown")
        close_value = fields.get("close_value", 0)
        account = fields.get("account (from account)", [None])[0]
        engage_date = fields.get("engage_date", None)
        close_date = fields.get("close_date", None)

        if isinstance(sector, list):
            sector = sector[0]
        if isinstance(region, list):
            region = region[0]

        if engage_date and close_date:
            engage_date = datetime.strptime(engage_date, "%Y-%m-%d")
            close_date = datetime.strptime(close_date, "%Y-%m-%d")
            time_to_sell = (close_date - engage_date).days
        else:
            time_to_sell = None

        # Si l'affaire est gagnée
        if deal_stage == "Won" and sales_agent:
            performance[sales_agent]["total_revenue"] += close_value
            performance[sales_agent]["sales_count"] += 1
            performance[sales_agent]["sectors"][sector] += 1
            performance[sales_agent]["clients"].add(account)

            # Par région
            performance[sales_agent]["regions"][region]["sales_count"] += 1
            performance[sales_agent]["regions"][region]["total_revenue"] += close_value
            
            if time_to_sell is not None:
                performance[sales_agent]["regions"][region]["times_to_sell"].append(time_to_sell)
                performance[sales_agent]["times_to_sell"].append(time_to_sell)

            # Chiffre d'affaires des managers
            managers_revenue[manager[0] if isinstance(manager, list) else manager] += close_value

            # Revenu des clients
            client_revenue[account] += close_value

    # Calcul des moyennes et transformation des sets en listes
    for agent, stats in performance.items():
        if stats["sales_count"] > 0:
            stats["average_sales_price"] = stats["total_revenue"] / stats["sales_count"]
        if stats["times_to_sell"]:
            stats["average_time_to_sell"] = sum(stats["times_to_sell"]) / len(stats["times_to_sell"])
        else:
            stats["average_time_to_sell"] = None
        stats["clients"] = list(stats["clients"])

        # Calcul par région
        for region, region_stats in stats["regions"].items():
            if region_stats["times_to_sell"]:
                region_stats["average_time_to_sell"] = sum(region_stats["times_to_sell"]) / len(region_stats["times_to_sell"])
            else:
                region_stats["average_time_to_sell"] = None

    ranking = sorted(
        performance.items(),
        key=lambda item: item[1]["sales_count"],
        reverse=True
    )

    return {
        "sales_agents_performance": performance,
        "ranking": [
            {"sales_agent": agent, "sales_count": stats["sales_count"]}
            for agent, stats in ranking
        ],
        "managers_revenue": managers_revenue,
        "client_revenue": {
            client: revenue / (performance[sales_agent]["clients"].count(client) if performance[sales_agent]["clients"].count(client) > 0 else 1)
            for client, revenue in client_revenue.items()
        }
    }


@app.get("/sales_agents/{name_agent}", response_model=SalesAgentDetailsResponse)
def sales_agent_details(name_agent: str):
    # Préparer les données
    agent_records = [
    record for record in records
    if record.get("fields", {}).get("sales_agent (from sales_agent)", [None])[0] == name_agent
    ]

    if not agent_records:
        return {"error": f"No records found for sales agent: {name_agent}"}

    total_sales = 0
    total_revenue = 0
    sales_prices = []
    time_to_sell = []
    product_sales = {}
    sector_sales = {}
    opportunities = {"Won": 0, "Lost": 0, "In Progress": 0}

    for record in agent_records:
        fields = record.get("fields", {})
        product_name = fields.get("product (from product)", [None])[0]
        sector = fields.get("sector (from account)", "Unknown")
        close_value = fields.get("close_value", 0)
        deal_stage = fields.get("deal_stage", "Unknown")
        engage_date = fields.get("engage_date", None)
        close_date = fields.get("close_date", None)

        if isinstance(sector, list):
            sector = sector[0]

        if isinstance(engage_date, str):
            engage_date = datetime.strptime(engage_date, "%Y-%m-%d")
        if isinstance(close_date, str):
            close_date = datetime.strptime(close_date, "%Y-%m-%d")

        if close_value > 0 and deal_stage == "Won":
            total_sales += 1
            total_revenue += close_value
            sales_prices.append(close_value)
            if engage_date and close_date:
                time_to_sell.append((close_date - engage_date).days)

            # Compter les ventes par produit
            if product_name not in product_sales:
                product_sales[product_name] = {"count": 0, "revenue": 0}
            product_sales[product_name]["count"] += 1
            product_sales[product_name]["revenue"] += close_value

            # Compter les ventes par secteur
            if sector not in sector_sales:
                sector_sales[sector] = {"count": 0, "revenue": 0}
            sector_sales[sector]["count"] += 1
            sector_sales[sector]["revenue"] += close_value

        # Compter les opportunités
        if deal_stage in opportunities:
            opportunities[deal_stage] += 1

    # Calculer les statistiques
    average_sales_price = sum(sales_prices) / len(sales_prices) if sales_prices else 0
    average_time_to_sell = sum(time_to_sell) / len(time_to_sell) if time_to_sell else 0

    # Top 3 produits
    top_products = sorted(
        product_sales.items(),
        key=lambda x: x[1]["count"],
        reverse=True
    )[:3]
    top_products = [
        {"name": product, "rank": rank + 1, "average_price": product_sales[product]["revenue"] / product_sales[product]["count"]}
        for rank, (product, data) in enumerate(top_products)
    ]

    # Top 3 secteurs
    top_sectors = sorted(
        sector_sales.items(),
        key=lambda x: x[1]["count"],
        reverse=True
    )[:3]
    top_sectors = [
        {"name": sector, "rank": rank + 1, "average_price": sector_sales[sector]["revenue"] / sector_sales[sector]["count"]}
        for rank, (sector, data) in enumerate(top_sectors)
    ]

    # Préparer la réponse
    return {
        "sales_agent": name_agent,
        "total_sales": total_sales,
        "average_sales_price": average_sales_price,
        "top_products": top_products,
        "top_sectors": top_sectors,
        "total_revenue": total_revenue,
        "opportunities": opportunities,
        "average_time_to_sell": average_time_to_sell,
    }


@app.get("/values", response_model=ValueResponse)
def get_values():
    # Préparer les listes uniques
    products = set()
    clients = set()
    sectors = set()
    sellers = set()
    managers = set()
    engage_months_years = set()
    close_months_years = set()

    for record in records:
        fields = record.get("fields", {})
        # Ajouter les éléments aux ensembles
        product = fields.get("product (from product)", [None])[0]
        client = fields.get("account (from account)", [None])[0]
        sector = fields.get("sector (from account)", [None])[0]
        seller = fields.get("sales_agent (from sales_agent)", [None])[0]
        manager = fields.get("manager (from sales_agent)", [None])[0]
        engage_date = fields.get("engage_date", None)
        close_date = fields.get("close_date", None)

        # Ajouter les valeurs aux ensembles correspondants
        if product:
            products.add(product)
        if client:
            clients.add(client)
        if sector:
            sectors.add(sector)
        if seller:
            sellers.add(seller)
        if manager:
            managers.add(manager)

        # Extraire les mois et années pour engage_date
        if engage_date:
            engage_month_year = datetime.strptime(engage_date, "%Y-%m-%d").strftime("%Y-%m")
            engage_months_years.add(engage_month_year)

        # Extraire les mois et années pour close_date
        if close_date:
            close_month_year = datetime.strptime(close_date, "%Y-%m-%d").strftime("%Y-%m")
            close_months_years.add(close_month_year)

    # Convertir les ensembles en listes pour la réponse JSON
    return {
        "products": list(products),
        "clients": list(clients),
        "sectors": list(sectors),
        "sellers": list(sellers),
        "managers": list(managers),
        "engage_months_years": sorted(list(engage_months_years)),  # Tri pour faciliter la lecture
        "close_months_years": sorted(list(close_months_years)),    # Tri pour faciliter la lecture
    }


@app.get("/accounts")
def get_accounts():
    # Préparer les données des clients
    client_revenues = {}
    client_orders = {}
    total_company_revenue = 0  # Revenu global de l'entreprise

    for record in records:
        fields = record.get("fields", {})
        client = fields.get("account (from account)", [None])[0]
        close_value = fields.get("close_value", 0)
        revenue = fields.get("revenue (from account)", [0])[0]  # Extraire la première valeur de la liste

        if client:
            # Ajouter aux revenus totaux
            if client not in client_revenues:
                client_revenues[client] = 0
                client_orders[client] = 0
            client_revenues[client] += close_value
            client_orders[client] += 1

        # Additionner au revenu global de l'entreprise
        total_company_revenue += revenue

    # Calcul de la part de chaque client
    client_revenue_shares = {
        client: {
            "percentage_of_total_revenue": f"{round((client_revenues[client] / total_company_revenue) * 100, 2)}%"
            if total_company_revenue > 0 else "N/A"
        }
        for client in client_revenues
    }

    # Calcul du classement des clients par nombre de commandes
    ranked_clients = sorted(client_orders.items(), key=lambda x: x[1], reverse=True)

    # Préparer la réponse
    return {
        "client_revenues": client_revenues,
        "ranked_clients": [
            {"client": client, "orders": orders, "rank": rank + 1}
            for rank, (client, orders) in enumerate(ranked_clients)
        ],
        "client_revenue_shares": client_revenue_shares,
        "total_company_revenue": round(total_company_revenue, 2),
    }
