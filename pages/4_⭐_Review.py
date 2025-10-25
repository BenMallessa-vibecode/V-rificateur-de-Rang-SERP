import streamlit as st
import requests
import pandas as pd
import time

st.set_page_config(page_title="📝 Avis Google en Masse par CID", layout="wide")
st.title("📝 Avis Google en Masse par CID")

st.sidebar.header("🔑 Paramètres API")
api_key = st.sidebar.text_input("Entrez votre clé API Serper.dev", type="password")
st.sidebar.write("🔗 [Obtenez votre clé API ici](https://serper.dev)")

# Formulaire d'entrée
cids_text = st.text_area("🆔 Entrez la Liste des CID (1 par ligne)", placeholder="3075219648616366458\n1234567890123456789")
gl = st.selectbox("🌍 Code Pays (gl)", ["fr", "us", "gb"], index=0)
hl = st.selectbox("🗣️ Code Langue (hl)", ["fr", "en"], index=0)

if st.button("Récupérer Tous les Avis"):
    if not api_key:
        st.error("🚨 Entrez d'abord la clé API !")
        st.stop()
    if not cids_text.strip():
        st.error("🚨 Entrez au moins 1 CID !")
        st.stop()

    cid_list = [cid.strip() for cid in cids_text.splitlines() if cid.strip()]
    all_reviews = []

    progress = st.progress(0, text="Récupération des avis...")

    for i, cid in enumerate(cid_list, start=1):
        url = "https://google.serper.dev/reviews"
        headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "cid": cid,
            "gl": gl,
            "hl": hl
        }

        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 200:
            reviews = response.json().get("reviews", [])[:5]
            for r in reviews:
                user = r.get("user", {})
                response_owner = r.get("response", {})
                media = r.get("media", [])

                all_reviews.append({
                    "CID": cid,
                    "Nom Utilisateur": user.get("name"),
                    "Lien Utilisateur": user.get("link"),
                    "Avis Utilisateur": user.get("reviews"),
                    "Photos Utilisateur": user.get("photos"),
                    "Miniature Utilisateur": user.get("thumbnail"),
                    "Extrait d'Avis": r.get("snippet"),
                    "Note": r.get("rating"),
                    "Date": r.get("date"),
                    "Date ISO": r.get("isoDate"),
                    "Réponse Propriétaire": response_owner.get("snippet"),
                    "Date Réponse Propriétaire": response_owner.get("date"),
                    "Nombre de Médias": len(media),
                    "ID Avis": r.get("id")
                })
        else:
            st.warning(f"❌ Échec de la récupération des avis pour le CID {cid} : {response.status_code}")
        
        # Optionnel : pause pour éviter les limites de taux
        time.sleep(1)

        progress.progress(i / len(cid_list), text=f"{i} sur {len(cid_list)} CID traités")

    if not all_reviews:
        st.warning("Aucun avis trouvé pour tous les CID.")
    else:
        df = pd.DataFrame(all_reviews)
        st.success(f"Récupération réussie de {len(df)} avis pour {len(cid_list)} CID.")
        st.dataframe(df, use_container_width=True)

        # Bouton de téléchargement CSV
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Télécharger Tous les Avis (.csv)",
            data=csv,
            file_name="avis_google_en_masse.csv",
            mime="text/csv"
        )
