import json
import asyncio
import re
from playwright.async_api import async_playwright

async def scrape_orange_fibre(context):
    page = await context.new_page()
    results = []
    try:
        print("⚡ Accès rapide à Orange Fibre...")
        
        # On n'attend plus le réseau, on attend juste que le code de base soit là
        await page.goto("https://www.orange.ma/WiFi-a-la-Maison/Fibre-d-Orange/Offres-Fibre-d-Orange", 
                        wait_until="commit", timeout=30000)
        
        # On attend spécifiquement l'apparition des cartes fibre que tu as trouvées
        print("⏳ Attente du conteneur fibre...")
        await page.wait_for_selector(".fibre-cards-container", timeout=20000)
        
        # On laisse 2 secondes pour que les prix s'injectent
        await asyncio.sleep(2)

        # On arrache tout le code HTML des cartes
        cards_html = await page.inner_html(".fibre-cards-container")
        
        # On cherche les prix (ex: 249, 299, 349...) suivis de DH
        # On cherche dans le code source pour ne rien rater
        found_prices = re.findall(r'(\d{3,4})\s*DH', cards_html, re.IGNORECASE)
        
        # On dédoublonne tout en gardant l'ordre
        unique_prices = []
        for p in found_prices:
            if p not in unique_prices: unique_prices.append(p)
        
        # Correspondance avec les débits (On sait qu'ils sont dans l'ordre)
        speeds = ["20M", "50M", "100M", "200M", "500M", "1G"]
        
        for i, price in enumerate(unique_prices):
            if i < len(speeds):
                results.append(f"Orange Fibre {speeds[i]} : {price} DH")

        if not results:
            return ["⚠️ Code chargé mais prix invisibles (Lazy Loading)"]

        return results

    except Exception as e:
        return [f"❌ Erreur : {str(e)}"]
    finally:
        await page.close()

async def main():
    async with async_playwright() as p:
        # On utilise des arguments pour booster la vitesse
        browser = await p.chromium.launch(headless=True, args=["--disable-http2"])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        data = await scrape_orange_fibre(context)
        
        print("\n--- RÉSULTATS EXTRAITS ---")
        for line in data:
            print(f"✅ {line}")

        with open("last_state.json", "w", encoding='utf-8') as f:
            json.dump({"Orange": data}, f, ensure_ascii=False, indent=4)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
