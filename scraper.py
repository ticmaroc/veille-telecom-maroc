import json
import asyncio
import random
import datetime
from playwright.async_api import async_playwright

# --- TA CONFIGURATION ORIGINALE ---
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

KEYWORDS = ["DH", "Dhs", "Go", "GB", "Heure", "H", "Min", "Illimit", "Méga", "Gbps", "Mbps"]
EXCLUDE = ["brancher", "configurer", "Copyright", "Avenue", "technicien", "débrancher", "Huawei", "iPhone", "Samsung", "cookies"]

def filter_useful_info(text):
    lines = text.split('\n')
    useful = []
    for line in lines:
        line = line.strip()
        # On garde la ligne si elle contient un mot clé et qu'elle n'est pas trop longue (bruit)
        if any(k.lower() in line.lower() for k in KEYWORDS) and 1 < len(line) < 85:
            if not any(e.lower() in line.lower() for e in EXCLUDE):
                if line not in useful:
                    useful.append(line)
    return useful

async def human_interaction(page):
    """Simule des mouvements pour débloquer les sites difficiles"""
    for _ in range(2):
        x, y = random.randint(100, 500), random.randint(100, 500)
        await page.mouse.move(x, y)
    await page.mouse.wheel(0, 300)

async def scrape_page(context, name, url):
    page = await context.new_page()
    # Cache le fait qu'on est un robot
    await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    try:
        print(f"🔄 Scan de {name}...")
        # Orange et Yoxo sont très lents à charger leurs scripts de sécurité
        wait_time = 15 if "orange" in url or "yoxo" in url else 5
        
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await human_interaction(page)
        await asyncio.sleep(wait_time)

        raw_text = await page.evaluate("document.body.innerText")
        infos = filter_useful_info(raw_text)
        
        await page.close()
        return infos if infos else ["⚠️ Site chargé mais aucune offre détectée"]
            
    except Exception as e:
        await page.close()
        return [f"❌ Erreur de connexion"]

async def run_scraper():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=[
            '--disable-blink-features=AutomationControlled',
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        ])
        context = await browser.new_context(viewport={'width': 1280, 'height': 800})
        
        final_results = {}
        for name, url in TARGETS.items():
            final_results[name] = await scrape_page(context, name, url)
            # Petit délai pour ne pas spammer
            await asyncio.sleep(random.uniform(1, 3))

        # --- SAUVEGARDE JSON ---
        with open("last_state.json", "w", encoding='utf-8') as f:
            json.dump(final_results, f, ensure_ascii=False, indent=4)

        # --- MISE À JOUR DU README (TON TABLEAU RICHE) ---
        date_now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        with open("README.md", "w", encoding='utf-8') as f:
            f.write(f"# 📡 Observatoire Télécom Maroc\n")
            f.write(f"*Dernière mise à jour : {date_now}*\n\n")
            f.write("| Service / Offre | Détails Détectés (Prix, Go, Heures) |\n")
            f.write("| :--- | :--- |\n")
            
            for op, infos in final_results.items():
                # On nettoie le nom (ex: Orange_Mobile -> Orange Mobile)
                display_name = op.replace('_', ' ')
                # On joint les infos avec des <br> pour que le tableau soit lisible
                details = " <br> ".join(infos)
                f.write(f"| **{display_name}** | {details} |\n")
        
        print("\n✅ Terminé ! Le README contient maintenant toutes les infos brutes.")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_scraper())
