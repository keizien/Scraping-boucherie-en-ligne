"""
Script de scraping pour la boucherie Janssen Carrier
Récupère les produits depuis l'API DigiCommerce et génère un CSV pour WooCommerce

Auteur: Généré par Antigravity
Date: 2026-01-22
"""

import requests
import csv
import json
import os
import sys
from datetime import datetime
from typing import Optional

# Configuration de l'encodage pour Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


# Configuration de l'API
API_URL = "https://api.digicommerce.be/v1/public/catalog"
SHOP_SUID = "uPuhejStsKNxeki5"
LANGUAGE = "fr"

SITE_URL = "https://boucheri.vds131.tmp-access.net"
WP_UPLOAD_PATH = "/wp-content/uploads/2026/01/"


def fetch_catalog_data() -> dict:
    """
    Récupère le catalogue complet depuis l'API DigiCommerce.
    
    Returns:
        dict: Les données complètes du catalogue
    """
    params = {
        "suid": SHOP_SUID,
        "lang": LANGUAGE,
        "delivery_method": "0"
    }
    
    print("🔄 Récupération des données depuis l'API DigiCommerce...")
    
    try:
        response = requests.get(API_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        print("✅ Données récupérées avec succès!")
        return data
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur lors de la récupération des données: {e}")
        raise


def extract_product_info(product: dict, category_name: str) -> dict:
    attribute = product.get("attribute", {})
    price = attribute.get("price", 0)
    promo_price = attribute.get("promo")

    sku = product.get("slug") or product.get("uniq", "")

    # ✅ Image = URL WordPress (PAS DigiCommerce)
    image_url = f"{SITE_URL}{WP_UPLOAD_PATH}{sku}.jpg"

    description = product.get("description", "") or ""

    allergens = product.get("allergens", [])
    allergen_names = ", ".join([a.get("name", "") for a in allergens]) if allergens else ""

    tags = product.get("tags", [])
    tag_names = ", ".join([t.get("name", "") for t in tags]) if tags else ""

    option_lists = product.get("option_lists", [])
    has_options = len(option_lists) > 0

    is_active = attribute.get("active", True)
    is_archived = attribute.get("archive", False)
    sold_out = attribute.get("sold_out", False)

    return {
        "sku": sku,
        "name": product.get("name", ""),
        "published": 1 if is_active and not is_archived else 0,
        "is_featured": 0,
        "visibility": "visible",
        "short_description": description,
        "description": description,
        "regular_price": price,
        "sale_price": promo_price if promo_price else "",
        "categories": category_name,
        "images": image_url,
        "stock_status": "outofstock" if sold_out else "instock",
        "manage_stock": 0,
        "tax_class": "",
        "weight": product.get("weight", ""),
        "tags": tag_names,
    }




def process_catalog(data: dict) -> list:
    """
    Traite le catalogue complet et extrait tous les produits.
    
    Args:
        data: Données brutes du catalogue
    
    Returns:
        list: Liste des produits traités
    """
    products = []
    
    # Traitement des catégories
    categories = data.get("categories", [])
    
    print(f"\n📦 Nombre de catégories trouvées: {len(categories)}")
    
    for category in categories:
        category_name = category.get("name", "Sans catégorie")
        category_products = category.get("products", [])
        
        print(f"  • {category_name}: {len(category_products)} produits")
        
        for product in category_products:
            product_info = extract_product_info(product, category_name)
            products.append(product_info)
    
    # Traitement des "bons plans" (produits mis en avant)
    good_deals = data.get("good_deals", {})
    
    # Produits favoris/mis en avant
    favorites = good_deals.get("favorite", [])
    if favorites:
        print(f"\n⭐ Produits favoris: {len(favorites)}")
        for product in favorites:
            category_slug = product.get("category_slug", "")
            # On essaie de trouver le nom de la catégorie
            cat_name = next(
                (c.get("name", "") for c in categories if c.get("slug") == category_slug),
                "Favoris"
            )
            product_info = extract_product_info(product, cat_name)
            product_info["is_featured"] = 1  # Marquer comme produit mis en avant
            
            # Éviter les doublons (le produit peut déjà être dans une catégorie)
            existing_skus = [p["sku"] for p in products]
            if product_info["sku"] not in existing_skus:
                products.append(product_info)
    
    # Produits en promo
    promos = good_deals.get("promo", [])
    if promos:
        print(f"🏷️  Produits en promo: {len(promos)}")
    
    return products


def download_images(products: list, output_dir: str = "images") -> None:
    os.makedirs(output_dir, exist_ok=True)
    print(f"\n📸 Téléchargement des images depuis DigiCommerce...")

    downloaded = 0
    skipped = 0
    errors = 0

    for product in products:
        image_url = product.get("images", "")
        if not image_url:
            skipped += 1
            continue

        sku = product.get("sku", "unknown")
        ext = ".jpg"
        if image_url.lower().endswith(".png"):
            ext = ".png"

        filepath = os.path.join(output_dir, f"{sku}{ext}")

        if os.path.exists(filepath):
            continue

        try:
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()

            with open(filepath, "wb") as f:
                f.write(response.content)

            downloaded += 1

        except Exception as e:
            errors += 1
            print(f"⚠️ Image échouée pour {sku}: {e}")

    print(f"✅ {downloaded} images téléchargées")
    print(f"⏭️ {skipped} produits sans image")
    print(f"❌ {errors} erreurs")




def export_to_woocommerce_csv(products: list, filename: str = "produits_woocommerce.csv") -> None:
    """
    Exporte les produits au format CSV compatible WooCommerce.
    
    Args:
        products: Liste des produits à exporter
        filename: Nom du fichier CSV de sortie
    """
    # Colonnes pour l'import WooCommerce
    # Voir: https://woocommerce.com/document/product-csv-importer-exporter/
    woo_columns = [
        "SKU",
        "Name",
        "Published",
        "Is featured?",
        "Visibility in catalog",
        "Short description",
        "Description",
        "Regular price",
        "Sale price",
        "Categories",
        "Images",
        "Stock status",
        "Manage stock?",
        "Tax class",
        "Weight (kg)",
        "Tags",
    ]
    
    print(f"\n📄 Export vers '{filename}'...")
    
    with open(filename, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")  # Point-virgule pour Excel FR
        writer.writerow(woo_columns)
        
        for product in products:
            row = [
                product.get("sku", ""),
                product.get("name", ""),
                product.get("published", 1),
                product.get("is_featured", 0),
                product.get("visibility", "visible"),
                product.get("short_description", ""),
                product.get("description", ""),
                product.get("regular_price", ""),
                product.get("sale_price", ""),
                product.get("categories", ""),
                product.get("images", ""),
                product.get("stock_status", "instock"),
                product.get("manage_stock", 0),
                product.get("tax_class", ""),
                product.get("weight", ""),
                product.get("tags", ""),
            ]
            writer.writerow(row)
    
    print(f"  ✅ {len(products)} produits exportés!")


def export_to_json(products: list, filename: str = "produits_complets.json") -> None:
    """
    Exporte les produits au format JSON (données complètes).
    
    Args:
        products: Liste des produits à exporter
        filename: Nom du fichier JSON de sortie
    """
    print(f"\n📄 Export JSON vers '{filename}'...")
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    
    print(f"  ✅ {len(products)} produits exportés en JSON!")


def export_categories(data: dict, filename: str = "categories.csv") -> None:
    """
    Exporte les catégories au format CSV pour WooCommerce.
    
    Args:
        data: Données du catalogue
        filename: Nom du fichier CSV de sortie
    """
    categories = data.get("categories", [])
    
    print(f"\n📁 Export des catégories vers '{filename}'...")
    
    with open(filename, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["Name", "Slug", "Description", "Image"])
        
        for cat in categories:
            media = cat.get("media", {})
            image_url = media.get("large_picture", "") or media.get("medium_picture", "")
            
            row = [
                cat.get("name", ""),
                cat.get("slug", ""),
                cat.get("description", "") or "",
                image_url,
            ]
            writer.writerow(row)
    
    print(f"  ✅ {len(categories)} catégories exportées!")


def print_summary(products: list, data: dict) -> None:
    """
    Affiche un résumé du scraping.
    """
    categories = data.get("categories", [])
    
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DU SCRAPING")
    print("=" * 60)
    print(f"  • Nombre total de produits: {len(products)}")
    print(f"  • Nombre de catégories: {len(categories)}")
    
    # Statistiques par catégorie
    cat_stats = {}
    for p in products:
        cat = p.get("categories", "Sans catégorie")
        cat_stats[cat] = cat_stats.get(cat, 0) + 1
    
    print("\n  Produits par catégorie:")
    for cat, count in sorted(cat_stats.items(), key=lambda x: -x[1]):
        print(f"    - {cat}: {count}")
    
    # Prix min/max
    prices = [p.get("regular_price", 0) for p in products if p.get("regular_price")]
    if prices:
        print(f"\n  • Prix minimum: {min(prices):.2f}€")
        print(f"  • Prix maximum: {max(prices):.2f}€")
        print(f"  • Prix moyen: {sum(prices)/len(prices):.2f}€")
    
    print("=" * 60)


def main():
    """
    Fonction principale du script de scraping.
    """
    print("=" * 60)
    print("🥩 SCRAPING BOUCHERIE JANSSEN CARRIER")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Source: {API_URL}")
    print("=" * 60)
    
    # 1. Récupération des données
    data = fetch_catalog_data()
    
    # 2. Traitement des produits
    products = process_catalog(data)
    
    # 3. Export des fichiers
    export_to_woocommerce_csv(products)
    export_to_json(products)
    export_categories(data)
    
    # 4. Téléchargement des images (optionnel - décommenter si nécessaire)
    download_images(products)
    
    # 5. Résumé
    print_summary(products, data)
    
    print("\n✅ Scraping terminé avec succès!")
    print("\nFichiers générés:")
    print("  • produits_woocommerce.csv - Import WooCommerce")
    print("  • produits_complets.json - Données complètes")
    print("  • categories.csv - Catégories")
    print("\n💡 Pour importer dans WooCommerce:")
    print("   1. Allez dans WooCommerce > Produits > Importer")
    print("   2. Sélectionnez le fichier 'produits_woocommerce.csv'")
    print("   3. Choisissez le séparateur ';' (point-virgule)")
    print("   4. Mappez les colonnes et lancez l'import")


if __name__ == "__main__":
    main()
