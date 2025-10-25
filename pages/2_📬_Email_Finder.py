import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
from urllib.parse import urlparse
import time
import dns.resolver
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# Fonction pour obtenir les résultats de recherche avec l'API serper.dev
def get_serp_results(api_key, query, num_results=20, location="US", lang="en"):
    url = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }
    
    gl = location.lower() if len(location) == 2 else location.lower()
    payload = {
        "q": query,
        "num": num_results,
        "location": location,
        "hl": lang,
        "gl": gl
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code != 200:
        st.error(f"❌ Erreur : {response.status_code} - {response.text}")
        return []
    
    result = response.json()
    organic = result.get('organic', [])
    results_list = [{'link': item['link'], 'title': item.get('title', 'N/A'), 'snippet': item.get('snippet', 'N/A')} for item in organic]
    return results_list

# Fonction pour générer dynamiquement des dorks
def build_dorks_for_domain(target_domain, sites=None, location=None, job_titles=None):
    base_dorks = []
    if target_domain:
        base_dorks.append(f'"{target_domain}" (email OR contact OR "@{target_domain}")')
        if location:
            base_dorks.append(f'"{target_domain}" (email OR contact) "{location}"')
        base_dorks.append(f'"{target_domain}" filetype:pdf (email OR contact)')
        base_dorks.append(f'"{target_domain}" filetype:xls (email OR contact)')
        base_dorks.append(f'intitle:"contact" "{target_domain}" email')
        base_dorks.append(f'"{target_domain}" "contact us"')
        if job_titles:
            for title in job_titles:
                base_dorks.append(f'"{title}" "{target_domain}" (email OR contact)')
                if location:
                    base_dorks.append(f'"{title}" "{target_domain}" "{location}" email')
    else:
        if job_titles:
            for title in job_titles:
                base_dorks.append(f'"{title}" (email OR contact OR "@")')
                if location:
                    base_dorks.append(f'"{title}" "{location}" (email OR contact)')
                base_dorks.append(f'intitle:"{title}" contact')
            if location:
                base_dorks.append(f'(Director OR "Head of" OR VP) "{location}" (email OR contact)')
    base_dorks = list(dict.fromkeys(base_dorks))
    dorks = []
    if sites:
        for base in base_dorks:
            for site in sites:
                dork = base + f' site:{site}'
                dorks.append(dork)
    else:
        dorks = base_dorks
    return dorks[:10]

# Fonction pour extraire les emails d'une page web avec améliorations
def extract_emails_from_url(url, target_domain=None):
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    def safe_get(session, url, max_retries=3):
        for attempt in range(max_retries):
            try:
                resp = session.get(url, timeout=10)
                if resp.status_code in [401, 403]:
                    return None  # Skip auth errors
                if resp.status_code == 200:
                    return resp
                # For other errors, retry
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
            except Exception as e:
                print(f"Tentative {attempt+1} échouée pour {url}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
        return None
    
    response = safe_get(session, url)
    status_code = response.status_code if response else None
    if not response:
        return [], "N/A", status_code
    
    soup = BeautifulSoup(response.text, 'html.parser')
    text = soup.get_text()
    
    # Déobfuscation des emails dans le texte avant extraction
    text = re.sub(r'\[at\]', '@', text)
    text = re.sub(r' \[at\] ', '@', text)
    text = re.sub(r' at ', '@', text)
    text = re.sub(r'\(at\)', '@', text)
    text = re.sub(r'\[dot\]', '.', text)
    text = re.sub(r' \[dot\] ', '.', text)
    text = re.sub(r' dot ', '.', text)
    text = re.sub(r'\(dot\)', '.', text)
    
    # Regex améliorée
    email_regex = re.compile(r'[\w\.-]+@[\w\.-]+\.\w{2,7}')
    emails = email_regex.findall(text)
    
    title = soup.title.string if soup.title else "N/A"
    
    # Nettoyage et validation
    processed_emails = clean_email_data(emails, target_domain)
    session.close()
    return processed_emails, title, status_code

# Fonction pour nettoyer et vérifier les emails avec MX et confiance
def clean_email_data(emails, target_domain=None):
    results = []
    for email in emails:
        email = re.sub(r'\[at\]| \(at\) | at ', '@', email)
        email = email.lower().strip('.,;:()[]<>')
        if not email or '@' not in email:
            continue
        
        # Filtrage par domaine cible si spécifié
        if target_domain:
            if not email.endswith(f'@{target_domain}'):
                continue
        
        # Vérification MX
        mx_valid = 'Non'
        try:
            domain = email.split('@')[1]
            dns.resolver.resolve(domain, 'MX')
            mx_valid = 'Oui'
        except Exception:
            pass
        
        results.append({
            'email': email,
            'mx_valid': mx_valid
        })
    
    return results

def get_provenance(dork):
    if 'contactout.com' in dork:
        return "ContactOut"
    elif 'rocketreach.co' in dork:
        return "RocketReach"
    else:
        return "Autre"

# Configuration de l'interface Streamlit
st.set_page_config(page_title="Trouveur d'Emails", layout="wide")

# Barre latérale pour l'entrée de la clé API
st.sidebar.header("🔑 Paramètres API")
api_key = st.sidebar.text_input("Entrez votre clé API Serper.dev", type="password")
st.sidebar.write("**[Obtenez votre clé API sur Serper.dev](https://serper.dev)**")

# Formulaire d'entrée pour la recherche d'emails
st.title("Trouveur d'Emails")
st.markdown("**Avertissement** : Respectez RGPD/CNIL. Usage personnel seulement. Pas de spam. Données publiques. Privilégiez API officielles pour volume. Pas d'énumération SMTP.")
st.subheader("Trouvez des Emails Partout sur Internet")

# Choisir l'option de recherche
search_option = st.selectbox("Choisissez l'option de recherche", ["Recherche Basée sur Domaine", "Recherche Basée sur Service", "Générer Permutations Emails"])

# Sélection des sites
site_options = ["Tous", "ContactOut", "RocketReach"]
site_choice = st.selectbox("Choisissez les sites", site_options)

if site_choice == "Tous":
    selected_sites = ["contactout.com", "rocketreach.co"]
elif site_choice == "ContactOut":
    selected_sites = ["contactout.com"]
else:
    selected_sites = ["rocketreach.co"]

if search_option == "Recherche Basée sur Domaine":
    with st.form("domain_search_form"):
        target_domain = st.text_input("Entrez le domaine cible (ex. : cermati.com)", placeholder="ex. : cermati.com")
        location = st.text_input("Code pays (ex. : FR, US)", placeholder="FR", value="FR")
        language = st.text_input("Code langue (ex. : fr, en)", placeholder="fr", value="fr")
        
        # Ajouter un slider pour le nombre de résultats de recherche
        num_results = st.slider("Nombre de résultats par dork", min_value=1, max_value=20, value=10, step=1)
        
        submitted = st.form_submit_button("Rechercher des Emails Basés sur le Domaine")

elif search_option == "Recherche Basée sur Service":
    with st.form("service_search_form"):
        service_name = st.text_input("Entrez le Nom du Service (ex. : Services SEO Paris)", placeholder="ex. : Services SEO Paris")
        location = st.text_input("Code pays (ex. : FR, US)", placeholder="FR", value="FR")
        language = st.text_input("Code langue (ex. : fr, en)", placeholder="fr", value="fr")
        
        # Ajouter un slider pour le nombre de résultats de recherche
        num_results = st.slider("Nombre de résultats par dork", min_value=1, max_value=20, value=10, step=1)
        
        submitted = st.form_submit_button("Rechercher des Emails Basés sur le Nom du Service")

else:
    with st.form("permutation_form"):
        first_name = st.text_input("Prénom", placeholder="John")
        last_name = st.text_input("Nom de famille", placeholder="Doe")
        domain = st.text_input("Domaine", placeholder="example.com")
        submitted = st.form_submit_button("Générer les Permutations d'Emails")

# Quand le formulaire est soumis
if submitted:
    if search_option == "Générer Permutations Emails":
        if not first_name or not last_name or not domain:
            st.error("❌ Veuillez fournir le prénom, le nom de famille et le domaine.")
            st.stop()

        first_name_clean = first_name.lower().strip()
        last_name_clean = last_name.lower().strip()
        domain_clean = domain.lower().strip().rstrip('.')

        if not domain_clean or '.' not in domain_clean:
            st.error("❌ Domaine invalide.")
            st.stop()

        mx_valid = "Non"
        try:
            dns.resolver.resolve(domain_clean, 'MX')
            mx_valid = "Oui"
        except:
            pass

        if mx_valid == "Non":
            st.error("❌ Le domaine n'a pas de records MX valide. Les permutations ne peuvent pas être générées de manière fiable.")
            st.stop()

        perms = [
            f"{first_name_clean}.{last_name_clean}@{domain_clean}",
            f"{first_name_clean[0]}.{last_name_clean}@{domain_clean}",
            f"{first_name_clean}.{last_name_clean[0]}@{domain_clean}",
            f"{first_name_clean}{last_name_clean}@{domain_clean}",
            f"{first_name_clean}@{domain_clean}",
            f"{last_name_clean}@{domain_clean}"
        ]

        current_time = datetime.now().isoformat()
        all_data = []
        for email in set(perms):
            all_data.append({
                'Emails': email,
                'URL': 'N/A',
                'Domaine': domain_clean,
                'Source Snippet': f"Permutation pour {first_name.title()} {last_name.title()}",
                'Page Title': 'Emails Générés',
                'Date Trouvée': current_time,
                'HTTP Status': 'N/A',
                'Méthode': 'Permutations',
                'Provenance': 'Généré',
                'MX Valide': mx_valid,
                'Confiance': 0.2
            })

        st.write("### Emails Générés :")

        email_df = pd.DataFrame(all_data)
        email_df = email_df.sort_values('Confiance', ascending=False)
        st.dataframe(email_df, width='stretch')

        csv = email_df.to_csv(index=False)
        st.download_button(
            label="📥 Télécharger CSV",
            data=csv,
            file_name="emails_permutations.csv",
            mime="text/csv"
        )
    else:
        if not api_key:
            st.error("🚨 Veuillez entrer votre clé API !")
            st.stop()

        st.info(f"Récupération des résultats de recherche pour la requête...")

        # Obtenir les résultats de recherche de l'API serper.dev en fonction de l'option choisie
        serp_results = []
        if search_option == "Recherche Basée sur Domaine":
            if not target_domain:
                st.error("❌ Veuillez entrer un domaine cible !")
                st.stop()

            # Génération dynamique de dorks
            dorks = build_dorks_for_domain(target_domain, sites=selected_sites, location=location)
            
            for dork in dorks:
                results = get_serp_results(api_key, dork, num_results=num_results, location=location, lang=language)
                for item in results:
                    item['dork'] = dork
                    serp_results.append(item)

        elif search_option == "Recherche Basée sur Service":
            if not service_name:
                st.error("❌ Veuillez entrer un nom de service !")
                st.stop()

            dorks = build_dorks_for_domain(None, sites=selected_sites, location=location, job_titles=[service_name])
            
            for dork in dorks:
                results = get_serp_results(api_key, dork, num_results=num_results, location=location, lang=language)
                for item in results:
                    item['dork'] = dork
                    serp_results.append(item)

        # Déduplication par link
        seen = set()
        unique_serp = []
        for item in serp_results:
            if item['link'] not in seen:
                seen.add(item['link'])
                unique_serp.append(item)

        if not unique_serp:
            st.error("Aucun site web trouvé !")
        else:
            # Scraping parallèle
            progress = st.progress(0)
            status_text = st.empty()
            all_data = []
            failed_urls = []
            total_urls = len(unique_serp)
            completed = 0

            def scrape_worker(item, target_for_scrape):
                return extract_emails_from_url(item['link'], target_for_scrape)

            target_for_scrape = target_domain if search_option == "Recherche Basée sur Domaine" else None

            with ThreadPoolExecutor(max_workers=3) as executor:
                future_to_item = {executor.submit(scrape_worker, item, target_for_scrape): item for item in unique_serp}
                
                for future in as_completed(future_to_item):
                    item = future_to_item[future]
                    url = item['link']
                    try:
                        processed_emails, title, status_code = future.result(timeout=30)
                        if processed_emails:
                            provenance = get_provenance(item['dork'])
                            current_time = datetime.now().isoformat()
                            http_status = str(status_code) if status_code else "N/A"
                            for p_email in processed_emails:
                                mx_valid = p_email['mx_valid']
                                confidence = 0.1 + (0.3 if mx_valid == "Oui" else 0)
                                all_data.append({
                                    'Emails': p_email['email'],
                                    'URL': url,
                                    'Domaine': urlparse(url).netloc,
                                    'Source Snippet': item['snippet'],
                                    'Page Title': title,
                                    'Date Trouvée': current_time,
                                    'HTTP Status': http_status,
                                    'Méthode': "Serper + Scraping",
                                    'Provenance': provenance,
                                    'MX Valide': mx_valid,
                                    'Confiance': round(confidence, 2)
                                })
                    except Exception as e:
                        failed_urls.append(url)
                        st.error(f"Erreur lors du scraping de {url}: {e}")
                    
                    time.sleep(1)  # Throttling entre scrapings
                    
                    completed += 1
                    progress.progress(completed / total_urls)
                    status_text.text(f'Progression : {completed}/{total_urls} URLs traitées')
                    time.sleep(0.5)  # Backoff global

            progress.empty()
            status_text.empty()
            
            if failed_urls:
                st.write(f"URLs échouées : {failed_urls}")
            
            if all_data:
                st.write("### Emails Trouvés :")
                
                # Créer DataFrame et dédupliquer
                email_df = pd.DataFrame(all_data)
                email_df = email_df.drop_duplicates(subset="Emails", keep="first")
                email_df = email_df.sort_values('Confiance', ascending=False)
                
                # Afficher les résultats
                st.dataframe(email_df, width='stretch')
                
                # Export CSV
                csv = email_df.to_csv(index=False)
                st.download_button(
                    label="📥 Télécharger CSV",
                    data=csv,
                    file_name="emails_trouves.csv",
                    mime="text/csv"
                )
            else:
                st.write("Aucun email trouvé dans les résultats.")
