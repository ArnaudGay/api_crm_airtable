import streamlit as st
import pandas as pd
import requests
import altair as alt
import plotly.express as px
from datetime import datetime
import locale


locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")

st.set_page_config(layout="wide")

def fetch_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur lors de l'appel à l'API : {e}")
        return None

# Page d'accueil
def page_accueil():
    st.title("Accueil")
    st.write("Bienvenue sur votre dashboard.")
    st.image("./ressources/logo.png", caption="HeticElectronics")

# Page Products
def page_products():
    st.title("Dashboard des Produits")
    base_url = "http://127.0.0.1:8000"

    # Fetch data from /products API
    st.header("Statistiques générales des produits")
    product_data = fetch_data(f"{base_url}/products")
    values_data = fetch_data(f'{base_url}/values')

    if product_data:
        # Display metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("Revenu total", f"{product_data['total_revenue']:,}".replace(',', ' ') + " €")
        col2.metric("Produits vendus", f"{product_data['sold_products_count']:,}".replace(',', ' '))
        col3.metric("Prix de vente moyen", f"{round(product_data['average_sales_price'], 2):,.2f}".replace(',', ' ') + " €")



        # Altair: Revenus par secteur
        st.subheader("Revenus par secteur")
        sector_revenue = product_data["sector_revenue"]
        if sector_revenue:
            df_sector_revenue = pd.DataFrame(
                sector_revenue.items(), columns=["Secteur", "Revenus"]
            )
            chart = (
                alt.Chart(df_sector_revenue)
                .mark_bar()
                .encode(
                    x=alt.X("Secteur", sort="ascending"),  # Tri des secteurs par ordre alphabétique
                    y="Revenus",
                    color="Secteur"
                )
                .properties(title="Revenus par secteur")
            )
            st.altair_chart(chart, use_container_width=True)


    # Les produits les plus vendus par secteur
    st.subheader("Produits les plus vendus par secteur")

    # Ajout d'une sélection dynamique pour choisir le secteur
    selected_sector = st.selectbox("Choisissez un secteur", sorted(values_data['sectors']))

    top_products_by_sector = product_data['top_products_by_sector']
    # Affichage du graphique pour le secteur sélectionné
    if selected_sector and selected_sector in top_products_by_sector:
        products = top_products_by_sector[selected_sector]
        if products:
            df_products = pd.DataFrame(products)
            fig = (
                alt.Chart(df_products)
                .mark_bar()
                .encode(
                    x=alt.X("product", sort=None),
                    y="sales",
                    color="product"
                )
                .properties(title=f"Produits les plus vendus ({selected_sector})")
            )
            st.altair_chart(fig, use_container_width=True)
        else:
            st.write(f"Aucun produit disponible pour le secteur : {selected_sector}")
    else:
        st.write("Aucune donnée disponible pour le secteur sélectionné.")

    # Fetch data for a specific product
    st.header("Détails par produit")
    product_name = st.selectbox("Entrez le nom d'un produit :", sorted(values_data['products']))

    if product_name:
        product_detail = fetch_data(f"{base_url}/products/{product_name}")

        if product_detail:
            # Display metrics
            st.write(f"**Produit : {product_detail['product_name']}**")
            col1, col2, col3 = st.columns(3)
            col1.metric("Revenu total", f"{product_detail['total_revenue']:,}".replace(',', ' ') + " €")
            col2.metric("Ventes totales", f"{product_detail['total_sold']:,}".replace(',', ' '))
            col3.metric("Prix moyen", f"{round(product_detail['average_sales_price'], 2):,.2f}".replace(',', ' ') + " €")


            # Altair: Statistiques mensuelles et Top clients côte à côte
            st.subheader("Statistiques mensuelles et Top clients")
            monthly_stats = product_detail["monthly_stats"]
            if monthly_stats:
                col1, col2 = st.columns([1, 1])

                # Statistiques mensuelles
                with col1:
                    df_monthly = pd.DataFrame.from_dict(monthly_stats, orient="index")
                    df_monthly["Mois"] = df_monthly.index
                    df_monthly = df_monthly.reset_index(drop=True)
                    df_monthly["Revenus"] = df_monthly["total_revenue"]

                    chart = (
                        alt.Chart(df_monthly)
                        .mark_line(point=True)
                        .encode(
                            x="Mois:T",
                            y="Revenus",
                            tooltip=["Mois", "Revenus"]
                        )
                        .properties(title="Revenus mensuels")
                    )
                    st.altair_chart(chart, use_container_width=True)

                # Sélecteurs et graphique des Top clients
                with col2:
                    # Trier les mois et les années dans l'ordre d'arrivée
                    sorted_dates = sorted(monthly_stats.keys(), key=lambda x: datetime.strptime(x, "%Y-%m"))
                    available_months = [datetime.strptime(date, "%Y-%m").strftime("%B").capitalize() for date in sorted_dates]
                    available_years = sorted({date.split("-")[0] for date in sorted_dates})

                    col1, col2 = st.columns([1, 1])
                    selected_year = col1.selectbox("Choisissez une année", available_years)
                    filtered_months = [
                        datetime.strptime(date, "%Y-%m").strftime("%B").capitalize()
                        for date in sorted_dates
                        if date.startswith(selected_year)
                    ]
                    selected_month = col2.selectbox("Choisissez un mois", filtered_months)

                    selected_date = f"{selected_year}-{datetime.strptime(selected_month, '%B').month:02d}"

                    if selected_date in monthly_stats:
                        stats = monthly_stats[selected_date]
                        df_clients = pd.DataFrame(
                            stats["clients"].items(), columns=["Client", "Nombre de ventes"]
                        )
                        if not df_clients.empty:
                            fig = px.pie(
                                df_clients,
                                names="Client",
                                values="Nombre de ventes",
                                title=f"Clients pour le mois de {selected_month} {selected_year}",
                                hole=0.4,
                                color_discrete_sequence=px.colors.sequential.RdBu
                            )
                            st.plotly_chart(fig)
                        else:
                            st.write("Aucun client pour cette période.")
                    else:
                        st.write("Aucune donnée pour la période sélectionnée.")

# Page Commerciaux
def page_sales_agent():
    st.title("Commerciaux")
    st.write("Analyse des performances des commerciaux.")

    base_url = "http://127.0.0.1:8000"

    # Fetch data from /sales_agent API
    sales_agents_data = fetch_data(f"{base_url}/sales_agents")

    if sales_agents_data:
        # Graphique : Revenus totaux par agent
        st.subheader("Revenus totaux par commerciaux")
        performance_data = sales_agents_data["sales_agents_performance"]
        df_revenue = pd.DataFrame({
            "Agent": performance_data.keys(),
            "Revenu total": [data["total_revenue"] for data in performance_data.values()]
        })

        # Trier les données par "Revenu total" dans l'ordre croissant
        df_revenue = df_revenue.sort_values(by="Revenu total", ascending=False)

        fig_revenue = px.bar(
            df_revenue,
            x="Revenu total",
            y="Agent",
            orientation="h",
            title="Revenu total par commerciaux",
            labels={"Agent": "Commerciaux", "Revenu total": "Revenu (€)"},
            text="Revenu total",
            color="Revenu total",
            color_continuous_scale=px.colors.sequential.Plasma
        )
        st.plotly_chart(fig_revenue)


        # Graphique : Nombre de ventes par secteur
        st.subheader("Nombre de ventes par secteur")
        sectors = []
        counts = []
        for agent, data in performance_data.items():
            for sector, count in data["sectors"].items():
                sectors.append(sector)
                counts.append(count)

        df_sectors = pd.DataFrame({"Secteur": sectors, "Nombre de ventes": counts})
        fig_sectors = px.sunburst(
            df_sectors,
            path=["Secteur"],
            values="Nombre de ventes",
            title="Répartition des ventes par secteur",
            color="Nombre de ventes",
            color_continuous_scale=px.colors.sequential.Agsunset
        )
        st.plotly_chart(fig_sectors)

        # Sélecteur pour afficher les détails d'un agent spécifique
        st.subheader("Détails par commericaux")
        selected_agent = st.selectbox("Choisissez un commercial", sorted(performance_data.keys()))

        if selected_agent:
            agent_details = fetch_data(f"{base_url}/sales_agents/{selected_agent}")

            if agent_details:
                st.write(f"**Commercial : {agent_details['sales_agent']}**")

                # Afficher les métriques
                col1, col2, col3 = st.columns(3)
                col1.metric("Total des ventes", f"{agent_details['total_sales']:,}".replace(',', ' '))
                col2.metric("Prix moyen", f"{round(agent_details['average_sales_price'], 2):,.2f}".replace(',', ' ') + " €")
                col3.metric("Revenu total", f"{agent_details['total_revenue']:,}".replace(',', ' ') + " €")


                # Graphique : Opportunités
                st.subheader("Opportunités")
                df_opportunities = pd.DataFrame(
                    agent_details["opportunities"].items(),
                    columns=["Statut", "Nombre"]
                )
                fig_opportunities = px.funnel(
                    df_opportunities,
                    x="Nombre",
                    y="Statut",
                    title="Répartition des opportunités",
                    color="Statut",
                    color_discrete_sequence=px.colors.qualitative.Set1
                )
                st.plotly_chart(fig_opportunities)

                # Graphique : Produits principaux
                st.subheader("Produits principaux")
                df_products = pd.DataFrame(agent_details["top_products"])

                # Trier les données par "average_price" dans l'ordre croissant
                df_products = df_products.sort_values(by="average_price", ascending=True)

                fig_products = px.scatter(
                    df_products,
                    x="name",
                    y="average_price",
                    size="average_price",
                    size_max=50,  # Taille maximale des points
                    title="Produits principaux par prix moyen",
                    labels={"name": "Produit", "average_price": "Prix moyen (€)"},
                    color="average_price",
                    color_continuous_scale=px.colors.sequential.Viridis
                )
                st.plotly_chart(fig_products)


                # Graphique : Secteurs principaux
                st.subheader("Secteurs principaux")
                df_sectors = pd.DataFrame(agent_details["top_sectors"])
                fig_top_sectors = px.treemap(
                    df_sectors,
                    path=["name"],
                    values="average_price",
                    title="Secteurs principaux par prix moyen",
                    color="average_price",
                    color_continuous_scale=px.colors.sequential.Blues
                )
                st.plotly_chart(fig_top_sectors)

# Menu de navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Aller à :", ("Accueil", "Produits", "Commerciaux"))

# Quel page afficher
if page == "Accueil":
    page_accueil()
elif page == "Produits":
    page_products()
elif page == "Commerciaux":
    page_sales_agent()
