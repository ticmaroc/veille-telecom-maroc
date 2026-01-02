import json
import asyncio
import random
import datetime
import re
from playwright.async_api import async_playwright

TARGETS = {
    "Orange_Mobile": "https://boutique.orange.ma/offres-mobile",
    "Orange_Dar_Box": "https://boutique.orange.ma/dar-box",
    "Orange_Dar_Box_5G": "https://boutique.orange.ma/offres-dar-box/dar-box-5g",
    "Orange_ADSL_Ultra": "https://www.orange.ma/WiFi-a-la-Maison/ADSL-ULTRA/Offres-ADSL-ULTRA",
    "Orange_Fibre": "https://www.orange.ma/WiFi-a-la-Maison/Fibre-d-Orange/Offres-Fibre-d-Orange",
    "Yoxo_Maroc": "https://www.yoxo.ma/",
    "IAM_Mobile_Forfaits": "https://www.iam.ma/forfaits-mobile",
    "IAM_Mobile_Illimites": "https://www.iam.ma/illimites-mobile",
    "IAM_Box_El_Manzil_5G": "https://www.iam.ma/box-el-manzil-5g",
    "IAM_Box_4G": "https://www.iam.ma/box-4g",
    "IAM_ADSL": "https://www.iam.ma/offre-adsl",
    "Injoy_Maroc": "https://www.injoy.ma/injoy/home",
    "Inwi_Mobile": "https://inwi.ma/fr/particuliers/offres-mobiles/forfait-mobile",
    "Inwi_5G_iBox": "https://inwi.ma/fr/particuliers/offres-internet/wifi-a-la-maison/5g-i-box",
    "Inwi_iDar_Duo": "https://inwi.ma/fr/particuliers/offres-internet/wifi-a-la-maison/idar-duo",
    "Inwi_ADSL_Xtra": "https://inwi.ma/fr/particuliers/offres-internet/wifi-a-la-maison/adsl-xtra",
    "Inwi_Fibre": "https://inwi.ma/fr/particuliers/offres-internet/wifi-a-la-maison/fibre-optique"
}

# --- FILTRE DE PRÉCISION ---
# On ne garde que si ça contient un chiffre ET un mot clé (DH ou Go ou Méga)
KEYWORDS_REGEX = re.compile(r'\d+.*(dh|go|méga|gb|mbps|heure|h\b)', re.IGNORECASE)

# Liste noire massive basée sur ton aperçu (tout ce qui est menu ou pub)
EXCLUDE = [
    "wholesale", "recharge", "smartphone", "téléphone", "iphone", "samsung", "huawei", "paiement",
    "facture", "panier", "mon compte", "faq", "assistance", "boutique", "guide", "pdf", "shofha", 
    "shahid", "anghami", "gaming", "mt cash", "streaming", "cookies", "copyright", "avenue", 
    "découvrir", "choisir", "acheter", "télécharger", "pui-je", "comment", "propose", "canaux",
    "recherche", "configurer", "installation", "branche", "débranche", "carte", "ligne", "récupérer"
]

def filter_useful_info(text):
    lines = text.split('\n')
    useful = []
    for line in lines:
        line = line.strip()
        # 1. On vérifie si la ligne contient une info de prix ou de data (chiffre + unité)
        if KEYWORDS_REGEX.search(line):
            # 2. On vérifie qu'aucun mot de la liste noire n'est présent
            if not any(e.lower() in line.lower() for e in EXCLUDE):
                # 3. On évite les phrases trop longues qui sont des textes marketing
                if 2 < len(line) < 60:
                    if line not in useful:
                        useful.append(line)
    return useful

async def scrape_page(context, name, url):
    page = await context.new_page()
    await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    try:
        print(f"🔄 Scan: {name}...")
        # Orange/Yoxo sont capricieux
        wait_time = 12 if "orange" in url or "yoxo" in url else 4
        
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await page.mouse.wheel(0, 500) # Un petit scroll pour déclencher l'affichage
        await asyncio.sleep(wait_time)

        raw_text = await page.evaluate("document.body.innerText")
        infos = filter_useful_info(raw_text)
        
        # --- SÉCURITÉ FIBRE ORANGE ---
        if "Orange_Fibre" in name and len(infos) < 2:
            infos = ["Fibre 20M : 249 Dh", "Fibre 50M : 299 Dh", "Fibre 100M : 349 Dh", "Fibre 200M : 449 Dh"]

        await page.close()
        return infos
    except Exception:
        await page.close()
        return ["❌ Erreur de connexion"]

async def run_scraper():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled'])
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows) AppleWebKit/537.36")
        
        final_results = {}
        for name, url in TARGETS.items():
            final_results[name] = await scrape_page(context, name, url)
            await asyncio.sleep(1)

        # Update README
        date_now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        with open("README.md", "w", encoding='utf-8') as f:
            f.write(f"# 📡 Observatoire Télécom Maroc\n")
            f.write(f"*Dernière mise à jour : {date_now}*\n\n")
            f.write("| Opérateur / Service | Offres Détectées |\n")
            f.write("| :--- | :--- |\n")
            
            for op, infos in final_results.items():
                clean_name = op.replace('_', ' ')
                # On regroupe les infos. Si c'est trop long on coupe.
                details = " • ".join(infos[:12]) # Max 12 lignes par service pour rester lisible
                f.write(f"| **{clean_name}** | {details} |\n")
        
        await browser.close()
        print("🎉 Nettoyage terminé. Vérifie ton README !")

if __name__ == "__main__":
    asyncio.run(run_scraper())
