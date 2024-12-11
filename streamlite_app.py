import streamlit as st
import requests

# Configuration de l'API FastAPI
API_URL = "http://127.0.0.1:8000"  # Remplacez par l'URL où l'API est déployée

st.title("Interface Streamlit pour votre API FastAPI")

# Section pour afficher les données globales des produits
st.header("Produits - Données globales")
if st.button("Charger les données des produits"):
    response = requests.get(f"{API_URL}/products")
    if response.status_code == 200:
        data = response.json()
        st.json(data)
    else:
        st.error(f"Erreur de connexion à l'API : {response.status_code}")

# Section pour consulter les détails d'un produit spécifique
st.header("Détails d'un produit spécifique")
product_name = st.text_input("Entrez le nom du produit")

if st.button("Afficher les détails du produit"):
    if product_name:
        response = requests.get(f"{API_URL}/products/{product_name}")
        if response.status_code == 200:
            product_details = response.json()
            st.json(product_details)
        else:
            st.error(f"Produit introuvable ou erreur : {response.status_code}")
    else:
        st.warning("Veuillez entrer un nom de produit.")

# Section pour obtenir des informations supplémentaires (si besoin)
# Vous pouvez étendre cette section en fonction des points de terminaison supplémentaires
