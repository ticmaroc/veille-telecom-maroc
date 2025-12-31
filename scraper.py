import json
import asyncio
import re
from playwright.async_api import async_playwright

async def get_price_from_svg(page, url):
    """Utilise Playwright pour lire le contenu du SVG sans bibliothèque extra"""
    try:
        # On demande au navigateur d'aller chercher le contenu brut de l'image
        response = await page.request.get(url)
        if response.status == 200:
            content = await response.text()
            # On cherche un nombre suivi de DH (ex: 249 DH) dans le code XML du SVG
            match = re.search(r'(\d+)\s*(?:DH|dh)', content)
            if match:
                return f"{match.group(1)} DH"
    except:
        pass
    return "Prix non textuel"

async def scrape_orange_fibre(context):
    page = await context.new_page()
    results = []
    try:
        print("🌐 Accès à Orange Fibre...")
        await page.goto("https://www.orange.ma/WiFi-a-la-Maison/Fibre-d-Orange/Offres-Fibre-d-Orange", wait_until="networkidle", timeout=60000)
        
        # On cible les cartes que vous avez trouvées
        cards = await page.query_selector_all(".fibre-card")
        for card in cards:
            img = await card.query_selector("img")
            if img:
                alt = await img.get_attribute("alt")
                src = await img.get_attribute("src")
                
                # On transforme l'URL relative en URL complète si besoin
                if src.startswith('/'):
                    src = "https://www.orange.ma" + src
                
                # On va lire le code de l'image
                price = await get_price_from_svg(page, src)
                results.append(f"Orange Fibre {alt} : {price}")
        
        await page.close()
        return results
    except Exception as e:
        print(f"❌ Erreur Orange : {e}")
        await page.close()
        return ["⚠️ Orange Fibre : Erreur de lecture"]

async def run_scraper():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0...")
        
        # On lance le scan spécifique pour Orange
        orange_results = await scrape_orange_fibre(context)
        
        # On affiche le résultat dans les logs pour vérifier
        for res in orange_results:
            print(f"✅ Trouvé : {res}")

        # Sauvegarde simple pour test
        with open("last_state.json", "w", encoding='utf-8') as f:
            json.dump({"Orange_Fibre": orange_results}, f, ensure_ascii=False, indent=4)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_scraper())
