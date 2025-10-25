import streamlit as st
import requests
import pandas as pd
import json

st.set_page_config(page_title="🗺️ Google Maps", layout="wide")

st.title("🗺️ Google Maps")
st.write("Trouvez des lieux basés sur une requête et affichez les résultats dans un tableau.")

api_key = st.sidebar.text_input("Entrez votre clé API Serper.dev", type="password")
st.sidebar.write("🔗 [Obtenez votre clé API ici](https://serper.dev)")

query = st.text_input("🔍 Rechercher un Lieu", placeholder="Exemple: tourisme à Paris, café à Lyon")

if st.button("Rechercher Maintenant"):
    if not api_key:
        st.error("🚨 Entrez d'abord la clé API !")
        st.stop()
    if not query:
        st.error("🚨 Entrez une requête de recherche !")
        st.stop()

    url = "https://google.serper.dev/maps"
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }
    payload = {"q": query}

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code != 200:
        st.error(f"Échec de l'obtention des résultats. Code: {response.status_code}")
        st.stop()

    data = response.json()
    places = data.get("places", [])
    center_ll = data.get("ll", "Non disponible")

    if not places:
        st.warning("Aucun lieu trouvé.")
    else:
        st.success(f"{len(places)} lieux trouvés. Position centrale de la carte: `{center_ll}`")

        # Extraction des données en liste de dictionnaires
        rows = []
        for p in places:
            rows.append({
                "Position": p.get("position"),
                "Nom": p.get("title"),
                "Adresse": p.get("address"),
                "Latitude": p.get("latitude"),
                "Longitude": p.get("longitude"),
                "Note": p.get("rating"),
                "Nombre de Notes": p.get("ratingCount"),
                "Type": p.get("type"),
                "Tous les Types": ", ".join(p.get("types", [])),
                "Horaires d'Ouverture": json.dumps(p.get("openingHours", {}), ensure_ascii=False),
                "Miniature": p.get("thumbnailUrl"),
                "CID": p.get("cid"),
                "FID": p.get("fid"),
                "ID du Lieu": p.get("placeId")
            })

        df = pd.DataFrame(rows)

        st.dataframe(df, use_container_width=True)

        # Bouton de téléchargement CSV
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Télécharger CSV",
            data=csv,
            file_name="lieux_maps.csv",
            mime="text/csv"
        )
