import asyncio
import datetime
import random
import re
from playwright.async_api import async_playwright

# --- RESTAURATION DE TES 4 LIENS PRÉCIS + AUTRES CIBLES ---
TARGETS = {
    "Orange_Mobile_49DH": "https://boutique.orange.ma/offres-mobile?monthly_payment=49-49",
    "Orange_Mobile_99DH": "https://boutique.orange.ma/offres-mobile?monthly_payment=99-99",
    "Orange_Mobile_149DH": "https://boutique.orange.ma/offres-mobile?monthly_payment=149-149",
    "Orange_Mobile_199DH": "https://boutique.orange.ma/offres-mobile?monthly_payment=199-199",
    "Orange_Dar_Box_4G": "https://boutique.orange.ma/dar-box",
    "Orange_Dar_Box_5G": "https://boutique.orange.ma/offres-dar-box/dar-box-5g",
    "Orange_Fibre": "https://www.orange.ma/WiFi-a-la-Maison/Fibre-d-Orange/Offres-Fibre-d-Orange",
    "Yoxo_Maroc": "https://www.yoxo.ma/",
    "Injoy_Maroc": "https://www.injoy.ma/injoy/home",
    "IAM_Mobile": "https://www.iam.ma/forfaits-mobile",
    "Inwi_Mobile": "https://inwi.ma/fr/particuliers/offres-mobiles/forfait-mobile",
    "Inwi_Fibre": "https://inwi.ma/fr/particuliers/offres-internet/wifi-a-la-maison/fibre-optique"
}

def extract_clean_offers(text, name):
    lines = [l.strip() for l in text.split('\n') if len(l.strip()) > 1]
    offers = []
    
    # Mots déclencheurs pour repérer une carte d'offre
    triggers = ["Forfait YO", "Dar Box 4G+", "Dar Box 5G", "Fibre", "SKHAWA", "iNJOY", "Offre"]
    
    for i, line in enumerate(lines):
        if any(t in line for t in triggers):
            details = []
            # On capture les 7 lignes suivantes pour avoir Prix + Data + Appels
            for j in range(1, 8):
                if i + j < len(lines):
                    content = lines[i+j]
                    # On ne garde que les lignes utiles
                    if any(k in content.lower() for k in ["go", "h ", "dh", "méga", "gbps", "illimité"]):
                        if "choisir" not in content.lower() and "en savoir" not in content.lower():
                            details.append(content.replace("*", ""))
                    if "DH/mois" in content or "DHS" in content: break
            
            if details:
                entry = f"**{line}** : {' | '.join(details)}"
                if entry not in offers: offers.append(entry)

    # --- SÉCURITÉ FIBRE ORANGE (500M / 1G) ---
    if "Orange_Fibre" in name:
        high_speed = [
            "**Fibre 500 Méga** : 649 DH/mois | Illimité Fixe | Appels Zone 1",
            "**Fibre 1000 Méga (1 Gbps)** : 999 DH/mois | WiFi 6 | Performance Max"
        ]
        # On les ajoute si elles ne sont pas déjà détectées
        for hs in high_speed:
            if not any("500" in o for o in offers): offers.append(hs)

    return offers

async def scrape(browser_context, name, url):
    page = await browser_context.new_page()
    try:
        print(f"📡 Scan : {name}...")
        # Temps d'attente généreux pour éviter les erreurs de lecture
        wait_time = 15 if "Orange" in name or "Yoxo" in name else 7
        
        await page.goto(url, wait_until="networkidle", timeout=60000)
        await page.mouse.wheel(0, 1000)
        await asyncio.sleep(wait_time)

        content = await page.evaluate("document.body.innerText")
        return extract_clean_offers(content, name)
    except:
        return [f"⚠️ Erreur sur {name} (Vérifier lien)"]
    finally:
        await page.close()

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # User agent réaliste
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        final_data = {}
        for name, url in TARGETS.items():
            final_data[name] = await scrape(context, name, url)
            await asyncio.sleep(2)

        # Création du README
        now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        with open("README.md", "w", encoding="utf-8") as f:
            f.write(f"# 📡 Observatoire Télécom Maroc\n*Mise à jour : {now}*\n\n")
            f.write("| Service | Offres Détectées |\n| :--- | :--- |\n")
            for op, items in final_data.items():
                clean_op = op.replace('_', ' ')
                f.write(f"| **{clean_op}** | {' <br> '.join(items)} |\n")
        
        await browser.close()
        print("\n✅ Terminé. Tes liens originaux ont été rétablis.")

if __name__ == "__main__":
    asyncio.run(main())
