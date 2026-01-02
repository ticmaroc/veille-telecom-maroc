import json
import asyncio
import re
from playwright.async_api import async_playwright

async def scrape_orange_fibre(page):
    results = []
    try:
        print("🕵️ Analyse des composants visuels d'Orange...")
        await page.goto("https://www.orange.ma/WiFi-a-la-Maison/Fibre-d-Orange/Offres-Fibre-d-Orange", 
                        wait_until="domcontentloaded", timeout=30000)
        
        # On attend que les images soient chargées dans le carrousel
        await asyncio.sleep(8)

        # On récupère TOUTES les images de la page
        images = await page.query_selector_all("img")
        detected_prices = []

        for img in images:
            src = await img.get_attribute("src") or ""
            alt = await img.get_attribute("alt") or ""
            
            # On cherche des chiffres liés au prix dans le nom du fichier ou le texte alternatif
            # On cherche un pattern de 3 chiffres (ex: 249, 349...)
            match = re.search(r'(\d{3,4})', src)
            if match and ("dh" in src.lower() or "go" in src.lower() or "mega" in alt.lower()):
                price = match.group(1)
                if price not in detected_prices and int(price) > 100:
                    detected_prices.append(price)

        # On trie les prix du plus petit au plus grand
        detected_prices.sort(key=int)

        # On associe aux offres connues (20M, 50M, 100M...)
        speeds = ["20M", "50M", "100M", "200M", "500M", "1G"]
        for i, price in enumerate(detected_prices):
            if i < len(speeds):
                results.append(f"Orange Fibre {speeds[i]} : {price} DH")

        if not results:
            return ["⚠️ Aucun prix détecté dans les noms d'images."]

        return results

    except Exception as e:
        return [f"❌ Erreur : {str(e)}"]

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # On simule un écran large pour éviter le carrousel mobile qui cache des infos
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        data = await scrape_orange_fibre(page)
        
        print("\n=== RÉSULTATS DE LA VEILLE TELECOM ===")
        for line in data:
            print(f"✅ {line}")

        with open("last_state.json", "w", encoding='utf-8') as f:
            json.dump({"Orange": data}, f, ensure_ascii=False, indent=4)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
