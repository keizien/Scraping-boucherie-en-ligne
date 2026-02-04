SCRAPING BOUCHERIE JANSSEN-CARRIER → WOOCOMMERCE

Ce projet permet de récupérer automatiquement le catalogue produits depuis l’API DigiCommerce,
de le traiter, puis de générer des fichiers compatibles WooCommerce (CSV, JSON, catégories),
avec gestion des images produits.


FONCTIONNALITÉS
- Récupération du catalogue via l’API DigiCommerce
- Traitement des catégories et produits
- Génération d’un CSV compatible WooCommerce
- Téléchargement des images produits depuis DigiCommerce
- Export des catégories
- Export JSON complet
- Résumé automatique du scraping


FICHIERS GÉNÉRÉS
- produits_woocommerce.csv : Import WooCommerce
- produits_complets.json : Données complètes
- categories.csv : Catégories WooCommerce
- images/ : Images produits téléchargées


PRÉREQUIS
- Python 3.9+
- Connexion internet
- Accès à une boutique DigiCommerce

Librairies nécessaires :
- requests


CONFIGURATION
Variables principales à adapter dans le script :

API_URL = https://api.digicommerce.be/v1/public/catalog
SHOP_SUID = VOTRE_SUID
LANGUAGE = fr

SITE_URL = https://votre-site-wordpress.com
WP_UPLOAD_PATH = /wp-content/uploads/2026/01/


UTILISATION
Lancer le script avec la commande :

python app.py

Le script :
1. Récupère les données depuis DigiCommerce
2. Traite les produits et catégories
3. Génère les fichiers CSV / JSON
4. Télécharge les images produits
5. Affiche un résumé final


IMPORT DANS WOOCOMMERCE
1. WooCommerce > Produits > Importer
2. Sélectionner produits_woocommerce.csv
3. Choisir le séparateur ;
4. Mapper les colonnes
5. Lancer l’import


GESTION DES IMAGES
- Les images sont téléchargées dans le dossier images/
- Elles peuvent être importées dans la médiathèque WordPress
- L’association image / produit peut être faite manuellement ou via un plugin


LIMITATIONS CONNUES
- Possibles doublons sur certains produits
- WooCommerce ne rattache pas automatiquement les images existantes
- Dépendance à la disponibilité de l’API DigiCommerce


AMÉLIORATIONS POSSIBLES
- Déduplication automatique des produits
- Association automatique des images côté WordPress
- Support multi-langue
- Gestion avancée des variations


AUTEUR
Projet réalisé dans le cadre d’un stage WordPress / WooCommerce
Scraping et automatisation du catalogue produits DigiCommerce
