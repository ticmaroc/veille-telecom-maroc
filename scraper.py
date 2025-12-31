import json
import asyncio
from playwright.async_api import async_playwright

# 1. Vos 17 cibles complètes
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

def filter_useful_info(text):
    lines = text.split('\n')
    useful = []
    for line in lines:
        line = line.strip()
        if any(k.lower() in line.lower() for k in KEYWORDS) and 1 < len(line) < 100:
            if line not in useful:
                useful.append(line)
    return useful

async def run_scraper():
    async with async_playwright() as p:
        # Initialisation du navigateur
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
        )
        
        final_results = {}
        print(f"🚀 Début du scan de {len(TARGETS)} pages...")

        for name, url in TARGETS.items():
            page = await context.new_page()
            try:
                print(f"🔍 Analyse : {name}")
                await page.goto(url, wait_until="networkidle", timeout=60000)
                
                # Attente pour laisser les prix s'afficher
                wait_time = 12 if any(x in url for x in ["yoxo", "orange", "injoy"]) else 7
                await asyncio.sleep(wait_time)
                
                # Scroll pour activer les éléments dynamiques
                await page.mouse.wheel(0, 1000)
                await asyncio.sleep(2)

                raw_text = await page.evaluate("document.body.innerText")
                final_results[name] = filter_useful_info(raw_text)
                print(f"✅ {name} OK")
            except Exception as e:
                final_results[name] = [f"⚠️ Erreur de chargement"]
                print(f"❌ Erreur sur {name}")
            await page.close()

        # Sauvegarde JSON
        with open("last_state.json", "w", encoding='utf-8') as f:
            json.dump(final_results, f, ensure_ascii=False, indent=4)

        # Mise à jour du Tableau de Bord (README.md)
        with open("README.md", "w", encoding='utf-8') as f:
            f.write("# 📡 Observatoire Télécom Maroc\n\n")
            f.write("| Offre / Service | Détails (Prix, Data, Vitesse) |\n")
            f.write("| :--- | :--- |\n")
            for op, infos in final_results.items():
                details = " <br> ".join(infos) if infos else "Rien détecté"
                f.write(f"| **{op.replace('_', ' ')}** | {details} |\n")
        
        await browser.close()
        print("📊 Tableau mis à jour !")

if __name__ == "__main__":
    asyncio.run(run_scraper())
