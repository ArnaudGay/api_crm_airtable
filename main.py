from fastapi import FastAPI
from airtable import Airtable

app = FastAPI()

base_key = "app7ChxNjx0ABZ0ez"
api_key = "patz6IUHqyzznnYVc.73d08d06e03c9cdd59e54d885d22aac9634d111a4e3f51ac4cb3b273a744ab8b"
BASE_ID = "appMdrgR2GRW3nmea"

clients_table = Airtable(base_key, "Clients", api_key)
ventes_table = Airtable(base_key, "Ventes", api_key)
produits_table = Airtable(base_key, "Produits", api_key)
@app.get("/kpi/ventes-totales")
async def get_ventes_totales():
    ventes = ventes_table.get_all()
    total = sum(record['fields'].get('Montant', 0) for record in ventes)
    return {"ventes_totales": total}

@app.get("/kpi/taux-conversion")
async def get_taux_conversion():
    clients = clients_table.get_all()
    ventes = ventes_table.get_all()
    taux = len(ventes) / len(clients) if len(clients) > 0 else 0
    return {"taux_conversion": taux}
    from datetime import datetime

@app.get("/rapports/ventes")
async def get_rapport_ventes(debut: str = None, fin: str = None, produit: str = None, client: str = None):
    ventes = ventes_table.get_all()
    
    if debut:
        debut = datetime.strptime(debut, "%Y-%m-%d")
        ventes = [v for v in ventes if datetime.strptime(v['fields']['Date'], "%Y-%m-%d") >= debut]
    
    if fin:
        fin = datetime.strptime(fin, "%Y-%m-%d")
        ventes = [v for v in ventes if datetime.strptime(v['fields']['Date'], "%Y-%m-%d") <= fin]
    
    if produit:
        ventes = [v for v in ventes if produit in v['fields'].get('Produit', [])]
    
    if client:
        ventes = [v for v in ventes if client in v['fields'].get('Client', [])]
    
    return {"ventes": ventes}
