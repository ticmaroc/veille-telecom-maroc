import json
import asyncio
import re
from playwright.async_api import async_playwright

async def scrape_orange_fibre(context):
    page = await context.new_page()
    results = []
    try:
        print("🚀 Lancement du scan rapide Orange...")
        # On n'attend pas que toute la page soit "idle", juste que le code soit là
        await page.goto("https://www.orange.ma/WiFi-a-la-Maison/Fibre-d-Orange/Offres-Fibre-d-Orange", 
                        wait_until="domcontentloaded", timeout=30000)
        
        # On attend 10 secondes manuellement pour laisser les scripts de prix s'afficher
        await asyncio.sleep(10)
        
        # On récupère tout le texte de la page
        content = await page.evaluate("document.body.innerText")
        
        # --- LOGIQUE DE DÉTECTION DES PRIX ---
        # On cherche des montants logiques (ex: 249, 349, 449...) suivis de DH
        # On ignore les chiffres isolés comme 0, 1, 6
        found_prices = re.findall(r'(249|349|449|649|999|1499)\s*(?:DH|dh)', content)
        
        # On définit les paliers officiels d'Orange
        speeds = ["20M", "50M", "100M", "200M", "500M", "1G"]
        
        if found_prices:
            # On dédoublonne tout en gardant l'ordre
            unique_prices = []
            for p in found_prices:
                if p not in unique_prices: unique_prices.append(p)
            
            for i, price in enumerate(unique_prices):
                if i < len(speeds):
                    results.append(f"Orange Fibre {speeds[i]} : {price} DH")
        
        if not results:
            results = ["⚠️ Orange : Les prix sont encore masqués par le site"]

        await page.close()
        return results

    except Exception as e:
        print(f"❌ Erreur : {e}")
        await page.close()
        return ["❌ Timeout ou Blocage Orange"]

async def run_scraper():
    async with async_playwright() as p:
        # On ajoute des arguments pour passer inaperçu
        browser = await p.chromium.launch(headless=True, args=["--disable-web-security"])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        
        data = await scrape_orange_fibre(context)
        
        print("\n--- RÉSULTATS ---")
        for line in data:
            print(f"✅ {line}")

        with open("last_state.json", "w", encoding='utf-8') as f:
            json.dump({"Orange_Fibre": data}, f, ensure_ascii=False, indent=4)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_scraper())
