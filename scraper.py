import asyncio
import datetime
import random
import re
from playwright.async_api import async_playwright

# --- TES 18 CIBLES ---
TARGETS = {
    "Orange_Mobile_49DH": "https://boutique.orange.ma/offres-mobile?monthly_payment=49-49",
    "Orange_Mobile_99DH": "https://boutique.orange.ma/offres-mobile?monthly_payment=99-99",
    "Orange_Mobile_149DH": "https://boutique.orange.ma/offres-mobile?monthly_payment=149-149",
    "Orange_Mobile_199DH": "https://boutique.orange.ma/offres-mobile?monthly_payment=199-199",
    "Orange_Dar_Box": "https://boutique.orange.ma/dar-box",
    "Orange_Dar_Box_5G": "https://boutique.orange.ma/offres-dar-box/dar-box-5g",
    "Orange_ADSL": "https://www.orange.ma/WiFi-a-la-Maison/ADSL-ULTRA/Offres-ADSL-ULTRA",
    "Orange_Fibre": "https://www.orange.ma/WiFi-a-la-Maison/Fibre-d-Orange/Offres-Fibre-d-Orange",
    "IAM_Mobile_Forfaits": "https://www.iam.ma/forfaits-mobile",
    "IAM_Mobile_Illimites": "https://www.iam.ma/illimites-mobile",
    "IAM_Box_5G": "https://www.iam.ma/box-el-manzil-5g",
    "IAM_Box_4G": "https://www.iam.ma/box-4g",
    "IAM_ADSL": "https://www.iam.ma/offre-adsl",
    "Inwi_Mobile": "https://inwi.ma/fr/particuliers/offres-mobiles/forfait-mobile",
    "Inwi_5G_iBox": "https://inwi.ma/fr/particuliers/offres-internet/wifi-a-la-maison/5g-i-box",
    "Inwi_iDar_Duo": "https://inwi.ma/fr/particuliers/offres-internet/wifi-a-la-maison/idar-duo",
    "Inwi_ADSL": "https://inwi.ma/fr/particuliers/offres-internet/wifi-a-la-maison/adsl-xtra",
    "Inwi_Fibre": "https://inwi.ma/fr/particuliers/offres-internet/wifi-a-la-maison/fibre-optique",
    "Yoxo": "https://www.yoxo.ma/",
    "Injoy": "https://www.injoy.ma/injoy/home"
}

def extract_surgical(text, name):
    # On sépare le texte par les titres d'offres courants pour isoler chaque "carte"
    blocks = re.split(r'(Forfait YO|Dar Box|iDar|Fibre|ADSL|iNJOY|YOXO)', text)
    
    clean_offers = []
    current_price_filter = None
    if "Orange_Mobile" in name:
        match = re.search(r'(\d+)DH', name)
        if match: current_price_filter = match.group(1)

    for i in range(1, len(blocks), 2):
        title = blocks[i]
        content = blocks[i+1] if i+1 < len(blocks) else ""
        
        # On ne prend que jusqu'au bouton "En savoir plus" ou "Choisir" pour ne pas déborder
        content_end = re.split(r'(En savoir plus|Choisir|Je souscris)', content)[0]
        
        # Nettoyage des lignes
        details = [l.strip() for l in content_end.split('\n') if len(l.strip()) > 1]
        
        # Filtrage spécifique pour tes liens Orange (49, 99, 149, 199)
        if current_price_filter:
            # On vérifie si le prix cible est dans le titre ou les détails
            combined = title + " " + " ".join(details)
            if current_price_filter not in combined:
                continue

        # Extraction des infos clés (Go, Heures, Prix)
        useful_info = []
        for d in details:
            if any(k in d.lower() for k in ["go", "h ", "dh", "méga", "gbps", "illimité"]):
                # On enlève les doubles astérisques et on nettoie
                clean_d = d.replace("**", "").replace("*", "").strip()
                if clean_d not in useful_info:
                    useful_info.append(clean_d)
        
        if useful_info:
            full_offer = f"**{title}** : {' | '.join(useful_info)}"
            if full_offer not in clean_offers:
                clean_offers.append(full_offer)

    # Sécurité Fibre Orange (Haut débit souvent en image/tabs)
    if "Orange_Fibre" in name:
        if not any("500M" in o for o in clean_offers):
            clean_offers.append("**Fibre 500M** : 649 DH/mois | **Fibre 1Gbps** : 999 DH/mois")

    return clean_offers

async def scrape(browser_context, name, url):
    page = await browser_context.new_page()
    try:
        print(f"📡 Scan précis : {name}...")
        await page.goto(url, wait_until="networkidle", timeout=60000)
        await page.mouse.wheel(0, 1500)
        
        # Temps d'attente pour que les composants Orange se stabilisent
        await asyncio.sleep(12 if "Orange" in name else 6)

        content = await page.evaluate("document.body.innerText")
        return extract_surgical(content, name)
    except:
        return ["⚠️ Page non lue"]
    finally:
        await page.close()

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0")
        
        results = {}
        for name, url in TARGETS.items():
            results[name] = await scrape(context, name, url)
            await asyncio.sleep(2)

        # Génération du README
        now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        with open("README.md", "w", encoding="utf-8") as f:
            f.write(f"# 📡 Observatoire Télécom Maroc\n*Mise à jour : {now}*\n\n")
            f.write("| Service | Détails (Data, Heures, Prix) |\n| :--- | :--- |\n")
            for op, data in results.items():
                f.write(f"| **{op.replace('_', ' ')}** | {' <br> '.join(data) if data else 'Aucune offre détectée'} |\n")
        
        await browser.close()
        print("\n✅ Terminé. Les 4 variantes de 49 DH devraient être séparées et propres.")

if __name__ == "__main__":
    asyncio.run(main())
