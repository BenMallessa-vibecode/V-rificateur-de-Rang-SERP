import streamlit as st
import requests
import pandas as pd
import re
from collections import Counter

st.set_page_config(page_title="🏆 Analyse de Mots-Clés Dorés", layout="wide")

st.title("🏆 Analyse de Mots-Clés Dorés")
st.markdown("""
Découvrez des mots-clés à fort potentiel (dorés) basés sur des recherches Google réelles.  
Entrez un mot-clé de base pour obtenir des suggestions de mots-clés connexes, organisées en clusters par intention (informationnelle, commerciale, etc.), avec un focus sur la longue traîne et l'intention commerciale.
""")

# Sidebar pour la clé API
st.sidebar.header("🔑 Paramètres API")
api_key = st.sidebar.text_input("Entrez votre clé API Serper.dev", type="password")
st.sidebar.write("**[Obtenez votre clé API sur Serper.dev](https://serper.dev/)**")

if not api_key:
    st.warning("🚨 Veuillez entrer votre clé API dans la barre latérale pour utiliser cette page.")
    st.stop()

# Formulaire d'entrée
with st.form("keyword_form"):
    seed_keyword = st.text_input("Mot-clé de base (ex. : 'marketing digital')", placeholder="Entrez un mot-clé de départ...")
    num_results = st.slider("Nombre de résultats à analyser", min_value=10, max_value=100, value=100, step=10)
    country = st.selectbox("Pays", options=["France", "États-Unis", "Royaume-Uni"], index=0)
    language = st.selectbox("Langue", options=["fr", "en", "es"], index=0)
    focus_intent = st.selectbox("Focus Intention", ["Toutes", "Commerciale", "Informationnelle"], index=0)
    
    submitted = st.form_submit_button("Analyser les Mots-Clés Dorés")

if submitted and seed_keyword:
    if not seed_keyword.strip():
        st.error("❌ Veuillez entrer un mot-clé de base.")
        st.stop()
    
    st.info(f"Analyse en cours pour '{seed_keyword}' dans {country} ({language})... Focus: {focus_intent}")
    
    # Fonction pour obtenir les résultats SERP pour une requête
    @st.cache_data(ttl=1800)
    def get_serp_data(api_key, query, num, gl, hl):
        url = "https://google.serper.dev/search"
        headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "q": query,
            "num": num,
            "gl": gl.lower(),
            "hl": hl
        }
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code != 200:
            st.error(f"❌ Erreur API pour '{query}' : {response.status_code}")
            return {}
        
        return response.json()

    # Fonction de calcul de score d'intention
    def calculate_intent_score(keyword, serp_data):
        score = {"informationnelle": 0, "commerciale": 0, "navigationnelle": 0, "locale": 0}
        
        # Critères mots-clés (50% poids)
        kw_lower = keyword.lower()
        if re.search(r"(comment|guide|définir|expliquer|quoi|qui|où|quand|pourquoi)", kw_lower):
            score["informationnelle"] += 30
        if re.search(r"(acheter|prix|comparer|meilleur|top|avis|promo|offre|commander|réservation|devis|tarif|coût|abordable|pas cher|2024|en ligne|meilleure offre|comparatif|acheter maintenant|promo limitée|réduction|bon plan|test et avis|acheter sur Amazon|prix comparé|meilleur rapport qualité prix|acheter d'occasion|location|abonnement|essai gratuit|code promo|black friday|soldes)", kw_lower):
            score["commerciale"] += 45  # Priorité haute avec patterns étendus
        if re.search(r"(site officiel|connexion|compte)", kw_lower):
            score["navigationnelle"] += 35
        if re.search(r"(près de moi|paris|lyon|france|local)", kw_lower):
            score["locale"] += 30
        
        # Longue traîne bonus
        if len(kw_lower.split()) > 4:
            for intent in score:
                score[intent] += 25  # Augmenté pour focus longue traîne
        
        # Critères SERP features (30% poids)
        ads_value = serp_data.get("ads", 0)
        if isinstance(ads_value, (list, tuple)):
            ads = len(ads_value)
        else:
            ads = ads_value  # Float ou int pour moyenne
        
        if ads > 2:
            score["commerciale"] += 35
        paa_value = serp_data.get("peopleAlsoAsk", 0)
        if isinstance(paa_value, (list, tuple)):
            paa = len(paa_value)
        else:
            paa = paa_value
        
        if paa > 3:
            score["informationnelle"] += 25
        if "knowledgeGraph" in serp_data and serp_data["knowledgeGraph"].get("type") == "Organization":
            score["navigationnelle"] += 20
        if "localResults" in serp_data:
            score["locale"] += 25
        if "shoppingResults" in serp_data:
            score["commerciale"] += 30
        
        # Critères snippets (20% poids)
        organic = serp_data.get("organic", [])[:5]
        for item in organic:
            snippet = item.get("snippet", "").lower()
            if re.search(r"(étapes|conseils|explication)", snippet):
                score["informationnelle"] += 15
            if re.search(r"(commander|acheter en ligne|prix à partir de|comparatif|avis clients|disponible en stock|livraison gratuite|retour gratuit|garantie|financement|leasing|test gratuit|démo|inscription newsletter pour promo)", snippet):
                score["commerciale"] += 25
        
        # Intention dominante
        dominant_intent = max(score, key=score.get)
        total_score = score[dominant_intent]
        
        return dominant_intent, total_score, score

    # Fonction de clustering
    def create_clusters(keywords_with_intent, seed_keyword, max_clusters=8):
        clusters = {}
        seed_words = set(seed_keyword.lower().split())
        
        for kw_data in keywords_with_intent:
            kw = kw_data["Mot-Clé"].lower()
            intent = kw_data["Intention"]
            common_words = set(kw.split()) & seed_words
            if len(common_words) > 1:
                cluster_key = f"{intent}_{'_'.join(sorted(common_words))[:20]}"
            else:
                cluster_key = f"{intent}_général"
            
            if cluster_key not in clusters:
                clusters[cluster_key] = {"intention": intent, "keywords": [], "theme": cluster_key.split("_", 1)[1] if "_" in cluster_key else "Général"}
            clusters[cluster_key]["keywords"].append(kw_data)
            
            # Limiter à 15 par cluster
            if len(clusters[cluster_key]["keywords"]) > 15:
                clusters[cluster_key]["keywords"] = clusters[cluster_key]["keywords"][:15]
        
        # Limiter et trier par taille
        sorted_clusters = sorted(clusters.values(), key=lambda c: len(c["keywords"]), reverse=True)[:max_clusters]
        return sorted_clusters

    # Fonction principale pour extraire les mots-clés (mise à jour)
    @st.cache_data(ttl=1800)
    def get_related_keywords(api_key, seed_keyword, num, gl, hl, focus_intent):
        # Variations adaptées au focus
        base_variations = [
            "", "meilleurs ", "top ", "guide ", "guide complet ", "tutoriel ", "comment ", "conseils ", "astuces ", "meilleures pratiques "
        ]
        commercial_variations = ["acheter ", "prix ", "comparer ", "promo ", "offre ", "meilleur rapport qualité prix "]
        
        variations = base_variations
        if focus_intent == "Commerciale":
            variations = commercial_variations[:8]  # Limiter pour API
        elif focus_intent == "Informationnelle":
            variations = ["guide ", "comment ", "tutoriel ", "conseils ", "expliquer ", "débutant ", "basique ", "étapes "]
        else:
            variations += commercial_variations[:4]  # Mix pour "Toutes"
        
        all_keywords = set()
        all_serp_data = []  # Pour agrégation moyenne
        
        for variation in variations[:10]:  # Limite API
            query = variation + seed_keyword
            result = get_serp_data(api_key, query, num, gl, hl)
            if not result:
                continue
            all_serp_data.append(result)
            
            organic = result.get("organic", [])
            people_also_ask = result.get("peopleAlsoAsk", [])
            related_searches = result.get("search_information", {}).get("relatedSearches", []) or []
            
            # Extraire de People Also Ask
            for paa in people_also_ask:
                kw = paa.get("query", "").strip()
                if kw and len(kw) > 3:
                    all_keywords.add(kw.lower())
            
            # Extraire de Related Searches
            for rs in related_searches:
                kw = rs.get("query", "").strip()
                if kw and len(kw) > 3:
                    all_keywords.add(kw.lower())
            
            # Extraire de titres et snippets
            for item in organic[:20]:
                title = item.get("title", "").lower()
                snippet = item.get("snippet", "").lower()
                
                if seed_keyword.lower() in title:
                    all_keywords.add(title.strip())
                
                if seed_keyword.lower() in snippet:
                    snippet_words = snippet.split()[:5]
                    if snippet_words:
                        all_keywords.add(" ".join(snippet_words).strip())
                
                # Mots-clés individuels
                stop_words = {"le", "la", "de", "du", "des", "un", "une", "et", "ou", "dans", "sur", "pour", "avec", "par", "les", "est", "sont"}
                for text in [title, snippet]:
                    words = [w for w in text.split() if len(w) > 3 and w not in stop_words and not w.isdigit()]
                    for word in words[:5]:
                        all_keywords.add(word)
        
        # Nettoyer et limiter
        unique_keywords = list(all_keywords)[:100]
        
        # Agréger serp_data moyenne pour scoring
        avg_serp = {}
        if all_serp_data:
            avg_ads = sum(len(s.get("ads", [])) for s in all_serp_data) / len(all_serp_data)
            avg_serp["ads"] = avg_ads
            # Ajouter autres agrégations si besoin
        
        keywords_with_intent = []
        for kw in unique_keywords:
            intent, score, details = calculate_intent_score(kw, avg_serp)
            if score > 50:
                keywords_with_intent.append({
                    "Mot-Clé": kw,
                    "Intention": intent,
                    "Score": score,
                    "Longue Traîne": "Oui" if len(kw.split()) > 4 else "Non",
                    "Type": "Suggestion Avancée"
                })
        
        # Créer clusters
        clusters = create_clusters(keywords_with_intent, seed_keyword)
        
        return clusters

    # Mapping des pays aux codes
    country_codes = {"France": "fr", "États-Unis": "us", "Royaume-Uni": "gb"}
    gl_code = country_codes.get(country, "fr")
    
    clusters = get_related_keywords(api_key, seed_keyword, num_results, gl_code, language, focus_intent)
    
    if clusters:
        # Préparer DataFrame global pour export
        all_kw_data = []
        for cluster in clusters:
            for kw in cluster["keywords"]:
                kw["Cluster"] = cluster["theme"]
                all_kw_data.append(kw)
        df_global = pd.DataFrame(all_kw_data)
        
        # Distribution des intentions pour visualisation
        intent_counts = df_global["Intention"].value_counts()
        st.subheader("📊 Distribution des Intentions")
        st.bar_chart(intent_counts)
        
        # Tabs par intention
        intent_tabs = {}
        for cluster in clusters:
            intent = cluster["intention"]
            if intent not in intent_tabs:
                intent_tabs[intent] = []
            intent_tabs[intent].append(cluster)
        
        for intent, intent_clusters in intent_tabs.items():
            with st.expander(f"🔍 Clusters {intent.capitalize()} ({sum(len(c['keywords']) for c in intent_clusters)} mots-clés)"):
                for cluster in intent_clusters:
                    st.write(f"**Thème : {cluster['theme']}**")
                    cluster_df = pd.DataFrame(cluster["keywords"])
                    st.dataframe(cluster_df[["Mot-Clé", "Score", "Longue Traîne"]], use_container_width=True)
        
        # Conseils mis à jour
        st.subheader("💡 Conseils pour l'Analyse")
        st.markdown("""
        - **Potentiel SEO** : Priorisez les mots-clés avec un volume de recherche élevé et une concurrence faible (utilisez des outils comme Google Keyword Planner pour le volume).
        - **Longue Traîne** : Les mots-clés plus longs (ex. : "meilleurs outils marketing digital 2024") convertissent mieux.
        - **Intention Utilisateur** : Analysez les extraits pour comprendre l'intention (informationnelle, transactionnelle). Focus commerciale pour les conversions.
        - **Intention Commerciale** : Ces clusters sont idéaux pour des campagnes ads ou pages produits ; priorisez ceux avec 'promo' ou 'prix' pour maximiser les conversions.
        - **Prochaines Étapes** : Testez ces mots-clés dans le vérificateur SERP principal pour voir les classements.
        """)
        
        # Téléchargement CSV global
        csv = df_global.to_csv(index=False, encoding="utf-8").encode("utf-8")
        st.download_button(
            label="📥 Télécharger la Liste CSV Complète",
            data=csv,
            file_name=f"mots_cles_dores_clusters_{seed_keyword.replace(' ', '_')}.csv",
            mime="text/csv"
        )
        
        st.success(f"Analyse terminée ! {len(all_kw_data)} mots-clés organisés en {len(clusters)} clusters.")
    else:
        st.warning("Aucun mot-clé connexe trouvé. Essayez un mot-clé plus général.")