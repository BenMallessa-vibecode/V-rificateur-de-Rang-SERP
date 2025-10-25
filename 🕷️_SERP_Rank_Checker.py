import streamlit as st
import pandas as pd
import requests
import pycountry
import geonamescache
from utils import sanitize_domain
from message import ABOUT_TEXT, APP_INTRO_TEXT, API_WARNING, KEYWORD_ERROR, DOMAIN_ERROR  

gc = geonamescache.GeonamesCache()
countries = [country.name for country in pycountry.countries]
languages = [f"{lang.alpha_2} - {lang.name}" for lang in pycountry.languages if hasattr(lang, 'alpha_2')]

# Récupérer toutes les villes de geonamescache (sans filtre pays)
ALL_CITIES = sorted([city["name"] for city in gc.get_cities().values()])

@st.cache_data(ttl=18000)
def get_serp_results(api_key, keyword, location, lang, site):
    url = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }

    payload = {
        "q": keyword,
        "location": location,
        "gl": lang,
        "hl": lang,
        "num": 100  
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 403:
        st.error("🚨 Clé API invalide ! Veuillez vérifier votre clé API Serper.dev.")
        st.stop()

    if response.status_code != 200:
        st.error(f"❌ Erreur : {response.status_code} - {response.text}")
        st.stop()

    result = response.json()
    filtered_result = next((item for item in result.get("organic", []) if site in item.get("link", "")), None)

    return {
        "Keyword": keyword,
        "Position": filtered_result["position"] if filtered_result else "Not Found",
        "URL": filtered_result["link"] if filtered_result else "N/A",
        "Top_100": result.get("organic", [])  
    }

def fetch_top_10(results):
    return results["Top_100"][:10]  

# Streamlit UI
st.set_page_config(page_title="SERP Rank Checker", layout="wide")

# Sidebar pour les paramètres API
st.sidebar.header("🔑 Paramètres API")
api_key = st.sidebar.text_input("Entrez votre clé API Serper.dev", type="password")
st.sidebar.write("**[Obtenez votre clé API sur Serper.dev](https://serper.dev/)**")

st.sidebar.markdown("---")
st.sidebar.markdown(ABOUT_TEXT) 

st.sidebar.markdown("---")
st.sidebar.link_button("🧙‍♂️ Connect with Me", "http://syahid.super.site/", use_container_width=True)

# Form input
st.title(APP_INTRO_TEXT)

with st.form("serp_form"):
    keywords = st.text_area("Mots-clés (un par ligne)", placeholder="Entrez les mots-clés ici...")

    selected_country = st.selectbox("Sélectionnez le Pays", options=countries, index=countries.index("France"))

    default_city = "Paris"
    city_index = ALL_CITIES.index(default_city) if default_city in ALL_CITIES else 0
    selected_city = st.selectbox("Sélectionnez la Ville (Optionnel)", options=ALL_CITIES, index=city_index)

    lang = st.selectbox("Sélectionnez la Langue", options=languages, index=languages.index("fr - French"))
    site = sanitize_domain(st.text_input("Domaine (ex. example.com)", placeholder="Entrez le domaine à suivre"))

    submitted = st.form_submit_button("Vérifier les Classements")

if submitted:
    if not api_key:
        st.error(API_WARNING)
        st.stop()  

    keyword_list = [kw.strip() for kw in keywords.split("\n") if kw.strip()]
    
    if not keyword_list:
        st.error(KEYWORD_ERROR)
    elif not site:
        st.error(DOMAIN_ERROR)
    else:
        st.info(f"Récupération des classements SERP pour {len(keyword_list)} mots-clés...")

        results = []
        top_10_results = {}

        # Format de localisation : "Ville, Pays" si ville sélectionnée, sinon seulement pays
        full_location = f"{selected_city}, {selected_country}"

        for keyword in keyword_list:
            result = get_serp_results(api_key, keyword, full_location, lang.split(" - ")[0], site)
            results.append(result)
            top_10_results[keyword] = fetch_top_10(result)

        df = pd.DataFrame(results).drop(columns=["Top_100"])

        # Créer des onglets pour les résultats
        tab1, tab2 = st.tabs(["📊 Tableau SERP", "🔍 Top 10 Résultats"])

        with tab1:
            st.write("### 📊 Résultats SERP")
            st.dataframe(df, use_container_width=True)

            # Opsi Download CSV
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Télécharger CSV",
                data=csv,
                file_name="serp_results.csv",
                mime="text/csv"
            )

        with tab2:
            st.write("### 🔍 Top 10 Résultats de Recherche pour Chaque Mot-Clé")

            for keyword, results in top_10_results.items():
                with st.expander(f"{keyword}"):
                    for idx, entry in enumerate(results, start=1):
                        title = entry.get("title", "No Title")
                        link = entry.get("link", "No Link")
                        snippet = entry.get("snippet", "No Snippet Available")
                        date = entry.get("date", "Unknown Date")

                        st.write(f"**{idx}. {title}**")  
                        st.markdown(f"🔗 [{link}]({link})")  
                        st.write(f"📅 {date} | {snippet}")  
                        st.write("---")  
