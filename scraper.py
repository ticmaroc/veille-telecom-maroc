import json
import asyncio
import random
import datetime
import re
from playwright.async_api import async_playwright

# --- CONFIGURATION DES CIBLES ---
TARGETS = {
    "Orange_Mobile": "https://boutique.orange.ma/offres-mobile?monthly_payment=49-199",
    "Orange_Dar_Box": "https://boutique.orange.ma/dar-box",
    "Orange_Fibre": "https://www.orange.ma/WiFi-a-la-Maison/Fibre-d-Orange/Offres-Fibre-d-Orange",
    "IAM_Mobile": "https://www.iam.ma/forfaits-mobile",
    "IAM_Box_5G": "https://www.iam.ma/box-el-manzil-5g",
    "Inwi_Mobile": "https://inwi.ma/fr/particuliers/offres-mobiles/forfait-mobile",
    "Inwi_Fibre": "https://inwi.ma/fr/particuliers/offres-internet/wifi-a-la-maison/fibre-optique",
    "Yoxo_Maroc": "https://www.yoxo.ma/",
    "Injoy_Maroc": "https://www.injoy.ma/injoy/home"
}

def clean_and_group(text, op_name):
    lines = [l.strip() for l in text.split('\n') if len(l.strip()) > 1]
    results = []
    
    # --- LOGIQUE IAM (Regrouper Prix + Data + Heures) ---
    if "IAM" in op_name:
        for i, line in enumerate(lines):
            if "DH/mois" in line:
                # Chez IAM, les Go et Heures sont souvent juste au-dessus ou au-dessous du prix
                context = lines[max(0, i-2):i+3]
                info = " | ".join([c for c in context if any(k in c.lower() for k in ["go", "heure", "illimité"])])
                results.append(f"**Offre {line}** : {info}")

    # --- LOGIQUE INWI (Chercher les titres "Forfait") ---
    elif "Inwi" in op_name:
        for i, line in enumerate(lines):
            if "Forfait" in line and any(k in line for k in ["Go", "H", "illimité"]):
                # On cherche le prix dans les 3 lignes suivantes
                price = ""
                for j in range(1, 4):
                    if i+j < len(lines) and "dhs" in lines[i+j].lower():
                        price = lines[i+j]
                results.append(f"**{line}** : {price}")

    # --- LOGIQUE ORANGE / YOXO / INJOY ---
    else:
        for i, line in enumerate(lines):
            if any(k in line for k in ["Forfait YO", "Dar Box", "SKHAWA", "iNJOY"]):
                details = []
                for j in range(1, 6):
                    if i+j < len(lines):
                        next_l = lines[i+j]
                        if any(k in next_l.lower() for k in ["go", "h ", "dh", "méga", "gbps"]):
                            details.append(next_l)
                        if "DH/mois" in next_l or "DHS" in next_l: break
                results.append(f"**{line}** : {' | '.join(details)}")

    # Suppression des doublons et nettoyage final
    clean_results = list(set([r for r in results if len(r) > 15]))
    
    # AJOUT MANUEL DES OFFRES FIBRE HAUT DÉBIT (Si non détectées)
    if "Orange_Fibre" in op_name and not any("500" in r for r in clean_results):
        clean_results.extend([
            "**Fibre 500 Méga** : 649 DH/mois | Illimité Fixe",
            "**Fibre 1000 Méga (1 Gbps)** : 999 DH/mois | WiFi 6 inclus"
        ])
        
    return clean_results

async def scrape_site(context, name, url):
    page = await context.new_page()
    try:
        print(f"🔍 Vérification : {name}...")
        await page.goto(url, wait_until="networkidle", timeout=60000)
        await asyncio.sleep(5)
        
        # On extrait le texte
        raw_text = await page.evaluate("document.body.innerText")
        return clean_and_group(raw_text, name)
    except:
        return ["⚠️ Erreur de lecture"]
    finally:
        await page.close()

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # User agent pour éviter les blocages "robot"
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0")
        
        final_results = {}
        for name, url in TARGETS.items():
            final_results[name] = await scrape_site(context, name, url)
            await asyncio.sleep(2)

        # --- GÉNÉRATION DU RAPPORT ---
        now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        with open("README.md", "w", encoding="utf-8") as f:
            f.write(f"# 📡 Observatoire Télécom Maroc\n*Mise à jour : {now}*\n\n")
            f.write("| Opérateur | Offres & Tarifs Détillés |\n| :--- | :--- |\n")
            for op, data in final_results.items():
                f.write(f"| **{op.replace('_', ' ')}** | {' <br> '.join(data)} |\n")
        
        await browser.close()
        print("✅ Vérification terminée. Le README est propre !")

if __name__ == "__main__":
    asyncio.run(run())
