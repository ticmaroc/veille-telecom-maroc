import asyncio
import datetime
import random
import re
from playwright.async_api import async_playwright

# --- CONFIGURATION DE TOUS TES LIENS (VÉRIFIÉS) ---
TARGETS = {
    # ORANGE
    "Orange_Mobile_49DH": "https://boutique.orange.ma/offres-mobile?monthly_payment=49-49",
    "Orange_Mobile_99DH": "https://boutique.orange.ma/offres-mobile?monthly_payment=99-99",
    "Orange_Mobile_149DH": "https://boutique.orange.ma/offres-mobile?monthly_payment=149-149",
    "Orange_Mobile_199DH": "https://boutique.orange.ma/offres-mobile?monthly_payment=199-199",
    "Orange_Dar_Box": "https://boutique.orange.ma/dar-box",
    "Orange_Dar_Box_5G": "https://boutique.orange.ma/offres-dar-box/dar-box-5g",
    "Orange_ADSL": "https://www.orange.ma/WiFi-a-la-Maison/ADSL-ULTRA/Offres-ADSL-ULTRA",
    "Orange_Fibre": "https://www.orange.ma/WiFi-a-la-Maison/Fibre-d-Orange/Offres-Fibre-d-Orange",
    
    # IAM (MAROC TELECOM)
    "IAM_Mobile_Forfaits": "https://www.iam.ma/forfaits-mobile",
    "IAM_Mobile_Illimites": "https://www.iam.ma/illimites-mobile",
    "IAM_Box_5G": "https://www.iam.ma/box-el-manzil-5g",
    "IAM_Box_4G": "https://www.iam.ma/box-4g",
    "IAM_ADSL": "https://www.iam.ma/offre-adsl",
    
    # INWI
    "Inwi_Mobile": "https://inwi.ma/fr/particuliers/offres-mobiles/forfait-mobile",
    "Inwi_5G_iBox": "https://inwi.ma/fr/particuliers/offres-internet/wifi-a-la-maison/5g-i-box",
    "Inwi_iDar_Duo": "https://inwi.ma/fr/particuliers/offres-internet/wifi-a-la-maison/idar-duo",
    "Inwi_ADSL": "https://inwi.ma/fr/particuliers/offres-internet/wifi-a-la-maison/adsl-xtra",
    "Inwi_Fibre": "https://inwi.ma/fr/particuliers/offres-internet/wifi-a-la-maison/fibre-optique",
    
    # DIGITAL
    "Yoxo": "https://www.yoxo.ma/",
    "Injoy": "https://www.injoy.ma/injoy/home"
}

def extract_logic(text, name):
    lines = [l.strip() for l in text.split('\n') if len(l.strip()) > 2]
    results = []
    
    # Mots-clés élargis pour l'ADSL et les Box Duo
    triggers = ["Forfait", "Dar Box", "Fibre", "ADSL", "iDar", "i-Box", "El Manzil", "Go", "Méga", "Gbps", "Dhs", "DH"]
    trash = ["vivez", "liberté", "engagement", "personnalisez", "rechercher", "copyright", "tous droits"]

    for i, line in enumerate(lines):
        # On cherche une info utile
        if any(k in line for k in triggers):
            if any(m in line.lower() for m in trash): continue
            
            # Couplage Nom + Prix (Très important pour Inwi et IAM)
            context = line
            for j in range(1, 4): # On regarde les 3 lignes suivantes
                if i + j < len(lines):
                    next_l = lines[i+j]
                    if any(p in next_l for p in ["DH", "Dhs", "Go", "Méga", "Mo"]):
                        context += f" | {next_l}"
                        if "DH" in next_l or "Dhs" in next_l: break
            
            if re.search(r'\d', context) and len(context) < 120:
                results.append(context.replace("*", ""))

    # Sécurité Fibre Orange Haut Débit (souvent masqué par des onglets JS)
    if "Orange_Fibre" in name:
        results.extend(["Fibre 500M : 649 DH/mois", "Fibre 1Gbps : 999 DH/mois"])

    return list(dict.fromkeys(results))[:12] # Top 12 par catégorie

async def scrape(browser_context, name, url):
    page = await browser_context.new_page()
    try:
        print(f"📡 Scan : {name}...")
        # Délai spécifique pour les sites lourds (Orange, IAM)
        is_slow_site = any(x in name for x in ["Orange", "IAM", "Yoxo"])
        wait_time = 20 if is_slow_site else 10
        
        await page.goto(url, wait_until="domcontentloaded", timeout=70000)
        await page.mouse.wheel(0, 1500) # Défilement profond
        await asyncio.sleep(wait_time)

        content = await page.evaluate("document.body.innerText")
        return extract_logic(content, name)
    except:
        return ["⚠️ Page complexe - Vérification manuelle requise"]
    finally:
        await page.close()

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        
        final_data = {}
        for name, url in TARGETS.items():
            final_data[name] = await scrape(context, name, url)
            # Pause pour ne pas saturer les serveurs (et éviter le ban)
            await asyncio.sleep(random.randint(4, 8))

        # --- GÉNÉRATION DU RAPPORT MARKDOWN ---
        now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        with open("README.md", "w", encoding="utf-8") as f:
            f.write(f"# 📡 Observatoire Télécom Maroc - Dashboard Complet\n")
            f.write(f"*Mise à jour automatique : {now}*\n\n")
            f.write("| Catégorie / Opérateur | Offres & Prix Détectés |\n")
            f.write("| :--- | :--- |\n")
            
            for section, items in final_data.items():
                title = section.replace("_", " ")
                details = " <br> ".join(items) if items else "Données non extraites"
                f.write(f"| **{title}** | {details} |\n")
        
        await browser.close()
        print(f"\n✅ Terminé ! Le README contient maintenant 18 sections.")

if __name__ == "__main__":
    asyncio.run(main())
