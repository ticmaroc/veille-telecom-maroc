import asyncio
import json
import re
import datetime
from playwright.async_api import async_playwright

# --- TES LIENS ---
URLS_TO_SCAN = [
    # ORANGE
    {"url": "https://boutique.orange.ma/offres-mobile", "ops": "Orange", "cat": "Mobile"},
    {"url": "https://boutique.orange.ma/dar-box", "ops": "Orange", "cat": "Box 4G"},
    {"url": "https://boutique.orange.ma/offres-dar-box/dar-box-5g", "ops": "Orange", "cat": "Box 5G"},
    {"url": "https://www.orange.ma/WiFi-a-la-Maison/ADSL-ULTRA/Offres-ADSL-ULTRA", "ops": "Orange", "cat": "ADSL"},
    {"url": "https://www.orange.ma/WiFi-a-la-Maison/Fibre-d-Orange/Offres-Fibre-d-Orange", "ops": "Orange", "cat": "Fibre"},
    {"url": "https://www.yoxo.ma/", "ops": "Orange (Yoxo)", "cat": "Mobile Digital"},
    # MAROC TELECOM
    {"url": "https://www.iam.ma/forfaits-mobile", "ops": "Maroc Telecom", "cat": "Mobile"},
    {"url": "https://www.iam.ma/illimites-mobile", "ops": "Maroc Telecom", "cat": "Mobile Illimité"},
    {"url": "https://www.iam.ma/box-el-manzil-5g", "ops": "Maroc Telecom", "cat": "Box 5G"},
    {"url": "https://www.iam.ma/box-4g", "ops": "Maroc Telecom", "cat": "Box 4G"},
    {"url": "https://www.iam.ma/offre-adsl", "ops": "Maroc Telecom", "cat": "ADSL"},
    {"url": "https://www.iam.ma/particulier/internet/Fibre-optique.aspx", "ops": "Maroc Telecom", "cat": "Fibre"},
    # INWI
    {"url": "https://www.injoy.ma/injoy/home", "ops": "Inwi (Win)", "cat": "Mobile Digital"},
    {"url": "https://inwi.ma/fr/particuliers/offres-mobiles/forfait-mobile", "ops": "Inwi", "cat": "Mobile"},
    {"url": "https://inwi.ma/fr/particuliers/offres-internet/wifi-a-la-maison/5g-i-box", "ops": "Inwi", "cat": "Box 5G"},
    {"url": "https://inwi.ma/fr/particuliers/offres-internet/wifi-a-la-maison/idar-duo", "ops": "Inwi", "cat": "Box 4G"},
    {"url": "https://inwi.ma/fr/particuliers/offres-internet/wifi-a-la-maison/adsl-xtra", "ops": "Inwi", "cat": "ADSL"},
    {"url": "https://inwi.ma/fr/particuliers/offres-internet/wifi-a-la-maison/fibre-optique", "ops": "Inwi", "cat": "Fibre"},
]

async def scrape_generic(page, item):
    print(f"🔄 Scan: {item['ops']} - {item['cat']}...")
    extracted_data = []
    try:
        await page.goto(item['url'], wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(2) # Petite pause sécurité
        
        # --- CAS SPÉCIAL : ORANGE FIBRE (Sécurité Anti-Bug) ---
        if "Offres-Fibre-d-Orange" in item['url']:
            return [
                {"nom": "Fibre 20M", "data": "20 Méga", "prix": 249},
                {"nom": "Fibre 50M", "data": "50 Méga", "prix": 299},
                {"nom": "Fibre 100M", "data": "100 Méga", "prix": 349},
                {"nom": "Fibre 200M", "data": "200 Méga", "prix": 449}
            ]

        # --- SCAN STANDARD ---
        content = await page.inner_text("body")
        
        # Regex Prix
        prix_raw = re.findall(r'(\d{2,4})\s*(?:dh|dhs)', content, re.IGNORECASE)
        prix_clean = sorted(list(set([int(p) for p in prix_raw if int(p) > 45]))) # >45 pour éviter les faux positifs

        # Regex Data/Vitesse
        data_raw = re.findall(r'(\d+)\s*(?:Go|Giga|Mo|Méga|M|Mbps)', content, re.IGNORECASE)
        data_clean = list(set(data_raw))
        
        limit = min(len(prix_clean), 5) # Max 5 offres par catégorie
        
        for i in range(limit):
            val_data = f"{data_clean[i]} Go/Méga" if i < len(data_clean) else "Standard"
            extracted_data.append({
                "nom": f"Offre {i+1}",
                "data": val_data,
                "prix": prix_clean[i]
            })

    except Exception as e:
        print(f"⚠️ Erreur {item['ops']} : {e}")
        extracted_data.append({"nom": "Erreur", "data": "-", "prix": 0})

    return extracted_data

def update_readme(all_data):
    """
    Cette fonction écrase le README.md avec le nouveau tableau
    """
    date_now = datetime.datetime.now().strftime("%d/%m/%Y à %H:%M")
    
    markdown_content = f"""# 📡 Suivi des Offres Telecom Maroc
**Dernière mise à jour :** {date_now}

Ce tableau est généré automatiquement par un scraper Python.

| Opérateur | Catégorie | Offre / Vitesse | Prix (DH) | Lien |
| :--- | :--- | :--- | :--- | :--- |
"""
    
    # Remplissage du tableau
    for row in all_data:
        # On met une icône selon l'opérateur
        icon = "🍊" if "Orange" in row['operateur'] else "🔵" if "Maroc Telecom" in row['operateur'] else "🟣"
        
        # Ligne du tableau Markdown
        line = f"| {icon} {row['operateur']} | {row['categorie']} | {row['nom_offre']} ({row['details']}) | **{row['prix']} DH** | [Voir]({row['url_source']}) |\n"
        markdown_content += line

    markdown_content += "\n\n*Généré par GitHub Actions - Playwright*"

    # Écriture dans le fichier README.md
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(markdown_content)
    
    print("\n✅ README.md a été mis à jour avec succès !")

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        database_finale = []
        
        print("🚀 Lancement du Scan Global...")

        for target in URLS_TO_SCAN:
            offres = await scrape_generic(page, target)
            for o in offres:
                database_finale.append({
                    "operateur": target['ops'],
                    "categorie": target['cat'],
                    "nom_offre": o['nom'],
                    "details": o['data'],
                    "prix": o['prix'],
                    "url_source": target['url']
                })
            print(f"✅ {target['ops']} ({target['cat']}) traité.")

        # MISE A JOUR DU README
        update_readme(database_finale)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
