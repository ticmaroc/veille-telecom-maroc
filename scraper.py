import asyncio
import json
import re
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("🌐 Connexion à Orange.ma...")
        # On charge la page
        await page.goto("https://www.orange.ma/WiFi-a-la-Maison/Fibre-d-Orange/Offres-Fibre-d-Orange", wait_until="networkidle")
        
        # On récupère toutes les images venant du serveur d'assets
        images = await page.query_selector_all("img")
        
        extracted_data = []
        current_speed = None

        for img in images:
            src = await img.get_attribute("src") or ""
            if "orange-maroc.net" in src:
                filename = src.split('/')[-1]
                
                # 1. On détecte la vitesse (ex: 20go.svg)
                if "go.svg" in filename or "mega.svg" in filename:
                    match = re.search(r'(\d+)', filename)
                    if match:
                        current_speed = match.group(1)
                
                # 2. On détecte le prix (ex: 249dh.svg)
                elif "dh.svg" in filename:
                    match = re.search(r'(\d+)', filename)
                    if match and current_speed:
                        extracted_data.append({
                            "vitesse": f"{current_speed}M",
                            "prix": int(match.group(1)),
                            "devise": "DH"
                        })
                        current_speed = None # Reset pour la carte suivante

        # Nettoyage des doublons (le carrousel répète parfois les éléments)
        unique_offres = list({v['vitesse']: v for v in extracted_data}.values())
        # Tri par vitesse pour un rendu propre
        unique_offres.sort(key=lambda x: int(x['vitesse'].replace('M', '')))

        # --- RÉSULTAT FINAL ---
        final_output = {
            "operateur": "Orange",
            "service": "Fibre Optique",
            "offres": unique_offres
        }

        # Sauvegarde en JSON
        with open("last_state.json", "w", encoding="utf-8") as f:
            json.dump(final_output, f, indent=4, ensure_ascii=False)

        print("\n✅ SCRAPPING RÉUSSI !")
        print(json.dumps(final_output, indent=4))

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
