import json
import os
import asyncio
from playwright.async_api import async_playwright

# Liste complète de vos liens (incluant l'ANRT)
TARGETS = {
    "Orange_Mobile": "https://boutique.orange.ma/offres-mobile",
    "Orange_DarBox": "https://boutique.orange.ma/dar-box",
    "Orange_DarBox_5G": "https://boutique.orange.ma/offres-dar-box/dar-box-5g",
    "Orange_ADSL": "https://www.orange.ma/WiFi-a-la-Maison/ADSL-ULTRA/Offres-ADSL-ULTRA",
    "Orange_Fibre": "https://www.orange.ma/WiFi-a-la-Maison/Fibre-d-Orange/Offres-Fibre-d-Orange",
    "Yoxo": "https://www.yoxo.ma/",
    "IAM_Forfaits": "https://www.iam.ma/forfaits-mobile",
    "IAM_Illimites": "https://www.iam.ma/illimites-mobile",
    "IAM_Box_5G": "https://www.iam.ma/box-el-manzil-5g",
    "IAM_Box_4G": "https://www.iam.ma/box-4g",
    "IAM_ADSL": "https://www.iam.ma/offre-adsl",
    "Injoy": "https://www.injoy.ma/injoy/home",
    "Inwi_Mobile": "https://inwi.ma/fr/particuliers/offres-mobiles/forfait-mobile",
    "Inwi_5G": "https://inwi.ma/fr/particuliers/offres-internet/wifi-a-la-maison/5g-i-box",
    "Inwi_iDar": "https://inwi.ma/fr/particuliers/offres-internet/wifi-a-la-maison/idar-duo",
    "Inwi_ADSL": "https://inwi.ma/fr/particuliers/offres-internet/wifi-a-la-maison/adsl-xtra",
    "Inwi_Fibre": "https://inwi.ma/fr/particuliers/offres-internet/wifi-a-la-maison/fibre-optique",
    "ANRT_Actu": "https://www.anrt.ma/actualites"
}

async def run_scraper():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # On charge l'ancienne mémoire
        if os.path.exists("last_state.json"):
            with open("last_state.json", "r") as f:
                memory = json.load(f)
        else:
            memory = {}

        new_memory = {}
        changes = []

        for name, url in TARGETS.items():
            page = await browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0")
            try:
                print(f"Vérification de {name}...")
                await page.goto(url, wait_until="networkidle", timeout=60000)
                # On extrait le texte principal (on évite les menus)
                content = await page.evaluate("document.body.innerText")
                clean_content = " ".join(content.split())[:5000] # Limite pour la comparaison
                
                if memory.get(name) and memory[name] != clean_content:
                    changes.append(f"🚨 CHANGEMENT DÉTECTÉ : {name}\nLien : {url}")
                
                new_memory[name] = clean_content
            except Exception as e:
                print(f"Erreur sur {name}: {e}")
            await page.close()

        # Sauvegarde de la nouvelle mémoire
        with open("last_state.json", "w") as f:
            json.dump(new_memory, f)

        if changes:
            print("\n".join(changes))
            # Ici, on pourra ajouter l'envoi vers Telegram plus tard
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_scraper())
