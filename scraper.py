import json
import os
import asyncio
from playwright.async_api import async_playwright

# VOTRE LISTE D'URLS (B) - 17 CIBLES
TARGETS = {
    "Orange_Mobile": "https://boutique.orange.ma/offres-mobile",
    "Orange_DarBox": "https://boutique.orange.ma/dar-box",
    "Orange_DarBox_5G": "https://boutique.orange.ma/offres-dar-box/dar-box-5g",
    "Orange_ADSL": "https://www.orange.ma/WiFi-a-la-Maison/ADSL-ULTRA/Offres-ADSL-ULTRA",
    "Orange_Fibre": "https://www.orange.ma/WiFi-a-la-Maison/Fibre-d-Orange/Offres-Fibre-d-Orange",
    "Yoxo": "https://www.yoxo.ma/",
    "IAM_Mobile": "https://www.iam.ma/forfaits-mobile",
    "IAM_Illimites": "https://www.iam.ma/illimites-mobile",
    "IAM_Box_5G": "https://www.iam.ma/box-el-manzil-5g",
    "IAM_Box_4G": "https://www.iam.ma/box-4g",
    "IAM_ADSL": "https://www.iam.ma/offre-adsl",
    "Injoy": "https://www.injoy.ma/injoy/home",
    "Inwi_Mobile": "https://inwi.ma/fr/particuliers/offres-mobiles/forfait-mobile",
    "Inwi_5G_Box": "https://inwi.ma/fr/particuliers/offres-internet/wifi-a-la-maison/5g-i-box",
    "Inwi_Idar_Duo": "https://inwi.ma/fr/particuliers/offres-internet/wifi-a-la-maison/idar-duo",
    "Inwi_ADSL": "https://inwi.ma/fr/particuliers/offres-internet/wifi-a-la-maison/adsl-xtra",
    "Inwi_Fibre": "https://inwi.ma/fr/particuliers/offres-internet/wifi-a-la-maison/fibre-optique"
}

# Mots-clés pour ne garder que les offres
KEYWORDS = ["DH", "Dhs", "Go", "Gb", "Heure", "Illimit", "Internet", "Fibre", "ADSL", "Promotion", "Offre", "Smartphone", "Box"]

def filter_useful_info(text):
    lines = text.split('\n')
    useful_lines = []
    for line in lines:
        line = line.strip()
        # On filtre : la ligne doit avoir un mot-clé et être une vraie info (entre 5 et 200 caractères)
        if any(key.lower() in line.lower() for key in KEYWORDS) and 5 < len(line) < 200:
            if line not in useful_lines:
                useful_lines.append(line)
    return "\n".join(useful_lines)

async def run_scraper():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # On simule un navigateur Chrome classique sur Windows
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 800}
        )
        
        new_memory = {}

        for name, url in TARGETS.items():
            page = await context.new_page()
            try:
                print(f"Vérification de {name}...")
                # Timeout réglé à 30 secondes pour plus de rapidité
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(4) 
                
                # Petit scroll pour charger les éléments dynamiques
                await page.evaluate("window.scrollTo(0, 500)")
                await asyncio.sleep(2)

                raw_text = await page.evaluate("document.body.innerText")
                clean_text = filter_useful_info(raw_text)
                
                new_memory[name] = clean_text if clean_text else "Page vide ou format non reconnu"
                print(f"✅ {name} terminé.")
            except Exception as e:
                print(f"❌ Erreur sur {name} : {e}")
                new_memory[name] = "Lien momentanément inaccessible"
            await page.close()

        # Sauvegarde avec indent=4 pour que ce soit joli à lire sur GitHub
        with open("last_state.json", "w", encoding='utf-8') as f:
            json.dump(new_memory, f, ensure_ascii=False, indent=4)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_scraper())
