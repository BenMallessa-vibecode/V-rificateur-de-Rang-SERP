# 🕷️ Vérificateur de Rang SERP

Un **simple, gratuit** vérificateur SERP — sans publicités, sans CAPTCHA, juste des résultats.

## 🚀 Introduction à l'Application

**Vérificateur de Rang SERP** est un outil léger et sans fioritures pour suivre les **classements de recherche Google** en utilisant l'[API Serper.dev](https://serper.dev/). 

Cette application a été enrichie de nouvelles fonctionnalités pour une expérience utilisateur plus complète et multilingue. Elle inclut désormais des traductions en français pour l'interface utilisateur, facilitant l'accès pour les francophones. De plus, des outils avancés comme le clustering de mots-clés, l'Email Finder avec utilisation de dorks et validation MX, ainsi que des analyses SERP, Golden Keywords, Reviews et Google Maps, sont intégrés pour une analyse SEO approfondie.

🔹 **Pas de publicités. Pas de distractions. Pas de CAPTCHA agaçant.**  
🔹 **Récupération rapide et fiable des données SERP.**  
🔹 **Gratuit jusqu'à 2 500 requêtes/mois.**  
🔹 **Téléchargement des résultats au format CSV pour une analyse ultérieure.**  
🔹 **Interface multilingue avec support français.**

## 🔑 Obtenir Votre Clé API

Cette application utilise [Serper.dev](https://serper.dev/), une puissante API de recherche Google qui fournit **2 500 requêtes gratuites par mois** (aucune carte de crédit requise).

1. Allez sur **[Serper.dev](https://serper.dev/)**
2. Inscrivez-vous gratuitement
3. Copiez votre **clé API**
4. Collez-la dans la barre latérale

## 🎯 Fonctionnalités Principales

✅ **Suivi en temps réel des positions SERP** : Analysez les classements pour vos mots-clés avec des détails sur les 10 premiers résultats (titre, URL, extrait).  
✅ **Recherche par mot-clé, pays et langue** : Personnalisez vos requêtes pour des résultats géolocalisés.  
✅ **Clustering de mots-clés** : Groupez automatiquement les mots-clés similaires pour une optimisation SEO plus efficace.  
✅ **Email Finder** : Recherchez des adresses email en utilisant des dorks Google avancés, avec validation MX pour vérifier la délivrabilité des emails.  
✅ **Golden Keywords** : Identifiez les mots-clés à fort potentiel de conversion basés sur des analyses SERP réelles.  
✅ **Analyse SERP** : Obtenez des insights détaillés sur les résultats de recherche, incluant positions et concurrents.  
✅ **Reviews (Avis Google)** : Récupérez et analysez les avis pour des établissements via leur CID Google.  
✅ **Google Maps** : Intégrez des recherches locales pour explorer les classements sur cartes.  
✅ **Support de téléchargement CSV** : Exportez vos données pour une analyse externe.  
✅ **Interface simple et sans distractions** : Traduite en français pour une utilisation intuitive.

## 🛠️ Installation et Utilisation

### 1️⃣ Installer les Dépendances

Assurez-vous d'avoir **Python 3.8+** installé, puis exécutez :

```bash
pip install -r requirements.txt
```

### 2️⃣ Lancer l'Application

```bash
streamlit run 🕷️_SERP_Rank_Checker.py
```

### 3️⃣ Utilisation

1. **Obtenez une Clé API** : Inscrivez-vous sur Serper.dev pour obtenir une clé gratuite.
2. **Entrez Vos Paramètres** : Dans l'interface (en français), saisissez vos mots-clés, le domaine à suivre, le pays et la langue.
3. **Lancez la Recherche** : Cliquez sur "Vérifier les Classements" pour interroger l'API Google via Serper.dev.
4. **Explorez les Outils** : Utilisez les onglets pour le clustering de mots-clés, l'Email Finder (avec dorks et validation MX), Golden Keywords, Reviews, ou Google Maps.
5. **Analysez les Résultats** : Visualisez les positions SERP dans un tableau, et téléchargez en CSV si nécessaire.

L'outil utilise l'API Serper.dev pour simuler des recherches Google authentiques, en respectant les limites de taux (2 crédits par requête).

## 📦 Dépendances

Basé sur `requirements.txt` :

- `streamlit` : Framework pour l'interface web.
- `pandas` : Manipulation et export des données.
- `requests` : Requêtes HTTP vers l'API.
- `pycountry` : Gestion des pays et langues.
- `geonamescache` : Cache pour les noms géographiques.
- `beautifulsoup4` : Parsing HTML pour les extractions.
- `dnspython` : Validation MX pour les emails.

## 🤝 Contribution et Licence

### Contribution

Les contributions sont les bienvenues ! Pour contribuer :
1. Forkez le projet.
2. Créez une branche pour votre fonctionnalité (`git checkout -b feature/nouvelle-fonction`).
3. Committez vos changements (`git commit -m 'Ajout: nouvelle fonctionnalité'`).
4. Poussez vers la branche (`git push origin feature/nouvelle-fonction`).
5. Ouvrez une Pull Request.

Respectez le code existant et ajoutez des tests si possible.

### Licence

Ce projet est sous licence [MIT](LICENSE). Voir le fichier LICENSE pour plus de détails.

## 💡 Cas d'Usage Pratiques

- **SEO pour les Entreprises** : Suivez le classement de votre site web pour des mots-clés spécifiques dans votre pays cible.
- **Marketing Digital** : Analysez la concurrence et utilisez le clustering pour optimiser vos campagnes.
- **Prospection Commerciale** : Trouvez des emails valides avec l'Email Finder pour contacter des prospects.
- **Gestion d'Avis** : Analysez les reviews pour améliorer la réputation en ligne.
- **Études de Marché** : Utilisez Google Maps et SERP pour des insights locaux.

## 🛡️ Conseils d'Utilisation

- **Économisez Vos Crédits** : Limitez les requêtes à 100 résultats max par recherche.
- **Respectez les Limites API** : Surveillez votre consommation sur le dashboard Serper.dev.
- **Sécurité** : L'outil ne stocke pas votre clé API.
- **Améliorations** : Intégrez des visualisations avancées pour des graphiques de tendances.

Pour des questions, contactez via le lien dans l'app.
